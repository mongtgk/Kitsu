import os

import httpx
from fastapi import status
from fastapi.testclient import TestClient
import pytest

# Ensure required environment variables are present for module imports.
# These are defaults used only if not already set, avoiding test isolation issues.
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
    
    # Should return 204 No Content for OPTIONS preflight
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
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
    
    # Should return 204 No Content for OPTIONS preflight
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
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


def test_cors_preflight_with_disallowed_origin() -> None:
    """Test that OPTIONS preflight with disallowed origin returns 204 without CORS headers."""
    client = TestClient(app)
    
    response = client.options(
        "/auth/login",
        headers={
            "Origin": "http://evil.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    
    # Should still return 204 (graceful handling)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Should NOT include Access-Control-Allow-Origin header for disallowed origin
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_with_trailing_slash() -> None:
    """Test that OPTIONS preflight with origin containing trailing slash is handled gracefully."""
    client = TestClient(app)
    
    response = client.options(
        "/auth/login",
        headers={
            "Origin": "http://localhost:3000/",  # Trailing slash
            "Access-Control-Request-Method": "POST",
        },
    )
    
    # Should return 204 (doesn't match allowed origin exactly)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Should NOT include CORS headers since origin doesn't match exactly
    assert "access-control-allow-origin" not in response.headers


def test_cors_preflight_auth_refresh() -> None:
    """Test that OPTIONS preflight request to /auth/refresh works correctly."""
    client = TestClient(app)
    
    response = client.options(
        "/auth/refresh",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_cors_preflight_auth_logout() -> None:
    """Test that OPTIONS preflight request to /auth/logout works correctly."""
    client = TestClient(app)
    
    response = client.options(
        "/auth/logout",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
