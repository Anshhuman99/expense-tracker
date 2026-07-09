# Spec: Delete Expense

## Overview
This feature allows logged-in users to delete their previously recorded expenses.
The user accesses this functionality by clicking the "Delete" link next to any expense in the transaction list on the profile dashboard.
Clicking this link redirects the user to a confirmation page that displays the expense details and asks them to confirm the deletion.
Upon confirmation (form submission), the expense record is deleted from the database and the user is redirected to the profile dashboard with a success flash message. The KPI stats and category breakdowns will instantly update to reflect the deletion.
If the user cancels, they are redirected back to the profile dashboard without any changes to the database.
Unauthorized requests (e.g. attempting to delete another user's expense, or accessing the delete routes while logged out) must be blocked with appropriate HTTP status codes or redirects with error messages.

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

---

## Routes
- `GET /expenses/<int:id>/delete`:
  - Protected route (redirects to `/login` if not authenticated).
  - Fetches the expense by `id` from the database.
  - Verifies that the expense exists (returns 404 Not Found if not found).
  - Verifies that the expense belongs to the currently logged-in user (returns 403 Forbidden if not the owner).
  - Renders the `delete_expense.html` template confirming the deletion and displaying the expense details.
- `POST /expenses/<int:id>/delete`:
  - Protected route.
  - Fetches the expense by `id` from the database.
  - Verifies that the expense exists (returns 404 Not Found if not found).
  - Verifies that the expense belongs to the currently logged-in user (returns 403 Forbidden if not the owner).
  - Deletes the expense record from the database.
  - Redirects to `/profile` with a success message.

---

## Database changes
No schema changes are required. The `expenses` table contains all the necessary columns.
The following helper function will be created:
- Add to `database/db.py`:
  - `delete_expense(expense_id, path=None)`: Deletes the expense record with the specified ID.

---

## Templates
### Create
- `templates/delete_expense.html`:
  - Extends `templates/base.html`.
  - Renders a card-based confirmation screen displaying the expense details (Amount, Category, Date, Description).
  - Includes a confirmation form submitting a POST request to `/expenses/<id>/delete`.
  - Includes a "Confirm Delete" submit button (using `var(--danger)` for hover/styling) and a "Cancel" link back to `/profile`.

### Modify
- `templates/profile.html`:
  - Update the actions column in the transaction table to include a "Delete" link/button next to the "Edit" link, pointing to `url_for('delete_expense', id=expense.id)`.

---

## Files to change
- `app.py`: Replace the stub route for `/expenses/<int:id>/delete` with the GET/POST implementation including authentication, ownership check, database deletion, and redirect.
- `database/db.py`: Add the `delete_expense` helper function.
- `templates/profile.html`: Add the "Delete" link/button in the actions column.

---

## Files to create
- `templates/delete_expense.html`: The HTML layout for the deletion confirmation page.
- `static/css/delete_expense.css`: Page-specific styles for the Delete Expense page (utilizing CSS variables).
- `tests/test_09-delete-expense.py`: Test suite verifying:
  - Guest redirection to login for both GET and POST requests.
  - Ownership validation (returns 403 when user attempts to delete someone else's expense).
  - Nonexistent expense checking (returns 404 for invalid ID).
  - Normal confirmation page loading (pre-filled fields and cancel link).
  - Successful deletion from the database, redirect, and flash message.
  - Instant update of stats on the profile dashboard.

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
- Restrict delete access to the owner of the expense.

---

## Definition of done
- [ ] Clicking the "Delete" link on the dashboard redirects the logged-in user to `/expenses/<id>/delete`.
- [ ] Accessing `/expenses/<id>/delete` (GET or POST) when not logged in redirects to `/login` with an error message.
- [ ] Attempting to delete a non-existent expense ID returns a 404 status.
- [ ] Attempting to delete an expense belonging to a different user returns a 403 Forbidden status.
- [ ] The delete confirmation page successfully displays the expense's details (Amount, Category, Date, and Description) and a Cancel link.
- [ ] Clicking "Cancel" redirects back to `/profile` without deleting the expense.
- [ ] Submitting the delete confirmation form deletes the expense from the database, redirects to `/profile`, and displays a success flash message.
- [ ] The dashboard stats and the category breakdown update immediately to reflect the deleted expense.
- [ ] Automated tests in `tests/test_09-delete-expense.py` verify all valid/invalid scenarios and pass successfully.
