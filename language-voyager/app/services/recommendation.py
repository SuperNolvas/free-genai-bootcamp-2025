from typing import List, Dict
from sqlalchemy.orm import Session
from ..models.content import LanguageContent
from ..models.progress import UserProgress
from ..models.poi import PointOfInterest

class ContentRecommender:
    @staticmethod
    def calculate_content_difficulty(base_difficulty: float, 
                                  mastery_level: float,
                                  visit_count: int) -> float:
        """Calculate adjusted difficulty based on user's mastery and visit count"""
        # Adjust difficulty based on mastery (higher mastery = higher difficulty)
        mastery_factor = (mastery_level / 100) * 0.3
        
        # Visits factor (more visits = gradually increasing difficulty)
        visit_factor = min((visit_count / 10) * 0.2, 0.2)  # Cap at 20% increase
        
        # Calculate final difficulty
        adjusted_difficulty = base_difficulty * (1 + mastery_factor + visit_factor)
        return min(adjusted_difficulty, 100)  # Cap at 100

    @staticmethod
    def get_recommended_content(db: Session,
                              user_progress: UserProgress,
                              poi: PointOfInterest,
                              content_type: str = None,
                              limit: int = 5) -> List[Dict]:
        """Get recommended content for a user based on their progress and POI context"""
        # Get user's mastery level for this POI
        poi_visits = user_progress.poi_progress.get(poi.id, {}).get("visits", 0)
        content_mastery = user_progress.content_mastery.get(content_type, {})
        avg_mastery = sum(content_mastery.values()) / len(content_mastery) if content_mastery else 0

        # Calculate adjusted difficulty target
        target_difficulty = ContentRecommender.calculate_content_difficulty(
            user_progress.proficiency_level,
            avg_mastery,
            poi_visits
        )

        # Base query
        query = db.query(LanguageContent).filter(
            LanguageContent.region == poi.region_id,
            LanguageContent.context_tags.contains([poi.poi_type])
        )

        # Filter by content type if specified
        if content_type:
            query = query.filter(LanguageContent.content_type == content_type)

        # Get content within appropriate difficulty range (±20%)
        min_difficulty = max(0, target_difficulty - 20)
        max_difficulty = min(100, target_difficulty + 20)
        query = query.filter(
            LanguageContent.difficulty_level.between(min_difficulty, max_difficulty)
        )

        # Order by how close the difficulty is to target
        # and exclude already mastered content
        content_items = query.all()
        recommendations = []
        
        for content in content_items:
            if content.id not in content_mastery:
                difficulty_match = abs(content.difficulty_level - target_difficulty)
                recommendations.append({
                    "content": content,
                    "match_score": 100 - difficulty_match
                })

        # Sort by match score and return top N
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        return [r["content"].to_dict() for r in recommendations[:limit]]