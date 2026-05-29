class LeaveError(Exception):
    """Base exception for leave management domain errors."""

    status_code = 422

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class NotFoundError(LeaveError):
    """Raised when an expected resource does not exist."""

    status_code = 404


class AuthorizationError(LeaveError):
    """Raised when an employee is not allowed to perform an action."""

    status_code = 403


class ConflictError(LeaveError):
    """Raised when an operation conflicts with current workflow state."""

    status_code = 409


class ValidationError(LeaveError):
    """Raised when input is semantically invalid."""

    status_code = 422


class InsufficientBalanceError(ValidationError):
    pass


class OverlappingLeaveError(ConflictError):
    pass


class SelfApprovalError(AuthorizationError):
    pass


class CannotModifyApprovedLeaveError(ConflictError):
    pass