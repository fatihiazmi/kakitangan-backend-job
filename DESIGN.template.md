# Design Document — Leave Management System

**Author:** Your Name
**Date:** YYYY-MM-DD

## 1. API Design

List the endpoints you designed. For each, include:
- HTTP method and path
- Request body shape
- Response shape
- Status codes (success + error)

## 2. Data Model

Describe the database tables and their relationships. Include:
- Columns and types
- Foreign keys
- Indexes
- Any enums

## 3. Edge Cases Identified

List the edge cases you considered and handled. Examples:
- Overlapping leave requests
- Insufficient balance
- Self-approval
- Leave spanning across years
- Public holidays / weekends (opt-in)
- Concurrent approvals by two managers
- Idempotency of leave submission

## 4. Tradeoffs and Decisions

For each major decision, explain:
- What you chose
- What alternatives you considered
- Why you made your choice

Examples:
- SQLite vs PostgreSQL for the demo
- sync vs async framework
- optimistic vs pessimistic locking for balance deduction
- date-range overlap query strategy

## 5. What I Would Do With More Time

Be honest. What would you improve, refactor, or add if you had
another week on this?

## 6. Running the Project

```bash
# Install
pip install -r requirements.txt

# Run
uvicorn src.app:app --reload

# Test
python -m pytest tests/
```
