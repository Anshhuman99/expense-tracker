# Spec: Search Expenses

## Overview
Introduce a keyword search capability for the user's expenses. Users should be able to type a search query in a text field on the main dashboard (`/profile`), and filter their transaction list to entries whose description or category matches the search term. The search should work in combination with existing category and date filters, and results should display matching expenses instantly and clearly.

## Depends on
- Step 13 (Responsive Design)
- Step 16 (Spending Insights)

## Routes
No new routes. The existing dashboard route (`/profile`) will be updated to handle an optional `q` or `search_query` GET parameter.

## Database changes
No database changes.

## Templates
- **Modify** `templates/profile.html`:
  - Add a search input field to the existing filters form.
  - Style the input to match the current premium look.
  - Retain the search input value upon form submission.

## Files to change
- `app.py`: Read the search query parameter from request GET args and pass it down to query and templates.
- `database/queries.py`: Ensure `get_filtered_expenses` is correctly utilized or enhanced (it already has `search_query` support; double check logic and integration).
- `templates/profile.html`: Update form structure to include search inputs and query values.
- `static/css/profile.css`: Add styles for search inputs, buttons, and matching highlighting if desired.

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
- The dashboard (`/profile`) has a visible text search input field for "Search expenses".
- Entering a keyword (matching description or category) and submitting filters updates the transaction table to only display matching items.
- The search query input preserves the value entered after submission.
- The search functions correctly alongside other filters (category, start_date, end_date).
- When no results are found, a friendly empty-state page or helper text is displayed (reusing Empty States styling from Step 11).
- Python test suite runs and all tests pass (`pytest` passes completely).
