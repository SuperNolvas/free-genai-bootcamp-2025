import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.poi import PointOfInterest
from app.models.region import Region
from app.models.content import LanguageContent, ContentType
from app.models.progress import UserProgress

@pytest.fixture
def test_region(test_db: Session):
    region = Region(
        id="tokyo_central",
        name="Tokyo Central",
        local_name="東京中心部",
        description="Central Tokyo area",
        languages=["ja"],
        bounds={"ne": {"lat": 35.7, "lon": 139.8}, "sw": {"lat": 35.6, "lon": 139.7}},
        center={"lat": 35.65, "lon": 139.75},
        difficulty_level=50,
        recommended_level=45,  # Adding this required field
        metadata={"dialect": "tokyo", "customs": {"greeting": "formal"}}
    )
    test_db.add(region)
    test_db.commit()
    return region

@pytest.fixture
def test_poi(test_db: Session, test_region: Region):
    poi = PointOfInterest(
        id="tokyo_station",
        name="Tokyo Station",
        local_name="東京駅",
        description="Historic railway station",
        local_description="歴史的な鉄道駅",
        poi_type="station",
        coordinates={"lat": 35.681236, "lon": 139.767125},
        region_id=test_region.id,
        difficulty_level=45,
        content_ids=["vocab_1", "phrase_1", "dialogue_1"]
    )
    test_db.add(poi)
    test_db.commit()
    return poi

@pytest.fixture
def test_content(test_db: Session, test_region: Region):
    contents = [
        LanguageContent(
            id="vocab_1",
            language="ja",
            region=test_region.id,
            content_type=ContentType.VOCABULARY,
            content={
                "word": "駅",
                "reading": "えき",
                "meaning": "station",
                "example": "東京駅は大きいです。"
            },
            difficulty_level=40,
            context_tags=["station"]
        ),
        LanguageContent(
            id="phrase_1",
            language="ja",
            region=test_region.id,
            content_type=ContentType.PHRASE,
            content={
                "phrase": "電車は何番線ですか？",
                "meaning": "Which platform is the train on?",
                "usage_notes": "Use at train stations"
            },
            difficulty_level=45,
            context_tags=["station"]
        ),
        LanguageContent(
            id="dialogue_1",
            language="ja",
            region=test_region.id,
            content_type=ContentType.DIALOGUE,
            content={
                "title": "Asking for Directions",
                "conversation": [
                    {"role": "A", "text": "すみません、新幹線のホームはどこですか？"},
                    {"role": "B", "text": "2階です。エスカレーターで上がってください。"}
                ]
            },
            difficulty_level=50,
            context_tags=["station"]
        )
    ]
    for content in contents:
        test_db.add(content)
    test_db.commit()
    return contents

async def test_get_poi_content(client, test_user, test_poi, test_content, test_db: Session):
    # Login
    response = await client.post("/auth/token", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    
    # Get POI content
    response = await client.get(
        f"/map/pois/{test_poi.id}/content",
        params={"language": "ja", "proficiency_level": 50},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    
    # Verify content structure
    assert len(data["vocabulary"]) == 1
    assert len(data["phrases"]) == 1
    assert len(data["dialogues"]) == 1
    assert data["local_context"]["dialect"] == "tokyo"
    assert data["difficulty_level"] == test_poi.difficulty_level

async def test_complete_poi_content(client, test_user, test_poi, test_content, test_db: Session):
    # Login
    response = await client.post("/auth/token", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    
    # Create initial progress
    progress = UserProgress(
        user_id=test_user.id,
        language="ja",
        region=test_poi.region_id,
        proficiency_level=0,
        poi_progress={},
        content_mastery={},
        achievements=[]
    )
    test_db.add(progress)
    test_db.commit()
    
    # Complete POI content
    response = await client.post(
        f"/progress/poi/{test_poi.id}/complete",
        json={
            "content_type": "vocabulary",
            "score": 85,
            "time_spent": 300,
            "completed_items": ["vocab_1"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    # Verify progress update
    progress = test_db.query(UserProgress).filter(
        UserProgress.user_id == test_user.id,
        UserProgress.region == test_poi.region_id
    ).first()
    
    assert "vocabulary" in progress.content_mastery
    assert progress.content_mastery["vocabulary"]["vocab_1"] == 85
    assert test_poi.id in progress.poi_progress
    assert progress.poi_progress[test_poi.id]["total_time"] == 300

async def test_achievement_unlocking(client, test_user, test_poi, test_content, test_db: Session):
    # Login
    response = await client.post("/auth/token", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    
    # Create progress with existing visits
    progress = UserProgress(
        user_id=test_user.id,
        language="ja",
        region=test_poi.region_id,
        proficiency_level=0,
        poi_progress={
            test_poi.id: {
                "visits": 4,
                "completed_content": [],
                "total_time": 1200,
                "last_visit": str(datetime.utcnow())
            }
        },
        content_mastery={},
        achievements=[]
    )
    test_db.add(progress)
    test_db.commit()
    
    # Complete content to trigger achievement
    response = await client.post(
        f"/progress/poi/{test_poi.id}/complete",
        json={
            "content_type": "vocabulary",
            "score": 90,
            "time_spent": 300,
            "completed_items": ["vocab_1"]
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    
    # Verify achievements
    assert len(data) > 0
    assert any(a["name"] == "Frequent Visitor" for a in data)
    
    # Verify progress update
    progress = test_db.query(UserProgress).filter(
        UserProgress.user_id == test_user.id,
        UserProgress.region == test_poi.region_id
    ).first()
    
    assert len(progress.achievements) > 0
    assert progress.poi_progress[test_poi.id]["visits"] == 5