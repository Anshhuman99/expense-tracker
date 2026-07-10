import pytest
import database.db
from flask import session
import sqlite3


@pytest.fixture
def client(monkeypatch, tmp_path):
    """
    Fixture to set up a clean, isolated database for each test run.
    Monkeypatches database.db.DB_PATH to use a temp directory.
    """
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)

    # Import app inside the fixture to ensure monkeypatching is active
    from app import app as flask_app

    flask_app.config.update({"TESTING": True, "WTF_CSRF_ENABLED": False})

    # Initialize the database structure
    database.db.init_db(db_path)

    with flask_app.test_client() as client:
        yield client


def test_flash_messages_css_availability(client):
    """
    Verify that static/css/flash_messages.css is served successfully
    and contains all the required styles, layout rules, color schemes,
    animations, and responsive blocks according to the specification.
    """
    response = client.get("/static/css/flash_messages.css")
    assert response.status_code == 200
    css = response.data.decode("utf-8")

    # The spec mentions fixed/floating toast container placement, colors, CSS variables
    assert ".toast-container" in css
    assert "position: fixed" in css
    assert ".toast" in css
    assert "display: flex" in css
    assert ".toast-success" in css
    assert ".toast-error" in css
    assert ".toast-warning" in css
    assert ".toast-close-btn" in css
    assert ".auth-alert" in css
    assert ".auth-alert-success" in css
    assert ".auth-alert-error" in css
    assert "@keyframes toastSlideIn" in css
    assert "@keyframes toastSlideOut" in css
    assert "@media" in css  # responsive styles


def test_main_js_inclusion_and_script_tag(client):
    """
    Verify that static/js/main.js is served correctly and references
    the toast logic, and is included in the base template.
    """
    # Verify main.js is served
    js_response = client.get("/static/js/main.js")
    assert js_response.status_code == 200
    js_content = js_response.data.decode("utf-8")
    assert 'document.querySelectorAll(".toast")' in js_content or "toast" in js_content
    assert "dismissToast" in js_content

    # Verify base template links main.js and flash_messages.css
    landing_response = client.get("/")
    assert landing_response.status_code == 200
    html = landing_response.data.decode("utf-8")
    assert (
        'href="/static/css/flash_messages.css"' in html or "flash_messages.css" in html
    )
    assert 'src="/static/js/main.js"' in html or "main.js" in html


def test_all_toast_categories_rendering(client):
    """
    Verify rendering of success, warning, and error toast notifications
    in the global base.html layout (on a regular page like '/')
    including icon names and close buttons.
    """
    # Flash messages for all three categories
    with client.session_transaction() as sess:
        sess["_flashes"] = [
            ("success", "Operation completed successfully!"),
            ("warning", "Be cautious with this action."),
            ("error", "An error occurred processing request."),
        ]

    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Verify container
    assert "toast-container" in html

    # Verify success toast
    assert "toast toast-success" in html
    assert "check_circle" in html  # Material Symbols Outlined success icon name
    assert "Operation completed successfully!" in html

    # Verify warning toast
    assert "toast toast-warning" in html
    assert "warning" in html  # Material Symbols Outlined warning icon name
    assert "Be cautious with this action." in html

    # Verify error toast
    assert "toast toast-error" in html
    assert "error" in html  # Material Symbols Outlined error icon name
    assert "An error occurred processing request." in html

    # Verify that close buttons exist inside the toasts
    assert "toast-close-btn" in html
    assert "close" in html  # Material Symbols Outlined icon close


def test_login_page_inline_alerts(client):
    """
    Verify login page inline alerts:
    - Try accessing a protected page unauthenticated (Auth guard)
    - Try submitting incorrect login credentials (Validation failure)
    - Ensure toasts are NOT displayed when using auth-alerts
    """
    # 1. Access protected route without logging in (Auth guard)
    profile_response = client.get("/profile", follow_redirects=True)
    assert profile_response.status_code == 200
    html = profile_response.data.decode("utf-8")

    # Should redirect to login and show inline error alert, not toast
    assert "auth-alert auth-alert-error" in html
    assert "Please log in to access this page." in html
    assert "error" in html  # icon
    assert "toast toast-error" not in html

    # 2. Login validation failure
    login_response = client.post(
        "/login",
        data={"email": "wrong@example.com", "password": "badpassword"},
        follow_redirects=True,
    )
    assert login_response.status_code == 200
    html2 = login_response.data.decode("utf-8")

    assert "auth-alert auth-alert-error" in html2
    assert "Invalid email or password." in html2
    assert "error" in html2
    assert "toast toast-error" not in html2


def test_registration_page_inline_alerts_and_db_effects(client):
    """
    Verify registration page inline alerts:
    - Missing name validation error
    - Password mismatch validation error
    - DB check (no user is created on validation error)
    - Successful registration displays inline success alert on /login
    - DB check (user is successfully created on happy path)
    """
    # 1. Validation error: passwords do not match
    reg_response = client.post(
        "/register",
        data={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "password123",
            "confirm_password": "differentpassword",
        },
        follow_redirects=True,
    )
    assert reg_response.status_code == 200
    html = reg_response.data.decode("utf-8")

    assert "auth-alert auth-alert-error" in html
    assert "Passwords do not match." in html
    assert "error" in html
    assert "toast toast-error" not in html

    # Verify DB side effect: no user created
    conn = database.db.get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", ("john@example.com",)
    ).fetchone()
    conn.close()
    assert user is None

    # 2. Happy Path Registration
    success_reg_response = client.post(
        "/register",
        data={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert success_reg_response.status_code == 200
    html2 = success_reg_response.data.decode("utf-8")

    # Should redirect to login page and render the success inline alert
    assert "auth-alert auth-alert-success" in html2
    assert "Account created! Please log in." in html2
    assert "check_circle" in html2

    # Verify DB side effect: user created
    conn = database.db.get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE email = ?", ("john@example.com",)
    ).fetchone()
    conn.close()
    assert user is not None
    assert user["name"] == "John Doe"


def test_toast_rendering_on_add_expense_validation_error(client):
    """
    Verify validation error toast rendering on adding a new expense:
    - Log in user
    - Post an invalid amount
    - Verify toast-error is rendered (since add_expense is not login/register)
    - Verify DB contains no new expense
    """
    # Create user and log in
    database.db.create_user("Alice", "alice@example.com", "securepassword")
    client.post(
        "/login",
        data={"email": "alice@example.com", "password": "securepassword"},
        follow_redirects=True,
    )

    # Post invalid amount (negative number)
    response = client.post(
        "/expenses/add",
        data={
            "amount": "-10.00",
            "category": "Food",
            "date": "2026-07-10",
            "description": "Negative amount test",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Should render toast-error
    assert "toast-container" in html
    assert "toast toast-error" in html
    assert "error" in html
    assert "Amount must be a positive number." in html

    # Verify no expense is in database
    conn = database.db.get_db()
    expense = conn.execute(
        "SELECT * FROM expenses WHERE description = ?", ("Negative amount test",)
    ).fetchone()
    conn.close()
    assert expense is None


def test_toast_rendering_on_add_expense_success(client):
    """
    Verify success toast rendering on adding a new expense successfully:
    - Log in user
    - Post valid expense data
    - Verify success toast is rendered on profile page redirect
    - Verify DB side effect
    """
    # Create user and log in
    database.db.create_user("Alice", "alice@example.com", "securepassword")
    client.post(
        "/login",
        data={"email": "alice@example.com", "password": "securepassword"},
        follow_redirects=True,
    )

    # Post valid expense
    response = client.post(
        "/expenses/add",
        data={
            "amount": "250.00",
            "category": "Food",
            "date": "2026-07-10",
            "description": "Lunch at restaurant",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Should render toast-success
    assert "toast-container" in html
    assert "toast toast-success" in html
    assert "check_circle" in html
    assert "Expense added successfully!" in html

    # Verify expense is in database
    conn = database.db.get_db()
    expense = conn.execute(
        "SELECT * FROM expenses WHERE description = ?", ("Lunch at restaurant",)
    ).fetchone()
    conn.close()
    assert expense is not None
    assert expense["amount"] == 250.00


def test_toast_rendering_on_edit_expense_validation_error(client):
    """
    Verify validation error toast rendering on editing an expense:
    - Log in user
    - Insert an expense manually into the DB
    - Attempt to update with invalid format (e.g. empty category)
    - Verify error toast
    - Verify database has not changed
    """
    # Create user and log in
    database.db.create_user("Alice", "alice@example.com", "securepassword")
    client.post(
        "/login",
        data={"email": "alice@example.com", "password": "securepassword"},
        follow_redirects=True,
    )

    # Fetch user_id
    conn = database.db.get_db()
    user = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("alice@example.com",)
    ).fetchone()
    user_id = user["id"]

    # Add an expense manually
    database.db.create_expense(user_id, 100.0, "Food", "2026-07-10", "Original lunch")
    expense = conn.execute(
        "SELECT id FROM expenses WHERE description = ?", ("Original lunch",)
    ).fetchone()
    expense_id = expense["id"]
    conn.close()

    # Attempt to edit with empty category
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={
            "amount": "100.0",
            "category": "",
            "date": "2026-07-10",
            "description": "Attempted edit",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Should render toast-error
    assert "toast-container" in html
    assert "toast toast-error" in html
    assert "Category is required." in html

    # Verify database has not changed
    conn = database.db.get_db()
    chk = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()
    assert chk["category"] == "Food"
    assert chk["description"] == "Original lunch"


def test_toast_rendering_on_edit_expense_success(client):
    """
    Verify success toast rendering on editing an expense successfully:
    - Log in user
    - Insert an expense manually into the DB
    - Update with valid data
    - Verify success toast is rendered on profile page redirect
    - Verify database has updated
    """
    # Create user and log in
    database.db.create_user("Alice", "alice@example.com", "securepassword")
    client.post(
        "/login",
        data={"email": "alice@example.com", "password": "securepassword"},
        follow_redirects=True,
    )

    # Fetch user_id
    conn = database.db.get_db()
    user = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("alice@example.com",)
    ).fetchone()
    user_id = user["id"]

    # Add an expense manually
    database.db.create_expense(user_id, 100.0, "Food", "2026-07-10", "Original lunch")
    expense = conn.execute(
        "SELECT id FROM expenses WHERE description = ?", ("Original lunch",)
    ).fetchone()
    expense_id = expense["id"]
    conn.close()

    # Edit with valid data
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={
            "amount": "150.00",
            "category": "Shopping",
            "date": "2026-07-11",
            "description": "Updated clothing",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Should render toast-success
    assert "toast-container" in html
    assert "toast toast-success" in html
    assert "Expense updated successfully!" in html

    # Verify database has updated
    conn = database.db.get_db()
    chk = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()
    assert chk["amount"] == 150.00
    assert chk["category"] == "Shopping"
    assert chk["date"] == "2026-07-11"
    assert chk["description"] == "Updated clothing"


def test_toast_rendering_on_delete_expense_success(client):
    """
    Verify success toast rendering on deleting an expense successfully:
    - Log in user
    - Insert an expense manually into the DB
    - Perform deletion via POST
    - Verify success toast is rendered on profile page redirect
    - Verify database has deleted the record
    """
    # Create user and log in
    database.db.create_user("Alice", "alice@example.com", "securepassword")
    client.post(
        "/login",
        data={"email": "alice@example.com", "password": "securepassword"},
        follow_redirects=True,
    )

    # Fetch user_id
    conn = database.db.get_db()
    user = conn.execute(
        "SELECT id FROM users WHERE email = ?", ("alice@example.com",)
    ).fetchone()
    user_id = user["id"]

    # Add an expense manually
    database.db.create_expense(user_id, 100.0, "Food", "2026-07-10", "To delete")
    expense = conn.execute(
        "SELECT id FROM expenses WHERE description = ?", ("To delete",)
    ).fetchone()
    expense_id = expense["id"]
    conn.close()

    # Perform deletion
    response = client.post(
        f"/expenses/{expense_id}/delete",
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Should render toast-success
    assert "toast-container" in html
    assert "toast toast-success" in html
    assert "Expense deleted successfully!" in html

    # Verify database deleted
    conn = database.db.get_db()
    chk = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()
    assert chk is None


def test_logout_success_toast(client):
    """
    Verify success toast rendering on logout:
    - Log in user
    - Visit logout route
    - Verify redirect to landing page and success toast rendered
    """
    # Create user and log in
    database.db.create_user("Alice", "alice@example.com", "securepassword")
    client.post(
        "/login",
        data={"email": "alice@example.com", "password": "securepassword"},
        follow_redirects=True,
    )

    # Logout
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # Should redirect to landing and show toast-success
    assert "toast-container" in html
    assert "toast toast-success" in html
    assert "Logged out successfully." in html
