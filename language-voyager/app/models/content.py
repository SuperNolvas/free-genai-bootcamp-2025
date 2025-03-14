from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Enum
from sqlalchemy.sql import func
import enum
from ..database.config import Base

class ContentType(str, enum.Enum):
    VOCABULARY = "vocabulary"
    PHRASE = "phrase"
    DIALOGUE = "dialogue"
    CULTURAL_NOTE = "cultural_note"

class LanguageContent(Base):
    __tablename__ = "language_content"
    
    id = Column(String, primary_key=True, index=True)  # Changed from Integer to String
    content_type = Column(String)  # Changed to String to match enum values directly
    language = Column(String)  # e.g., "japanese", "korean"
    region = Column(String)    # Geographic region relevance
    content = Column(JSON)     # Actual content with translations
    context_tags = Column(JSON) # e.g., ["restaurant", "formal", "greeting"]
    difficulty_level = Column(Float)  # 1-5 scale
    location_relevance = Column(String)  # Coordinates or area identifier
    vector_embedding = Column(JSON, nullable=True)  # For semantic search
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self) -> dict:
        """Convert the content to a dictionary format matching ContentItem schema"""
        return {
            "id": self.id,
            "content": self.content,
            "difficulty_level": self.difficulty_level,
            "content_type": self.content_type
        }