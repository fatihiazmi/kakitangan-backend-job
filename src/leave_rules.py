from datetime import date

from src.models import LeaveRequest, LeaveStatus


def calculate_leave_days(start_date: date, end_date: date) -> int:
    """Return inclusive calendar days between start and end dates."""
    return (end_date - start_date).days + 1


def validate_leave_date_range(start_date: date, end_date: date) -> None:
    if start_date > end_date:
        raise ValueError("Start date must be before or equal to end date")

    if start_date < date.today():
        raise ValueError("Back-dated leave requests are not allowed")

    if calculate_leave_days(start_date, end_date) < 1:
        raise ValueError("Leave request must be at least 1 day")


def ensure_leave_can_be_reviewed(leave_request: LeaveRequest) -> None:
    if leave_request.status != LeaveStatus.PENDING:
        raise ValueError(
            f"Only pending leave requests can be reviewed. "
            f"Current status is {leave_request.status.value}"
        )


def ensure_leave_can_be_cancelled(leave_request: LeaveRequest) -> None:
    if leave_request.status not in (LeaveStatus.PENDING, LeaveStatus.APPROVED):
        raise ValueError(
            f"Only pending or approved leave requests can be cancelled. "
            f"Current status is {leave_request.status.value}"
        )