# Spec: Excel Export

## Overview
Allow users to download their filtered/sorted list of expenses as a formatted Excel (.xlsx) file. The Excel export must preserve all active filters (category, date range, search query, sorting) currently applied on the dashboard, but export the entire matching list — not just the paginated subset. The generated workbook must have a styled header row, auto-sized columns, and formatted amount cells to make the spreadsheet immediately readable.

## Depends on
- Step 20 (CSV Export)

## Routes
- **Create** `GET /expenses/export/excel`:
  - Authentication required.
  - Accepts standard filter query parameters: `category`, `start_date`, `end_date`, `search_query`, `sort_by`, `order`.
  - Generates an Excel workbook (.xlsx) containing all matching expenses for the authenticated user.
  - Returns the workbook as an attachment with appropriate headers:
    - `Content-Disposition: attachment; filename=spendly_expenses_<timestamp>.xlsx`
    - `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

## Database changes
No database changes.

## Templates
- **Modify** `templates/profile.html`:
  - Add an "Export Excel" button in the dashboard card header `.card-actions` container alongside the existing "Export CSV" and "Add Expense" buttons.
  - The link must construct the URL carrying all active filters to pass them to `/expenses/export/excel`.

## Files to change
- `app.py`:
  - Import `openpyxl` and relevant styling classes at the top of the file.
  - Implement `/expenses/export/excel` route.
  - Include auth guard.
  - Extract active filters using `_get_filter_params()`, fetch matching expenses using `get_filtered_expenses(...)` with `limit=None`, generate an openpyxl workbook with formatted headers and data rows, and return as a file download.
  - Use `_sanitize_csv_value()` equivalent concept — values written to Excel cells are inherently safe from formula injection when set via openpyxl.
- `templates/profile.html`:
  - Add the "Export Excel" button carrying current active filters inside the `.card-actions` block.
- `static/css/profile.css`:
  - Add `.btn-excel` style class for the Excel button, using CSS variables for colours.
- `requirements.txt`:
  - Add `openpyxl` as a new approved dependency.

## Files to create
None.

## New dependencies
- `openpyxl` — required for generating `.xlsx` Excel files. This is explicitly pre-approved in CLAUDE.md Step 21 roadmap description. Must be added to `requirements.txt` after installation.

## Rules for implementation
- No SQLAlchemy/ORMs
- Parameterised queries only
- CSS variables only
- No hardcoded colours
- All templates extend base.html
- Correct response content type (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`) and file attachment headers.
- Use `io.BytesIO` to build the Excel file in memory — do not write to disk.
- Excel workbook must include:
  - Sheet name: "Expenses"
  - Header row: Date, Category, Description, Amount
  - Bold header row
  - Amount column formatted as a number with 2 decimal places
  - All columns auto-fitted to content width (approximate)

## Definition of done
- An "Export Excel" button is visible on the dashboard (`/profile`) when there are expenses to export.
- Clicking "Export Excel" downloads an `.xlsx` file containing all transactions matching the active filters and sorting criteria.
- The Excel file has headers: "Date", "Category", "Description", "Amount" with bold formatting.
- Amounts are formatted as numeric values with 2 decimal places.
- If there are no expenses matching the current filters, the button is either hidden or the download handles it gracefully (a workbook with just headers).
- `openpyxl` is added to `requirements.txt`.
- Python test suite runs and all tests pass (`pytest` passes completely), including new Excel export tests.
