## Opea Megaservice

### Utilise scaffold python code from documentation for Megaservice

https://opea-project.github.io/latest/GenAIComps/README.html#megaservice

### Refer to example usage 

https://github.com/opea-project/GenAIExamples/blob/main/ChatQnA/chatqna.py

### Working with Ollama_LLM container

The dockerfile needs work but the code does bring up Uvicorn running on http://0.0.0.0:8000

```json
{"detail":"Not Found"}
```
### Setup Ollama Docker Image shell script to pull image and run

```sh
#!/bin/bash

# Set environment variables
export OLLAMA_LLM_SERVICE_HOST_IP=0.0.0.0
export OLLAMA_LLM_SERVICE_PORT=9000

# Ensure Docker daemon is running
sudo systemctl start docker

# Remove any existing container with the same name
docker rm -f ollama_llm_service

# Run the Docker container using the ollama/ollama image
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Print the status of the running container
docker ps -a | grep ollama
```

### Install httpx service and also add to requirements
pip install httpx



