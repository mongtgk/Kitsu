class DomainError(Exception):
    """Base class for domain-level errors."""


class BusinessRuleViolation(DomainError):
    """Raised when a business rule is violated."""

