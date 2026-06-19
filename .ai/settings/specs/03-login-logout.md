# Spec: Login and Logout

## 1. Overview

Implement the authentication flow (Login and Logout) for Spendly. This includes validating credentials, managing session state, updating navigation menus dynamically based on login status, and protecting authenticated routes.

---

## 2. Depends on

- Step 01: Database Setup
- Step 02: Registration

---

## 3. Routes

- `GET /login` — Renders the login page — Public
- `POST /login` — Handles user authentication and session creation — Public
- `GET /logout` — Ends the user session and redirects — Logged-in
- `GET /profile` — Renders the profile stub (modified to require login) — Logged-in

---

## 4. Database changes

- No database changes (uses existing `users` table)

---

## 5. Templates (Create / Modify)

### A. Modify `templates/login.html`
- Replace hardcoded `action="/login"` in the `<form>` tag with `action="{{ url_for('login') }}"`.
- Display flashed messages using the standard flash block matching the layout in `templates/register.html`.

### B. Modify `templates/base.html`
- Update the navigation links in the header dynamically:
  - If a user is logged in (session contains `user_id`), display `"Hello, <user_name>!"`, a link to the profile page, and a `"Sign out"` link.
  - If no user is logged in, display `"Sign in"` and `"Get started"` (link to register).
- Ensure navigation links use `url_for()`.

---

## 6. Files to change

- `database/db.py`
  - Add `get_user_by_email(email, path=None)` helper:
    - Queries the database for a user matching the provided email.
    - Returns the `sqlite3.Row` representing the user or `None` if not found.

- `app.py`
  - Update imports to include `session`, `g`, and `check_password_hash` from `werkzeug.security`.
  - Add a `@app.before_request` hook to load the logged-in user into Flask's `g.user` if `user_id` exists in the session.
  - Update `login` route to handle both `GET` and `POST` requests:
    - On `GET`, render the login page.
    - On `POST`, extract `email` and `password` from the form.
    - Retrieve the user via `get_user_by_email()`.
    - If user exists and password matches (using `check_password_hash`), set `user_id` and `user_name` in Flask's `session`. Flash a success message `"Logged in successfully."` and redirect to `profile` page.
    - If credentials are invalid, flash `"Invalid email or password."` (category: `"error"`) and render `login.html`.
  - Update `logout` route:
    - Clear the session (`session.clear()`).
    - Flash a success message `"Logged out successfully."` and redirect to the landing page (`url_for('landing')`).
  - Update `profile` route:
    - If user is not logged in (no `user_id` in session), flash `"Please log in to access this page."` and redirect to `url_for('login')`.
    - If logged in, render the profile stub.

- `templates/login.html`
  - Modify the form action to use `url_for('login')`.

- `templates/base.html`
  - Make navigation bar dynamic based on login state.

---

## 7. Files to create

- `tests/test_login_logout.py`
  - Write test cases using `pytest` and Flask test client:
    - `test_login_page_loads`: GET `/login` returns 200 and loads login form.
    - `test_login_success`: POST valid credentials redirects to profile, sets session `user_id` / `user_name`, and flashes success.
    - `test_login_invalid_email`: POST unregistered email flashes `"Invalid email or password."`
    - `test_login_wrong_password`: POST registered email with incorrect password flashes `"Invalid email or password."`
    - `test_logout_clears_session`: GET `/logout` when logged in clears session, flashes `"Logged out successfully."`, and redirects to landing page.
    - `test_profile_requires_login`: GET `/profile` without login redirects to `/login` and flashes `"Please log in to access this page."`.
    - `test_profile_loads_when_logged_in`: GET `/profile` with active login session loads successfully.

---

## 8. New dependencies

- No new dependencies

---

## 9. Rules for Implementation

- No SQLAlchemy/ORMs
- Parameterised queries only
- Passwords verified with `werkzeug.security.check_password_hash`
- CSS variables only
- No hardcoded colours
- All templates extend base.html

---

## 10. Definition of Done

- [ ] Form action in `templates/login.html` uses `url_for('login')`
- [ ] Navigation bar dynamically shows user greeting and "Sign out" link if logged in, or "Sign in" and "Get started" if logged out
- [ ] `get_user_by_email` query in `database/db.py` uses parameterized SQL
- [ ] Password validation uses `check_password_hash`
- [ ] Login errors flash `"Invalid email or password."` with category `"error"`
- [ ] Logged-out users are prevented from accessing `/profile` and redirected to `/login`
- [ ] Logging out clears the Flask session
- [ ] `tests/test_login_logout.py` contains comprehensive test suite and all tests pass
