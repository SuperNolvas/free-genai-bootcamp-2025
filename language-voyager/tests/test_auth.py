from fastapi.testclient import TestClient
import pytest
from app.auth.utils import create_access_token
from sqlalchemy import text
import uuid

@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpass123"
    }

@pytest.fixture(autouse=True)
def cleanup_verification_state(test_db):
    yield
    # Clean up test users
    test_db.execute(text("DELETE FROM users WHERE email LIKE '%@example.com' OR username LIKE 'testuser%'"))
    test_db.commit()

@pytest.fixture(autouse=True)
def setup_test_state(test_db):
    # Clean up before test
    test_db.execute(text("DELETE FROM users WHERE email LIKE '%@example.com' OR username LIKE 'testuser%'"))
    test_db.commit()
    yield

def test_register_user(client, test_db):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_register@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    
    # Check basic user data
    assert data["email"] == "test_register@example.com"
    assert data["username"] == "testuser"
    assert data["is_active"] == False  # User starts inactive until email verification
    assert not data["email_verified"]  # Email should not be verified yet
    
    # Get verification token from response
    assert "verification_token" in data
    verification_token = data["verification_token"]
    
    # Verify email
    verify_response = client.post(
        f"/api/v1/auth/verify-email?token={verification_token}"
    )
    assert verify_response.status_code == 200
    
    # Login after verification
    login_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test_register@example.com",
            "password": "testpass123"
        }
    )
    assert login_response.status_code == 200

def test_register_duplicate_email(client, test_db):
    # Register first user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_duplicate@example.com",
            "username": "testuser1",
            "password": "testpass123"
        }
    )
    
    # Try to register with same email
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_duplicate@example.com",
            "username": "testuser2",
            "password": "testpass123"
        }
    )
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]

def test_login_success(client, test_db):
    # Register user first
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_login@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    verification_token = response.json()["verification_token"]
    
    # Verify email before attempting login 
    verify_response = client.post(
        f"/api/v1/auth/verify-email?token={verification_token}"
    )
    assert verify_response.status_code == 200

    # Try to login after verification
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test_login@example.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_unverified_user(client, test_db):
    # Register but don't verify
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_unverified@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    # Try to login without verification
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test_unverified@example.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == 401
    assert "Please verify your email" in response.json()["detail"]

def test_login_wrong_password(client, test_db):
    # Register user first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_wrong_pass@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    # Try to login with wrong password
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test_wrong_pass@example.com",
            "password": "wrongpass"
        }
    )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_get_current_user(client, test_db):
    # Register and get verification token
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_current@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    verification_token = register_response.json()["verification_token"]
    
    # Verify email
    verify_response = client.post(
        f"/api/v1/auth/verify-email?token={verification_token}"
    )
    assert verify_response.status_code == 200
    
    # Login after verification
    login_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test_current@example.com",
            "password": "testpass123"
        }
    )
    token = login_response.json()["access_token"]

    # Get current user profile
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == "test_current@example.com"
    assert data["username"] == "testuser"
    assert data["is_active"] == True  # Should be active after verification
    assert data["email_verified"] == True  # Email should show as verified

def test_protected_route_no_token(client, test_db):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_register_sends_verification_email(client, test_db):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_verify_email@example.com",
            "username": "testuser_verify",  # Use unique username
            "password": "testpass123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert not data["is_active"]  # User should start inactive
    assert "verification_token" in data  # Should include verification token
    
    # Verify user exists in database but is inactive
    user_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test_verify_email@example.com",
            "password": "testpass123"
        }
    )
    assert user_response.status_code == 401
    assert "Please verify your email" in user_response.json()["detail"]

def test_verify_email(client, test_db):
    # Register a new user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_verification@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    # Get verification token from database
    from app.models.user import User
    user = test_db.query(User).filter(User.email == "test_verification@example.com").first()
    token = user.verification_token
    assert token is not None
    
    # Verify email
    response = client.post(f"/api/v1/auth/verify-email?token={token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Email verified successfully"
    
    # Verify user can now log in
    login_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test_verification@example.com",
            "password": "testpass123"
        }
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

def test_verify_email_invalid_token(client):
    response = client.post("/api/v1/auth/verify-email?token=invalid_token")
    assert response.status_code == 400
    assert "Invalid or expired verification token" in response.json()["detail"]

def test_request_password_reset(client, test_db):
    # Register and verify a user first
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_reset_request@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    # Request password reset
    response = client.post(
        "/api/v1/auth/request-password-reset",
        json={"email": "test_reset_request@example.com"}
    )
    assert response.status_code == 200
    assert "password reset link has been sent" in response.json()["message"]

def test_reset_password(client, test_db):
    # Register a user
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test_reset@example.com",
            "username": "testuser",
            "password": "testpass123"
        }
    )
    
    # Request password reset
    client.post(
        "/api/v1/auth/request-password-reset",
        json={"email": "test_reset@example.com"}
    )
    
    # Get reset token from database
    from app.models.user import User
    user = test_db.query(User).filter(User.email == "test_reset@example.com").first()
    token = user.password_reset_token
    assert token is not None
    
    # Reset password
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": token,
            "new_password": "newpass123"
        }
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successfully"
    
    # Verify can login with new password
    login_response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "test_reset@example.com",
            "password": "newpass123"
        }
    )
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()

def test_reset_password_invalid_token(client):
    response = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": "invalid_token",
            "new_password": "newpass123"
        }
    )
    assert response.status_code == 400
    assert "Invalid or expired reset token" in response.json()["detail"]