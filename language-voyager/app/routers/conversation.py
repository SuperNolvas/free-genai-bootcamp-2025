from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
from datetime import datetime
from ..database.config import get_db
from ..auth.utils import get_current_active_user
from ..models.user import User
from ..services.openrouter import OpenRouterService
from .schemas.conversation import ConversationRequest, ConversationResponse, Message
from ..core.schemas import ResponseModel

router = APIRouter(
    prefix="/conversation",
    tags=["conversation"],
    dependencies=[Depends(get_current_active_user)]
)

async def get_openrouter_service() -> OpenRouterService:
    return OpenRouterService()

@router.post("/chat", response_model=ResponseModel[ConversationResponse])
async def chat(
    request: ConversationRequest,
    current_user: User = Depends(get_current_active_user),
    llm_service: OpenRouterService = Depends(get_openrouter_service),
    db: Session = Depends(get_db)
) -> ResponseModel[ConversationResponse]:
    """Generate a context-aware conversation response"""
    try:
        # Format messages for OpenRouter API
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in request.messages
        ]
        
        # Get response from LLM
        response = await llm_service.generate_conversation(
            messages=api_messages,
            context=request.context.model_dump(),
            temperature=request.temperature,
            model=request.model
        )
        
        # Extract assistant's message
        assistant_message = Message(
            role="assistant",
            content=response["choices"][0]["message"]["content"],
            timestamp=datetime.utcnow()
        )
        
        # Parse response for corrections and cultural notes
        # This could be enhanced with more sophisticated parsing
        corrections = []
        cultural_notes = []
        message_content = assistant_message.content.lower()
        
        if "correction:" in message_content or "correct way to say:" in message_content:
            # Simple correction extraction
            corrections = [
                {"original": p.split(":")[0].strip(), "corrected": p.split(":")[1].strip()}
                for p in message_content.split("\n")
                if ":" in p and ("correction" in p.lower() or "correct way to say" in p.lower())
            ]
        
        if "cultural note:" in message_content or "in our culture" in message_content:
            # Simple cultural note extraction
            cultural_notes = [
                note.strip()
                for note in message_content.split("\n")
                if note.lower().startswith("cultural note:") or "in our culture" in note.lower()
            ]
        
        conversation_response = ConversationResponse(
            message=assistant_message,
            context=request.context,
            corrections=corrections or None,
            cultural_notes=cultural_notes or None
        )
        
        return ResponseModel(
            success=True,
            message="Conversation response generated successfully",
            data=conversation_response
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating conversation response: {str(e)}"
        )