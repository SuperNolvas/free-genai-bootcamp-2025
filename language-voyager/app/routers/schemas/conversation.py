from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import datetime

class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = None

class ConversationContext(BaseModel):
    poi_type: str
    formality_level: str
    dialect: str
    difficulty_level: float
    region_specific_customs: Optional[Dict[str, str]] = None

class ConversationRequest(BaseModel):
    messages: List[Message]
    context: ConversationContext
    temperature: Optional[float] = 0.7
    model: Optional[str] = None

class ConversationResponse(BaseModel):
    message: Message
    context: ConversationContext
    corrections: Optional[List[Dict[str, str]]] = None  # Language corrections if any
    cultural_notes: Optional[List[str]] = None  # Relevant cultural context