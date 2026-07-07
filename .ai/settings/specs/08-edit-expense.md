# Spec: Edit Expense

## Overview
This feature allows logged-in users to modify their previously recorded expenses.
The user accesses this functionality by clicking the "Edit" link next to any expense in the transaction list on the profile dashboard.
The edit page displays a form pre-populated with the current details of the selected expense:
1. Amount: A positive decimal value.
2. Category: A select dropdown with allowed categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other).
3. Date: A date picker showing the expense's date.
4. Description: An optional text description (max 25 characters).

Upon form submission, if validation passes, the expense record is updated in the database and the user is redirected to the profile dashboard with a success flash message. The KPI stats and category breakdowns will instantly update to reflect the edits.
If validation fails, the form is re-rendered with appropriate error flashes.
Unauthorized requests (e.g. attempting to edit another user's expense, or accessing the edit route while logged out) must be blocked with appropriate HTTP status codes or redirects with error messages.

---

## Depends on
- Step 1: Database Setup
- Step 2: Registration
- Step 3: Login / Logout
- Step 4: Profile Page Design
- Step 5: Backend Route Profile Page
- Step 6: Data Filter for Profile Page
- Step 7: Add Expense

---

## Routes
- `GET /expenses/<int:id>/edit`:
  - Protected route (redirects to `/login` if not authenticated).
  - Fetches the expense by `id` from the database.
  - Verifies that the expense exists (returns 404 if not found).
  - Verifies that the expense belongs to the currently logged-in user (returns 403 Forbidden if not the owner).
  - Renders the `edit_expense.html` template pre-filled with the expense's details.
- `POST /expenses/<int:id>/edit`:
  - Protected route.
  - Validates ownership of the expense.
  - Processes and validates the submitted form data:
    - Amount: Must be a positive, finite number.
    - Category: Must be non-empty and one of the allowed categories.
    - Date: Must be a valid date in `YYYY-MM-DD` format.
    - Description: Must not exceed 250 characters.
  - Updates the expense record in the database.
  - Redirects to `/profile` with a success message, or re-renders the form with error flashes if validation fails.

---

## Database changes
No schema changes are required. The `expenses` table contains all the necessary columns.
The following helper functions will be created/modified:
- Add to `database/queries.py`:
  - `get_expense_by_id(expense_id, path=None)`: Fetches a single expense record by its ID. Returns a dictionary/Row or None.
- Add to `database/db.py`:
  - `update_expense(expense_id, amount, category, date, description, path=None)`: Updates the amount, category, date, and description for the specified expense ID.
- Modify in `database/queries.py`:
  - Update `get_recent_transactions(user_id, limit=10, path=None)` to select the `id` column from the `expenses` table, enabling templates to construct edit links.

---

## Templates
### Create
- `templates/edit_expense.html`:
  - Extends `templates/base.html`.
  - Renders a card-based form containing Amount, Category, Date, and Description fields.
  - Pre-fills all inputs with the existing expense details.
  - Includes a "Save Changes" submit button and a "Cancel" link back to `/profile`.

### Modify
- `templates/profile.html`:
  - Add an "Actions" header column to the transaction table.
  - For each transaction row, render an "Edit" link/button pointing to `url_for('edit_expense', id=expense.id)`.

---

## Files to change
- `app.py`: Replace the stub route for `/expenses/<int:id>/edit` with the GET/POST implementation including authentication, ownership check, validation, and redirect.
- `database/queries.py`:
  - Add `get_expense_by_id` helper.
  - Modify `get_recent_transactions` to retrieve the `id` column.
- `database/db.py`: Add `update_expense` helper.
- `templates/profile.html`: Add actions column and edit button/link.

---

## Files to create
- `templates/edit_expense.html`: The HTML layout for the editing form.
- `static/css/edit_expense.css`: Page-specific styles for the Edit Expense page.
- `tests/test_edit_expense.py`: Test suite verifying load details, authentication, ownership validation, field validations, database persistence, and redirects.

---

## New dependencies
No new dependencies.

---

## Rules for implementation
- No SQLAlchemy/ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- CSS variables only
- No hardcoded colours
- All templates extend base.html
- Ensure SQLite foreign keys are turned ON via connection hook in `get_db()`.
- Validate that the input amount is positive (> 0).
- Standardize on `YYYY-MM-DD` date formatting.
- Restrict edit access to the owner of the expense.

---

## Definition of done
- [ ] Clicking the "Edit" link on the dashboard redirects the logged-in user to `/expenses/<id>/edit`.
- [ ] Accessing `/expenses/<id>/edit` when not logged in redirects to `/login` with an error message.
- [ ] Attempting to edit a non-existent expense ID returns a 404 status.
- [ ] Attempting to edit an expense belonging to a different user returns a 403 Forbidden status.
- [ ] The edit form successfully displays with all input fields pre-populated with the expense's current values.
- [ ] Submitting the form with a negative, zero, or non-numeric amount displays a validation error.
- [ ] Submitting the form with an empty category or an invalid category displays a validation error.
- [ ] Submitting the form with an empty or invalid date displays a validation error.
- [ ] Submitting a valid form updates the expense in the database, redirects to `/profile`, and displays a success flash message.
- [ ] The dashboard stats and the category breakdown update immediately to reflect the edited expense.
- [ ] Clicking the "Cancel" button redirects the user to `/profile` without modifying the database.
- [ ] Automated tests in `tests/test_edit_expense.py` verify all valid/invalid scenarios and pass successfully.
