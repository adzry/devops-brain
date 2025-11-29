"""
SDK Exceptions

Custom exceptions for the DevOps Brain SDK.
"""


class DevOpsBrainError(Exception):
    """Base exception for SDK errors."""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class AuthenticationError(DevOpsBrainError):
    """Authentication failed."""
    pass


class RateLimitError(DevOpsBrainError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: float = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class TaskError(DevOpsBrainError):
    """Task execution failed."""
    
    def __init__(self, message: str, task_id: str = None, **kwargs):
        super().__init__(message, **kwargs)
        self.task_id = task_id


class ValidationError(DevOpsBrainError):
    """Request validation failed."""
    pass


class TimeoutError(DevOpsBrainError):
    """Request timed out."""
    pass
