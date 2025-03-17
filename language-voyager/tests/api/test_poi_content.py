import pytest
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.models.poi import PointOfInterest
from app.models.region import Region
from app.models.content import LanguageContent, ContentType
from app.models.progress import UserProgress

@pytest.fixture(autouse=True)
def clean_user_progress(test_db: Session):
    """Clean up user progress before and after each test"""
    # Clean before test
    test_db.query(UserProgress).delete()
    test_db.commit()
    
    yield
    
    # Clean after test
    test_db.query(UserProgress).delete()
    test_db.commit()
    test_db.expire_all()  # Clear SQLAlchemy's identity map

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
        region_metadata={"dialect": "tokyo", "customs": {"greeting": "formal"}}
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
        type="station",
        location={"lat": 35.681236, "lon": 139.767125},
        region_id=test_region.id,
        difficulty=45,
        content={
            "en": {
                "title": "Tokyo Station",
                "description": "Historic railway station",
                "hints": ["Look for the red brick building", "Main entrance faces Marunouchi"]
            },
            "ja": {
                "title": "東京駅",
                "description": "歴史的な鉄道駅",
                "hints": ["赤レンガの建物を探してください", "丸の内側に正面玄関があります"]
            }
        },
        achievement_criteria={
            "type": "visit",
            "requirements": {}
        },
        points_value=10,
        time_estimate=30,
        learning_objectives={
            "vocabulary": ["駅", "電車", "新幹線"],
            "grammar": ["～はどこですか"],
            "cultural": ["Train station etiquette"]
        }
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
    assert data["difficulty_level"] == test_poi.difficulty  # Update to use correct field name

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
    
    # Get or create initial progress
    progress = test_db.query(UserProgress).filter(
        UserProgress.user_id == test_user.id,
        UserProgress.region_id == test_poi.region_id
    ).first()
    
    if not progress:
        progress = UserProgress(
            user_id=test_user.id,
            language="ja",
            region_id=test_poi.region_id,  # Use region_id instead of region
            proficiency_level=0,
            poi_progress={},
            content_mastery={},
            achievements=[]
        )
        test_db.add(progress)
        test_db.commit()
        test_db.refresh(progress)
    
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
    
    # Get or create progress record
    progress = test_db.query(UserProgress).filter(
        UserProgress.user_id == test_user.id,
        UserProgress.region_id == test_poi.region_id
    ).first()
    
    if not progress:
        progress = UserProgress(
            user_id=test_user.id,
            language="ja",
            region_id=test_poi.region_id,  # Use region_id instead of region
            proficiency_level=0,
            poi_progress={},
            content_mastery={},
            achievements=[]
        )
        test_db.add(progress)
        test_db.commit()
        test_db.refresh(progress)
    
    # Clear existing progress and set initial visit count to 4
    progress.poi_progress = {}
    progress.poi_progress[test_poi.id] = {
        "visits": 4,
        "completed_content": [],
        "total_time": 1200,
        "last_visit": str(datetime.utcnow())
    }
    flag_modified(progress, "poi_progress")  # Mark JSON field as modified
    test_db.commit()
    
    # Refresh to ensure we have the latest state
    test_db.refresh(progress)
    test_db.expire_all()  # Clear SQLAlchemy's identity map
    
    # Verify initial state
    progress = test_db.query(UserProgress).filter(
        UserProgress.user_id == test_user.id,
        UserProgress.region_id == test_poi.region_id  # Changed from region to region_id
    ).first()
    assert progress.poi_progress[test_poi.id]["visits"] == 4
    
    # Complete content to trigger achievement
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
    test_db.refresh(progress)  # Ensure we have latest data
    
    assert len(progress.achievements) > 0
    assert progress.poi_progress[test_poi.id]["visits"] == 5

@pytest.mark.asyncio
async def test_content_difficulty_progression(async_client, test_user, test_poi, test_content, test_db: Session):
    """Test the content difficulty progression system"""
    # Login and setup
    response = await async_client.post("/api/v1/auth/token", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    token = response.json()["access_token"]

    # Clean any existing progress first
    test_db.query(UserProgress).delete()
    test_db.commit()

    # Create progress with exact values to test mastery factor calculation 
    progress = UserProgress(
        user_id=test_user.id,
        language="ja",
        region_id=test_poi.region_id,  # FIXED: Set the region_id properly
        region_name=test_poi.region_id,  # Set region_name for backward compatibility
        proficiency_level=50,
        poi_progress={
            test_poi.id: {
                "visits": 3,  # Set exactly to 3 for the test
                "completed_content": ["vocab_1"],
                "total_time": 900,
                "last_visit": str(datetime.utcnow())
            }
        },
        content_mastery={
            "vocabulary": {"vocab_1": 85}  # This should give us exactly 0.255 mastery factor
        },
        achievements=[]
    )
    
    # Properly persist the progress record
    test_db.add(progress)
    test_db.flush()  # Make sure the record is created before modifying JSON
    flag_modified(progress, "poi_progress")  # Mark JSON field as modified
    flag_modified(progress, "content_mastery")  # Mark JSON field as modified
    test_db.commit()
    test_db.refresh(progress)

    # Verify progress was correctly saved to database
    saved_progress = test_db.query(UserProgress).filter(
        UserProgress.user_id == test_user.id,
        UserProgress.region_id == test_poi.region_id  # Use region_id consistently
    ).first()
    
    assert saved_progress is not None
    assert saved_progress.poi_progress[test_poi.id]["visits"] == 3
    assert "vocabulary" in saved_progress.content_mastery
    assert saved_progress.content_mastery["vocabulary"]["vocab_1"] == 85
    
    # Clear any existing progress from other tests
    test_db.query(UserProgress).filter(
        UserProgress.user_id != test_user.id  # Keep our test user's progress
    ).delete()
    test_db.commit()

    # Get POI content to check difficulty progression
    response = await async_client.get(
        f"/api/v1/map/pois/{test_poi.id}/content",
        params={"language": "ja", "proficiency_level": 50},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()["data"]

    # Verify difficulty factors are present
    factors = data["local_context"]["difficulty_factors"]
    assert "base_difficulty" in factors
    assert "mastery_factor" in factors
    assert "visit_factor" in factors

    print(f"Debug values - mastery_factor: {factors['mastery_factor']}, visit_factor: {factors['visit_factor']}")
    print(f"Expected mastery_factor: {(85/100) * 0.3}")
    
    # Verify base difficulty matches POI
    assert factors["base_difficulty"] == test_poi.difficulty

    # Verify mastery factor (30% max increase)
    mastery_factor = factors["mastery_factor"]
    assert 0 <= mastery_factor <= 0.3
    assert mastery_factor == pytest.approx((85/100) * 0.3, rel=0.01)

    # Verify visit factor (20% max increase)
    visit_factor = factors["visit_factor"]
    assert 0 <= visit_factor <= 0.2
    assert visit_factor == pytest.approx((3/10) * 0.2, rel=0.01)  # Should be 0.06 for 3 visits
    
    # Verify difficulty progression
    progression = data["local_context"]["difficulty_progression"]
    assert len(progression) == 5  # Next 5 visits
    
    # Verify progression increases with visits but stays within bounds
    base_difficulty = test_poi.difficulty
    previous = None
    for visit_num in range(4, 9):  # Visits 4-8
        visit_key = f"visit_{visit_num}"
        assert visit_key in progression
        current = progression[visit_key]
        
        # Verify difficulty is within ±20% of base
        max_difficulty = base_difficulty * 1.2
        assert current <= max_difficulty
        
        # Verify progressive increase
        if previous is not None:
            assert current >= previous
        previous = current

@pytest.mark.asyncio
async def test_content_recommendation(async_client, test_user, test_poi, test_content, test_db: Session):
    """Test the content recommendation system"""
    # Login and setup
    response = await async_client.post("/api/v1/auth/token", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    
    # Create progress with some mastered content
    progress = UserProgress(
        user_id=test_user.id,
        language="ja",
        region_id=test_poi.region_id,
        proficiency_level=50,
        poi_progress={
            test_poi.id: {
                "visits": 2,
                "completed_content": ["vocab_1"],
                "total_time": 600,
                "last_visit": str(datetime.utcnow())
            }
        },
        content_mastery={
            "vocabulary": {"vocab_1": 100}  # Fully mastered
        },
        achievements=[]
    )
    test_db.add(progress)
    flag_modified(progress, "poi_progress")  # Mark JSON field as modified
    flag_modified(progress, "content_mastery")  # Mark JSON field as modified
    test_db.commit()
    test_db.refresh(progress)  # Refresh to ensure we have latest data

    # Get POI content
    response = await async_client.get(
        f"/api/v1/map/pois/{test_poi.id}/content",
        params={"language": "ja", "proficiency_level": 50},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()["data"]

    # Verify content filtering
    vocab_items = data["vocabulary"]
    for item in vocab_items:
        # Already mastered content should be marked as completed
        if item["id"] == "vocab_1":
            assert item["completed"] == True
            assert item["mastery_level"] == 100
        else:
            assert item["completed"] == False
            assert item["mastery_level"] == 0

        # Verify difficulty is appropriate (within ±20% of user level)
        assert abs(item["difficulty_level"] - 50) <= 10  # ±20% of 50

    # Verify POI context is included
    assert data["local_context"]["dialect"] == "tokyo"
    assert "formality_level" in data["local_context"]
    assert "region_specific_customs" in data["local_context"]

@pytest.mark.asyncio
async def test_difficulty_adaptation(async_client, test_user, test_poi, test_content, test_db: Session):
    """Test how content difficulty adapts based on user progress"""
    # Login and setup
    response = await async_client.post("/api/v1/auth/token", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    token = response.json()["access_token"]

    # Initial request with no progress should return base difficulty
    response = await async_client.get(
        f"/api/v1/map/pois/{test_poi.id}/content",
        params={"language": "ja", "proficiency_level": 50},
        headers={"Authorization": f"Bearer {token}"}
    )
    initial_difficulty = response.json()["data"]["difficulty_level"]
    assert initial_difficulty == test_poi.difficulty  # Should be 45.0

    # Clean any existing progress first
    test_db.query(UserProgress).delete()
    test_db.commit()

    # Create progress with high mastery (should trigger adaptation)
    progress = UserProgress(
        user_id=test_user.id,
        language="ja",
        region_id=test_poi.region_id,
        region_name=test_poi.region_id,
        proficiency_level=50,
        poi_progress={
            test_poi.id: {
                "visits": 5,
                "completed_content": ["vocab_1", "phrase_1"],
                "total_time": 1500,
                "last_visit": str(datetime.utcnow())
            }
        },
        content_mastery={
            "vocabulary": {"vocab_1": 90},  # 90% mastery
            "phrase": {"phrase_1": 85}      # 85% mastery
        },
        achievements=[]
    )

    # Properly persist the progress record
    test_db.add(progress)
    test_db.flush()  # Make sure the record is created
    flag_modified(progress, "poi_progress")
    flag_modified(progress, "content_mastery")
    test_db.commit()
    test_db.refresh(progress)

    # Verify progress was saved correctly
    saved_progress = test_db.query(UserProgress).filter(
        UserProgress.user_id == test_user.id,
        UserProgress.language == "ja",
        UserProgress.region_id == test_poi.region_id
    ).first()
    assert saved_progress.poi_progress[test_poi.id]["visits"] == 5
    assert "vocab_1" in saved_progress.content_mastery["vocabulary"]
    assert saved_progress.content_mastery["vocabulary"]["vocab_1"] == 90

    # Get content after progress
    response = await async_client.get(
        f"/api/v1/map/pois/{test_poi.id}/content",
        params={"language": "ja", "proficiency_level": 50},
        headers={"Authorization": f"Bearer {token}"}
    )
    data = response.json()["data"]
    adapted_difficulty = data["difficulty_level"]
    factors = data["local_context"]["difficulty_factors"]

    # Calculate expected difficulty
    avg_mastery = (90 + 85) / 2  # Average of mastery scores
    expected_mastery_factor = (avg_mastery / 100) * 0.3  # 30% max from mastery
    expected_visit_factor = min((5 / 10) * 0.2, 0.2)  # 20% max from visits
    expected_total_factor = min(expected_mastery_factor + expected_visit_factor, 0.2)  # Cap at 20% total
    expected_difficulty = test_poi.difficulty * (1 + expected_total_factor)

    # Verify difficulty increased appropriately
    print(f"Initial difficulty: {initial_difficulty}")
    print(f"Adapted difficulty: {adapted_difficulty}") 
    print(f"Expected difficulty: {expected_difficulty}")
    print(f"Factors used: mastery={factors['mastery_factor']}, visits={factors['visit_factor']}")

    assert adapted_difficulty > initial_difficulty
    assert adapted_difficulty == pytest.approx(expected_difficulty, rel=0.01)  # Within 1% of expected

@pytest.mark.asyncio
async def test_version_control(async_client, test_user, test_poi, test_content, test_db: Session):
    """Test POI content version control functionality"""
    # Login
    response = await async_client.post("/api/v1/auth/token", data={
        "username": test_user.email,
        "password": "testpass123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Initial version check
    response = await async_client.get(
        f"/api/v1/map/pois/{test_poi.id}/version",
        params={"client_version": 1},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert not data["needs_update"]
    
    # Make test user an admin for content update
    test_user.is_admin = True
    test_db.commit()
    
    # Update content version
    response = await async_client.post(
        f"/api/v1/map/pois/{test_poi.id}/content",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["current_version"] == 2
    
    # Verify version mismatch is detected
    response = await async_client.get(
        f"/api/v1/map/pois/{test_poi.id}/content",
        params={
            "language": "ja",
            "proficiency_level": 50,
            "client_version": 1
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 409  # Version mismatch error