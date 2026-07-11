# Spec: PDF Reports

## Overview
Allow users to download their filtered/sorted list of expenses as a printable, styled PDF report. The PDF report must preserve all active filters (category, date range, search query, sorting) currently applied on the dashboard, but export the entire matching list — not just the paginated subset. The generated PDF must be professionally formatted with a title, summary metrics (Total Spent, Transaction Count), a clean table, page numbers, and proper alignment.

## Depends on
- Step 21 (Excel Export)

## Routes
- **Create** `GET /expenses/export/pdf`:
  - Authentication required.
  - Accepts standard filter query parameters: `category`, `start_date`, `end_date`, `search_query`, `sort_by`, `order`.
  - Generates a PDF document containing the matching expenses.
  - Returns the PDF as an attachment with headers:
    - `Content-Disposition: attachment; filename=spendly_report_<timestamp>.pdf`
    - `Content-Type: application/pdf`

## Database changes
No database changes.

## Templates
- **Modify** `templates/profile.html`:
  - Add an "Export PDF" button in the dashboard card header `.card-actions` container alongside "Export CSV" and "Export Excel".
  - The link must construct the URL carrying all active filters to pass them to `/expenses/export/pdf`.

## Files to change
- `app.py`:
  - Import `reportlab` classes at the top of the file.
  - Implement `/expenses/export/pdf` route.
  - Include auth guard.
  - Extract active filters using `_get_filter_params()`, fetch matching expenses using `get_filtered_expenses(...)` with `limit=None`, generate a reportlab SimpleDocTemplate in-memory, apply styles, build the layout, and return as a file download.
- `templates/profile.html`:
  - Add the "Export PDF" button carrying current active filters inside the `.card-actions` block.
- `static/css/profile.css`:
  - Add `.btn-pdf` style class for the PDF button, using CSS variables for colours.
- `requirements.txt`:
  - Add `reportlab` as a new approved dependency.

## Files to create
None.

## New dependencies
- `reportlab` — required for generating PDF documents programmatically in Python. This is explicitly pre-approved in CLAUDE.md Step 22 roadmap description. Must be added to `requirements.txt` after installation.

## Rules for implementation
- No SQLAlchemy/ORMs
- Parameterised queries only
- CSS variables only
- No hardcoded colours
- All templates extend base.html
- Correct response content type (`application/pdf`) and file attachment headers.
- Use `io.BytesIO` to build the PDF file in memory — do not write to disk.
- PDF design must include:
  - Document Title: "Spendly Expense Report"
  - Generated Timestamp & Filter description
  - Summary cards/text showing: "Total Spent", "Total Transactions"
  - Tabular list: Date, Category, Description, Amount
  - Alternating row backgrounds or clean table styling using ReportLab `TableStyle`
  - Brand green header row theme (`#2D6A4F`) matching the app styling
  - Dynamic page numbers using a canvas helper or simple custom template

## Definition of done
- An "Export PDF" button is visible on the dashboard (`/profile`) when there are expenses to export.
- Clicking "Export PDF" downloads a `.pdf` file containing all transactions matching the active filters and sorting criteria.
- The PDF file contains a header with summary statistics and a formatted transaction table.
- Amounts are formatted as numeric values with 2 decimal places.
- If there are no expenses matching the current filters, the button is either hidden or the download handles it gracefully (a report with just headers).
- `reportlab` is added to `requirements.txt`.
- Python test suite runs and all tests pass (`pytest` passes completely), including new PDF export tests.
