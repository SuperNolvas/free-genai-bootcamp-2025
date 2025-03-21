from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from datetime import datetime
import logging
from ..database.config import get_db
from ..auth.utils import get_current_active_user
from ..models.user import User
from ..services.openrouter import OpenRouterService
from ..services.location_manager import location_manager
from .schemas.conversation import ConversationRequest, ConversationResponse, Message
from ..core.schemas import ResponseModel
from fastapi.encoders import jsonable_encoder

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

router = APIRouter(
    prefix="/conversation",
    tags=["conversation"],
    dependencies=[Depends(get_current_active_user)]
)

openrouter_service = OpenRouterService()

async def get_openrouter_service() -> OpenRouterService:
    return OpenRouterService()

@router.post("/chat", response_model=ResponseModel[dict])
async def chat(
    messages: List[Message],
    context: Optional[Dict] = None
) -> ResponseModel[dict]:
    """Generate a conversation response using the LLM."""
    if context is None:
        context = {}

    # Include current location details in the context
    current_location_details = location_manager.get_current_location_details()
    if current_location_details:
        context["current_location"] = current_location_details

    try:
        # Convert Pydantic models to dict for serialization
        dict_messages = [jsonable_encoder(msg) for msg in messages]
        response = await openrouter_service.generate_conversation(dict_messages, context)
        return ResponseModel(
            success=True,
            message="Conversation response generated successfully",
            data=response
        )
    except Exception as e:
        logger.error(f"Error generating conversation response: {e}")
        return ResponseModel(
            success=False,
            message=f"Error generating conversation response: {str(e)}",
            data={}
        )