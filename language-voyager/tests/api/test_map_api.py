import pytest
from datetime import datetime
from app.models.region import Region
from app.models.progress import UserProgress
from app.models.user import User

@pytest.fixture
def test_user(test_db):
    user = User(
        email="test_user@example.com",  # Different email from auth_headers
        username="testuser_fixture",
        hashed_password="hash"
    )
    test_db.add(user)
    test_db.commit()
    return user

@pytest.fixture
def auth_headers(client):
    # Register and login a test user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test@example.com",
            "password": "testpass123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_regions(test_db):
    regions = [
        Region(
            id="tokyo",
            name="Tokyo",
            local_name="東京",
            description="The bustling capital of Japan",
            languages=[{
                "language_code": "ja",
                "name": "Japanese",
                "local_name": "日本語",
                "required_level": 0.0
            }],
            bounds={
                "north": 35.8187,
                "south": 35.5311,
                "east": 139.9224,
                "west": 139.5804
            },
            center={
                "lat": 35.6762,
                "lon": 139.6503
            },
            difficulty_level=20.0,
            requirements=None,  # Starting region
            total_pois=100,
            total_challenges=25,
            recommended_level=0.0
        ),
        Region(
            id="kyoto",
            name="Kyoto",
            local_name="京都",
            description="The cultural heart of Japan",
            languages=[{
                "language_code": "ja",
                "name": "Japanese",
                "local_name": "日本語",
                "required_level": 20.0
            }],
            bounds={
                "north": 35.1075,
                "south": 34.8705,
                "east": 135.8552,
                "west": 135.6155
            },
            center={
                "lat": 35.0116,
                "lon": 135.7681
            },
            difficulty_level=40.0,
            requirements={"tokyo": 30.0},  # Requires Tokyo proficiency
            total_pois=80,
            total_challenges=20,
            recommended_level=30.0
        )
    ]
    
    for region in regions:
        test_db.add(region)
    test_db.commit()
    return regions

@pytest.fixture
def auth_user(client, test_db):
    """Get the user created by auth_headers fixture"""
    # Try to register the user (may already exist)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    # Either the user was just created or already exists
    # In either case, we can query by email since we know it
    return test_db.query(User).filter(User.email == "test@example.com").first()

def test_list_regions_no_progress(client, auth_headers, test_regions):
    """Test listing regions when user has no progress"""
    response = client.get("/api/v1/map/regions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert len(data["data"]) == 2
    
    # Tokyo should be available (starting region)
    tokyo = next(r for r in data["data"] if r["id"] == "tokyo")
    assert tokyo["is_available"] is True
    assert tokyo["requirements"] is None
    
    # Kyoto should be locked
    kyoto = next(r for r in data["data"] if r["id"] == "kyoto")
    assert kyoto["is_available"] is False
    assert kyoto["requirements"] == {"tokyo": 30.0}

def test_list_regions_with_progress(client, auth_headers, test_regions, test_db, auth_user):
    """Test listing regions when user has sufficient progress"""
    # Add progress for Tokyo using the authenticated user
    progress = UserProgress(
        user_id=auth_user.id,  # Use auth_user instead of test_user
        language="japanese",
        region="tokyo",
        proficiency_level=35.0  # Above required 30.0
    )
    test_db.add(progress)
    test_db.commit()
    
    response = client.get("/api/v1/map/regions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    
    # Both regions should be available
    tokyo = next(r for r in data["data"] if r["id"] == "tokyo")
    kyoto = next(r for r in data["data"] if r["id"] == "kyoto")
    
    assert tokyo["is_available"] is True
    assert kyoto["is_available"] is True
    assert kyoto["requirements"] is None  # Requirements met, should be None

def test_list_regions_insufficient_progress(client, auth_headers, test_regions, test_db, auth_user):
    """Test listing regions when user has insufficient progress"""
    # Add progress for Tokyo but below required level
    progress = UserProgress(
        user_id=auth_user.id,  # Use auth_user instead of test_user
        language="japanese",
        region="tokyo",
        proficiency_level=25.0  # Below required 30.0
    )
    test_db.add(progress)
    test_db.commit()
    
    response = client.get("/api/v1/map/regions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    
    kyoto = next(r for r in data["data"] if r["id"] == "kyoto")
    assert kyoto["is_available"] is False
    assert kyoto["requirements"] == {"tokyo": 30.0}