import pytest
from sqlalchemy.exc import IntegrityError
from app.models.user import User

def test_create_user(test_db):
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="somehash",
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    
    fetched_user = test_db.query(User).first()
    assert fetched_user.email == "test@example.com"
    assert fetched_user.username == "testuser"
    assert fetched_user.is_active == True

def test_unique_email_constraint(test_db):
    user1 = User(
        email="test@example.com",
        username="user1",
        hashed_password="hash1"
    )
    test_db.add(user1)
    test_db.commit()
    
    user2 = User(
        email="test@example.com",
        username="user2",
        hashed_password="hash2"
    )
    test_db.add(user2)
    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()

def test_unique_username_constraint(test_db):
    user1 = User(
        email="user1@example.com",
        username="testuser",
        hashed_password="hash1"
    )
    test_db.add(user1)
    test_db.commit()
    
    user2 = User(
        email="user2@example.com",
        username="testuser",
        hashed_password="hash2"
    )
    test_db.add(user2)
    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()

def test_default_values(test_db):
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hash"
    )
    test_db.add(user)
    test_db.commit()
    
    fetched_user = test_db.query(User).first()
    assert fetched_user.is_active == True
    assert fetched_user.is_superuser == False
    assert fetched_user.created_at is not None
    assert fetched_user.updated_at is not None