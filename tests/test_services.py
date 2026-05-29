"""
Tests for the leave management service layer.

These tests are currently empty and use placeholder asserts.
When you implement src/services.py, write real tests here.

Consider:
- What happens when you try to create overlapping leave?
- What happens when balance is insufficient?
- Can an employee approve their own leave?
- Can you cancel an already-cancelled leave?
- Does cancelling an approved leave restore the balance?
"""

import unittest
from datetime import date, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base
from src.models import Employee, LeaveBalance, LeaveType, LeaveStatus
from src.services import (
    seed_demo_data,
    create_leave_request,
    approve_leave_request,
    cancel_leave_request,
    get_leave_requests,
    get_leave_balances,
    InsufficientBalanceError,
    OverlappingLeaveError,
    SelfApprovalError,
    CannotModifyApprovedLeaveError,
    LeaveError,
)


class TestLeaveServices(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        cls.Session = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)

        self.db = self.Session()
        seed_demo_data(self.db)

        self.alice = self.db.query(Employee).filter(Employee.email == "alice@company.com").first()
        self.bob = self.db.query(Employee).filter(Employee.email == "bob@company.com").first()
        self.carol = self.db.query(Employee).filter(Employee.email == "carol@company.com").first()

    def tearDown(self):
        self.db.close()

    def test_create_leave_request(self):
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=2)

        leave_request = create_leave_request(
            self.db,
            employee_id=self.bob.id,
            leave_type=LeaveType.ANNUAL,
            start_date=start,
            end_date=end,
            reason="Family trip",
        )

        self.assertIsNotNone(leave_request.id)
        self.assertEqual(leave_request.employee_id, self.bob.id)
        self.assertEqual(leave_request.leave_type, LeaveType.ANNUAL)
        self.assertEqual(leave_request.start_date, start)
        self.assertEqual(leave_request.end_date, end)
        self.assertEqual(leave_request.reason, "Family trip")
        self.assertEqual(leave_request.status, LeaveStatus.PENDING)

    def test_create_leave_request_rejects_backdated_leave(self):
        start = date.today() - timedelta(days=1)
        end = date.today() + timedelta(days=1)

        with self.assertRaises(LeaveError):
            create_leave_request(
                self.db,
                employee_id=self.bob.id,
                leave_type=LeaveType.ANNUAL,
                start_date=start,
                end_date=end,
            )

    def test_create_leave_request_rejects_invalid_date_range(self):
        start = date.today() + timedelta(days=10)
        end = date.today() + timedelta(days=7)

        with self.assertRaises(LeaveError):
            create_leave_request(
                self.db,
                employee_id=self.bob.id,
                leave_type=LeaveType.ANNUAL,
                start_date=start,
                end_date=end,
            )

    def test_create_leave_request_insufficient_balance(self):
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=20)

        with self.assertRaises(InsufficientBalanceError):
            create_leave_request(
                self.db,
                employee_id=self.bob.id,
                leave_type=LeaveType.ANNUAL,
                start_date=start,
                end_date=end,
            )

    def test_create_leave_request_overlapping_dates(self):
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=2)

        create_leave_request(
            self.db,
            employee_id=self.bob.id,
            leave_type=LeaveType.ANNUAL,
            start_date=start,
            end_date=end,
        )

        with self.assertRaises(OverlappingLeaveError):
            create_leave_request(
                self.db,
                employee_id=self.bob.id,
                leave_type=LeaveType.ANNUAL,
                start_date=start + timedelta(days=1),
                end_date=end + timedelta(days=1),
            )

    def test_approve_leave_request(self):
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=2)

        leave_request = create_leave_request(
            self.db,
            employee_id=self.bob.id,
            leave_type=LeaveType.ANNUAL,
            start_date=start,
            end_date=end,
        )

        approved = approve_leave_request(
            self.db,
            leave_request_id=leave_request.id,
            approver_id=self.alice.id,
            decision=LeaveStatus.APPROVED,
        )

        self.assertEqual(approved.status, LeaveStatus.APPROVED)
        self.assertEqual(approved.approved_by, self.alice.id)
        self.assertIsNotNone(approved.approved_at)

        balance = (
            self.db.query(LeaveBalance)
            .filter(
                LeaveBalance.employee_id == self.bob.id,
                LeaveBalance.leave_type == LeaveType.ANNUAL,
                LeaveBalance.year == start.year,
            )
            .first()
        )

        self.assertEqual(balance.used_days, 3)

    def test_reject_leave_request_does_not_deduct_balance(self):
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=2)

        leave_request = create_leave_request(
            self.db,
            employee_id=self.bob.id,
            leave_type=LeaveType.ANNUAL,
            start_date=start,
            end_date=end,
        )

        rejected = approve_leave_request(
            self.db,
            leave_request_id=leave_request.id,
            approver_id=self.alice.id,
            decision=LeaveStatus.REJECTED,
        )

        self.assertEqual(rejected.status, LeaveStatus.REJECTED)

        balance = (
            self.db.query(LeaveBalance)
            .filter(
                LeaveBalance.employee_id == self.bob.id,
                LeaveBalance.leave_type == LeaveType.ANNUAL,
                LeaveBalance.year == start.year,
            )
            .first()
        )

        self.assertEqual(balance.used_days, 0)

    def test_self_approval_rejected(self):
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=1)

        leave_request = create_leave_request(
            self.db,
            employee_id=self.bob.id,
            leave_type=LeaveType.ANNUAL,
            start_date=start,
            end_date=end,
        )

        with self.assertRaises(SelfApprovalError):
            approve_leave_request(
                self.db,
                leave_request_id=leave_request.id,
                approver_id=self.bob.id,
                decision=LeaveStatus.APPROVED,
            )

    def test_non_manager_approval_rejected(self):
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=1)

        leave_request = create_leave_request(
            self.db,
            employee_id=self.bob.id,
            leave_type=LeaveType.ANNUAL,
            start_date=start,
            end_date=end,
        )

        with self.assertRaises(LeaveError):
            approve_leave_request(
                self.db,
                leave_request_id=leave_request.id,
                approver_id=self.carol.id,
                decision=LeaveStatus.APPROVED,
            )

    def test_double_approval_rejected(self):
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=1)

        leave_request = create_leave_request(
            self.db,
            employee_id=self.bob.id,
            leave_type=LeaveType.ANNUAL,
            start_date=start,
            end_date=end,
        )

        approve_leave_request(
            self.db,
            leave_request_id=leave_request.id,
            approver_id=self.alice.id,
            decision=LeaveStatus.APPROVED,
        )

        with self.assertRaises(CannotModifyApprovedLeaveError):
            approve_leave_request(
                self.db,
                leave_request_id=leave_request.id,
                approver_id=self.alice.id,
                decision=LeaveStatus.APPROVED,
            )

    def test_cancel_pending_leave(self):
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=1)

        leave_request = create_leave_request(
            self.db,
            employee_id=self.bob.id,
            leave_type=LeaveType.ANNUAL,
            start_date=start,
            end_date=end,
        )

        cancelled = cancel_leave_request(
            self.db,
            leave_request_id=leave_request.id,
            employee_id=self.bob.id,
        )

        self.assertEqual(cancelled.status, LeaveStatus.CANCELLED)

    def test_cancel_approved_leave_restores_balance(self):
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=2)

        leave_request = create_leave_request(
            self.db,
            employee_id=self.bob.id,
            leave_type=LeaveType.ANNUAL,
            start_date=start,
            end_date=end,
        )

        approve_leave_request(
            self.db,
            leave_request_id=leave_request.id,
            approver_id=self.alice.id,
            decision=LeaveStatus.APPROVED,
        )

        balance_before_cancel = (
            self.db.query(LeaveBalance)
            .filter(
                LeaveBalance.employee_id == self.bob.id,
                LeaveBalance.leave_type == LeaveType.ANNUAL,
                LeaveBalance.year == start.year,
            )
            .first()
        )
        self.assertEqual(balance_before_cancel.used_days, 3)

        cancelled = cancel_leave_request(
            self.db,
            leave_request_id=leave_request.id,
            employee_id=self.bob.id,
        )

        self.assertEqual(cancelled.status, LeaveStatus.CANCELLED)

        balance_after_cancel = (
            self.db.query(LeaveBalance)
            .filter(
                LeaveBalance.employee_id == self.bob.id,
                LeaveBalance.leave_type == LeaveType.ANNUAL,
                LeaveBalance.year == start.year,
            )
            .first()
        )
        self.assertEqual(balance_after_cancel.used_days, 0)

    def test_cancel_by_non_owner_rejected(self):
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=1)

        leave_request = create_leave_request(
            self.db,
            employee_id=self.bob.id,
            leave_type=LeaveType.ANNUAL,
            start_date=start,
            end_date=end,
        )

        with self.assertRaises(LeaveError):
            cancel_leave_request(
                self.db,
                leave_request_id=leave_request.id,
                employee_id=self.carol.id,
            )

    def test_cancel_already_cancelled_leave_rejected(self):
        start = date.today() + timedelta(days=7)
        end = start + timedelta(days=1)

        leave_request = create_leave_request(
            self.db,
            employee_id=self.bob.id,
            leave_type=LeaveType.ANNUAL,
            start_date=start,
            end_date=end,
        )

        cancel_leave_request(
            self.db,
            leave_request_id=leave_request.id,
            employee_id=self.bob.id,
        )

        with self.assertRaises(CannotModifyApprovedLeaveError):
            cancel_leave_request(
                self.db,
                leave_request_id=leave_request.id,
                employee_id=self.bob.id,
            )

    def test_list_leave_requests_with_filters(self):
        first_start = date.today() + timedelta(days=7)
        second_start = date.today() + timedelta(days=14)

        bob_leave = create_leave_request(
            self.db,
            employee_id=self.bob.id,
            leave_type=LeaveType.ANNUAL,
            start_date=first_start,
            end_date=first_start + timedelta(days=1),
        )

        create_leave_request(
            self.db,
            employee_id=self.carol.id,
            leave_type=LeaveType.SICK,
            start_date=second_start,
            end_date=second_start,
        )

        items, total = get_leave_requests(
            self.db,
            employee_id=self.bob.id,
            status=LeaveStatus.PENDING,
            leave_type=LeaveType.ANNUAL,
            from_date=first_start,
            to_date=first_start + timedelta(days=1),
            page=1,
            page_size=10,
        )

        self.assertEqual(total, 1)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].id, bob_leave.id)

    def test_list_leave_requests_with_pagination(self):
        for offset in range(3):
            start = date.today() + timedelta(days=7 + (offset * 3))
            create_leave_request(
                self.db,
                employee_id=self.bob.id,
                leave_type=LeaveType.ANNUAL,
                start_date=start,
                end_date=start,
            )

        items, total = get_leave_requests(
            self.db,
            employee_id=self.bob.id,
            page=1,
            page_size=2,
        )

        self.assertEqual(total, 3)
        self.assertEqual(len(items), 2)

    def test_get_leave_balances(self):
        balances = get_leave_balances(self.db, employee_id=self.bob.id)

        self.assertEqual(len(balances), 2)

        balance_types = {balance.leave_type for balance in balances}
        self.assertIn(LeaveType.ANNUAL, balance_types)
        self.assertIn(LeaveType.SICK, balance_types)

    def test_get_leave_balances_rejects_unknown_employee(self):
        with self.assertRaises(LeaveError):
            get_leave_balances(self.db, employee_id=9999)


if __name__ == "__main__":
    unittest.main()