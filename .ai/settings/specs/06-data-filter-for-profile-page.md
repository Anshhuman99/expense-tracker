# Spec: Data Filter For Profile Page

## Overview
This feature introduces filtering capabilities to the expense list on the user profile page. Users will be able to filter their transaction history dynamically using a form on the dashboard. The filters include:
1. Text search (`q`): Case-insensitive match on expense description and category name.
2. Category (`category`): Select dropdown containing all unique categories the user has logged (fetched dynamically from the database), plus an "All Categories" option.
3. Date range (`start_date` and `end_date`): Start and end date picker inputs.

The table list on the left will filter down to matching transactions. When filters are active, the default transaction list limit of 10 will be increased to a higher limit of 100 to allow searching through history.
KPI stats (Total Spent, Spent This Month, and Transactions count) and the Category Breakdown sidebar will remain unfiltered (representing overall lifetime/monthly summaries) to preserve context.
If no filters are active, the page shows the 10 most recent transactions as in Step 5.

---

## Depends on
- Step 1: Database setup (schema and `get_db` helper exist)
- Step 2: Registration (`users` are stored in database)
- Step 3: Login / Logout (session is managed, `/profile` is protected)
- Step 4: Profile page static UI (template exists)
- Step 5: Backend route connection (`get_user_by_id`, `get_summary_stats`, `get_recent_transactions`, and `get_category_breakdown` exist)

---

## Routes
No new routes. The existing GET `/profile` route is modified to accept optional query parameters:
- `q` (string, optional): Text to search in description and category.
- `category` (string, optional): Category to filter.
- `start_date` (string, optional): ISO date format `YYYY-MM-DD`.
- `end_date` (string, optional): ISO date format `YYYY-MM-DD`.

If parameters are present, the page applies the filters. If parameters are absent, it defaults to unfiltered.

---

## Database changes
No database changes. The dynamic filters will query the existing `expenses` table.
The following new helper functions will be added to `database/queries.py`:
- `get_categories(user_id, path=None)`: Retrieves all unique categories recorded by a specific user, sorted alphabetically.
- `get_filtered_expenses(user_id, category=None, start_date=None, end_date=None, search_query=None, limit=None, path=None)`: Constructs and executes a dynamic, parameterized SQLite query based on active search criteria.

---

## Templates
Modify: `templates/profile.html`
- Add a new filters form container inside the main content column, directly above the transactions table.
- Populate the category `<select>` dropdown dynamically from a list of unique categories logged by the user.
- Retain form input values (text input, category selection, date pickers) after form submission.
- Dynamically change the section header from "Recent Expenses" to "Filtered Expenses" when any filter is active.
- Display a "Clear" button/link when any filter is active to reset all inputs and remove the query parameters.
- Show an empty-state message inside the table if no matching expenses are found.

---

## Files to change
- `app.py`: Update the `profile` route to extract query parameters, fetch dynamic categories, fetch filtered expenses when applicable, and pass filter states back to the template.
- `templates/profile.html`: Embed the filter form, handle state retention, conditional headers, and the "Clear" action.
- `static/css/profile.css`: Add styling for the filters card, form grid, group inputs, labels, and filter actions (with responsive layouts for mobile screens).

---

## Files to create
No new files.

---

## New dependencies
No new dependencies.

---

## Rules for implementation
- No SQLAlchemy or ORMs
- Raw sqlite3 only via get_db()
- Parameterised SQL queries only
- Never concatenate user input into SQL
- Passwords hashed with werkzeug
- CSS variables only
- No hardcoded colours
- No inline styles
- All templates extend base.html
- Business logic belongs in Python, not Jinja templates
- Do not filter the summary KPI stats or category breakdown sidebar; only filter the main transaction table.
- If no filters are active, retrieve the 10 most recent transactions. If filters are active, retrieve matching transactions up to a limit of 100.
- Category retrieval: Query distinct categories logged by the user (`SELECT DISTINCT category FROM expenses WHERE user_id = ? ORDER BY category ASC`).

---

## Validation and Edge Cases
- Missing inputs: Empty strings are ignored and treated as "no filter" for that field.
- Malformed inputs: If start/end dates do not conform to `YYYY-MM-DD` (e.g. invalid date text), handle gracefully without crashing (ignore them or treat as empty).
- Conflicting values: If `start_date` > `end_date`, the query returns 0 results. The page remains functional.
- Text search: SQL query uses parameterized `LIKE` with wildcards `%` on description or category, handled safely without raw string injection.

---

## Behaviour
- Default behavior: Loading `/profile` without arguments fetches the 10 most recent transactions.
- Filtered behavior: Submitting filters requests `/profile?q=...&category=...&start_date=...&end_date=...` and displays all matching transactions up to 100.
- AND behavior: If multiple filters are set (e.g., category and search query), the query combines them using `AND` operators in the SQL `WHERE` clause.
- Persistence of state: Active values are passed back to the template and rendered in input elements' `value` attributes and selected dropdown option.
- Resetting: Clicking "Clear" resets all query parameters and reloads the default route.

---

## Testing
Create new automated tests in `tests/test_filtering.py`:
- Test default/unfiltered view (displays recent 10 transactions).
- Test category filtering (returns only transactions matching the chosen category).
- Test text search (matches description case-insensitively).
- Test date filtering (inclusive bounds, no results when bounds don't overlap).
- Test combined filters (AND logic for query, category, and dates).
- Test state retention in HTML response.
- Test that KPI stats and category breakdown remain unchanged when filters are active.

---

## Definition of Done
- [ ] Visiting `/profile` with no parameters loads the dashboard with 10 most recent transactions.
- [ ] Selecting a category filters the table to show only items matching that category.
- [ ] Specifying a date range filters the table to show items within that range (inclusive).
- [ ] Inputting a search query filters the table to matching descriptions or categories case-insensitively.
- [ ] Applying multiple filters filters the table to items matching all criteria (AND logic).
- [ ] Submitted filter values are prefilled/selected in the form fields after page load.
- [ ] "Clear" button resets filters, reloads default dashboard, and is hidden when no filters are active.
- [ ] KPI cards and category breakdown sidebar remain unfiltered when filters are applied.
- [ ] Heading changes to "Filtered Expenses" if a filter is active, otherwise shows "Recent Expenses".
- [ ] Database query uses parameterized arguments for all filters.
- [ ] Table shows a custom empty state message when no transactions match the filters.
- [ ] Automated tests in `tests/test_filtering.py` verify all filter behaviors and pass successfully.
