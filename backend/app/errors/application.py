class ApplicationError(Exception):
    code: str = "APPLICATION_ERROR"
    message: str = "Application error"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class RateLimitExceeded(ApplicationError):
    code = "RATE_LIMITED"
    message = "Rate limit exceeded"


class PermissionDenied(ApplicationError):
    code = "PERMISSION_DENIED"
    message = "Insufficient permissions"


class AuthenticationError(ApplicationError):
    code = "AUTHENTICATION_FAILED"
    message = "Authentication failed"


class OrchestrationError(ApplicationError):
    code = "ORCHESTRATION_ERROR"
    message = "Orchestration failed"

