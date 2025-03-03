# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os

from comps import MegaServiceEndpoint, MicroService, ServiceOrchestrator, ServiceRoleType, ServiceType
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
CHATQNA_SERVICE_HOST_IP = os.getenv("CHATQNA_SERVICE_HOST_IP", "0.0.0.0")
CHATQNA_SERVICE_PORT = int(os.getenv("CHATQNA_SERVICE_PORT", 8888))

# TTS service configuration
TTS_SERVICE_HOST_IP = os.getenv("TTS_SERVICE_HOST_IP", "0.0.0.0")
TTS_SERVICE_PORT = int(os.getenv("TTS_SERVICE_PORT", 7055))

# Define input/output alignment functions
def align_inputs(source_output, target_input):
    """Align outputs from source to inputs for target.
    
    This function handles the data flow between microservices.
    """
    if source_output is None:
        return {}
        
    # When flowing from ChatQnA to TTS, we need to extract the text response
    if "choices" in source_output:
        # Extract text from ChatQnA response to send to TTS
        if len(source_output["choices"]) > 0:
            text = source_output["choices"][0]["message"]["content"]
            return {"text": text}
    
    return source_output

def align_outputs(output):
    """Standardize the output format from microservices."""
    return output


class ChatQnATTSService:
    """Megaservice that combines ChatQnA for text processing and TTS for audio conversion."""
    
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        
        # Setup the service orchestrator with alignment functions
        ServiceOrchestrator.align_inputs = align_inputs
        ServiceOrchestrator.align_outputs = align_outputs
        self.megaservice = ServiceOrchestrator()
        
        # Define a unique endpoint for this megaservice
        self.endpoint = "/v1/chatqna-tts"
    
    def add_remote_service(self):
        """Connect to the microservices and define the flow between them."""
        
        # ChatQnA service for text processing
        chatqna = MicroService(
            name="chatqna",
            host=CHATQNA_SERVICE_HOST_IP,
            port=CHATQNA_SERVICE_PORT,
            endpoint="/v1/chatqna",
            use_remote_service=True,
            service_type=ServiceType.MEGASERVICE,  # ChatQnA is itself a megaservice
        )
        
        # TTS service for audio conversion
        tts = MicroService(
            name="tts",
            host=TTS_SERVICE_HOST_IP,
            port=TTS_SERVICE_PORT,
            endpoint="/v1/tts",
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
        
        # Parse the incoming request as a ChatCompletion request
        chat_request = ChatCompletionRequest.parse_obj(data)
        prompt = handle_message(chat_request.messages)
        
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
            initial_inputs={"messages": prompt}, 
            llm_parameters=parameters,
            voice=data.get("voice", "default")  # Optional voice parameter
        )
        
        # Extract the final result from the TTS service
        last_node = runtime_graph.all_leaves()[-1]
        audio_response = result_dict[last_node]
        
        return audio_response
    
    def start(self):
        """Start the megaservice."""
        
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=ChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )
        
        # Add the route to handle requests
        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])
        
        # Start the service
        self.service.start()


if __name__ == "__main__":
    # Create and start the ChatQnA+TTS megaservice
    chatqna_tts = ChatQnATTSService(port=MEGA_SERVICE_PORT)
    chatqna_tts.add_remote_service()
    chatqna_tts.start()