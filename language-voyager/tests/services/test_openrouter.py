import pytest
from datetime import datetime
from app.services.openrouter import OpenRouterService
from app.routers.schemas.conversation import Message, ConversationContext

@pytest.mark.asyncio
async def test_openrouter_conversation():
    """Test conversation generation with OpenRouter API"""
    service = OpenRouterService()
    
    # Test conversation context
    context = {
        "poi_type": "train_station",
        "formality_level": "polite",
        "dialect": "standard",
        "difficulty_level": 50,
        "region_specific_customs": {
            "station_etiquette": "Stand in line, let others exit first"
        }
    }
    
    # Test messages
    messages = [
        {
            "role": "user",
            "content": "Can you help me ask where platform 4 is in Japanese?"
        }
    ]
    
    # Generate conversation
    response = await service.generate_conversation(
        messages=messages,
        context=context,
        temperature=0.7
    )
    
    # Verify response structure
    assert "choices" in response
    assert len(response["choices"]) > 0
    assert "message" in response["choices"][0]
    assert "content" in response["choices"][0]["message"]
    assert isinstance(response["choices"][0]["message"]["content"], str)
    
    # Verify response content relevance (should include Japanese and platform references)
    content = response["choices"][0]["message"]["content"].lower()
    assert any(word in content for word in ["platform", "番線", "ホーム", "4"])
    assert "polite" in service._build_system_prompt(context).lower()

@pytest.mark.asyncio
async def test_system_prompt_generation():
    """Test system prompt building with various contexts"""
    service = OpenRouterService()
    
    # Test formal setting
    formal_context = {
        "poi_type": "temple",
        "formality_level": "formal",
        "dialect": "standard",
        "difficulty_level": 75,
        "region_specific_customs": {
            "shoes": "Remove shoes before entering",
            "photos": "No photos inside temple buildings"
        }
    }
    
    formal_prompt = service._build_system_prompt(formal_context)
    assert "formal" in formal_prompt.lower()
    assert "temple" in formal_prompt.lower()
    assert "75/100" in formal_prompt
    assert "shoes" in formal_prompt.lower()
    assert "photos" in formal_prompt.lower()