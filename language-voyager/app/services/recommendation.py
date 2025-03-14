from typing import List, Dict
from sqlalchemy.orm import Session
from ..models.content import LanguageContent
from ..models.progress import UserProgress
from ..models.poi import PointOfInterest

class ContentRecommender:
    @staticmethod
    def calculate_content_difficulty(base_difficulty: float, mastery_level: float, visit_count: int) -> float:
        """Calculate adjusted difficulty based on user mastery and visit count"""
        # Mastery reduces difficulty (max 30% reduction)
        mastery_factor = (mastery_level / 100) * 0.3
        
        # Visits increase difficulty (max 20% increase)
        visit_factor = min((visit_count / 10) * 0.2, 0.2)
        
        # Combine factors - mastery reduces, visits increase
        adjusted_difficulty = base_difficulty * (1 - mastery_factor + visit_factor)
        
        # Keep within 0-100 range
        return max(0, min(100, adjusted_difficulty))

    @staticmethod
    def get_recommended_content(db: Session,
                              user_progress: UserProgress,
                              poi: PointOfInterest,
                              content_type: str = None,
                              limit: int = 5) -> List[Dict]:
        """Get recommended content for a user based on their progress and POI context"""
        # Get user's mastery level for this POI
        poi_visits = user_progress.poi_progress.get(poi.id, {}).get("visits", 0)
        
        # Calculate overall mastery level across all content types
        all_mastery = []
        for ct_mastery in user_progress.content_mastery.values():
            all_mastery.extend(ct_mastery.values())
        avg_mastery = sum(all_mastery) / len(all_mastery) if all_mastery else 0

        # Calculate adjusted difficulty target using POI difficulty as base
        target_difficulty = ContentRecommender.calculate_content_difficulty(
            poi.difficulty_level,
            avg_mastery,
            poi_visits
        )

        # Base query - removed strict context tag matching
        query = db.query(LanguageContent).filter(
            LanguageContent.region == poi.region_id
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

        # Get all matching content
        content_items = query.all()
        recommendations = []
        
        for content in content_items:
            # Check if content is already mastered
            type_mastery = user_progress.content_mastery.get(content.content_type, {})
            if content.id not in type_mastery:
                # Calculate match score based on difficulty and context relevance
                difficulty_match = abs(content.difficulty_level - target_difficulty)
                context_match = 1.0 if poi.poi_type in content.context_tags else 0.5
                match_score = (100 - difficulty_match) * context_match
                
                recommendations.append({
                    "content": content,
                    "match_score": match_score
                })

        # Sort by match score and return top N
        recommendations.sort(key=lambda x: x["match_score"], reverse=True)
        
        # Convert content items to dictionaries
        result = []
        for r in recommendations[:limit]:
            content_dict = r["content"].to_dict()
            content_dict["completed"] = False  # Not mastered since we filtered those out
            content_dict["mastery_level"] = 0  # No mastery yet
            result.append(content_dict)
            
        return result