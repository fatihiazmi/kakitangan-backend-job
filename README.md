# Join Kakitangan as Backend Developer

We are a leading HR SaaS platform in Malaysia — and we're hiring a **senior backend developer** (~7 years experience) to join our team.

This challenge is designed to simulate real work: ambiguous requirements, design decisions, tradeoffs, and edge cases. We want to see how you **think**, **communicate**, and **code**.

---

## The Challenge: Leave Management API

Kakitangan needs a **leave management system**. Employees request leave, managers approve or reject, and balances track usage.

We've built a skeleton FastAPI app with:
- **`src/models.py`** — Database models (Employee, LeaveRequest, LeaveBalance)
- **`src/app.py`** — FastAPI routes (wired to services with stubs)
- **`src/services.py`** — Business logic layer (**you implement this**)
- **`src/database.py`** — SQLAlchemy engine & session
- **`tests/test_services.py`** — Unit tests (**you expand these**)
- **`tests/test_api.py`** — Integration tests (**you expand these**)

Your job: **implement the service layer** and **write comprehensive tests**.

---

## Requirements

### Must have
- `create_leave_request` — validate dates, check balance, prevent overlap
- `approve_leave_request` — manager approval, deduct balance, no self-approval
- `cancel_leave_request` — owner can cancel pending/approved leaves, restore balance
- `get_leave_requests` — filtered listing with pagination
- `get_leave_balances` — show remaining days per type per year
- Tests covering at least the key edge cases

### Should consider
- What happens with concurrent leave approvals?
- How do you handle leaves that span weekends or public holidays?
- Is the balance deduction idempotent?
- What if two managers try to approve the same request?
- How would you handle half-day leaves?

### Nice to have (not required, but impressive)
- Proper error messages with user-friendly status codes
- Request validation via Pydantic (already scaffolded)
- Pagination with cursor-based or offset-based approach
- Logging or structured error reporting

---

## How to Submit

1. **Fork** this repository
2. **Design first**: Write a `DESIGN.md` covering:
   - API design decisions
   - Data model considerations
   - Edge cases you identified
   - Tradeoffs you made and why
   - What you'd do with more time
3. **Implement** the service functions in `src/services.py`
4. **Write tests** in `tests/test_services.py` (and `test_api.py` if you want)
5. **Verify**: `make test` passes, `make run` starts the server
6. **Commit** your changes with clear, descriptive messages
7. **Submit a pull request** with your DESIGN.md, code, tests, and a note about yourself

---

## How We Evaluate

| Dimension | What we look for |
|-----------|-----------------|
| **Technical** | Code structure, error handling, test coverage, API design, database considerations |
| **Thinking** | Edge cases identified, tradeoff analysis, clarity of DESIGN.md, scalability awareness |
| **Communication** | DESIGN.md clarity, PR description, commit messages, code comments (used sparingly but well) |

We know coding agents exist. That's fine — but your DESIGN.md and PR communication will reveal the depth of your thinking. We also conduct a **follow-up technical discussion** on your PR to separate genuine understanding from generated code.

---

## Running the Project

```bash
# Install
make install

# Run the server
make run

# Run tests
make test

# Clean up
make clean
```

---

## Questions?

Having issues? Not sure the repo is active? Create an issue using the question template. We'll respond.

---

*We're excited to see your approach. Good luck.*
