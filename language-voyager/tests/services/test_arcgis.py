import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from datetime import datetime, timedelta
from app.services.arcgis import ArcGISService
from app.models.arcgis_usage import ArcGISUsage

@pytest.fixture
def mock_redis():
    with patch('app.services.arcgis.redis_client') as mock_redis:
        yield mock_redis

@pytest.fixture
def mock_aiohttp_session():
    with patch('aiohttp.ClientSession') as mock_session:
        mock_context = MagicMock()
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = {"result": "test"}
        mock_context.__aenter__.return_value = mock_response
        mock_session.return_value.get.return_value = mock_context
        yield mock_session

@pytest.fixture
def arcgis_service(test_db):
    return ArcGISService(test_db)

@pytest.mark.asyncio
async def test_credit_usage_tracking(arcgis_service, test_db, mock_aiohttp_session):
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
    # Add usage records up to daily credit limit
    credits_per_op = 0.04
    num_ops = int(arcgis_service.api_settings.ARCGIS_MAX_CREDITS_PER_DAY / credits_per_op)
    
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
    # Add usage records up to warning threshold (80%)
    limit = ArcGISUsage.MONTHLY_LIMITS["geocoding"]
    num_ops = int(limit * 0.85)  # 85% of limit to trigger warning
    
    for _ in range(num_ops):
        usage = ArcGISUsage(
            operation_type="geocoding",
            credits_used=0.04,
            timestamp=datetime.utcnow()
        )
        test_db.add(usage)
    test_db.commit()
    
    # Check if alert is triggered
    within_limit, percentage, alert_level = await arcgis_service._check_usage_limits("geocoding")
    assert within_limit is True
    assert percentage > 80
    assert alert_level == "warning"

@pytest.mark.asyncio
async def test_error_handling(arcgis_service, mock_aiohttp_session):
    # Setup mock API error
    mock_response = MagicMock()
    mock_response.status = 403
    mock_context = MagicMock()
    mock_context.__aenter__.return_value = mock_response
    mock_aiohttp_session.return_value.get.return_value = mock_context
    
    with pytest.raises(HTTPException) as exc_info:
        await arcgis_service._make_request("test", {}, "geocoding")
    assert exc_info.value.status_code == 403