# Implementation Plan - Profile Page / Dashboard Design (Step 04)

This plan outlines the steps required to implement the user profile page and personal dashboard (`/profile`) in Spendly.

## Goal Description

Build a personal dashboard page (`/profile`) that displays:
1. User details (name, email, member since date).
2. Key performance metrics (Total spent, amount spent this month, transaction count).
3. Visual expense breakdown by category with progress bars.
4. Recent activity showing the last 5 transactions.

We will isolate the dashboard styling to a new page-specific stylesheet `static/css/profile.css` to respect the guidelines in `CLAUDE.md`.

---

## User Review Required

> [!IMPORTANT]
> **Dashboard Styling Isolation**: We will put all dashboard layout and element styles in a separate CSS file at `static/css/profile.css` and link it dynamically from `profile.html`. This keeps `static/css/style.css` clean and modular.

---

## Open Questions

> [!NOTE]
> There are no unresolved open questions. The layout uses standard grid coordinates matching the existing design tokens and variables in `static/css/style.css`.

---

## Proposed Changes

### Database Layer

#### [MODIFY] [db.py](file:///Users/anshumanai/Desktop/expense-tracker/database/db.py)
- Implement helper functions to query user-specific expense data:
  - `get_user_expense_stats(user_id, path=None)`: Returns aggregate stats (total amount spent, transaction count, and current calendar month's total spent).
  - `get_user_category_breakdown(user_id, path=None)`: Returns categories and sum of expenses in each category for the user, sorted by amount descending.
  - `get_user_recent_expenses(user_id, limit=5, path=None)`: Returns the list of the most recent 5 expenses (id, amount, category, date, description) sorted by date descending.

---

### Page-Specific Stylesheet

#### [NEW] [profile.css](file:///Users/anshumanai/Desktop/expense-tracker/static/css/profile.css)
- Implement styling for the dashboard layout elements:
  - `.dashboard-container` and `.dashboard-header` layouts.
  - Grid layout (`.stats-grid`) for KPI cards.
  - Split column grid (`.dashboard-columns`) for the main panel and sidebar.
  - Expense table styling (`.expense-table`), header cells, alternating borders, and alignment.
  - Category badges (`.category-badge`) with unique backgrounds mapping to categories.
  - Progress bar track and colored indicators (`.progress-bar-track`, `.progress-bar`).

---

### Backend Logic

#### [MODIFY] [app.py](file:///Users/anshumanai/Desktop/expense-tracker/app.py)
- Import `get_user_expense_stats`, `get_user_category_breakdown`, and `get_user_recent_expenses` from `database.db`.
- Update the `/profile` route to:
  - Check if the user is authenticated. If not, redirect to `/login` with an error message.
  - Fetch stats, category breakdowns, and the 5 most recent expenses.
  - Render `profile.html` passing the fetched collections.

---

### Templates

#### [NEW] [profile.html](file:///Users/anshumanai/Desktop/expense-tracker/templates/profile.html)
- Create a new template extending `base.html` that renders:
  - Dynamic user greeting and registration details.
  - Metric summary cards (Total spent, current month spending, transaction count).
  - List of recent transactions in a clean table format.
  - Sidebar showing category breakdowns with percentages and progress bars.
  - Dynamic stylesheet inclusion inside the `{% block head %}` block.

---

### Test Suite

#### [NEW] [test_profile_page.py](file:///Users/anshumanai/Desktop/expense-tracker/tests/test_profile_page.py)
- Write test cases:
  - `test_profile_guest_redirect`: Guests attempting to access `/profile` are redirected to `/login` with an error flash.
  - `test_profile_loads_empty`: Logged-in user with no expenses sees empty dashboard states.
  - `test_profile_loads_seeded_data`: Logged-in demo user (seeded with 8 expenses) sees correct populated stats, recent transaction table records, and category progress bars.

---

## Verification Plan

### Automated Tests
Run pytest in the workspace to verify the implementation:
```bash
pytest tests/test_profile_page.py
```

### Manual Verification
- Start the server using `python app.py`.
- Log in using `demo@spendly.com` / `demo123`.
- Verify:
  - Redirect to the profile page `/profile` works and shows the dashboard.
  - "Hello, Demo User!" navbar greeting is displayed.
  - Stats display aggregate totals correctly (e.g. ₹391.25 total spent across 8 transactions).
  - Category breakdown bars are colored and correspond to seeded percentages.
  - Recent activity shows the list of seeded transactions ordered by date.
