import os

class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lyrics.db")
    OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "your_ollama_api_key")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "your_aws_access_key_id")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "your_aws_secret_access_key")
    BEDROCK_MODEL = os.getenv("BEDROCK_MODEL", "mistral-7b")
    INSTRUCTOR_MODEL = os.getenv("INSTRUCTOR_MODEL", "instructor-model-name")
    DUCKDUCKGO_API_URL = "https://api.duckduckgo.com/"