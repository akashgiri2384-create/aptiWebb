"""
Custom exceptions for Quizzy platform.
"""


class QuizzyException(Exception):
    """Base exception for Quizzy-specific errors."""
    pass


class InsufficientKeysException(QuizzyException):
    """Raised when user doesn't have enough keys to unlock a daily quiz."""
    pass


class QuizAlreadyAttemptedException(QuizzyException):
    """Raised when user tries to retake a quiz that can't be retaken."""
    pass


class InvalidQuizAttemptException(QuizzyException):
    """Raised when quiz attempt data is invalid."""
    pass


class AdFraudDetectedException(QuizzyException):
    """Raised when ad fraud is detected."""
    pass


class RateLimitExceededException(QuizzyException):
    """Raised when rate limit is exceeded."""
    pass
