# Spec: CSV Export

## Overview
Allow users to download their filtered/sorted list of expenses as a spreadsheet-compatible CSV file. The CSV export must preserve all active filters (category, date range, search query, sorting) currently applied on the dashboard, but it must export the entire matching list of transactions, not just the paginated subset.

## Depends on
- Step 19 (Pagination)

## Routes
- **Create** `GET /expenses/export/csv`:
  - Authentication required.
  - Accepts standard filter query parameters: `category`, `start_date`, `end_date`, `search_query`, `sort_by`, `order`.
  - Generates a CSV file containing all matching expenses for the authenticated user.
  - Returns the CSV content as an attachment with appropriate headers (`Content-Disposition: attachment; filename=spendly_expenses_<timestamp>.csv` and `Content-Type: text/csv`).

## Database changes
No database changes.

## Templates
- **Modify** `templates/profile.html`:
  - Add an "Export CSV" button in the dashboard card header or filter block next to the "Add Expense" button.
  - The link must construct the URL carrying all active filters to pass them to `/expenses/export/csv`.

## Files to change
- `app.py`:
  - Implement `/expenses/export/csv` route.
  - Include auth guard.
  - Extract active filters, fetch matching expenses using `get_filtered_expenses(...)` without limiting the results (i.e. `limit=None`), write to CSV format, and return as a file download.
- `templates/profile.html`:
  - Add the "Export CSV" button carrying current active filters.
- `static/css/profile.css`:
  - Style the "Export CSV" button appropriately to align with Spendly's visual aesthetics.

## Files to create
None.

## New dependencies
No new dependencies. Standard Python library `csv` and `io.StringIO` will be used.

## Rules for implementation
- No SQLAlchemy/ORMs
- Parameterised queries only
- CSS variables only
- No hardcoded colours
- All templates extend base.html
- Correct response content type (`text/csv`) and file attachment headers.

## Definition of done
- An "Export CSV" button is visible on the dashboard (`/profile`) when there are expenses to export.
- Clicking "Export CSV" downloads a CSV file containing all transactions matching the active filters and sorting criteria.
- The CSV file has headers: "Date", "Category", "Description", "Amount".
- Amounts are formatted correctly.
- If there are no expenses matching the current filters, the button is either hidden or disabled, or downloading handles it gracefully (e.g. an empty CSV with just headers).
- Python test suite runs and all tests pass (`pytest` passes completely), including new CSV export tests.
