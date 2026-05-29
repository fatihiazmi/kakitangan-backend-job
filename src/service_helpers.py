from sqlalchemy.orm import Session

from src import repositories
from src.exceptions import InsufficientBalanceError, NotFoundError
from src.models import Employee, LeaveBalance, LeaveRequest, LeaveType


def get_employee_or_raise(db: Session, employee_id: int) -> Employee:
    employee = repositories.get_employee(db, employee_id)
    if not employee:
        raise NotFoundError(f"Employee {employee_id} not found")
    return employee


def get_leave_request_or_raise(db: Session, leave_request_id: int) -> LeaveRequest:
    leave_request = repositories.get_leave_request(db, leave_request_id)
    if not leave_request:
        raise NotFoundError(f"Leave request {leave_request_id} not found")
    return leave_request


def get_balance_or_raise(
    db: Session,
    employee_id: int,
    leave_type: LeaveType,
    year: int,
) -> LeaveBalance:
    balance = repositories.get_leave_balance(
        db,
        employee_id=employee_id,
        leave_type=leave_type,
        year=year,
    )

    if not balance:
        raise InsufficientBalanceError(
            f"No leave balance found for employee {employee_id}, "
            f"type {leave_type.value}, year {year}"
        )

    return balance