from datetime import datetime, timezone
from typing import Any, Dict

import jwt

from ..config import settings
from ..utils.security import hash_refresh_token


class InvalidTokenError(Exception):
    """Raised when a token cannot be parsed or is malformed."""


class ExpiredTokenError(Exception):
    """Raised when a token has expired."""


def parse_token_payload(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredTokenError from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError from exc


def validate_access_token(token: str) -> Dict[str, Any]:
    payload = parse_token_payload(token)

    exp = payload.get("exp")
    if exp is None:
        raise InvalidTokenError()
    # Ensure expiration is still valid if exp is a numeric timestamp
    if isinstance(exp, (int, float)):
        if datetime.fromtimestamp(exp, tz=timezone.utc) <= datetime.now(timezone.utc):
            raise ExpiredTokenError()

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise InvalidTokenError()

    return payload


def validate_refresh_token(token: str) -> str:
    if not token or not isinstance(token, str):
        raise InvalidTokenError()
    return hash_refresh_token(token)
