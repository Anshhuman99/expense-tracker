# Spec: Monthly Budget System

## Overview
Allow users to create and manage monthly spending budgets on a per-category basis. Each budget defines a target limit for a single category in a specific month. The budgets page displays each active budget as a progress bar showing the percentage spent vs. the limit, colour-coded to indicate normal / approaching / exceeded states. Users can create, edit, and delete budgets. The system reads from the existing `expenses` table to calculate actual spending — no changes to `expenses` or `users` are required.

---

## Depends on
- Step 1: Database Setup
- Step 2: Registration
- Step 3: Login / Logout
- Step 4: Profile Page Design
- Step 5: Backend Route Profile Page
- Step 6: Data Filter for Profile Page
- Step 7: Add Expense
- Step 8: Edit Expense
- Step 9: Delete Expense
- Step 10: Custom Error Pages
- Step 11: Empty States
- Step 12: Better Flash Messages
- Step 13: Responsive Design

---

## Routes

### `GET /budgets`
- Auth required.
- Displays the user's budgets for the selected month (defaults to the current month).
- Accepts an optional `?month=YYYY-MM` query parameter to view a different month.
- For each budget row, queries the `expenses` table to compute the total spent in that category for the selected month.
- Renders progress bars and status indicators.
- Shows an empty state with a call-to-action if no budgets exist for the month.

### `GET /budgets/add`
- Auth required.
- Renders a form with fields: category (dropdown of `ALLOWED_CATEGORIES`), amount (positive number), month (defaults to current `YYYY-MM`).

### `POST /budgets/add`
- Auth required.
- Validates:
  - `category` must be one of `ALLOWED_CATEGORIES`.
  - `amount` must be a positive number (same validation rules as expenses).
  - `month` must be a valid `YYYY-MM` string.
  - A budget for the same user + category + month must not already exist (unique constraint).
- On success, inserts into `budgets` table and redirects to `/budgets` with a success flash.
- On validation failure, re-renders the form with errors and preserves input values.

### `GET /budgets/<int:id>/edit`
- Auth required. Ownership-checked.
- Pre-populates the form with current budget values.

### `POST /budgets/<int:id>/edit`
- Auth required. Ownership-checked.
- Same validation as add, but the uniqueness check excludes the current budget's own row.
- On success, updates the row and redirects to `/budgets` with a success flash.

### `GET /budgets/<int:id>/delete`
- Auth required. Ownership-checked.
- Renders a confirmation page showing the budget details.

### `POST /budgets/<int:id>/delete`
- Auth required. Ownership-checked.
- Deletes the budget and redirects to `/budgets` with a success flash.

---

## Database changes

### New table: `budgets`
Created via migration file `database/migrations/001_add_budgets_table.sql`.

```sql
CREATE TABLE IF NOT EXISTS budgets (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL REFERENCES users(id),
    category  TEXT    NOT NULL,
    amount    REAL    NOT NULL,
    month     TEXT    NOT NULL,
    created_at TEXT   DEFAULT (datetime('now')),
    UNIQUE(user_id, category, month)
);
```

Column notes:
- `amount` — the budget limit (positive REAL, same rounding rules as expenses).
- `month` — stored as `YYYY-MM` text (e.g. `"2026-07"`).
- The `UNIQUE(user_id, category, month)` constraint prevents duplicate budgets for the same user + category + month.

### Migration application
- `database/db.py` `init_db()` must be updated to apply migration files from `database/migrations/` in numeric order after the base schema.

No changes to the `expenses` or `users` tables.

---

## Templates

### Create
- `templates/budgets.html` — main budgets overview page with month selector and progress bars.
- `templates/add_budget.html` — add budget form.
- `templates/edit_budget.html` — edit budget form (pre-populated).
- `templates/delete_budget.html` — delete confirmation page.

### Modify
- `templates/base.html` — add a "Budgets" link to the navbar (visible only when logged in), after "Dashboard" and before "Analytics".

---

## Files to change
- `app.py` — add 6 new route handlers (GET/POST for add, edit, delete; GET for list), import new query functions, add budget validation logic.
- `database/db.py` — update `init_db()` to scan and execute `database/migrations/*.sql` files in sorted order after base schema creation.
- `database/queries.py` — add budget query functions (see Files to create section).
- `templates/base.html` — add "Budgets" nav link.
- `static/css/style.css` — add active-nav highlighting for the budgets link if not already generic.

---

## Files to create
- `database/migrations/001_add_budgets_table.sql` — migration DDL for the `budgets` table.
- `templates/budgets.html` — budget overview page with month navigation and progress bars.
- `templates/add_budget.html` — add budget form.
- `templates/edit_budget.html` — edit budget form.
- `templates/delete_budget.html` — delete budget confirmation.
- `static/css/budgets.css` — page-specific styles for the budgets pages (progress bars, status indicators, month selector).

---

## New dependencies
No new dependencies.

---

## Rules for implementation
- No SQLAlchemy/ORMs.
- Parameterised queries only.
- Passwords hashed with werkzeug.
- CSS variables only.
- No hardcoded colours.
- All templates extend `base.html`.
- All budget query functions (CRUD + spending aggregation) belong in `database/queries.py` — do not add query logic to `db.py` or route handlers.
- Budget `amount` follows the same rounding rules as expense `amount` (round to 2 decimal places on every read, write, and calculation).
- The month selector must default to the current month and allow navigating to previous/next months via query parameter — do not use JavaScript date pickers.
- Progress bar colour states must use CSS variables (e.g. `--budget-ok`, `--budget-warning`, `--budget-exceeded`) and transition smoothly.
- Threshold suggestions: ≤ 75% = normal, 75–100% = warning, > 100% = exceeded.
- Ownership must be checked on every edit/delete route — abort(403) if the budget does not belong to the logged-in user.
- The uniqueness constraint (user + category + month) must be enforced both at the database level (UNIQUE constraint) and with a user-friendly flash message on `IntegrityError`.
- Empty state on `/budgets` must follow the pattern established in Step 11, with an illustration and a call-to-action button linking to `/budgets/add`.
- Responsive layout must follow the patterns established in Step 13.

---

## Definition of done
- [ ] Migration `001_add_budgets_table.sql` exists and creates the `budgets` table with the correct schema and UNIQUE constraint.
- [ ] `init_db()` in `db.py` applies migrations from `database/migrations/` in sorted order.
- [ ] All 6 budget routes (`/budgets`, `/budgets/add` GET+POST, `/budgets/<id>/edit` GET+POST, `/budgets/<id>/delete` GET+POST) are functional and auth-guarded.
- [ ] Budget validation rejects missing/invalid category, non-positive amounts, malformed months, and duplicate user+category+month combinations.
- [ ] Ownership is enforced on edit and delete routes (403 for non-owners).
- [ ] `/budgets` page displays progress bars showing actual spending vs. budget limit for each category in the selected month.
- [ ] Progress bars are colour-coded: normal (≤ 75%), warning (75–100%), exceeded (> 100%).
- [ ] Month navigation (previous / next) works via query parameter.
- [ ] Empty state is shown when no budgets exist for the selected month.
- [ ] "Budgets" link appears in the navbar for logged-in users.
- [ ] All templates extend `base.html` and use `url_for()` for links.
- [ ] No inline CSS, no inline JavaScript, no hardcoded colours.
- [ ] All SQL uses parameterised queries.
- [ ] Pages are responsive (desktop, tablet, mobile).
- [ ] Existing tests continue to pass (`pytest`).
