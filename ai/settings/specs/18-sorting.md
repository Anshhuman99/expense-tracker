# Spec: Sorting

## Overview
Allow expenses to be sorted by multiple fields. Support sorting by date, amount, and category, and provide both ascending and descending ordering options on the main dashboard (`/profile`).

## Depends on
- Step 17 (Search Expenses)

## Routes
No new routes. The existing dashboard route (`/profile`) will be updated to handle sorting arguments.

## Database changes
No database changes.

## Templates
- **Modify** `templates/profile.html`:
  - Add sort control dropdowns or clickable table headers for sorting transactions by Date, Category, and Amount.
  - Support ascending and descending directions.
  - Maintain the active sort parameters upon refreshing or submitting filters.

## Files to change
- `app.py`: Read the sort parameter (`sort_by`) and order parameter (`order`) from GET request arguments and pass them to the query layer and template context.
- `database/queries.py`: Enhance the database query helpers to order results dynamically according to `sort_by` and `order` criteria.
- `templates/profile.html`: Introduce interactive sorting controls to the user interface.

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
- The dashboard page (`/profile`) offers control options for selecting sorting field (Date, Amount, Category) and direction (Ascending, Descending).
- Changing sorting criteria refreshes the page and orders transactions appropriately according to selected keys.
- Selected sorting parameters are preserved in UI controls upon submission.
- Sorting works in unison with search and filter parameters (e.g. searching "Swiggy" sorted by Amount DESC).
- Python test suite runs and all tests pass (`pytest` passes completely).
