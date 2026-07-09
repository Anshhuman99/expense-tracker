# Implementation Plan - Login and Logout (Step 03)

This plan outlines the steps required to implement the user login, session management, dynamic navigation, route protection, and tests for Spendly.

## Goal Description

Implement session-based authentication for Spendly. Users should be able to log in with valid credentials, end their session via logout, view a personalized navigation bar when authenticated, and be restricted from viewing protected pages (like `/profile`) unless logged in.

---

## User Review Required

- **Protected Routes**: We are introducing login protection for the `/profile` route. If a logged-out user tries to access `/profile`, they will be redirected to the login page with an error flash message.
- **Navbar Layout**: The navigation bar in `templates/base.html` will dynamically show a welcoming message (`"Hello, <name>!"`), a link to the profile page, and a `"Sign out"` button when a user session exists.

---

## Open Questions

> [!NOTE]
> **Session Lifetime**: We will use Flask's default session behavior (non-permanent cookie that expires when the user closes their browser). Let us know if you want to configure custom session lifetimes or cookies.

---

## Proposed Changes

### Database Layer

#### [MODIFY] [db.py](file:///Users/anshumanai/Desktop/expense-tracker/database/db.py)
- Implement a helper function `get_user_by_email(email, path=None)` to look up users:
```python
def get_user_by_email(email, path=None):
    conn = get_db(path)
    try:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return user
    finally:
        conn.close()
```

---

### Backend Logic

#### [MODIFY] [app.py](file:///Users/anshumanai/Desktop/expense-tracker/app.py)
- Import `session`, `g` from `flask`.
- Import `check_password_hash` from `werkzeug.security`.
- Implement a `@app.before_request` hook to load the current user from the database if `user_id` exists in the session:
```python
@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        conn = get_db()
        g.user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
```
- Update `/login` route:
  - Add `methods=["GET", "POST"]` support.
  - On `POST`:
    - Retrieve `email` (strip whitespaces) and `password`.
    - Fetch the user using `get_user_by_email(email)`.
    - Verify credentials using `check_password_hash(user['password_hash'], password)`.
    - If validation fails, flash `"Invalid email or password."` (category `"error"`) and render `login.html`.
    - If valid, set `user_id` and `user_name` in the session, flash `"Logged in successfully."` (category `"success"`), and redirect to `url_for('profile')`.
- Update `/logout` route:
  - Clear the Flask session using `session.clear()`.
  - Flash `"Logged out successfully."` (category `"success"`).
  - Redirect to the landing page `url_for('landing')`.
- Update `/profile` route:
  - Add authorization check: if `session.get("user_id")` is not set, flash `"Please log in to access this page."` (category `"error"`) and redirect to `url_for('login')`.

---

### Templates

#### [MODIFY] [login.html](file:///Users/anshumanai/Desktop/expense-tracker/templates/login.html)
- Change `<form method="POST" action="/login">` to `<form method="POST" action="{{ url_for('login') }}">`.

#### [MODIFY] [base.html](file:///Users/anshumanai/Desktop/expense-tracker/templates/base.html)
- Update navigation links block in the header to conditionally render options based on `session.get('user_id')`:
```html
<div class="nav-links">
    {% if session.get('user_id') %}
        <span class="nav-user">Hello, {{ session.get('user_name') }}</span>
        <a href="{{ url_for('profile') }}">Profile</a>
        <a href="{{ url_for('logout') }}" class="nav-cta">Sign out</a>
    {% else %}
        <a href="{{ url_for('login') }}">Sign in</a>
        <a href="{{ url_for('register') }}" class="nav-cta">Get started</a>
    {% endif %}
</div>
```

---

### Test Suite

#### [NEW] [test_login_logout.py](file:///Users/anshumanai/Desktop/expense-tracker/tests/test_login_logout.py)
- Create a test suite using `pytest` and Flask test client:
  - Use `monkeypatch` to mock `database.db.DB_PATH` to ensure database tests run against an isolated temporary test database.
  - Implement the following tests:
    - `test_login_page_loads`: GET `/login` renders the login form.
    - `test_login_success`: POST valid credentials for the seeded demo user (`demo@spendly.com` / `demo123`), redirects, sets session keys, and flashes success.
    - `test_login_invalid_email`: POST unregistered email, flashes error.
    - `test_login_wrong_password`: POST wrong password, flashes error.
    - `test_logout_clears_session`: Logging out clears session, redirects to landing page, and flashes success.
    - `test_profile_requires_login`: Requesting `/profile` as guest redirects to `/login` with an error message.
    - `test_profile_loads_when_logged_in`: Requesting `/profile` as logged-in user renders the stub message successfully.

---

## Verification Plan

### Automated Tests
Run pytest in the workspace to verify the implementation:
```bash
pytest tests/test_login_logout.py
```

### Manual Verification
- Start the server using `python app.py`.
- Navigate to `/login`:
  - Attempt to log in with unregistered email (e.g., `notfound@example.com`). Verify error message.
  - Attempt to log in with correct email but wrong password. Verify error message.
  - Log in with seeded credentials (`demo@spendly.com` / `demo123`). Verify redirect to profile and success message.
  - Verify that the navigation bar updates to "Hello, Demo User!", "Profile", and "Sign out".
- Click "Sign out":
  - Verify redirect to the landing page and success flash message.
  - Verify navigation bar resets to "Sign in" and "Get started".
- Attempt to navigate directly to `/profile` while logged out:
  - Verify redirect to `/login` and error flash message.
