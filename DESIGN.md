# Design Document — Leave Management System

**Author:** Nik
**Date:** 2026-05-29

## 1. API Design

The API is implemented using FastAPI. I kept the route handlers thin and delegated business workflow decisions to the service layer. The API exposes endpoints for employees, leave requests, leave approvals/cancellations, and leave balances.

### `GET /employees`

Returns all employees.

**Request body:** None

**Response shape:**

```json
[
  {
    "id": 1,
    "name": "Alice Manager",
    "email": "alice@company.com",
    "department": "Engineering",
    "manager_id": null
  }
]
```

**Status codes:**

* `200 OK` — employees returned successfully

---

### `GET /employees/{employee_id}`

Returns one employee and their leave balances.

**Request body:** None

**Response shape:**

```json
{
  "employee": {
    "id": 2,
    "name": "Bob Engineer",
    "email": "bob@company.com",
    "department": "Engineering",
    "manager_id": 1
  },
  "leave_balances": [
    {
      "leave_type": "annual",
      "year": 2026,
      "total_days": 14,
      "used_days": 0,
      "remaining_days": 14
    }
  ]
}
```

**Status codes:**

* `200 OK` — employee found
* `404 Not Found` — employee does not exist

---

### `POST /leave-requests`

Creates a new leave request.

**Request body:**

```json
{
  "employee_id": 2,
  "leave_type": "annual",
  "start_date": "2026-06-05",
  "end_date": "2026-06-07",
  "reason": "Family trip"
}
```

**Response shape:**

```json
{
  "id": 1,
  "employee_id": 2,
  "leave_type": "annual",
  "start_date": "2026-06-05",
  "end_date": "2026-06-07",
  "reason": "Family trip",
  "status": "pending",
  "approved_by": null,
  "approved_at": null
}
```

**Status codes:**

* `201 Created` — leave request created
* `422 Unprocessable Entity` — invalid date range, backdated request, overlapping leave, insufficient balance, or unknown employee

---

### `GET /leave-requests`

Lists leave requests with filtering and pagination.

**Query parameters:**

* `employee_id`
* `status`
* `leave_type`
* `from_date`
* `to_date`
* `page`
* `page_size`

**Request body:** None

**Response shape:**

```json
{
  "items": [
    {
      "id": 1,
      "employee_id": 2,
      "leave_type": "annual",
      "start_date": "2026-06-05",
      "end_date": "2026-06-07",
      "reason": "Family trip",
      "status": "pending",
      "approved_by": null,
      "approved_at": null
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Status codes:**

* `200 OK` — leave requests returned successfully
* `422 Unprocessable Entity` — invalid query parameters, such as invalid page or page size

---

### `GET /leave-requests/{leave_request_id}`

Returns a single leave request.

**Request body:** None

**Response shape:**

```json
{
  "id": 1,
  "employee_id": 2,
  "leave_type": "annual",
  "start_date": "2026-06-05",
  "end_date": "2026-06-07",
  "reason": "Family trip",
  "status": "pending",
  "approved_by": null,
  "approved_at": null
}
```

**Status codes:**

* `200 OK` — leave request found
* `404 Not Found` — leave request does not exist

---

### `POST /leave-requests/{leave_request_id}/review`

Approves or rejects a pending leave request.

In the current scaffold, the approver is hardcoded as employee ID `1`. In the demo data, this represents Alice Manager.

**Request body:**

```json
{
  "decision": "approved"
}
```

or:

```json
{
  "decision": "rejected"
}
```

**Response shape:**

```json
{
  "id": 1,
  "employee_id": 2,
  "leave_type": "annual",
  "start_date": "2026-06-05",
  "end_date": "2026-06-07",
  "reason": "Family trip",
  "status": "approved",
  "approved_by": 1,
  "approved_at": "2026-05-29T10:00:00"
}
```

**Status codes:**

* `200 OK` — leave request reviewed successfully
* `422 Unprocessable Entity` — request is not pending, decision is invalid, approver is not authorized, self-approval attempted, or balance is insufficient at approval time

---

### `POST /leave-requests/{leave_request_id}/cancel`

Cancels a pending or approved leave request.

**Query parameters:**

* `employee_id` — the employee attempting the cancellation

**Request body:** None

**Response shape:**

```json
{
  "id": 1,
  "employee_id": 2,
  "leave_type": "annual",
  "start_date": "2026-06-05",
  "end_date": "2026-06-07",
  "reason": "Family trip",
  "status": "cancelled",
  "approved_by": 1,
  "approved_at": "2026-05-29T10:00:00"
}
```

**Status codes:**

* `200 OK` — leave request cancelled successfully
* `422 Unprocessable Entity` — employee is not the owner, leave request cannot be cancelled, or leave request does not exist

---

### `GET /leave-balances/{employee_id}`

Returns leave balances for an employee. If no year is supplied, the current year is used.

**Query parameters:**

* `year` optional

**Request body:** None

**Response shape:**

```json
[
  {
    "leave_type": "annual",
    "year": 2026,
    "total_days": 14,
    "used_days": 3,
    "remaining_days": 11
  },
  {
    "leave_type": "sick",
    "year": 2026,
    "total_days": 12,
    "used_days": 0,
    "remaining_days": 12
  }
]
```

**Status codes:**

* `200 OK` — balances returned successfully
* `422 Unprocessable Entity` — employee does not exist

---

## 2. Data Model

The system uses three main tables: `employees`, `leave_requests`, and `leave_balances`.

### `employees`

Represents employees and their reporting structure.

| Column       | Type     | Notes                                  |
| ------------ | -------- | -------------------------------------- |
| `id`         | Integer  | Primary key, indexed                   |
| `name`       | String   | Required                               |
| `email`      | String   | Required, unique, indexed              |
| `department` | String   | Required                               |
| `manager_id` | Integer  | Nullable foreign key to `employees.id` |
| `joined_at`  | Date     | Defaults to current date               |
| `created_at` | DateTime | Defaults to current UTC datetime       |
| `updated_at` | DateTime | Updated on modification                |

**Relationships:**

* An employee may have a manager through `manager_id`.
* An employee may have many leave requests.
* An employee may have many leave balances.

Because `leave_requests` has two foreign keys to `employees` — `employee_id` and `approved_by` — the model explicitly specifies `foreign_keys` on the relationships to avoid ambiguous SQLAlchemy joins.

---

### `leave_requests`

Represents a leave application submitted by an employee.

| Column        | Type     | Notes                                           |
| ------------- | -------- | ----------------------------------------------- |
| `id`          | Integer  | Primary key, indexed                            |
| `employee_id` | Integer  | Required foreign key to `employees.id`, indexed |
| `leave_type`  | Enum     | Required                                        |
| `start_date`  | Date     | Required                                        |
| `end_date`    | Date     | Required                                        |
| `reason`      | String   | Optional                                        |
| `status`      | Enum     | Defaults to `pending`                           |
| `approved_by` | Integer  | Nullable foreign key to `employees.id`          |
| `approved_at` | DateTime | Nullable                                        |
| `created_at`  | DateTime | Defaults to current UTC datetime                |
| `updated_at`  | DateTime | Updated on modification                         |

**Relationships:**

* A leave request belongs to one employee.
* A leave request may have one approver.

**Enums:**

`LeaveStatus`:

* `pending`
* `approved`
* `rejected`
* `cancelled`

`LeaveType`:

* `annual`
* `sick`
* `personal`
* `maternity`
* `paternity`
* `unpaid`

---

### `leave_balances`

Represents an employee’s leave entitlement and usage by leave type and year.

| Column        | Type     | Notes                                           |
| ------------- | -------- | ----------------------------------------------- |
| `id`          | Integer  | Primary key, indexed                            |
| `employee_id` | Integer  | Required foreign key to `employees.id`, indexed |
| `leave_type`  | Enum     | Required                                        |
| `year`        | Integer  | Required                                        |
| `total_days`  | Float    | Required, defaults to `0`                       |
| `used_days`   | Float    | Required, defaults to `0`                       |
| `created_at`  | DateTime | Defaults to current UTC datetime                |
| `updated_at`  | DateTime | Updated on modification                         |

The model exposes a computed property:

```python
remaining_days = total_days - used_days
```

In a production database, I would add a uniqueness constraint on:

```text
employee_id, leave_type, year
```

This would ensure one balance row per employee, leave type, and year.

---

## 3. Edge Cases Identified

### Overlapping leave requests

The system prevents an employee from submitting a leave request that overlaps with an existing `pending` or `approved` leave request.

The overlap condition is:

```text
existing.start_date <= requested.end_date
AND existing.end_date >= requested.start_date
```

Rejected and cancelled leave requests do not block new requests.

---

### Insufficient balance

The system checks leave balance when a leave request is created. It also checks again during approval.

Checking again during approval is important because the employee’s balance may have changed after the request was created.

---

### Self-approval

Employees cannot approve their own leave requests.

Even if an employee somehow has approval authority, the service layer explicitly rejects self-approval.

---

### Approval authority

Only the employee’s direct manager can approve or reject a leave request.

The current implementation uses the employee’s `manager_id` relationship. In a production system, this could be expanded to support department heads, HR admins, delegated approvers, or approval chains.

---

### Cancelling approved leave

Employees can cancel their own pending or approved leave requests.

If the leave request was already approved, the used balance is restored.

---

### Cancelling rejected or already-cancelled leave

Rejected or already-cancelled leave requests cannot be cancelled again.

This prevents invalid workflow transitions and avoids accidental balance changes.

---

### Invalid date ranges

The system rejects leave requests where:

```text
start_date > end_date
```

It also rejects backdated leave requests.

---

### Leave duration calculation

Leave duration is calculated as inclusive calendar days:

```text
2026-06-01 to 2026-06-01 = 1 day
2026-06-01 to 2026-06-03 = 3 days
```

This keeps the demo simple and predictable.

---

### Leave spanning across years

The current implementation uses the `start_date.year` to determine which leave balance row to use.

This is a simplification. For production, leave spanning across calendar years should be split by year so that each year’s balance is deducted accurately.

---

### Public holidays and weekends

The current implementation counts calendar days, including weekends and public holidays.

This was a deliberate simplification for the challenge. A production-grade system should support a working-day calendar, public holidays by country/state, and company-specific holiday policies.

---

### Concurrent approvals

The current implementation prevents double deduction by only allowing approval from the `pending` state.

However, true concurrent approval safety requires database-level transaction protection. In production, I would use row-level locking or optimistic concurrency control around the `leave_requests` and `leave_balances` rows.

---

### Idempotency of leave submission

The current implementation prevents duplicate overlapping active leave requests, which helps avoid accidental duplicate submissions.

For production, I would also consider an idempotency key for create requests, especially if clients may retry after network failures.

---

## 4. Tradeoffs and Decisions

### Thin API layer, explicit service layer

**Decision:**
Keep FastAPI route handlers thin and place workflow logic in the service layer.

**Reasoning:**
Route handlers should focus on HTTP concerns, request parsing, response formatting, and error translation. The service layer is easier to test directly and keeps business rules independent from FastAPI.

---

### Module boundaries

I split the service implementation into small modules with clear responsibilities:

- `services.py` contains application use cases and transaction boundaries.
- `repositories.py` contains SQLAlchemy query helpers.
- `leave_rules.py` contains pure business rules and calculations.
- `service_helpers.py` contains reusable service-level guards such as `get_employee_or_raise`.
- `exceptions.py` contains domain-specific exceptions and HTTP status metadata.

This keeps the service layer readable while avoiding putting database, validation, and exception concerns into one large module.

---

### Synchronous SQLAlchemy access

**Decision:**
Use the existing synchronous SQLAlchemy session pattern.

**Alternatives considered:**

* Async SQLAlchemy
* Async database drivers

**Reasoning:**
The existing project scaffold is synchronous. Keeping the implementation synchronous avoids unnecessary framework changes and keeps the focus on business correctness.

For higher-throughput production systems, async could be considered, but correctness and transaction handling would still be the priority.

---

### Inclusive calendar-day calculation

**Decision:**
Use inclusive calendar days for leave duration.

```text
duration = (end_date - start_date).days + 1
```

**Alternatives considered:**

* Business-day calculation
* Holiday-aware calculation
* Half-day support

**Reasoning:**
Inclusive calendar days are simple, transparent, and easy to test. This is acceptable for the challenge because the README asks candidates to consider weekends and holidays but does not require a full calendar engine.

---

### Balance deduction on approval

**Decision:**
Check balance on creation, but deduct balance only when the request is approved.

**Reasoning:**
Deducting only on approval aligns with the idea that pending leave has not yet been granted. Checking on creation provides fast feedback to the employee, while checking again on approval protects against stale balance data.

A production system might introduce a reserved balance field to distinguish pending reservations from approved usage.

---

### Offset-based pagination

**Decision:**
Use offset-based pagination with `page` and `page_size`.

**Alternatives considered:**

* Cursor-based pagination
* Keyset pagination

**Reasoning:**
Offset pagination is simple and sufficient for the expected scale of this challenge. Cursor pagination would be better for very large datasets or high-write tables, but it would add complexity that is not necessary here.

---

### Date-range overlap query

**Decision:**
Use a direct SQL date-range overlap condition:

```text
existing.start_date <= requested.end_date
AND existing.end_date >= requested.start_date
```

**Alternatives considered:**

* Load records into memory and compare in Python.
* Use database-specific range types.
* Add exclusion constraints.

**Reasoning:**
The SQL condition is simple, efficient, and database-portable. In PostgreSQL, a production version could use range types and exclusion constraints for stronger database-level protection.

---

### Optimistic vs pessimistic locking

**Decision:**
The current implementation relies on workflow state checks and transaction commits, but does not implement explicit locking.

**Alternatives considered:**

* Pessimistic locking using `SELECT ... FOR UPDATE`
* Optimistic locking using a version column
* Database constraints and retry logic

**Reasoning:**
SQLite does not support the same row-level locking model as PostgreSQL, so implementing realistic concurrency control in this demo would be limited. In production, I would add transactional locking around approval and balance deduction to prevent race conditions between concurrent managers.

---

## 5. What I Would Do With More Time

Given another week, I would improve the system in the following areas:

### Stronger transaction and concurrency control

I would wrap approval and cancellation in explicit database transactions and use row-level locking for the relevant leave request and leave balance rows.

For PostgreSQL, this would likely involve:

```sql
SELECT ... FOR UPDATE
```

on the balance row during approval and cancellation.

---

### Year-splitting for cross-year leave

Currently, a leave spanning multiple years uses the start date’s year for balance lookup.

I would split leave duration across years, for example:

```text
2026-12-30 to 2027-01-02
```

would deduct from both the 2026 and 2027 balances.

---

### Business-day and holiday calendar support

I would add a calendar service that can calculate chargeable leave days based on:

* weekends
* public holidays
* country/state
* company-specific holidays
* employee work schedule

This would make leave calculations more realistic for HR usage.

---

### Half-day leave

The current model uses start and end dates only. I would add support for partial-day leave by introducing fields such as:

```text
start_half_day
end_half_day
duration_days
```

or by storing leave sessions explicitly.

---

### Approval comments and audit trail

The current model stores approval status but does not store review comments or a full event history.

I would add an audit table such as `leave_request_events` with:

* leave request ID
* actor ID
* action
* previous status
* new status
* comment
* timestamp

This would improve traceability and compliance.

---

### Better authorization model

Currently, approval authority is based on the employee’s direct manager.

I would extend this to support:

* HR admins
* delegated approvers
* department-level approvers
* multi-step approval workflows

---

### More precise API errors

The current app maps service errors to `422 Unprocessable Entity`.

I would introduce more granular HTTP errors:

* `404` for missing resources
* `403` for unauthorized approval/cancellation
* `409` for workflow conflicts or overlapping leave
* `422` for validation errors

---

### Database constraints and indexes

I would add database-level constraints such as:

* unique constraint on `(employee_id, leave_type, year)` for leave balances
* indexes for common leave request filters
* possibly exclusion constraints for overlapping approved leave in PostgreSQL

---

### Observability

I would add structured logging around key workflow events:

* leave request created
* leave approved
* leave rejected
* leave cancelled
* balance deducted
* balance restored

This would make debugging and auditing easier.

---

## 6. Running the Project

```bash
# Install
pip install -r requirements.txt

# Run
uvicorn src.app:app --reload

# Test
python -m pytest tests/
```

Alternatively, the project includes a Makefile:

```bash
# Install
make install

# Run
make run

# Test
make test
```
