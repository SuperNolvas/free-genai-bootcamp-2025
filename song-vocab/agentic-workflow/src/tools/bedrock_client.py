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
    """Process text using Amazon Bedrock's Nova Micro model."""
    client = get_bedrock_client()
    
    # Create a more straightforward prompt for the model
    prompt = (
        "Task: Format the following song lyrics clearly, preserving line breaks and structure.\n\n"
        "Instructions:\n"
        "1. Remove any unnecessary metadata or headers\n"
        "2. Keep verse and chorus structure\n"
        "3. Preserve line breaks\n"
        "4. Format for readability\n\n"
        "Lyrics to format:\n\n"
        f"{text}\n\n"
        "Formatted lyrics:"
    )
    
    # Prepare the request body for Nova Micro
    body = {
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 2000,
            "temperature": 0.1,  # Lower temperature for more consistent formatting
            "topP": 1.0,
            "stopSequences": []
        }
    }
    
    try:
        response = client.invoke_model(
            modelId=Config.BEDROCK_MODEL,
            body=json.dumps(body)
        )
        response_body = json.loads(response['body'].read())
        
        # Handle the response and extract the formatted lyrics
        output = response_body.get('results', [{"outputText": text}])[0].get('outputText', text)
        
        # If we get an error message, return the original text
        if "unable to respond" in output.lower() or "sorry" in output.lower():
            return text
            
        return output.strip()
    except Exception as e:
        print(f"Error processing with Bedrock: {e}")
        return text