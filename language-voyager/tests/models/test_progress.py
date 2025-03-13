import pytest
from app.models.user import User
from app.models.progress import UserProgress

@pytest.fixture
def test_user(test_db):
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hash"
    )
    test_db.add(user)
    test_db.commit()
    return user

def test_create_progress(test_db, test_user):
    progress = UserProgress(
        user_id=test_user.id,
        language="japanese",
        region="tokyo",
        proficiency_level=85.0,
        completed_challenges=[{"id": "vocab_1", "score": 85}],
        vocabulary_mastered={"こんにちは": 0.95},
        last_location="35.6762,139.6503"
    )
    test_db.add(progress)
    test_db.commit()
    
    fetched_progress = test_db.query(UserProgress).first()
    assert fetched_progress.language == "japanese"
    assert fetched_progress.region == "tokyo"
    assert fetched_progress.proficiency_level == 85.0
    assert len(fetched_progress.completed_challenges) == 1
    assert fetched_progress.vocabulary_mastered["こんにちは"] == 0.95
    assert fetched_progress.last_location == "35.6762,139.6503"

def test_progress_user_relationship(test_db, test_user):
    progress = UserProgress(
        user_id=test_user.id,
        language="japanese",
        region="tokyo",
        proficiency_level=85.0
    )
    test_db.add(progress)
    test_db.commit()
    
    # Test relationship from progress to user
    fetched_progress = test_db.query(UserProgress).first()
    assert fetched_progress.user.id == test_user.id
    assert fetched_progress.user.email == test_user.email
    
    # Test relationship from user to progress
    fetched_user = test_db.query(User).first()
    assert len(fetched_user.progress) == 1
    assert fetched_user.progress[0].language == "japanese"

def test_multiple_progress_entries(test_db, test_user):
    # Add progress for different languages/regions
    progress1 = UserProgress(
        user_id=test_user.id,
        language="japanese",
        region="tokyo",
        proficiency_level=85.0
    )
    progress2 = UserProgress(
        user_id=test_user.id,
        language="japanese",
        region="osaka",
        proficiency_level=75.0
    )
    test_db.add_all([progress1, progress2])
    test_db.commit()
    
    # Check user has multiple progress entries
    user_progress = test_db.query(UserProgress).filter_by(user_id=test_user.id).all()
    assert len(user_progress) == 2
    
    # Verify progress entries are distinct
    assert user_progress[0].region != user_progress[1].region
    assert user_progress[0].proficiency_level != user_progress[1].proficiency_level

def test_progress_timestamps(test_db, test_user):
    progress = UserProgress(
        user_id=test_user.id,
        language="japanese",
        region="tokyo",
        proficiency_level=85.0
    )
    test_db.add(progress)
    test_db.commit()
    
    fetched_progress = test_db.query(UserProgress).first()
    assert fetched_progress.created_at is not None
    assert fetched_progress.updated_at is not None