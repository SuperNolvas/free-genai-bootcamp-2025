from comps import MicroService, ServiceOrchestrator, ServiceType, ServiceRoleType
from comps.cores.proto.api_protocol import ChatCompletionRequest, ChatCompletionResponse, ChatMessage, UsageInfo

import os
import httpx
from fastapi import FastAPI, HTTPException

EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = os.getenv("EMBEDDING_SERVICE_PORT", 6000)
OLLAMA_LLM_SERVICE_HOST_IP = os.getenv("OLLAMA_LLM_SERVICE_HOST_IP", "0.0.0.0")
OLLAMA_LLM_SERVICE_PORT = os.getenv("OLLAMA_LLM_SERVICE_PORT", 11434)

app = FastAPI()

class ExampleService:
    def __init__(self, host="0.0.0.0", port=8000):
        print('hello')
        os.environ["TELEMETRY_ENDPOINT"] = ""
        self.host = host
        self.port = port
        self.endpoint = "/v1/example-service"
        self.megaservice = ServiceOrchestrator()

    def add_remote_service(self):
        embedding = MicroService(
            name="embedding",
            host=EMBEDDING_SERVICE_HOST_IP,
            port=EMBEDDING_SERVICE_PORT,
            endpoint="/v1/embeddings",
            use_remote_service=True,
            service_type=ServiceType.EMBEDDING,
        )
        ollama_llm = MicroService(
            name="ollama_llm",
            host=OLLAMA_LLM_SERVICE_HOST_IP,
            port=OLLAMA_LLM_SERVICE_PORT,
            endpoint="/v1/chat/completions",
            use_remote_service=True,
            service_type=ServiceType.LLM,
        )
        #attempting to add the services to the orchestrator
        self.megaservice.add(embedding).add(ollama_llm)
        self.megaservice.flow_to(embedding, ollama_llm)

    def start(self):
        self.service = MicroService(
            self.__class__.__name__,
            service_role=ServiceRoleType.MEGASERVICE,
            host=self.host,
            port=self.port,
            endpoint=self.endpoint,
            input_datatype=ChatCompletionRequest,
            output_datatype=ChatCompletionResponse,
        )

        self.service.add_route(self.endpoint, self.handle_request, methods=["POST"])

        self.service.start()

    async def handle_request(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        try:
            # Format the request for Ollama
            ollama_request = {
                "model": request.model or "llama3.2:1b",  # or whatever default model you're using
                "messages": [
                    {
                        "role": "user",
                        "content": request.messages  # assuming messages is a string
                    }
                ],
                "stream": False  # disable streaming for now
            }
            
            # Send the request to the Ollama service
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"http://{OLLAMA_LLM_SERVICE_HOST_IP}:{OLLAMA_LLM_SERVICE_PORT}/v1/chat/completions",
                    json=ollama_request
                )
                response.raise_for_status()
                result = response.json()
            
            # Extract the actual content from the response
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "No response content available")

            # Create the response
            response = ChatCompletionResponse(
                model=request.model or "example-model",
                choices=[
                    ChatCompletionResponseChoice(
                        index=0,
                        message=ChatMessage(
                            role="assistant",
                            content=content
                        ),
                        finish_reason="stop"
                    )
                ],
                usage=UsageInfo(
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0
                )
            )
            
            return response
            
        except Exception as e:
            # Handle any errors
            raise HTTPException(status_code=500, detail=str(e))

example = ExampleService()
example.add_remote_service()
example.start()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Opea Megaservice"}

@app.get("/favicon.ico")
async def favicon():
    return {"message": "Favicon not found"}