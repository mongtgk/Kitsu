import asyncio
import os

import pytest
from starlette.requests import Request

# Ensure required environment variables are present for module imports.
os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db"
)

from app.auth.helpers import require_any_permission, require_permission
from app.errors import PermissionError


def make_request(path: str = "/collections") -> Request:
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "headers": [],
        }
    )


def test_require_permission_allows_guest_read() -> None:
    checker = require_permission("read:content")
    asyncio.run(checker(request=make_request("/collections"), user=None))


def test_require_permission_denies_and_logs(caplog: pytest.LogCaptureFixture) -> None:
    checker = require_permission("write:profile")
    with caplog.at_level("WARNING"):
        with pytest.raises(PermissionError):
            asyncio.run(checker(request=make_request("/collections"), user=None))
    assert any("write:profile" in record.getMessage() for record in caplog.records)
    assert any("/collections" in record.getMessage() for record in caplog.records)


def test_require_any_permission_allows_when_one_matches() -> None:
    checker = require_any_permission(["write:profile", "read:content"])
    asyncio.run(checker(request=make_request("/collections"), user=None))
