# Spec: Add Expense

## Overview
This feature allows logged-in users to record new expenses through an intuitive form. 
The form includes:
1. Amount: A required positive decimal value representing the expense amount.
2. Category: A required select dropdown containing a set of pre-defined categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other).
3. Date: A required date picker, defaulting to the current date.
4. Description: An optional text input describing the expense.

When submitted, the expense is saved to the database, associated with the current logged-in user, and the user is redirected back to the profile dashboard with a success message. The new expense immediately updates the user's dashboard KPI statistics and recent transaction list.

---

## Depends on
- Step 1: Database Setup
- Step 2: Registration
- Step 3: Login / Logout
- Step 4: Profile Page Design
- Step 5: Backend Route Profile Page
- Step 6: Data Filter for Profile Page

---

## Routes
- `GET /expenses/add`: 
  - Protected route (redirects to `/login` if not authenticated).
  - Renders the `add_expense.html` template.
- `POST /expenses/add`:
  - Protected route.
  - Processes the new expense data.
  - Validates inputs: amount (must be positive float/decimal), category (must be one of the allowed values), date (must be non-empty and a valid YYYY-MM-DD string).
  - Inserts the new record into the `expenses` database table.
  - Redirects to `/profile` with a success message, or re-renders the form with error flashes.

---

## Database changes
No database changes are required since the `expenses` table already exists and contains the necessary columns (`id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`).
The following new helper will be added to `database/db.py`:
- `create_expense(user_id, amount, category, date, description, path=None)`: Inserts a new expense row into the database.

---

## Templates
### Create
- `templates/add_expense.html`: 
  - Extends `templates/base.html`.
  - Displays a clean form card centered on the page.
  - Contains fields: Amount (number type with step="0.01"), Category (select dropdown), Date (date type pre-filled), Description (textarea or text type).
  - Includes a submit button ("Add Expense") and a cancel link ("Cancel") pointing to `/profile`.

---

## Files to change
- `app.py`: Replace the stub route for `/expenses/add` with implementation for both GET and POST requests. Apply user authorization check, data validation, invoke database helper to insert expense, flash messages, and redirect.
- `database/db.py`: Add the `create_expense` helper function.

---

## Files to create
- `templates/add_expense.html`: The HTML layout for the form page.
- `static/css/add_expense.css`: Page-specific styles for the Add Expense page.
- `tests/test_add_expense.py`: Automated tests verifying form loading, authorization, validations, successful addition, and redirection.

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

---

## Definition of done
- [ ] Visiting `/expenses/add` when not logged in redirects to `/login` with a warning flash message.
- [ ] Visiting `/expenses/add` when logged in successfully renders the Add Expense page.
- [ ] The date input default value is pre-filled with the current date (server time, local date).
- [ ] Submitting the form with a negative, zero, or non-numeric amount displays a validation error message.
- [ ] Submitting the form with an empty category or a category outside of the allowed options displays a validation error message.
- [ ] Submitting the form with an empty or invalid date format displays a validation error.
- [ ] Submitting a valid form adds the expense to the database table, redirects to `/profile`, and displays a success flash message.
- [ ] The newly added expense is visible on the profile dashboard, and the KPI stats (total spent, monthly total, transaction count) are correctly updated.
- [ ] Clicking the "Cancel" button returns the user to the profile page without adding any expense.
- [ ] Automated tests in `tests/test_add_expense.py` verify all valid/invalid scenarios and pass successfully.
