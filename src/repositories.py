from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from src.models import Employee, LeaveBalance, LeaveRequest, LeaveStatus, LeaveType


def get_employee(db: Session, employee_id: int) -> Optional[Employee]:
    return db.query(Employee).filter(Employee.id == employee_id).first()


def get_leave_request(db: Session, leave_request_id: int) -> Optional[LeaveRequest]:
    return (
        db.query(LeaveRequest)
        .filter(LeaveRequest.id == leave_request_id)
        .first()
    )


def get_leave_balance(
    db: Session,
    employee_id: int,
    leave_type: LeaveType,
    year: int,
) -> Optional[LeaveBalance]:
    return (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type == leave_type,
            LeaveBalance.year == year,
        )
        .first()
    )


def has_overlapping_leave(
    db: Session,
    employee_id: int,
    start_date: date,
    end_date: date,
) -> bool:
    return (
        db.query(LeaveRequest)
        .filter(
            LeaveRequest.employee_id == employee_id,
            LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
            LeaveRequest.start_date <= end_date,
            LeaveRequest.end_date >= start_date,
        )
        .first()
        is not None
    )


def query_leave_requests(
    db: Session,
    employee_id: Optional[int] = None,
    status: Optional[LeaveStatus] = None,
    leave_type: Optional[LeaveType] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
):
    query = db.query(LeaveRequest)

    if employee_id is not None:
        query = query.filter(LeaveRequest.employee_id == employee_id)

    if status is not None:
        query = query.filter(LeaveRequest.status == status)

    if leave_type is not None:
        query = query.filter(LeaveRequest.leave_type == leave_type)

    if from_date is not None:
        query = query.filter(LeaveRequest.start_date >= from_date)

    if to_date is not None:
        query = query.filter(LeaveRequest.end_date <= to_date)

    return query


def list_leave_balances(
    db: Session,
    employee_id: int,
    year: int,
) -> list[LeaveBalance]:
    return (
        db.query(LeaveBalance)
        .filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.year == year,
        )
        .order_by(LeaveBalance.leave_type.asc())
        .all()
    )