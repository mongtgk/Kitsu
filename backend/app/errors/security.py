class SecurityError(Exception):
    code: str = "SECURITY_ERROR"
    message: str = "Security error"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class InvalidTokenError(SecurityError):
    code = "INVALID_TOKEN"
    message = "Invalid token"


class ExpiredTokenError(SecurityError):
    code = "TOKEN_EXPIRED"
    message = "Token has expired"


class TokenTypeError(SecurityError):
    code = "TOKEN_TYPE_INVALID"
    message = "Invalid token type"

