import pytest
from app.services.recommendation import ContentRecommender
from app.models.content import LanguageContent, ContentType
from app.models.progress import UserProgress
from app.models.poi import PointOfInterest
from app.models.region import Region

@pytest.fixture
def test_region(test_db):
    region = Region(
        id="tokyo",
        name="Tokyo",
        local_name="東京",
        languages=["ja"],
        difficulty_level=50
    )
    test_db.add(region)
    test_db.commit()
    return region

@pytest.fixture
def test_poi(test_db, test_region):
    poi = PointOfInterest(
        id="tokyo_station",
        name="Tokyo Station",
        local_name="東京駅",
        region_id=test_region.id,
        poi_type="station",
        difficulty_level=50
    )
    test_db.add(poi)
    test_db.commit()
    return poi

@pytest.fixture
def test_content(test_db, test_region):
    contents = []
    content_data = [
        {
            "id": "easy_vocab",
            "content_type": ContentType.VOCABULARY,
            "difficulty_level": 30,
            "content": {"word": "駅", "reading": "えき", "meaning": "station"}
        },
        {
            "id": "medium_vocab",
            "content_type": ContentType.VOCABULARY,
            "difficulty_level": 50,
            "content": {"word": "改札口", "reading": "かいさつぐち", "meaning": "ticket gate"}
        },
        {
            "id": "hard_vocab",
            "content_type": ContentType.VOCABULARY,
            "difficulty_level": 70,
            "content": {"word": "特急列車", "reading": "とっきゅうれっしゃ", "meaning": "limited express"}
        }
    ]
    
    for data in content_data:
        content = LanguageContent(
            id=data["id"],
            language="ja",
            region=test_region.id,
            content_type=data["content_type"],
            difficulty_level=data["difficulty_level"],
            content=data["content"],
            context_tags=["station"]
        )
        test_db.add(content)
        contents.append(content)
    
    test_db.commit()
    return contents

@pytest.fixture
def test_progress(test_db, test_user, test_region, test_poi):
    progress = UserProgress(
        user_id=test_user.id,
        language="ja",
        region=test_region.id,
        proficiency_level=50,
        poi_progress={
            test_poi.id: {
                "visits": 3,
                "completed_content": ["easy_vocab"],
                "total_time": 900
            }
        },
        content_mastery={
            ContentType.VOCABULARY: {
                "easy_vocab": 90
            }
        }
    )
    test_db.add(progress)
    test_db.commit()
    return progress

def test_calculate_content_difficulty():
    """Test difficulty calculation based on mastery and visits"""
    # Base case
    difficulty = ContentRecommender.calculate_content_difficulty(50, 0, 0)
    assert difficulty == 50  # No adjustment

    # High mastery
    difficulty = ContentRecommender.calculate_content_difficulty(50, 100, 0)
    assert difficulty == 65  # 30% increase from mastery

    # Many visits
    difficulty = ContentRecommender.calculate_content_difficulty(50, 0, 10)
    assert difficulty == 60  # 20% increase from visits

    # Combined factors
    difficulty = ContentRecommender.calculate_content_difficulty(50, 100, 10)
    assert difficulty == 75  # Combined increase

    # Test maximum cap
    difficulty = ContentRecommender.calculate_content_difficulty(90, 100, 10)
    assert difficulty == 100  # Capped at 100

def test_get_recommended_content(test_db, test_progress, test_poi, test_content):
    """Test content recommendations based on user progress"""
    recommendations = ContentRecommender.get_recommended_content(
        db=test_db,
        user_progress=test_progress,
        poi=test_poi,
        content_type=ContentType.VOCABULARY,
        limit=5
    )

    assert len(recommendations) == 2  # Should exclude already mastered content
    
    # Verify recommendations are ordered by difficulty match
    difficulties = [r["difficulty_level"] for r in recommendations]
    target_difficulty = ContentRecommender.calculate_content_difficulty(
        test_progress.proficiency_level,
        90,  # Mastery from test_progress
        3    # Visits from test_progress
    )
    
    # Check that difficulties are closer to target
    assert abs(difficulties[0] - target_difficulty) <= abs(difficulties[1] - target_difficulty)

def test_recommendations_respect_content_type(test_db, test_progress, test_poi, test_content):
    """Test that recommendations filter by content type"""
    recommendations = ContentRecommender.get_recommended_content(
        db=test_db,
        user_progress=test_progress,
        poi=test_poi,
        content_type=ContentType.DIALOGUE,  # No dialogue content in fixtures
        limit=5
    )
    
    assert len(recommendations) == 0  # No dialogue content should be found

def test_recommendations_exclude_mastered(test_db, test_progress, test_poi, test_content):
    """Test that mastered content is excluded from recommendations"""
    recommendations = ContentRecommender.get_recommended_content(
        db=test_db,
        user_progress=test_progress,
        poi=test_poi,
        content_type=ContentType.VOCABULARY,
        limit=5
    )
    
    # Verify the mastered content is not included
    content_ids = [r["id"] for r in recommendations]
    assert "easy_vocab" not in content_ids  # This was marked as mastered in test_progress