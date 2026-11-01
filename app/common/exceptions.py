"""Domain and application exception hierarchy."""

from typing import Optional, Any


class AppException(Exception):
    """Base exception for all application errors."""
    def __init__(self, message: str, code: Optional[str] = None, details: Optional[Any] = None) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details


class EntityNotFoundError(AppException):
    """Raised when a requested entity/record does not exist."""
    pass


class DuplicateEntityError(AppException):
    """Raised when a unique constraint or code collision occurs."""
    pass


class ValidationError(AppException):
    """Raised when an entity fails domain or schema validation."""
    pass


class SecurityError(AppException):
    """Raised when cryptographic or access integrity fails."""
    pass


class StorageError(AppException):
    """Raised when managed file attachment operations fail."""
    pass


class BackupError(AppException):
    """Raised when backup or restore integrity operations fail."""
    pass
