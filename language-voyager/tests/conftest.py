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
from app.auth.utils import get_password_hash

# Test database URL
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def test_db():
    # Create test database in memory
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Add SQLite timestamp update trigger
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    @event.listens_for(engine, "connect")
    def enable_sqlite_timestamps(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("CREATE TRIGGER IF NOT EXISTS update_timestamp "
                      "AFTER UPDATE ON users "
                      "FOR EACH ROW "
                      "BEGIN "
                      "   UPDATE users SET updated_at = CURRENT_TIMESTAMP "
                      "   WHERE id = NEW.id; "
                      "END;")
        cursor.execute("CREATE TRIGGER IF NOT EXISTS update_progress_timestamp "
                      "AFTER UPDATE ON user_progress "
                      "FOR EACH ROW "
                      "BEGIN "
                      "   UPDATE user_progress SET updated_at = CURRENT_TIMESTAMP "
                      "   WHERE id = NEW.id; "
                      "END;")
        cursor.close()
    
    # Override the get_db dependency
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal()
    
    # Drop tables after tests
    Base.metadata.drop_all(bind=engine)

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

@pytest.fixture
def client(test_db):
    """Synchronous client for non-async tests"""
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def test_settings():
    return get_settings()