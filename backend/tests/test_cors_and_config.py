import os

import httpx
from fastapi import status
from fastapi.testclient import TestClient
import pytest

# Ensure required environment variables are present for module imports.
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db"
)

from app.main import app  # noqa: E402
from app.api.proxy.common import get_client  # noqa: E402


def test_cors_preflight_options_auth_login() -> None:
    """Test that OPTIONS preflight request to /auth/login returns successful status and CORS headers."""
    client = TestClient(app)
    
    response = client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    
    # Should return 200 OK for OPTIONS preflight
    assert response.status_code == status.HTTP_200_OK
    
    # Check CORS headers are present
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-methods" in response.headers
    assert "POST" in response.headers["access-control-allow-methods"]
    assert "access-control-allow-credentials" in response.headers
    assert response.headers["access-control-allow-credentials"] == "true"


def test_cors_preflight_options_auth_register() -> None:
    """Test that OPTIONS preflight request to /auth/register returns successful status and CORS headers."""
    client = TestClient(app)
    
    response = client.options(
        "/auth/register",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    
    # Should return 200 OK for OPTIONS preflight
    assert response.status_code == status.HTTP_200_OK
    
    # Check CORS headers are present
    assert "access-control-allow-origin" in response.headers
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


@pytest.mark.asyncio
async def test_httpx_client_follows_redirects() -> None:
    """Test that the httpx client created by get_client() has redirect following enabled."""
    client = await get_client()
    
    # Check that follow_redirects is True
    assert client.follow_redirects is True
    
    await client.aclose()
