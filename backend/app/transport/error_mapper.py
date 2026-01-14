from fastapi import status

from ..errors import (
    AlreadyExists,
    ApplicationError,
    AuthenticationError,
    BusinessRuleViolation,
    DomainError,
    EntityNotFound,
    ExpiredTokenError,
    InvalidState,
    InvalidTokenError,
    OrchestrationError,
    PermissionDenied,
    RateLimitExceeded,
    SecurityError,
    TokenTypeError,
)
from ..errors.transport import AppError

HANDLED_EXCEPTIONS = {
    EntityNotFound: (status.HTTP_404_NOT_FOUND, EntityNotFound.code, EntityNotFound.message),
    AlreadyExists: (status.HTTP_409_CONFLICT, AlreadyExists.code, AlreadyExists.message),
    InvalidState: (status.HTTP_400_BAD_REQUEST, InvalidState.code, InvalidState.message),
    BusinessRuleViolation: (
        status.HTTP_400_BAD_REQUEST,
        BusinessRuleViolation.code,
        BusinessRuleViolation.message,
    ),
    RateLimitExceeded: (
        status.HTTP_429_TOO_MANY_REQUESTS,
        RateLimitExceeded.code,
        RateLimitExceeded.message,
    ),
    PermissionDenied: (status.HTTP_403_FORBIDDEN, PermissionDenied.code, PermissionDenied.message),
    AuthenticationError: (
        status.HTTP_401_UNAUTHORIZED,
        AuthenticationError.code,
        AuthenticationError.message,
    ),
    OrchestrationError: (
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        OrchestrationError.code,
        OrchestrationError.message,
    ),
    InvalidTokenError: (status.HTTP_401_UNAUTHORIZED, InvalidTokenError.code, InvalidTokenError.message),
    ExpiredTokenError: (status.HTTP_401_UNAUTHORIZED, ExpiredTokenError.code, ExpiredTokenError.message),
    TokenTypeError: (status.HTTP_401_UNAUTHORIZED, TokenTypeError.code, TokenTypeError.message),
}


def map_exception(exc: Exception) -> AppError:
    for exc_type, (status_code, code, message) in HANDLED_EXCEPTIONS.items():
        if isinstance(exc, exc_type):
            return AppError(message=message, code=code, status_code=status_code)

    if isinstance(exc, DomainError):
        return AppError(
            message=exc.message if hasattr(exc, "message") else "Domain error",
            code=getattr(exc, "code", "DOMAIN_ERROR"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, SecurityError):
        return AppError(
            message=getattr(exc, "message", "Security error"),
            code=getattr(exc, "code", "SECURITY_ERROR"),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if isinstance(exc, ApplicationError):
        return AppError(
            message=getattr(exc, "message", "Application error"),
            code=getattr(exc, "code", "APPLICATION_ERROR"),
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    return AppError(
        message="Internal server error",
        code="INTERNAL_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


HANDLED_EXCEPTION_TYPES = tuple(HANDLED_EXCEPTIONS.keys())

