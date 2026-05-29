"""
Business logic layer for leave management.

This module exposes the public service functions used by the FastAPI routes.
It coordinates validation, repository access, status transitions, and commits.
"""

import logging
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src import repositories
from src.exceptions import (
    AuthorizationError,
    CannotModifyApprovedLeaveError,
    InsufficientBalanceError,
    LeaveError,
    OverlappingLeaveError,
    SelfApprovalError,
    ValidationError,
    NotFoundError,
)
from src.leave_rules import (
    calculate_leave_days,
    ensure_leave_can_be_cancelled,
    ensure_leave_can_be_reviewed,
    validate_leave_date_range,
)
from src.models import Employee, LeaveBalance, LeaveRequest, LeaveType, LeaveStatus
from src.service_helpers import (
    get_balance_or_raise,
    get_employee_or_raise,
    get_leave_request_or_raise,
)

logger = logging.getLogger(__name__)


def create_leave_request(
    db: Session,
    employee_id: int,
    leave_type: LeaveType,
    start_date: date,
    end_date: date,
    reason: Optional[str] = None,
) -> LeaveRequest:
    get_employee_or_raise(db, employee_id)

    try:
        validate_leave_date_range(start_date, end_date)
    except ValueError as exc:
        raise LeaveError(str(exc)) from exc

    if repositories.has_overlapping_leave(db, employee_id, start_date, end_date):
        raise OverlappingLeaveError(
            "Leave request overlaps with an existing pending or approved leave"
        )

    requested_days = calculate_leave_days(start_date, end_date)
    balance = get_balance_or_raise(db, employee_id, leave_type, start_date.year)

    if balance.remaining_days < requested_days:
        raise InsufficientBalanceError(
            f"Insufficient {leave_type.value} leave balance. "
            f"Requested {requested_days} day(s), "
            f"available {balance.remaining_days} day(s)"
        )

    leave_request = LeaveRequest(
        employee_id=employee_id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
        status=LeaveStatus.PENDING,
    )

    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)

    return leave_request


def approve_leave_request(
    db: Session,
    leave_request_id: int,
    approver_id: int,
    decision: LeaveStatus,
) -> LeaveRequest:
    if decision not in (LeaveStatus.APPROVED, LeaveStatus.REJECTED):
        raise LeaveError("Decision must be either approved or rejected")

    leave_request = get_leave_request_or_raise(db, leave_request_id)
    approver = get_employee_or_raise(db, approver_id)

    try:
        ensure_leave_can_be_reviewed(leave_request)
    except ValueError as exc:
        raise CannotModifyApprovedLeaveError(str(exc)) from exc

    if leave_request.employee_id == approver.id:
        raise SelfApprovalError("Employees cannot approve their own leave requests")

    if leave_request.employee.manager_id != approver.id:
        raise LeaveError("Only the employee's manager can approve or reject this leave request")

    if decision == LeaveStatus.APPROVED:
        requested_days = calculate_leave_days(
            leave_request.start_date,
            leave_request.end_date,
        )

        balance = get_balance_or_raise(
            db,
            leave_request.employee_id,
            leave_request.leave_type,
            leave_request.start_date.year,
        )

        if balance.remaining_days < requested_days:
            raise InsufficientBalanceError(
                f"Insufficient {leave_request.leave_type.value} leave balance. "
                f"Requested {requested_days} day(s), "
                f"available {balance.remaining_days} day(s)"
            )

        balance.used_days += requested_days

    leave_request.status = decision
    leave_request.approved_by = approver.id
    leave_request.approved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(leave_request)

    return leave_request


def cancel_leave_request(
    db: Session,
    leave_request_id: int,
    employee_id: int,
) -> LeaveRequest:
    leave_request = get_leave_request_or_raise(db, leave_request_id)
    get_employee_or_raise(db, employee_id)

    if leave_request.employee_id != employee_id:
        raise LeaveError("Only the leave request owner can cancel this request")

    try:
        ensure_leave_can_be_cancelled(leave_request)
    except ValueError as exc:
        raise CannotModifyApprovedLeaveError(str(exc)) from exc

    if leave_request.status == LeaveStatus.APPROVED:
        requested_days = calculate_leave_days(
            leave_request.start_date,
            leave_request.end_date,
        )

        balance = get_balance_or_raise(
            db,
            leave_request.employee_id,
            leave_request.leave_type,
            leave_request.start_date.year,
        )

        balance.used_days = max(0, balance.used_days - requested_days)

    leave_request.status = LeaveStatus.CANCELLED

    db.commit()
    db.refresh(leave_request)

    return leave_request


def get_leave_requests(
    db: Session,
    employee_id: Optional[int] = None,
    status: Optional[LeaveStatus] = None,
    leave_type: Optional[LeaveType] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[LeaveRequest], int]:
    if page < 1:
        raise LeaveError("Page must be greater than or equal to 1")

    if page_size < 1:
        raise LeaveError("Page size must be greater than or equal to 1")

    query = repositories.query_leave_requests(
        db,
        employee_id=employee_id,
        status=status,
        leave_type=leave_type,
        from_date=from_date,
        to_date=to_date,
    )

    total_count = query.count()

    items = (
        query
        .order_by(LeaveRequest.start_date.desc(), LeaveRequest.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return items, total_count


def get_leave_balances(
    db: Session,
    employee_id: int,
    year: Optional[int] = None,
) -> list[LeaveBalance]:
    get_employee_or_raise(db, employee_id)

    balance_year = year or date.today().year

    return repositories.list_leave_balances(db, employee_id, balance_year)


def seed_demo_data(db: Session) -> None:
    """Seed database with demo employees and leave balances for testing."""
    from src.models import LeaveType, LeaveBalance

    existing = db.query(Employee).first()
    if existing:
        return

    alice = Employee(name="Alice Manager", email="alice@company.com", department="Engineering")
    bob = Employee(name="Bob Engineer", email="bob@company.com", department="Engineering", manager=alice)
    carol = Employee(name="Carol Engineer", email="carol@company.com", department="Engineering", manager=alice)
    db.add_all([alice, bob, carol])
    db.flush()

    year = date.today().year
    balances = [
        LeaveBalance(employee_id=bob.id, leave_type=LeaveType.ANNUAL, year=year, total_days=14),
        LeaveBalance(employee_id=bob.id, leave_type=LeaveType.SICK, year=year, total_days=12),
        LeaveBalance(employee_id=carol.id, leave_type=LeaveType.ANNUAL, year=year, total_days=14),
        LeaveBalance(employee_id=carol.id, leave_type=LeaveType.SICK, year=year, total_days=12),
    ]
    db.add_all(balances)
    db.commit()