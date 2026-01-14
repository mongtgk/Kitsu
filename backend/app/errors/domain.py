class DomainError(Exception):
    code: str = "DOMAIN_ERROR"
    message: str = "Domain error"

    def __init__(self, message: str | None = None) -> None:
        if message is not None:
            self.message = message
        super().__init__(self.message)


class BusinessRuleViolation(DomainError):
    code = "BUSINESS_RULE_VIOLATION"
    message = "Business rule violated"


class EntityNotFound(DomainError):
    code = "NOT_FOUND"
    message = "Entity not found"


class AlreadyExists(DomainError):
    code = "ALREADY_EXISTS"
    message = "Entity already exists"


class InvalidState(DomainError):
    code = "INVALID_STATE"
    message = "Invalid entity state"

