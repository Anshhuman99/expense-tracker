# Implementation Plan - Data Filter for Profile Page (Step 06)

This plan outlines the steps required to implement dynamic data filtering and searching on the user's dashboard (profile page) transaction history list.

## Goal Description
Build a filtering system on the `/profile` page allowing users to filter expenses by:
1. Search query (`q`): Case-insensitive match on description and category.
2. Category (`category`): Selected from a dropdown containing unique categories logged by the user.
3. Date range (`start_date` and `end_date`): Filter within inclusive calendar bounds.

Only the transaction history table will filter down (up to a limit of 100). The KPI summary cards and the Category Breakdown sidebar will remain unfiltered (representing overall totals). When active, the filters will be retained in the form inputs, the header will display "Filtered Expenses", and a "Clear" button will allow resetting the filters.

---

## User Review Required

> [!IMPORTANT]
> **Dynamic Categories**: The category dropdown will be loaded dynamically from the database based on the unique categories the user has logged. If the user has no logged expenses, the dropdown will display only "All Categories".
> **Metric Independence**: KPI cards and sidebar breakdown stats will intentionally remain unfiltered (global/monthly lifetime statistics) to provide context on total budget status even when looking at filtered transactions.

---

## Open Questions

> [!NOTE]
> There are no unresolved open questions. The design handles empty states, invalid date bounds, and text search cases cleanly.

---

## Proposed Changes

### Database Query Layer

#### [MODIFY] [queries.py](file:///Users/anshumanai/Desktop/expense-tracker/database/queries.py)
Create two new query helper functions:
- `get_categories(user_id, path=None)`:
  - Queries `SELECT DISTINCT category FROM expenses WHERE user_id = ? ORDER BY category ASC`.
  - Returns a list of category strings.
- `get_filtered_expenses(user_id, category=None, start_date=None, end_date=None, search_query=None, limit=None, path=None)`:
  - Dynamically builds a parameterized query:
    - Base: `SELECT id, amount, category, date, description FROM expenses WHERE user_id = ?`
    - Adds `AND category = ?` if `category` is provided.
    - Adds `AND date >= ?` if `start_date` is provided.
    - Adds `AND date <= ?` if `end_date` is provided.
    - Adds `AND (description LIKE ? OR category LIKE ?)` if `search_query` is provided (using `%search%` wildcards).
    - Sorts with `ORDER BY date DESC, id DESC`.
    - Restricts with `LIMIT ?` if `limit` is provided.
  - Returns a list of dictionaries matching the schema keys.

---

### Backend Logic

#### [MODIFY] [app.py](file:///Users/anshumanai/Desktop/expense-tracker/app.py)
- Import `get_categories` and `get_filtered_expenses` from `database.queries`.
- Update the `/profile` route:
  - Extract query params `q`, `category`, `start_date`, `end_date` from `request.args`.
  - Create `active_filters` dict to pass back for form state retention.
  - Determine `is_filtered` based on whether any query parameter is present and non-empty.
  - Fetch dynamic list of categories using `get_categories(user_id)`.
  - Fetch expenses:
    - If `is_filtered` is True, fetch using `get_filtered_expenses(...)` with `limit=100`.
    - If `is_filtered` is False, default to `get_recent_transactions(user_id, limit=10)`.
  - Pass `categories`, `active_filters`, `is_filtered`, and `recent_expenses` to the rendering template.

---

### Templates

#### [MODIFY] [profile.html](file:///Users/anshumanai/Desktop/expense-tracker/templates/profile.html)
- Add `<div class="filters-card">` with a `<form>` immediately above the `<div class="table-responsive">` container:
  - Text input for description search.
  - Dropdown select for categories (looping over `categories` returned from backend).
  - Two date input pickers (`start_date`, `end_date`).
  - Submit button labeled "Filter".
  - Conditional reset link/button labeled "Clear" (visible only if `is_filtered` is True).
- Pre-populate all input elements using `active_filters` to retain state.
- Change the heading dynamically: `{% if is_filtered %}Filtered Expenses{% else %}Recent Expenses{% endif %}`.
- Update table empty state block to show "No matching expenses found." when filtered.

---

### Styling

#### [MODIFY] [profile.css](file:///Users/anshumanai/Desktop/expense-tracker/static/css/profile.css)
Add filter form styling rules at the bottom of the stylesheet:
- `.filters-card`: Add padding, border, radius, and warm paper background.
- `.filters-form`: Use grid layout (`grid-template-columns: 2fr 1.5fr 1.25fr 1.25fr auto;`) aligned to flex-end.
- `.filter-group`: Display flex-direction column with small labels and styled inputs/dropdowns.
- `.filter-actions`: Display flex layout for buttons.
- `@media (max-width: 900px)`: Responsive override to 2-column grid layout.
- `@media (max-width: 600px)`: Responsive override to 1-column grid layout.
- Use only existing CSS variables for colors, borders, and margins.

---

### Test Suite

#### [NEW] [test_filtering.py](file:///Users/anshumanai/Desktop/expense-tracker/tests/test_filtering.py)
Write automated tests covering:
- Query helpers:
  - `get_categories` for empty and seeded database states.
  - `get_filtered_expenses` for individual parameters (category, text search, date range) and combination filters.
- Route-level tests:
  - Default view returns 10 recent transactions.
  - Filtered requests return correct counts and matching items.
  - Form inputs on returned page contain submitted values (state retention).
  - "Clear" button is visible when filtered, hidden when default.
  - KPI stats and category breakdown are independent and do not change when transaction filter is active.

---

## Verification Plan

### Automated Tests
Run pytest in the workspace directory:
```bash
pytest tests/test_filtering.py
pytest tests/test_profile_page.py
```

### Manual Verification
- Start Flask development server: `python app.py`.
- Log in as the seeded user (`demo@spendly.com` / `demo123`).
- Test dropdown options: confirm they display "Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other".
- Test category filter: select **Transport** -> confirm only "Uber" is displayed, and the title changes to "Filtered Expenses".
- Test text search: input **Lunch** -> table displays only "Lunch".
- Test date range: set bounds from **2026-06-03** to **2026-06-08** -> table displays "Uber", "Electricity", and "Pharmacy".
- Test Clear: click **Clear** -> page reloads without query parameters, displays "Recent Expenses" with all 8 items, and hides the "Clear" button.
- Verify stats cards and breakdown sidebar totals do not change when filtering is active.
