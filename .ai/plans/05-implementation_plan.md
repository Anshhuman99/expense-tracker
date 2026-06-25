# Implementation Plan - Backend Route for Profile Page (Step 05)

This plan outlines the steps required to replace the hardcoded profile page / dashboard data with live queries against the SQLite database.

## Goal Description
Build a dynamic dashboard page (`/profile`) that displays:
1. User details (name, email, member since date formatted as "Month YYYY").
2. Key performance metrics (Total spent, amount spent this month, transaction count, and top category).
3. Visual expense breakdown by category with percentages summing to exactly 100%.
4. Recent activity showing the last 10 transactions.

We will keep Flask-independent database query code in a new file `database/queries.py` and call these queries in the `/profile` route of `app.py`.

---

## User Review Required

> [!IMPORTANT]
> **Rounding Remainder Adjustment**: As specified, category percentage values must sum to exactly 100%. We will use integer rounding and adjust the largest category's percentage to absorb any rounding remainder.
> **Current Month Calculations**: The current month spent calculation will run dynamically inside the `/profile` route based on the server's current date.

---

## Open Questions

> [!NOTE]
> There are no unresolved open questions. The tests verify empty states as well as the seeded data.

---

## Proposed Changes

### Database Query Layer

#### [NEW] [queries.py](file:///Users/anshumanai/Desktop/expense-tracker/database/queries.py)
Create a new queries module containing raw SQLite queries with parameterised SQL. It will contain:
- `get_user_by_id(user_id, path=None)`: Fetches `name`, `email`, and formats `created_at` as "Month YYYY".
- `get_summary_stats(user_id, path=None)`: Retrieves `total_spent`, `transaction_count`, and `top_category` (broken alphabetically in case of ties).
- `get_recent_transactions(user_id, limit=10, path=None)`: Retrieves the most recent `limit` transactions ordered by `date DESC, id DESC`.
- `get_category_breakdown(user_id, path=None)`: Retrieves category breakdown, calculating percentages and adjusting the largest category so the total sums to exactly 100%.

---

### Backend Logic

#### [MODIFY] [app.py](file:///Users/anshumanai/Desktop/expense-tracker/app.py)
- Import query helpers from `database.queries`.
- Update the `/profile` route:
  - Check if `session.get("user_id")` exists. If not, redirect to `/login`.
  - Fetch user details using `get_user_by_id`.
  - Fetch summary stats using `get_summary_stats`.
  - Fetch category breakdown using `get_category_breakdown`.
  - Fetch recent transactions using `get_recent_transactions(user_id, limit=10)`.
  - Compute the current month spent based on `date LIKE 'YYYY-MM%'`.
  - Pass the dynamic values to the template.

---

### Templates

#### [MODIFY] [profile.html](file:///Users/anshumanai/Desktop/expense-tracker/templates/profile.html)
- Update headers to display `user.name`, `user.email`, and `user.member_since` instead of `g.user` fields (if passing `user` dict from route).
- Confirm ₹ symbol is used for all amounts.
- Confirm category breakdown uses the correct keys (`cat.name`, `cat.amount`, `cat.pct` instead of hardcoded/mismatched keys).

---

### Test Suite

#### [NEW] [test_backend_connection.py](file:///Users/anshumanai/Desktop/expense-tracker/tests/test_backend_connection.py)
- Write tests for the backend query helpers:
  - `get_user_by_id`: valid id and invalid id
  - `get_summary_stats`: user with expenses and user with no expenses
  - `get_recent_transactions`: list sorted newest-first and empty list
  - `get_category_breakdown`: sorted list with percentages summing to 100, and empty list for user with no expenses

---

## Verification Plan

### Automated Tests
Run pytest in the workspace:
```bash
pytest tests/test_backend_connection.py
pytest tests/test_profile_page.py
```

### Manual Verification
- Start the server: `python app.py`.
- Log in as the seed user (`demo@spendly.com` / `demo123`).
- Verify the details:
  - Welcome banner greeting: "Welcome back, Demo User"
  - Email and Member Since dates are displayed dynamically.
  - KPI Cards match seed totals: ₹391.25 total spent across 8 transactions, top category "Bills".
  - Recent Expenses table shows all 8 seeded transactions, newest first.
  - Category Breakdown shows percentages summing to 100% (Bills at 30%, Shopping at 22%, etc.).
- Register a brand-new user and log in to verify empty states:
  - Welcome banner greeting shows new username.
  - Total Spent is ₹0.00, transaction count is 0.
  - Recent expenses displays empty state text.
  - Category breakdown displays empty state text.
