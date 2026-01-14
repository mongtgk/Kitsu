from datetime import datetime, timezone
from typing import Any, Dict

import jwt

from ..config import settings
from ..errors.security import ExpiredTokenError, InvalidTokenError
from ..utils.security import hash_refresh_token


def _parse_token_payload(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.ExpiredSignatureError as exc:
        raise ExpiredTokenError from exc
    except jwt.InvalidTokenError as exc:
        raise InvalidTokenError from exc


def validate_access_token(token: str) -> Dict[str, Any]:
    payload = _parse_token_payload(token)

    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise InvalidTokenError()

    return payload


def validate_refresh_token(token: str) -> str:
    if not token or not isinstance(token, str):
        raise InvalidTokenError()
    return hash_refresh_token(token)
