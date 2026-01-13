import os
from typing import Iterable

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
import pytest

os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/db"
)

from app.dependencies import get_db  # noqa: E402
from app.errors import AppError, AuthError, error_payload  # noqa: E402
from app.routers.auth import router  # noqa: E402
from app.use_cases.auth.register_user import AuthTokens  # noqa: E402
from app.utils.rate_limit import auth_rate_limiter  # noqa: E402


@pytest.fixture(autouse=True)
def clear_rate_limiter():
    auth_rate_limiter.clear()
    yield
    auth_rate_limiter.clear()


def make_app(
    monkeypatch: pytest.MonkeyPatch,
    *,
    login_handler=None,
    refresh_handler=None,
) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    async def fake_get_db():
        yield None

    app.dependency_overrides[get_db] = fake_get_db

    if login_handler is not None:
        monkeypatch.setattr("app.routers.auth.login_user", login_handler)
    if refresh_handler is not None:
        monkeypatch.setattr("app.routers.auth.refresh_session", refresh_handler)

    @app.exception_handler(AppError)
    async def handle_app_error(_request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(exc.code, exc.message, exc.details),
        )

    return TestClient(app)


def test_login_rate_limit_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing_login(_db, _email, _password):
        raise AuthError()

    client = make_app(monkeypatch, login_handler=failing_login)
    payload = {"email": "user@example.com", "password": "bad-password"}

    for _ in range(5):
        response = client.post("/auth/login", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post("/auth/login", json=payload)

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.json()["code"] == "RATE_LIMITED"


def test_login_success_resets_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    outcomes: Iterable[str] = iter(
        [
            "fail",
            "fail",
            "success",
            "fail",
            "fail",
            "fail",
            "fail",
            "fail",
            "fail",
        ]
    )

    async def login_handler(_db, _email, _password):
        result = next(outcomes)
        if result == "fail":
            raise AuthError()
        return AuthTokens(access_token="a", refresh_token="r")

    client = make_app(monkeypatch, login_handler=login_handler)
    payload = {"email": "user@example.com", "password": "bad-password"}

    for _ in range(2):
        response = client.post("/auth/login", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post("/auth/login", json=payload)
    assert response.status_code == status.HTTP_200_OK

    for _ in range(5):
        response = client.post("/auth/login", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post("/auth/login", json=payload)
    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.json()["code"] == "RATE_LIMITED"


def test_refresh_rate_limit_exceeded(monkeypatch: pytest.MonkeyPatch) -> None:
    async def failing_refresh(_db, _token):
        raise AuthError()

    client = make_app(monkeypatch, refresh_handler=failing_refresh)
    payload = {"refresh_token": "bad-refresh-token"}

    for _ in range(5):
        response = client.post("/auth/refresh", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    response = client.post("/auth/refresh", json=payload)

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.json()["code"] == "RATE_LIMITED"
