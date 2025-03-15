from sqlalchemy import Column, String, Integer, JSON, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database.config import Base
import uuid

class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)  # Changed to Integer
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Changed to Integer
    type = Column(String, nullable=False)  # 'location', 'language', 'milestone'
    achievement_id = Column(String, nullable=False)  # reference to achievement definition
    points = Column(Integer, default=0)
    progress = Column(Integer, default=0)  # Progress towards completion (0-100)
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    achievement_metadata = Column(JSON)  # Additional achievement-specific data

    # Relationships
    user = relationship("User", back_populates="achievements")

    @property
    def is_completed(self):
        return self.progress >= 100 and self.completed_at is not None

    @classmethod
    def get_language_achievements(cls, language_code: str):
        """Define language-specific achievement templates"""
        return [
            {
                "id": f"vocab_mastery_{language_code}",
                "name": f"Vocabulary Master ({language_code})",
                "description": "Master 1000 vocabulary words",
                "type": "language_proficiency",
                "target": 1000,
                "metadata": {"type": "vocabulary", "language": language_code}
            },
            {
                "id": f"dialect_explorer_{language_code}",
                "name": f"Dialect Explorer ({language_code})",
                "description": "Interact with speakers from 5 different regions",
                "type": "language_proficiency",
                "target": 5,
                "metadata": {"type": "regional_dialect", "language": language_code}
            },
            {
                "id": f"conversation_master_{language_code}",
                "name": f"Conversation Master ({language_code})",
                "description": "Complete 50 contextual conversations",
                "type": "language_proficiency",
                "target": 50,
                "metadata": {"type": "conversation", "language": language_code}
            }
        ]

    @classmethod
    def calculate_progress(cls, stats, achievement_type):
        """Calculate achievement progress based on user stats"""
        # ...existing code...

class AchievementDefinition(Base):
    __tablename__ = "achievement_definitions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)
    points = Column(Integer, default=0)
    requirements = Column(JSON)  # {type: str, criteria: dict}
    tier = Column(Integer, default=1)  # Achievement tier/level
    is_active = Column(Boolean, default=True)
    achievement_metadata = Column(JSON)  # Additional configuration data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "description": self.description,
            "points": self.points,
            "requirements": self.requirements,
            "tier": self.tier,
            "is_active": self.is_active,
            "achievement_metadata": self.achievement_metadata
        }

    def validate_requirements(self, progress_data: dict) -> bool:
        """
        Validate if achievement requirements are met
        Args:
            progress_data: Dict containing relevant progress data
        Returns:
            bool: Whether requirements are met
        """
        if not self.requirements:
            return False
            
        req_type = self.requirements["type"]
        criteria = self.requirements["criteria"]
        
        if req_type == "visit_count":
            # Check number of unique POIs visited
            visited = progress_data.get("visited_pois", [])
            return len(visited) >= criteria["count"]
            
        elif req_type == "language_level":
            # Check language proficiency level
            current_level = progress_data.get("language_level", 0)
            return current_level >= criteria["level"]
            
        elif req_type == "points":
            # Check total points earned
            total_points = progress_data.get("total_points", 0)
            return total_points >= criteria["min_points"]
            
        elif req_type == "streak":
            # Check daily streak
            current_streak = progress_data.get("daily_streak", 0)
            return current_streak >= criteria["days"]
            
        elif req_type == "completion":
            # Check region completion percentage
            completion = progress_data.get("completion_percentage", 0)
            return completion >= criteria["percentage"]
            
        return False