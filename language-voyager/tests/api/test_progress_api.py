import pytest
from fastapi.testclient import TestClient

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

def test_create_progress(client, auth_headers):
    response = client.post(
        "/api/v1/progress/",
        headers=auth_headers,
        json={
            "language": "japanese",
            "region": "tokyo",
            "activity_type": "vocabulary",
            "score": 85,
            "metadata": {
                "id": "vocab_1",
                "words": ["こんにちは", "さようなら"]
            }
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["message"] == "Progress updated successfully"
    assert data["data"]["language"] == "japanese"
    assert data["data"]["region"] == "tokyo"
    assert data["data"]["proficiency_level"] == 85.0
    assert "vocab_1" in data["data"]["completed_challenges"]

def test_get_overall_progress(client, auth_headers):
    # First create some progress
    client.post(
        "/api/v1/progress/",
        headers=auth_headers,
        json={
            "language": "japanese",
            "region": "tokyo",
            "activity_type": "vocabulary",
            "score": 85,
            "metadata": {"id": "vocab_1"}
        }
    )
    
    response = client.get("/api/v1/progress/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["message"] == "Progress retrieved successfully"
    assert data["data"]["total_languages"] == 1
    assert data["data"]["total_regions"] == 1
    assert "japanese" in data["data"]["languages"]
    assert data["data"]["languages"]["japanese"] == 85.0

def test_get_language_progress(client, auth_headers):
    # Create progress for Japanese
    client.post(
        "/api/v1/progress/",
        headers=auth_headers,
        json={
            "language": "japanese",
            "region": "tokyo",
            "activity_type": "vocabulary",
            "score": 85,
            "metadata": {"id": "vocab_1"}
        }
    )
    
    response = client.get("/api/v1/progress/language/japanese", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["message"] == "Progress retrieved for language: japanese"
    assert len(data["data"]) == 1
    assert data["data"][0]["language"] == "japanese"
    assert data["data"][0]["region"] == "tokyo"
    assert data["data"][0]["proficiency_level"] == 85.0

def test_get_region_progress(client, auth_headers):
    # Create progress for Tokyo region
    client.post(
        "/api/v1/progress/",
        headers=auth_headers,
        json={
            "language": "japanese",
            "region": "tokyo",
            "activity_type": "vocabulary",
            "score": 85,
            "metadata": {"id": "vocab_1"}
        }
    )
    
    response = client.get("/api/v1/progress/region/tokyo", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["message"] == "Progress retrieved for region: tokyo"
    assert len(data["data"]) == 1
    assert data["data"][0]["language"] == "japanese"
    assert data["data"][0]["region"] == "tokyo"
    assert data["data"][0]["proficiency_level"] == 85.0

def test_unauthorized_access(client):
    response = client.get("/api/v1/progress/")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_multiple_progress_updates(client, auth_headers):
    # Create first progress entry
    client.post(
        "/api/v1/progress/",
        headers=auth_headers,
        json={
            "language": "japanese",
            "region": "tokyo",
            "activity_type": "vocabulary",
            "score": 85,
            "metadata": {"id": "vocab_1"}
        }
    )
    
    # Create second progress entry for same language/region
    response = client.post(
        "/api/v1/progress/",
        headers=auth_headers,
        json={
            "language": "japanese",
            "region": "tokyo",
            "activity_type": "vocabulary",
            "score": 90,
            "metadata": {"id": "vocab_2"}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert data["data"]["proficiency_level"] == 87.5  # Average of 85 and 90
    assert len(data["data"]["completed_challenges"]) == 2