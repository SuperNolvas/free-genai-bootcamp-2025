# ChatQnA+TTS Megaservice

This megaservice combines two powerful microservices:
1. **ChatQnA**: A RAG-based question answering service that processes text queries by retrieving relevant information and generating responses
2. **TTS (Text-to-Speech)**: A service that converts text to spoken audio

## Architecture

The ChatQnA+TTS Megaservice orchestrates these two microservices to create an end-to-end pipeline:
1. User submits a text query
2. ChatQnA processes the query using RAG (Retrieval-Augmented Generation)
3. TTS converts ChatQnA's text response to audio
4. User receives an audio response to their original query

## Quick Start

### 1. Set Environment Variables

```bash
export host_ip=<your External Public IP>  # export host_ip=$(hostname -I | awk '{print $1}')

# ChatQnA service
export CHATQNA_SERVICE_HOST_IP=${host_ip}
export CHATQNA_SERVICE_PORT=8888

# TTS service
export TTS_SERVICE_HOST_IP=${host_ip}
export TTS_SERVICE_PORT=7055

# Megaservice port
export MEGA_SERVICE_PORT=8000
```

### 2. Run with Docker Compose

```bash
docker compose up -d
```

This will start all necessary services, including the underlying microservices needed by ChatQnA.

### 3. Test the Megaservice

```bash
curl http://${host_ip}:8000/v1/chatqna-tts \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "messages": "What is the revenue of Nike in 2023?",
    "max_tokens": 128,
    "voice": "default"
  }' \
  --output response.wav
```

The `voice` parameter is optional. Available options are:
- `"default"` (female voice)
- `"male"` (male voice)

The response will be a WAV file containing the spoken answer to your question.

## API Reference

### Endpoint

`POST /v1/chatqna-tts`

### Request Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| messages | string or array | The query to send to ChatQnA |
| max_tokens | integer | (Optional) Maximum number of tokens in the response |
| temperature | float | (Optional) Controls randomness of output |
| top_k | integer | (Optional) Number of top tokens to consider |
| top_p | float | (Optional) Cumulative probability threshold |
| voice | string | (Optional) Voice type: "default" or "male" |

### Response

The response is a binary audio file (WAV format) containing the spoken answer to the query.

## Deployment

The docker-compose.yaml file includes all necessary services:
- tei-embedding-server: For generating embeddings
- retriever-server: For retrieving relevant documents
- redis-vector-db: Vector database for document storage
- tei-reranking-server: For reranking retrieved results
- vllm-server: LLM service for generating responses
- speecht5-server: TTS service for converting text to speech
- chatqna-backend-server: The ChatQnA megaservice
- chatqna-tts-server: The ChatQnA+TTS megaservice

## Architecture Diagram

```
┌─────────────┐         ┌──────────────────────────────────────┐         ┌─────────────┐
│  User Input │────────▶│            ChatQnA Service           │────────▶│  TTS Service │
│   (Text)    │         │                                      │         │  (SpeechT5)  │
└─────────────┘         │ ┌─────────┐ ┌────────┐ ┌─────────┐   │         └──────┬──────┘
                        │ │Embedding│ │Retriever│ │Reranking│   │                │
                        │ └────┬────┘ └───┬────┘ └────┬────┘   │                │
                        │      │          │           │        │                │
                        │      └──────────┼───────────┘        │                │
                        │                 │                    │                │
                        │           ┌─────┴─────┐              │                │
                        │           │    LLM    │              │                │
                        │           └───────────┘              │                │
                        └──────────────────────────────────────┘                │
                                                                                │
                                                                        ┌───────▼──────┐
                                                                        │ User Output  │
                                                                        │   (Audio)    │
                                                                        └──────────────┘
```