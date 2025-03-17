from typing import List, Dict
import logging
from sqlalchemy.orm import Session
from ..models.content import LanguageContent, ContentType
from ..models.progress import UserProgress
from ..models.poi import PointOfInterest
from ..models.achievement import Achievement, AchievementDefinition

logger = logging.getLogger(__name__)

class ContentRecommender:
    @staticmethod
    def calculate_content_difficulty(base_difficulty: float, mastery_level: float, visit_count: int) -> float:
        """Calculate adjusted difficulty based on user mastery and visit count"""
        # Calculate mastery factor (max 30% increase)
        mastery_factor = (mastery_level / 100) * 0.3
        
        # Calculate visit factor (max 20% increase) 
        visit_factor = min((visit_count / 10) * 0.2, 0.2)
        
        # Apply both adjustments independently
        total_adjustment = mastery_factor + visit_factor
        
        # Calculate adjusted difficulty with total adjustment
        adjusted_difficulty = base_difficulty * (1 + total_adjustment)
        
        # Keep within reasonable bounds (0-100)
        return min(max(adjusted_difficulty, 0), 100)
        
    @staticmethod
    def get_recommended_content(
        db: Session,
        user_progress: UserProgress,
        poi: PointOfInterest,
        content_type: str = None,
        limit: int = 5,
        completed_content: List[str] = None
    ) -> List[Dict]:
        """Get recommended content for a user based on their progress and POI context"""
        logger.info(f"Getting content recommendations for POI {poi.id}, type {content_type}")
        
        # Ensure user_progress.poi_progress is initialized
        poi_progress = {}
        if hasattr(user_progress, 'poi_progress') and user_progress.poi_progress:
            # Access POI-specific progress data
            poi_progress = user_progress.poi_progress.get(poi.id, {})
        
        # Get completed content
        completed_items = set(poi_progress.get("completed_content", []))
        if completed_content:
            completed_items.update(completed_content)
            
        # Get mastery info from content_mastery
        type_mastery = {}
        
        # Ensure content_mastery is initialized
        if hasattr(user_progress, 'content_mastery') and user_progress.content_mastery:
            if content_type:
                # Try different variations of the content type key
                content_type_str = str(content_type)
                possible_keys = [
                    content_type_str,
                    content_type_str.lower(),
                    content_type_str.upper(),
                    "vocabulary" if content_type_str.upper() == "VOCABULARY" else None
                ]
                possible_keys = [k for k in possible_keys if k]
                
                for key in possible_keys:
                    if key in user_progress.content_mastery:
                        type_mastery = user_progress.content_mastery[key]
                        break
            
            # Also look for any mastery data that might contain our content IDs
            # This handles the case where content_type might be an enum but stored as a string
            if not type_mastery:
                for key, value in user_progress.content_mastery.items():
                    if isinstance(value, dict):
                        type_mastery.update(value)
        
        logger.info(f"POI progress for {poi.id}: {poi_progress}")
        logger.info(f"Completed items from progress: {completed_items}")
        logger.info(f"Content mastery: {type_mastery}")
        
        # Query base content
        query = db.query(LanguageContent).filter(
            LanguageContent.region == poi.region_id
        )
        
        if user_progress.language:
            query = query.filter(LanguageContent.language == user_progress.language)
            
        # Filter by content type if specified
        if content_type:
            if isinstance(content_type, str):
                try:
                    enum_type = ContentType[content_type.upper()]
                    query = query.filter(LanguageContent.content_type == enum_type)
                except KeyError:
                    logger.warning(f"Invalid content type: {content_type}")
            else:
                query = query.filter(LanguageContent.content_type == content_type)
                
        # Get matching content
        content_items = query.all()
        logger.info(f"Found {len(content_items)} content items")
        recommendations = []
        
        for content in content_items:
            # Check if content is completed (in completed_items OR has mastery)
            is_completed = (
                content.id in completed_items or 
                content.id in type_mastery
            )
            
            # Get mastery level if it exists
            mastery_level = type_mastery.get(content.id, 0)
            
            logger.info(f"Processing content {content.id}:")
            logger.info(f"- In completed_items: {content.id in completed_items}")
            logger.info(f"- In type_mastery: {content.id in type_mastery}")
            logger.info(f"- Final completed status: {is_completed}")
            logger.info(f"- Mastery level: {mastery_level}")
            
            # Calculate recommendation score
            difficulty_match = 1.0  # Default to perfect match for now
            context_match = 1.0 if poi.type in content.context_tags else 0.5
            match_score = difficulty_match * context_match * 100
            
            content_dict = {
                "id": content.id,
                "content": content.content,
                "difficulty_level": content.difficulty_level,
                "completed": is_completed,  # This should now be correct
                "mastery_level": mastery_level
            }
            
            recommendations.append({
                "content": content_dict,
                "match_score": match_score
            })
            
        # Sort by match score
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        return [r["content"] for r in recommendations[:limit]]

class LanguageProgressService:
    def __init__(self, db: Session):
        self.db = db

    async def update_language_progress(self, user_id: int, language_code: str, activity_data: Dict):
        """
        Update user's language progress and check for achievements
        """
        progress = self._get_or_create_progress(user_id, language_code)
        
        # Update progress based on activity
        if activity_data.get("type") == "vocabulary":
            progress.vocabulary_count += 1
        elif activity_data.get("type") == "conversation":
            progress.conversation_count += 1
        elif activity_data.get("type") == "regional_interaction":
            if activity_data["region_id"] not in progress.visited_regions:
                progress.visited_regions.append(activity_data["region_id"])
        
        self.db.commit()
        
        # Check and award achievements
        await self._check_achievements(user_id, language_code, progress)
    
    def _get_or_create_progress(self, user_id: int, language_code: str) -> UserProgress:
        progress = self.db.query(UserProgress).filter(
            UserProgress.user_id == user_id,
            UserProgress.language_code == language_code
        ).first()
        
        if not progress:
            progress = UserProgress(
                user_id=user_id,
                language_code=language_code,
                vocabulary_count=0,
                conversation_count=0,
                visited_regions=[]
            )
            self.db.add(progress)
            
        return progress
    
    async def _check_achievements(self, user_id: int, language_code: str, progress: UserProgress):
        """Check and award language-specific achievements"""
        achievements = Achievement.get_language_achievements(language_code)
        
        for achievement_template in achievements:
            existing = self.db.query(Achievement).filter(
                Achievement.user_id == user_id,
                Achievement.achievement_id == achievement_template["id"]
            ).first()
            
            if existing and existing.is_completed:
                continue
                
            current_progress = self._calculate_achievement_progress(
                achievement_template, 
                progress
            )
            
            if not existing:
                achievement = Achievement(
                    user_id=user_id,
                    type=achievement_template["type"],
                    achievement_id=achievement_template["id"],
                    progress=current_progress,
                    achievement_metadata=achievement_template["metadata"]
                )
                self.db.add(achievement)
            else:
                existing.progress = current_progress
                
            self.db.commit()
    
    def _calculate_achievement_progress(self, template: Dict, progress: UserProgress) -> int:
        """Calculate progress percentage for an achievement"""
        metadata = template["metadata"]
        target = template["target"]
        
        if metadata["type"] == "vocabulary":
            current = progress.vocabulary_count
        elif metadata["type"] == "conversation":
            current = progress.conversation_count
        elif metadata["type"] == "regional_dialect":
            current = len(progress.visited_regions)
        else:
            return 0
            
        return min(100, int((current / target) * 100))
