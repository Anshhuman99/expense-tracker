# Spec: Registration

## 1. Overview

Implement input validation and robustness for the registration feature in Spendly. 
Ensure that user accounts are registered correctly with valid data, duplicate registrations are prevented, and errors are handled and displayed user-friendly. on success user is shwon a success mesaage 

---

## 2. Depends on

- Step 01: Database Setup

---

## 3. Routes

- No new routes
- Modify existing `/register` route (both `GET` and `POST`) in `app.py` to add input validation and display error messages.

---

## 4. Database changes

- No database changes

---

## 5. Templates (Create / Modify)

### A. Modify `templates/register.html`
- Replace hardcoded `action="/register"` in the `<form>` tag with `action="{{ url_for('register') }}"`.
- Ensure all form inputs (`name`, `email`, `password`) have correct attributes to assist browser-side validation (e.g. `minlength="8"` on password, `required` attribute, proper type attributes).

---

## 6. Files to change

- `app.py`
  - Update `register()` view function:
    - Extract form inputs and trim/strip whitespaces from `name` and `email`.
    - Perform backend validation checks:
      1. Name must not be empty after trimming.
      2. Email must not be empty and must follow a basic valid email pattern (contains `@` and a period `.`).
      3. Password must be at least 8 characters long.
    - If any validation fails, flash a corresponding error message (category: `"error"`) and render the `register.html` template.
    - If all validations pass, attempt to call `create_user(name, email, password)`.
    - If an `sqlite3.IntegrityError` is raised (indicating the email is already in use), flash `"Email already registered."` (category: `"error"`) and render the `register.html` template.
    - If registration succeeds, flash `"Account created! Please log in."` (category: `"success"`) and redirect to `url_for('login')`.

- `templates/register.html`
  - Update the action attribute to use `url_for('register')`.
  - Add client-side validation hints like `minlength="8"` to password field.

---

## 7. Files to create

- `tests/test_register.py`
  - Write test cases using `pytest` and Flask test client:
    - `test_register_page_loads`: GET `/register` returns HTTP 200 and renders the registration page.
    - `test_register_success`: POST valid registration details, database record is created, flashes success message, and redirects to `/login`.
    - `test_register_duplicate_email`: Attempt to register with an already existing email, flash `"Email already registered."` and render registration page again.
    - `test_register_missing_fields`: POST missing fields, error is flashed.
    - `test_register_empty_name`: POST with empty name or name containing only whitespace, error is flashed.
    - `test_register_invalid_email`: POST with invalid email format (e.g. missing `@` or `.`), error is flashed.
    - `test_register_short_password`: POST with password shorter than 8 characters, error is flashed.

---

## 8. New dependencies

- No new dependencies

---

## 9. Rules for Implementation

- No SQLAlchemy/ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (already done by `create_user` in `database/db.py`)
- CSS variables only
- No hardcoded colours
- All templates extend base.html

---

## 10. Definition of Done

- [ ] Form action in `templates/register.html` uses `url_for('register')`
- [ ] User name input is trimmed of whitespace before validation
- [ ] Validation checks for empty name, invalid email, and password length (< 8 chars) are enforced in python code
- [ ] Database error on duplicate email is handled gracefully with an error flash message
- [ ] Successful registration stores password hashed using `werkzeug.security`
- [ ] Successful registration flashes a success message and redirects to `/login`
- [ ] Registration page displays flashed errors and success messages properly
- [ ] `tests/test_register.py` is written and all tests pass successfully
