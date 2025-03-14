from typing import Dict, List, Optional
from pydantic import BaseModel
import aiohttp
from datetime import datetime
from ..core.config import get_settings

settings = get_settings()

class OpenRouterService:
    """Service for handling OpenRouter API interactions and conversation management"""
    
    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1"
        self.api_key = settings.OPENROUTER_API_KEY
        self.default_model = settings.OPENROUTER_DEFAULT_MODEL or "anthropic/claude-2"  # Use configured model or fallback
        
    async def _make_request(self, endpoint: str, data: Dict) -> Dict:
        """Make authenticated request to OpenRouter API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://language-voyager.example.com",  # Required by OpenRouter
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/{endpoint}",
                json=data,
                headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ValueError(f"OpenRouter API error: {error_text}")
                return await response.json()

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
        
        all_messages = [system_msg] + messages
        
        data = {
            "model": model or self.default_model,
            "messages": all_messages,
            "temperature": temperature,
            "max_tokens": 1000,
        }
        
        return await self._make_request("chat/completions", data)

    def _build_system_prompt(self, context: Dict) -> str:
        """Build system prompt with relevant context"""
        poi_type = context.get("poi_type", "location")
        formality = context.get("formality_level", "neutral")
        dialect = context.get("dialect", "standard")
        difficulty = context.get("difficulty_level", 50)
        
        prompt = f"""You are a native {dialect} speaker helping someone learn the language. 
Current location: {poi_type}
Speaking style: {formality}
Difficulty level: {difficulty}/100

Guidelines:
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