from typing import Dict, List, Optional
import aiohttp
from datetime import datetime
import json
import logging
import os
from ..core.config import get_settings
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder

settings = get_settings()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Ensure debug logging is enabled

class OpenRouterService:
    """Service for handling OpenRouter API interactions and conversation management"""
    
    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1"
        self.api_key = settings.OPENROUTER_API_KEY
        self.default_model = settings.LLM_MODEL or "anthropic/claude-2"  # Use configured model or fallback
        
        if not self.api_key:
            logger.error("OpenRouter API key not found in environment variables")
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        
        logger.info(f"OpenRouter service initialized with model: {self.default_model}")

    def _serialize_messages(self, messages: List[Dict[str, str] | BaseModel]) -> List[Dict[str, str]]:
        """Serialize messages to JSON-compatible format"""
        return [
            jsonable_encoder(msg) if isinstance(msg, BaseModel) else msg
            for msg in messages
        ]

    async def _make_request(self, endpoint: str, data: Dict) -> Dict:
        """Make authenticated request to OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/language-voyager",  # More specific referer
            "X-Title": "Language Voyager",
            "Content-Type": "application/json"
        }
        
        logger.debug(f"Making request to OpenRouter with model: {data.get('model')}")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/{endpoint}",
                    json=data,
                    headers=headers,
                    ssl=True  # Ensure SSL verification is enabled
                ) as response:
                    response_text = await response.text()
                    logger.debug(f"OpenRouter response status: {response.status}")
                    logger.debug(f"OpenRouter response headers: {response.headers}")  # Add headers logging
                    
                    if response.status != 200:
                        try:
                            error_json = json.loads(response_text)
                            error_message = error_json.get('error', {}).get('message', response_text)
                            logger.error(f"OpenRouter API error: {error_message}")
                        except:
                            error_message = response_text
                        raise ValueError(f"OpenRouter API error: {error_message}")
                    
                    try:
                        return json.loads(response_text)
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON response from OpenRouter: {response_text}")
                        raise ValueError(f"Invalid JSON response from OpenRouter: {response_text}")
            except aiohttp.ClientError as e:
                logger.error(f"Network error when calling OpenRouter API: {str(e)}")
                raise ValueError(f"Network error when calling OpenRouter API: {str(e)}")
            except Exception as e:
                logger.error(f"Unexpected error calling OpenRouter API: {str(e)}")
                raise ValueError(f"Unexpected error calling OpenRouter API: {str(e)}")

    async def generate_conversation(
        self,
        messages: List[Dict[str, str]],
        context: Dict,
        temperature: float = 0.7,
        model: Optional[str] = None
    ) -> Dict:
        """Generate a conversation response with location and learning context"""
        
        # Add context to system message
        system_msg = {
            "role": "system",
            "content": self._build_system_prompt(context)
        }
        
        # Ensure messages are in the correct format
        formatted_messages = []
        for msg in messages:
            if isinstance(msg, dict):
                formatted_msg = {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                }
                formatted_messages.append(formatted_msg)
            else:
                formatted_msg = jsonable_encoder(msg)
                formatted_messages.append(formatted_msg)
        
        all_messages = [system_msg] + formatted_messages
        
        data = {
            "model": model or self.default_model,
            "messages": all_messages,
            "temperature": temperature,
            "max_tokens": 1000,
        }
        
        try:
            response = await self._make_request("chat/completions", data)
            
            # Ensure response is in the expected format
            if not response or "choices" not in response or not response["choices"]:
                raise ValueError("Invalid response format from OpenRouter API")
            
            assistant_message = response["choices"][0]["message"]
            return {
                "message": {
                    "role": "assistant",
                    "content": assistant_message["content"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
        except Exception as e:
            logger.error(f"Error in generate_conversation: {str(e)}")
            raise

    def _build_system_prompt(self, context: Dict) -> str:
        """Build system prompt with relevant context"""
        poi_type = context.get("poi_type", "location")
        formality = context.get("formality_level", "neutral")
        dialect = context.get("dialect", "standard")
        difficulty = context.get("difficulty_level", 50)
        current_location = context.get("current_location", {})
        
        prompt = f"""You are a native {dialect} speaker helping someone learn the language. 
Current location: {current_location.get('local_name', 'Unknown Location')}
Location type: {poi_type}
Speaking style: {formality}
Difficulty level: {difficulty}/100

Guidelines:
- When asked about the current location, use the Japanese name: {current_location.get('local_name')}
- Use appropriate formality for the location type
- Stay in character as a native speaker
- Maintain conversation difficulty around {difficulty}/100
- Use {dialect} dialect features when appropriate
- Natural conversations about this location type
- Correct major language errors gently
- Provide cultural context when relevant"""

        # Add location-specific custom rules
        customs = context.get("region_specific_customs", {})
        if customs:
            prompt += "\n\nLocal customs to consider:"
            for custom, desc in customs.items():
                prompt += f"\n- {custom}: {desc}"

        return prompt