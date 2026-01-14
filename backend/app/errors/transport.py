from typing import Any

from fastapi import status


class AppError(Exception):
    code: str = "APP_ERROR"
    message: str = "Application error"
    status_code: int = status.HTTP_400_BAD_REQUEST
    details: Any | None = None

    def __init__(
        self,
        message: str | None = None,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: Any | None = None,
    ):
        if message is not None:
            self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        if details is not None:
            self.details = details

        super().__init__(self.message)


def error_payload(code: str, message: str, details: Any | None = None) -> dict[str, Any]:
    return {"code": code, "message": message, "details": details}

