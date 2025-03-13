import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database.config import Base, get_db
from app.main import app
from app.core.config import get_settings

# Test database URL
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture
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
def client(test_db):
    # Create test client with database session
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def test_settings():
    return get_settings()