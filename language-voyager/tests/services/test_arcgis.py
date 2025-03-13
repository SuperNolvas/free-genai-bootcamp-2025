import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import HTTPException
from datetime import datetime, timedelta
import aiohttp
from app.services.arcgis import ArcGISService
from app.models.arcgis_usage import ArcGISUsage
from app.core.config import get_settings

@pytest.fixture
def mock_redis():
    with patch('app.services.arcgis.redis_client') as mock_redis:
        yield mock_redis

@pytest.fixture
def mock_response():
    response = AsyncMock()
    response.status = 200
    response.json.return_value = {"result": "test"}
    return response

@pytest.fixture
def mock_aiohttp_session(mock_response):
    """Create a properly mocked aiohttp session"""
    async def get(*args, **kwargs):
        return mock_response
    
    session = AsyncMock()
    session.get = AsyncMock(side_effect=get)
    
    with patch('aiohttp.ClientSession', return_value=session):
        yield session

@pytest.fixture
def arcgis_service(test_db):
    return ArcGISService(test_db)

@pytest.mark.asyncio
async def test_credit_usage_tracking(arcgis_service, test_db, mock_aiohttp_session, mock_response):
    # Reset any existing usage
    test_db.query(ArcGISUsage).delete()
    test_db.commit()
    
    # Test making a request and tracking credits
    params = {"location": "test"}
    await arcgis_service._make_request("geocoding", params, "geocoding")
    
    # Verify credit usage was logged
    usage = test_db.query(ArcGISUsage).first()
    assert usage is not None
    assert usage.operation_type == "geocoding"
    assert usage.credits_used == 0.04  # Geocoding credit cost
    assert usage.cached is False

@pytest.mark.asyncio
async def test_cache_hits(arcgis_service, test_db, mock_redis, mock_aiohttp_session):
    # Reset any existing usage
    test_db.query(ArcGISUsage).delete()
    test_db.commit()
    
    # Setup mock cache hit
    mock_redis.get.return_value = b'{"result": "cached"}'
    
    params = {"location": "test"}
    result = await arcgis_service._make_request("geocoding", params, "geocoding")
    
    # Verify cache hit was logged
    usage = test_db.query(ArcGISUsage).first()
    assert usage.cached is True
    assert result == {"result": "cached"}

@pytest.mark.asyncio
async def test_monthly_limit_enforcement(arcgis_service, test_db):
    # Reset any existing usage
    test_db.query(ArcGISUsage).delete()
    test_db.commit()
    
    # Add usage records up to limit
    for _ in range(500):  # Place search limit
        usage = ArcGISUsage(
            operation_type="place_search",
            credits_used=0.04,
            timestamp=datetime.utcnow()
        )
        test_db.add(usage)
    test_db.commit()
    
    # Verify limit is enforced
    with pytest.raises(HTTPException) as exc_info:
        await arcgis_service._check_usage_limits("place_search")
    assert exc_info.value.status_code == 429
    assert "Monthly limit" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_daily_credit_limit(arcgis_service, test_db):
    # Reset any existing usage
    test_db.query(ArcGISUsage).delete()
    test_db.commit()
    
    # Add usage records up to daily credit limit
    credits_per_op = 0.04
    num_ops = int(arcgis_service.settings.ARCGIS_MAX_CREDITS_PER_DAY / credits_per_op)
    
    for _ in range(num_ops):
        usage = ArcGISUsage(
            operation_type="geocoding",
            credits_used=credits_per_op,
            timestamp=datetime.utcnow()
        )
        test_db.add(usage)
    test_db.commit()
    
    # Verify credit limit is enforced
    with pytest.raises(HTTPException) as exc_info:
        await arcgis_service._check_usage_limits("geocoding")
    assert exc_info.value.status_code == 429
    assert "Daily ArcGIS credit limit reached" in str(exc_info.value.detail)

@pytest.mark.asyncio
async def test_usage_alerts(arcgis_service, test_db):
    # Reset any existing usage
    test_db.query(ArcGISUsage).delete()
    test_db.commit()
    
    # Add usage records up to warning threshold (80%)
    limit = ArcGISUsage.MONTHLY_LIMITS["geocoding"]
    num_ops = int(limit * 0.85)  # 85% of limit
    
    for _ in range(num_ops):
        usage = ArcGISUsage(
            operation_type="geocoding",
            credits_used=0.04,
            timestamp=datetime.utcnow()
        )
        test_db.add(usage)
    test_db.commit()
    
    # Check if alert is triggered
    within_limit, percentage, alert_level = ArcGISUsage.check_monthly_limit(test_db, "geocoding")
    assert within_limit is True
    assert percentage >= 80  # Should be around 85%
    assert alert_level == "warning"

@pytest.mark.asyncio
async def test_error_handling(arcgis_service, mock_aiohttp_session):
    # Create a mock response with error status
    error_response = AsyncMock()
    error_response.status = 403
    error_response.json.return_value = {"error": "Forbidden"}
    
    # Update the session's get method to return error response
    async def get_error(*args, **kwargs):
        return error_response
    
    mock_aiohttp_session.get = AsyncMock(side_effect=get_error)
    
    with pytest.raises(HTTPException) as exc_info:
        await arcgis_service._make_request("test", {}, "geocoding")
    assert exc_info.value.status_code == 403

@pytest.mark.asyncio
@pytest.mark.integration
async def test_real_arcgis_integration(test_db):
    """
    This test makes a real API call to ArcGIS to verify the API key is working.
    Skip this test if you don't want to use actual credits.
    """
    settings = get_settings()
    if not settings.ARCGIS_API_KEY:
        pytest.skip("No ArcGIS API key configured")
    
    service = ArcGISService(test_db)
    
    # Test a simple geocoding request
    result = await service.geocode_location("Tokyo Station, Japan")
    
    assert result is not None
    assert "candidates" in result  # ArcGIS geocoding returns candidates
    assert len(result["candidates"]) > 0
    
    # Verify a usage record was created
    usage = test_db.query(ArcGISUsage).first()
    assert usage is not None
    assert usage.operation_type == "geocoding"
    assert usage.credits_used == 0.04
    assert usage.cached is False