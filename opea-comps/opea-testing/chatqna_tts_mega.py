# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import asyncio
from typing import Dict, Any, Optional
import aiohttp

from comps.cores.mega.micro_service import MicroService
from comps.cores.mega.orchestrator import ServiceOrchestrator
from comps.cores.mega.constants import ServiceRoleType, ServiceType
from comps.cores.mega.utils import handle_message
from comps.cores.proto.api_protocol import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from comps.cores.proto.docarray import LLMParams
from fastapi import Request
from fastapi.responses import StreamingResponse

# Environment variables configuration
MEGA_SERVICE_PORT = int(os.getenv("MEGA_SERVICE_PORT", 8000))

# ChatQnA service configuration
CHATQNA_SERVICE_HOST_IP = os.getenv("CHATQNA_SERVICE_HOST_IP", "chatqna-backend-server")
CHATQNA_SERVICE_PORT = int(os.getenv("CHATQNA_SERVICE_PORT", 80))

# TTS service configuration
TTS_SERVICE_HOST_IP = os.getenv("TTS_SERVICE_HOST_IP", "speecht5-server")
TTS_SERVICE_PORT = int(os.getenv("TTS_SERVICE_PORT", 7055))  # Updated to match actual speecht5 server port

# Define input/output alignment functions
def align_inputs(inputs: Dict[str, Any], target_node: str, 
                runtime_graph: Optional[Any] = None, 
                llm_parameters_dict: Optional[Dict[str, Any]] = None,
                **kwargs) -> Dict[str, Any]:
    """Align outputs from source to inputs for target.
    
    Args:
        inputs: Dictionary containing input data or response from previous service
        target_node: Name of the target service node
        runtime_graph: Optional runtime graph object
        llm_parameters_dict: Optional LLM parameters
        **kwargs: Additional keyword arguments including 'voice'
    
    Returns:
        Dict[str, Any]: Aligned inputs for the target service
    """
    if inputs is None or not isinstance(inputs, dict):
        return {}

    # Handle initial input to ChatQnA service
    if "messages" in inputs:
        return inputs
        
    # When flowing from ChatQnA to TTS, extract the text response
    if "choices" in inputs:
        if len(inputs["choices"]) > 0:
            text = inputs["choices"][0]["message"]["content"]
            # Include voice parameter if provided
            result = {"text": text}
            if "voice" in kwargs:
                result["voice"] = kwargs["voice"]
            return result
    
    return inputs

def align_outputs(output: Dict[str, Any], cur_node: str = None,
                 inputs: Optional[Dict[str, Any]] = None,
                 runtime_graph: Optional[Any] = None,
                 llm_parameters_dict: Optional[Dict[str, Any]] = None,
                 **kwargs) -> Dict[str, Any]:
    """Standardize the output format from microservices.
    
    Args:
        output: Output from the service to be aligned
        cur_node: Current node in service graph
        inputs: Original inputs
        runtime_graph: Runtime graph object
        llm_parameters_dict: LLM parameters
        **kwargs: Additional keyword arguments including 'voice'
    
    Returns:
        Dict[str, Any]: Standardized output
    """
    return output


class ChatQnATTSService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        
        # Setup the service orchestrator
        self.megaservice = ServiceOrchestrator()
        # Set alignment functions on the instance
        self.megaservice.align_inputs = align_inputs
        self.megaservice.align_outputs = align_outputs
        
        # Define a unique endpoint for this megaservice
        self.endpoint = "/v1/chatqna-tts"
    
    async def wait_for_service(self, name: str, host: str, port: int, max_retries: int = 10, delay: int = 5):
        """Wait for a service to become available.
        
        Args:
            name: Service name for logging
            host: Service host
            port: Service port
            max_retries: Maximum number of retry attempts
            delay: Delay between retries in seconds
        """
        print(f"[INFO] Checking {name} service at {host}:{port}")
        endpoints = {
            "ChatQnA": "/v1/chat/completions",
            "TTS": "/v1/audio/speech"
        }
        health_endpoint = endpoints.get(name, "/healthz")
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    url = f"http://{host}:{port}{health_endpoint}"
                    print(f"[INFO] Attempting to connect to {url}")
                    
                    # Use POST for TTS service with proper payload, GET for others
                    if name == "TTS":
                        # Send properly formatted payload for TTS using the OpenAI-compatible format
                        payload = {
                            "input": "test",
                            "voice": "default",
                            "response_format": "mp3"
                        }
                        async with session.post(url, json=payload) as response:
                            if response.status == 200:
                                print(f"[INFO] Successfully connected to {name}")
                                return True
                    else:
                        async with session.get(url) as response:
                            if response.status in [200, 404]:  # 404 is ok for POST-only endpoints
                                print(f"[INFO] Successfully connected to {name}")
                                return True
            except Exception as e:
                print(f"[WARN] Attempt {attempt + 1}/{max_retries} to connect to {name} failed: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"[INFO] Waiting {delay} seconds before retry...")
                    await asyncio.sleep(delay)
                continue
        print(f"[ERROR] Failed to connect to {name} service after {max_retries} attempts")
        return False

    def add_remote_service(self):
        """Connect to the microservices and define the flow between them."""
        
        # ChatQnA service for text processing
        chatqna = MicroService(
            name="chatqna",
            host=CHATQNA_SERVICE_HOST_IP,
            port=CHATQNA_SERVICE_PORT,
            endpoint="/v1/chat/completions",  # Updated to standard ChatGPT-style endpoint
            use_remote_service=True,
            service_type=ServiceType.GATEWAY,
        )
        
        # TTS service for audio conversion
        tts = MicroService(
            name="tts",
            host=TTS_SERVICE_HOST_IP,
            port=TTS_SERVICE_PORT,
            endpoint="/v1/audio/speech",  # Updated to standard TTS endpoint
            use_remote_service=True,
            service_type=ServiceType.TTS,
        )
        
        # Add services to the orchestrator
        self.megaservice.add(chatqna).add(tts)
        
        # Define the flow: ChatQnA output goes to TTS input
        self.megaservice.flow_to(chatqna, tts)
    
    async def handle_request(self, request: Request):
        """Handle incoming requests, process through ChatQnA, then through TTS."""
        
        data = await request.json()
        
        # Format messages as a list with role and content
        if isinstance(data["messages"], str):
            messages = [{"role": "user", "content": data["messages"]}]
        else:
            messages = data["messages"]
        
        # Parse the incoming request using model_validate
        chat_request = ChatCompletionRequest.model_validate({
            **data,
            "messages": messages
        })
        
        # Configure parameters for the LLM in ChatQnA service
        parameters = LLMParams(
            max_tokens=chat_request.max_tokens if chat_request.max_tokens else 1024,
            top_k=chat_request.top_k if chat_request.top_k else 10,
            top_p=chat_request.top_p if chat_request.top_p else 0.95,
            temperature=chat_request.temperature if chat_request.temperature else 0.01,
            frequency_penalty=chat_request.frequency_penalty if chat_request.frequency_penalty else 0.0,
            presence_penalty=chat_request.presence_penalty if chat_request.presence_penalty else 0.0,
            repetition_penalty=chat_request.repetition_penalty if chat_request.repetition_penalty else 1.03,
            stream=False,  # We can't stream when chaining to TTS
            chat_template=chat_request.chat_template if chat_request.chat_template else None,
        )
        
        # Schedule the execution of the service pipeline
        result_dict, runtime_graph = await self.megaservice.schedule(
            initial_inputs={"messages": messages},  # Pass formatted messages directly
            llm_parameters=parameters,
            voice=data.get("voice", "default")
        )
        
        # Extract the final result from the TTS service
        last_node = runtime_graph.all_leaves()[-1]
        audio_response = result_dict[last_node]
        
        return audio_response
    
    async def start(self):
        """Start the megaservice with service health checks."""
        
        # Wait for dependent services
        chatqna_ready = await self.wait_for_service(
            "ChatQnA", CHATQNA_SERVICE_HOST_IP, CHATQNA_SERVICE_PORT
        )
        tts_ready = await self.wait_for_service(
            "TTS", TTS_SERVICE_HOST_IP, TTS_SERVICE_PORT
        )
        
        if not (chatqna_ready and tts_ready):
            raise RuntimeError("Required services are not available")
        
        # Initialize the FastAPI app directly
        from fastapi import FastAPI
        app = FastAPI()
        
        # Configure CORS
        from fastapi.middleware.cors import CORSMiddleware
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Add the route to handle requests
        app.post(self.endpoint)(self.handle_request)
        
        return app

if __name__ == "__main__":
    import uvicorn
    import asyncio
    
    # Create the ChatQnA+TTS megaservice
    chatqna_tts = ChatQnATTSService(host="0.0.0.0", port=MEGA_SERVICE_PORT)
    chatqna_tts.add_remote_service()
    
    # Get the FastAPI app
    app = asyncio.run(chatqna_tts.start())
    
    # Run the FastAPI app with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=MEGA_SERVICE_PORT)