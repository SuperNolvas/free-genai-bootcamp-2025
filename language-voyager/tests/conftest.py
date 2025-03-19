import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.database.config import Base, get_db
from app.main import app
from app.core.config import get_settings
from app.models.user import User
from app.models.progress import UserProgress
from app.models.achievement import Achievement, AchievementDefinition
from app.models.region import Region
from app.models.poi import PointOfInterest
from app.auth.utils import get_password_hash

# Test database URL
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    # Create all tables at the start of testing
    Base.metadata.create_all(bind=engine)
    yield
    # Clean up after all tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def test_user(test_db: Session):
    """Create a test user for authentication"""
    # First try to get existing user
    user = test_db.query(User).filter(User.email == "test@example.com").first()
    
    if not user:
        user = User(
            email="test@example.com",
            hashed_password=get_password_hash("testpass123"),
            is_active=True,
            username="testuser"
        )
        test_db.add(user)
        try:
            test_db.commit()
            test_db.refresh(user)
        except Exception:
            test_db.rollback()
            raise
    
    # Make sure the instance is attached to the session
    if not test_db.is_active:
        test_db.begin()
    if user not in test_db:
        user = test_db.merge(user)
    
    return user

@pytest_asyncio.fixture
async def async_client(test_db):
    """Create async test client"""
    def override_get_db():
        try:
            yield test_db
        finally:
            if test_db.is_active:
                test_db.rollback()
    
    app.dependency_overrides[get_db] = override_get_db
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def client():
    with TestClient(app) as client:
        yield client

@pytest.fixture
def test_settings():
    return get_settings()

@pytest.fixture(scope="function")
def test_db_cleanup(test_db):
    """Clean up the test database after each test"""
    yield test_db
    # Clean up users and verification tokens
    test_db.query(User).delete()
    test_db.commit()