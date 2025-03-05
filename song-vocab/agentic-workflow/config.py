import os

class Config:
    # Database configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lyrics.db")
    
    # AWS/Bedrock configuration
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "your_aws_access_key_id")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "your_aws_secret_access_key")
    AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
    BEDROCK_MODEL = os.getenv("BEDROCK_MODEL", "amazon.titan-text-lite-v1")
    
    # Third-party API configuration
    DUCKDUCKGO_API_URL = "https://api.duckduckgo.com/"