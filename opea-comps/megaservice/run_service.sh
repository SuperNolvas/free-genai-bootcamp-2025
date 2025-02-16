#!/bin/bash

# Set environment variables
export OLLAMA_LLM_SERVICE_HOST_IP=0.0.0.0
export OLLAMA_LLM_SERVICE_PORT=11434

# Ensure Docker daemon is running
sudo systemctl start docker

# Remove any existing container with the same name
docker rm -f ollama_llm_service

# Run the Docker container using the ollama/ollama image
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# Print the status of the running container
docker ps -a | grep ollama