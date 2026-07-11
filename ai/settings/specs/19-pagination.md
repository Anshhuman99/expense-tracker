# Spec: Pagination

## Overview
Improve performance for users with many expenses by displaying expenses in manageable pages with navigation controls on the main dashboard (`/profile`). Active filters (category, date range, search query, sorting) must be maintained when changing pages.

## Depends on
- Step 18 (Sorting)

## Routes
No new routes. The existing dashboard route (`/profile`) will be updated to handle pagination arguments.

## Database changes
No database changes.

## Templates
- **Modify** `templates/profile.html`:
  - Add pagination navigation controls at the bottom of the expenses list/table.
  - Controls should include:
    - Previous and Next page buttons/links (disabled or hidden when on first/last page respectively).
    - Numeric page links (e.g., Page 1, 2, 3...) to go directly to a page.
    - Information about the current page, e.g., "Showing 11-20 of 45 expenses".
  - Ensure all page links maintain the current active filter values (category, start_date, end_date, search_query, sort_by, order) in the URL query string.

## Files to change
- `database/queries.py`:
  - Enhance `get_filtered_expenses(...)` to accept `limit` and `offset` arguments to support database-level pagination.
  - Implement a new helper `get_filtered_expenses_count(...)` to fetch the total count of expenses matching the active filters.
- `app.py`:
  - Extract the `page` (default 1) parameter from the request GET arguments.
  - Validate and cap `page` if it is outside the valid range.
  - Use `get_filtered_expenses_count(...)` to count the total matching expenses.
  - Call `get_filtered_expenses(...)` with appropriate `limit=10` and `offset` computed based on `page`.
  - Calculate total pages and pass pagination variables to the template context (e.g., `current_page`, `total_pages`, `total_count`, `per_page`).
- `templates/profile.html`:
  - Render the pagination controls beneath the table.
  - Ensure they are styled nicely using existing CSS variables.
- `static/css/profile.css`:
  - Add styles for pagination controls (e.g., `.pagination`, `.page-link`, `.page-info`, active/disabled states).

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy/ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (n/a for this step)
- CSS variables only
- No hardcoded colours
- All templates extend base.html

## Definition of done
- The dashboard page (`/profile`) shows expenses limited to 10 per page.
- Pagination navigation controls (Previous, Next, page numbers) are displayed below the expenses table.
- Navigating pages preserves all active filters (search query, category, start date, end date, sorting columns, sorting direction).
- A message like "Showing X-Y of Z expenses" is displayed, reflecting the correct count of expenses.
- Cap pagination gracefully: if page is requested out of bounds, default to page 1 or the last page as appropriate.
- Python test suite runs and all tests pass (`pytest` passes completely), including new pagination tests.
