from typing import List, Dict
from sqlalchemy.orm import Session
from ..models.content import LanguageContent
from ..models.progress import UserProgress
from ..models.poi import PointOfInterest

class ContentRecommender:
    @staticmethod
    def calculate_content_difficulty(base_difficulty: float, mastery_level: float, visit_count: int) -> float:
        """Calculate adjusted difficulty based on user mastery and visit count"""
        # Mastery increases difficulty (max 30% increase)
        mastery_factor = (mastery_level / 100) * 0.3  # Remove rounding here
        
        # Visits increase difficulty (max 20% increase)
        visit_factor = min((visit_count / 10) * 0.2, 0.2)
        
        # Calculate total adjustment
        adjustment = mastery_factor + visit_factor
        
        # Apply adjustment to base difficulty
        adjusted_difficulty = base_difficulty * (1 + adjustment)
        
        # Keep within 0-100 range and ensure it's not less than base difficulty
        return max(min(100, adjusted_difficulty), base_difficulty)

    @staticmethod
    def get_recommended_content(db: Session,
                              user_progress: UserProgress,
                              poi: PointOfInterest,
                              content_type: str = None,
                              limit: int = 5) -> List[Dict]:
        """Get recommended content for a user based on their progress and POI context"""
        # Get user's POI-specific mastery and visits
        poi_progress = user_progress.poi_progress.get(poi.id, {})
        poi_visits = poi_progress.get("visits", 0)
        
        # Calculate content type specific mastery
        type_mastery = user_progress.content_mastery.get(content_type, {})
        avg_mastery = sum(type_mastery.values()) / len(type_mastery) if type_mastery else 0
        
        # Calculate target difficulty using POI difficulty as base
        target_difficulty = ContentRecommender.calculate_content_difficulty(
            poi.difficulty_level,
            avg_mastery,
            poi_visits
        )
        
        # Base query - filter by region, language and content type
        query = db.query(LanguageContent).filter(
            LanguageContent.region == poi.region_id,
            LanguageContent.language == user_progress.language
        )
        
        if content_type:
            query = query.filter(LanguageContent.content_type == content_type)
        
        # Get all matching content within appropriate difficulty range (±20%)
        min_difficulty = max(0, target_difficulty - 20)
        max_difficulty = min(100, target_difficulty + 20)
        query = query.filter(
            LanguageContent.difficulty_level.between(min_difficulty, max_difficulty)
        )
        
        # Get all matching content
        content_items = query.all()
        recommendations = []
        
        for content in content_items:
            # Calculate match score based on difficulty and context relevance
            difficulty_match = 1 - (abs(content.difficulty_level - target_difficulty) / 20)
            context_match = 1.0 if poi.poi_type in content.context_tags else 0.5
            match_score = difficulty_match * context_match * 100
            
            # Create content item dict matching the schema
            content_dict = {
                "id": content.id,
                "content": content.content,
                "difficulty_level": content.difficulty_level,
                "completed": content.id in poi_progress.get("completed_content", []),
                "mastery_level": type_mastery.get(content.id, 0)
            }
            
            recommendations.append({
                "content": content_dict,
                "match_score": match_score
            })
        
        # Sort by match score
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Return top N recommendations
        return [r["content"] for r in recommendations[:limit]]