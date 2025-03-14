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
        recommended_level=45,
        metadata={"dialect": "tokyo", "customs": {"greeting": "formal"}}
    )
    
    existing = test_db.query(Region).filter(Region.id == region.id).first()
    if not existing:
        test_db.add(region)
        test_db.commit()
        test_db.refresh(region)
    else:
        region = existing
    
    # Ensure instance is attached to session
    if region not in test_db:
        region = test_db.merge(region)
    
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
    
    existing = test_db.query(PointOfInterest).filter(PointOfInterest.id == poi.id).first()
    if not existing:
        test_db.add(poi)
        test_db.commit()
        test_db.refresh(poi)
    else:
        poi = existing
    
    # Ensure instance is attached to session
    if poi not in test_db:
        poi = test_db.merge(poi)
    
    return poi

@pytest.fixture
def test_content(test_db: Session, test_region: Region):
    contents = []
    content_data = [
        {
            "id": "vocab_1",
            "content_type": ContentType.VOCABULARY,
            "content": {
                "word": "駅",
                "reading": "えき",
                "meaning": "station",
                "example": "東京駅は大きいです。"
            },
            "difficulty_level": 40
        },
        {
            "id": "phrase_1",
            "content_type": ContentType.PHRASE,
            "content": {
                "phrase": "電車は何番線ですか？",
                "meaning": "Which platform is the train on?",
                "usage_notes": "Use at train stations"
            },
            "difficulty_level": 45
        },
        {
            "id": "dialogue_1",
            "content_type": ContentType.DIALOGUE,
            "content": {
                "title": "Asking for Directions",
                "conversation": [
                    {"role": "A", "text": "すみません、新幹線のホームはどこですか？"},
                    {"role": "B", "text": "2階です。エスカレーターで上がってください。"}
                ]
            },
            "difficulty_level": 50
        }
    ]
    
    for data in content_data:
        existing = test_db.query(LanguageContent).filter(LanguageContent.id == data["id"]).first()
        if not existing:
            content = LanguageContent(
                id=data["id"],
                language="ja",
                region=test_region.id,
                content_type=data["content_type"],
                content=data["content"],
                difficulty_level=data["difficulty_level"],
                context_tags=["station"]
            )
            test_db.add(content)
            contents.append(content)
        else:
            contents.append(existing)
    
    if contents:
        test_db.commit()
        for content in contents:
            test_db.refresh(content)
            # Ensure instance is attached to session
            if content not in test_db:
                content = test_db.merge(content)
    
    return contents

@pytest.mark.asyncio
async def test_get_poi_content(async_client, test_user, test_poi, test_content, test_db: Session):
    # Login
    response = await async_client.post("/api/v1/auth/token", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Make sure POI is attached to session
    test_poi = test_db.merge(test_poi)
    
    # Get POI content
    response = await async_client.get(
        f"/api/v1/map/pois/{test_poi.id}/content",
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

@pytest.mark.asyncio
async def test_complete_poi_content(async_client, test_user, test_poi, test_content, test_db: Session):
    # Login
    response = await async_client.post("/api/v1/auth/token", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Make sure POI is attached to session
    test_poi = test_db.merge(test_poi)
    
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
    
    existing_progress = test_db.query(UserProgress).filter(
        UserProgress.user_id == test_user.id,
        UserProgress.region == test_poi.region_id
    ).first()
    
    if not existing_progress:
        test_db.add(progress)
        test_db.commit()
        test_db.refresh(progress)
    else:
        progress = existing_progress
    
    # Complete POI content - Update endpoint URL to match router
    response = await async_client.post(
        f"/api/v1/progress/poi/{test_poi.id}/complete",
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
    progress = test_db.merge(progress)  # Re-attach to session
    
    assert "vocabulary" in progress.content_mastery
    assert progress.content_mastery["vocabulary"]["vocab_1"] == 85
    assert test_poi.id in progress.poi_progress
    assert progress.poi_progress[test_poi.id]["total_time"] == 300

@pytest.mark.asyncio
async def test_achievement_unlocking(async_client, test_user, test_poi, test_content, test_db: Session):
    # Login
    response = await async_client.post("/api/v1/auth/token", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Make sure POI is attached to session
    test_poi = test_db.merge(test_poi)
    
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
    
    existing_progress = test_db.query(UserProgress).filter(
        UserProgress.user_id == test_user.id,
        UserProgress.region == test_poi.region_id
    ).first()
    
    if not existing_progress:
        test_db.add(progress)
        test_db.commit()
        test_db.refresh(progress)
    else:
        progress = existing_progress
    
    # Complete content to trigger achievement - Update endpoint URL to match router
    response = await async_client.post(
        f"/api/v1/progress/poi/{test_poi.id}/complete",
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
    progress = test_db.merge(progress)  # Re-attach to session
    
    assert len(progress.achievements) > 0
    assert progress.poi_progress[test_poi.id]["visits"] == 5