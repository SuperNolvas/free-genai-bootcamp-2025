from comps import MicroService, ServiceOrchestrator, ServiceType, ServiceRoleType
from comps.cores.proto.api_protocol import ChatCompletionRequest, ChatCompletionResponse, ChatMessage, UsageInfo

import os

EMBEDDING_SERVICE_HOST_IP = os.getenv("EMBEDDING_SERVICE_HOST_IP", "0.0.0.0")
EMBEDDING_SERVICE_PORT = os.getenv("EMBEDDING_SERVICE_PORT", 6000)
OLLAMA_LLM_SERVICE_HOST_IP = os.getenv("OLLAMA_LLM_SERVICE_HOST_IP", "0.0.0.0")
OLLAMA_LLM_SERVICE_PORT = os.getenv("OLLAMA_LLM_SERVICE_PORT", 9000)


class ExampleService:
    def __init__(self, host="0.0.0.0", port=8000):
        self.host = host
        self.port = port
        self.endpoint = "/v1/chat/example-service"
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

        example = ExampleService()
        example.add_remote_service()
        example.start()
        example.megaservice.run()