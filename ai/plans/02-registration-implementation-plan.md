# Implementation Plan - User Registration (Step 02)

This plan outlines the steps required to implement robust validation, error handling, CSS styling, and comprehensive tests for the user registration flow in Spendly.

## Goal Description

Improve the registration flow by validating user inputs (whitespace trimmed name, valid email structure, minimum 8-character password) on both the client-side and backend. We'll handle duplicate email scenarios gracefully, show proper visual success/error feedback (including styling `.auth-success` in CSS and enabling flash messages on `/login`), and add isolated automated tests.

---

## User Review Required

We identified two secondary improvements needed for a complete user experience:
1. **Style Addition in `static/css/style.css`**: Currently, there is a class for `.auth-error` but no `.auth-success` class. We will add a styled `.auth-success` alert box that uses the existing CSS variables.
2. **Flash Messages in `templates/login.html`**: After successful registration, we redirect the user to `/login` with a success flash message. However, the login template currently does not display flashed messages. We will add the flash rendering block to `login.html`.

---

## Open Questions

> [!IMPORTANT]
> **Email Validation Pattern**: For backend validation, we plan to use a standard email regex pattern: `r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"`. Let us know if you prefer a different validation pattern or if this standard check is sufficient.

---

## Proposed Changes

### Configuration and CSS

#### [MODIFY] [static/css/style.css](file:///Users/anshumanai/Desktop/expense-tracker/static/css/style.css)
- Add style definitions for `.auth-success` to align with the visual style of `.auth-error` but using green variables:
```css
.auth-success {
    background: var(--accent-light);
    color: var(--accent);
    border: 1px solid #c2dfce;
    border-radius: var(--radius-sm);
    padding: 0.75rem 1rem;
    font-size: 0.875rem;
    margin-bottom: 1.25rem;
}
```

---

### Templates

#### [MODIFY] [templates/register.html](file:///Users/anshumanai/Desktop/expense-tracker/templates/register.html)
- Change `<form method="POST" action="/register">` to use Jinja: `<form method="POST" action="{{ url_for('register') }}">`.
- Add `minlength="8"` and `required` attributes to the password input.

#### [MODIFY] [templates/login.html](file:///Users/anshumanai/Desktop/expense-tracker/templates/login.html)
- Add flash messages container right above the form inside the auth card to display the success message after registration redirection.

---

### Backend Logic

#### [MODIFY] [app.py](file:///Users/anshumanai/Desktop/expense-tracker/app.py)
- Modify `register()` route to:
  1. Retrieve form inputs (`name`, `email`, `password`).
  2. Trim whitespace from `name` and `email` using `.strip()`.
  3. Validate inputs:
     - Name must not be empty.
     - Email must match the validation regex.
     - Password must be at least 8 characters.
  4. If any checks fail, call `flash("Error message", "error")` and render `register.html`.
  5. Attempt to insert user via `create_user(name, email, password)`.
  6. Catch `sqlite3.IntegrityError` to detect duplicate email, flashing `"Email already registered."` and rendering `register.html`.
  7. On success, flash `"Account created! Please log in."` with category `"success"` and redirect to `/login`.

---

### Test Suite

#### [NEW] [tests/test_register.py](file:///Users/anshumanai/Desktop/expense-tracker/tests/test_register.py)
- Create a test file utilizing a Flask test client.
- Use `monkeypatch` to mock `database.db.DB_PATH` so database tests are fully isolated and run in a temporary test database.
- Implement tests for:
  - `test_register_page_loads`: Renders registration form correctly.
  - `test_register_success`: Successful post redirects, hashes password, saves record.
  - `test_register_duplicate_email`: Flashes unique constraint violation.
  - `test_register_empty_name`: Flashes empty name validation.
  - `test_register_invalid_email`: Flashes invalid email format validation.
  - `test_register_short_password`: Flashes short password length validation.

---

## Verification Plan

### Automated Tests
Run pytest in the workspace to verify the implementation:
```bash
pytest tests/test_register.py
```

### Manual Verification
- Start the server using `python app.py`.
- Navigate to `/register` and test:
  - Submitting an empty name.
  - Submitting an invalid email address (e.g. `user@com`).
  - Submitting a password shorter than 8 characters.
  - Registering a new valid user (should redirect to login with a green success message).
  - Registering a user with the same email again (should display a red error message).
