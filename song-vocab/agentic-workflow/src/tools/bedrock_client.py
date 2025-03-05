import boto3
import json
from config import Config

def get_bedrock_client():
    """Initialize and return a Bedrock client."""
    return boto3.client(
        'bedrock-runtime',
        aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
        region_name=Config.AWS_REGION
    )

def process_with_bedrock(text: str) -> str:
    """Process text using Amazon Bedrock's model."""
    client = get_bedrock_client()
    
    # Prepare the prompt
    body = {
        "prompt": f"\n\nHuman: Analyze these song lyrics and improve their formatting:\n{text}\n\nAssistant:",
        "max_tokens": 2000,
        "temperature": 0.7,
        "stop_sequences": ["\n\nHuman:"]
    }
    
    try:
        response = client.invoke_model(
            modelId=Config.BEDROCK_MODEL,
            body=json.dumps(body)
        )
        response_body = json.loads(response['body'].read())
        return response_body.get('completion', text)
    except Exception as e:
        print(f"Error processing with Bedrock: {e}")
        return text