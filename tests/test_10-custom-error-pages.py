import pytest
import sqlite3
import database.db
from database.queries import get_expense_by_id, get_user_by_id


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


def test_404_not_found_unauthenticated(client):
    """
    Verify that accessing a nonexistent route without logging in returns 404,
    renders the custom 404 page extending base.html, links to static/css/errors.css,
    displays the correct details/icon, and provides a button to return to the Home page.
    """
    response = client.get("/this-route-does-not-exist-at-all")
    assert response.status_code == 404
    html = response.data.decode("utf-8")

    # Verify custom 404 template indicators
    assert "404" in html
    assert "Page Not Found" in html
    assert "We can't seem to find the page you're looking for." in html
    assert "🧭" in html  # Compass icon

    # Verify extending base.html
    assert "Spendly" in html
    assert "navbar" in html
    assert "footer" in html

    # Verify link to static/css/errors.css
    assert 'href="/static/css/errors.css"' in html or "errors.css" in html

    # Verify return to Home button for unauthenticated users
    assert 'href="/"' in html or "Go to Home" in html
    assert "Go to Dashboard" not in html


def test_404_not_found_authenticated(client):
    """
    Verify that accessing a nonexistent route as a logged-in user returns 404,
    and provides a button/link to return to the Dashboard (/profile).
    """
    # Create and login user
    database.db.create_user("Alice", "alice@example.com", "alicepassword")
    client.post(
        "/login", data={"email": "alice@example.com", "password": "alicepassword"}
    )

    response = client.get("/this-route-does-not-exist-at-all")
    assert response.status_code == 404
    html = response.data.decode("utf-8")

    # Verify custom 404 indicators
    assert "Page Not Found" in html

    # Verify return to Dashboard button for authenticated users
    assert 'href="/profile"' in html or "Go to Dashboard" in html
    assert "Go to Home" not in html


def test_404_not_found_invalid_route_parameters(client):
    """
    Verify that accessing an invalid parameter route (e.g. non-integer ID for edit)
    triggers Flask's routing failure, returning 404 and rendering the custom 404 page.
    """
    database.db.create_user("Alice", "alice@example.com", "alicepassword")
    client.post(
        "/login", data={"email": "alice@example.com", "password": "alicepassword"}
    )

    # Non-integer ID 'abc' is not matched by <int:id>
    response = client.get("/expenses/abc/edit")
    assert response.status_code == 404
    html = response.data.decode("utf-8")
    assert "Page Not Found" in html
    assert 'href="/profile"' in html or "Go to Dashboard" in html


def test_404_not_found_nonexistent_expense(client):
    """
    Verify that attempting to edit a non-existent expense ID (which is an integer)
    triggers an abort(404) inside the route, rendering the custom 404 error page.
    """
    database.db.create_user("Alice", "alice@example.com", "alicepassword")
    client.post(
        "/login", data={"email": "alice@example.com", "password": "alicepassword"}
    )

    response = client.get("/expenses/99999/edit")
    assert response.status_code == 404
    html = response.data.decode("utf-8")
    assert "Page Not Found" in html
    assert 'href="/profile"' in html or "Go to Dashboard" in html


def test_403_forbidden_unauthenticated(client, monkeypatch):
    """
    Verify that triggering a 403 Forbidden without logging in returns 403,
    renders the custom 403 page extending base.html, links to static/css/errors.css,
    displays the correct details/icon, and provides a button to Sign In.
    """
    from app import app as flask_app
    from flask import abort

    monkeypatch.setitem(flask_app.view_functions, "terms", lambda: abort(403))

    response = client.get("/terms")
    assert response.status_code == 403
    html = response.data.decode("utf-8")

    # Verify custom 403 template indicators
    assert "403" in html
    assert "Access Denied" in html
    assert "You do not have permission to view or manage this resource." in html
    assert "🔒" in html  # Lock icon

    # Verify extending base.html
    assert "Spendly" in html
    assert "navbar" in html
    assert "footer" in html

    # Verify return to Sign In button for unauthenticated users
    assert 'href="/login"' in html or "Sign In" in html
    assert "Go to Dashboard" not in html


def test_403_forbidden_authenticated_ownership_violation_edit_get(client):
    """
    Verify that an authenticated user attempting to GET another user's expense edit page
    triggers abort(403) and displays the custom 403 error page with a Dashboard link.
    """
    # Create two users
    database.db.create_user("Alice", "alice@example.com", "alicepassword")
    database.db.create_user("Bob", "bob@example.com", "bobpassword")

    # Alice creates an expense
    conn = database.db.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (1, 100.0, "Food", "2026-07-09", "Alice's lunch"),
    )
    conn.commit()
    expense_id = conn.execute("SELECT id FROM expenses WHERE user_id = 1").fetchone()[
        "id"
    ]
    conn.close()

    # Bob logs in
    client.post("/login", data={"email": "bob@example.com", "password": "bobpassword"})

    # Bob attempts to access Alice's expense
    response = client.get(f"/expenses/{expense_id}/edit")
    assert response.status_code == 403
    html = response.data.decode("utf-8")

    assert "Access Denied" in html
    assert "403" in html
    assert 'href="/profile"' in html or "Go to Dashboard" in html
    assert "Sign In" not in html


def test_403_forbidden_authenticated_ownership_violation_edit_post(client):
    """
    Verify that an authenticated user attempting to POST an update to another user's expense
    triggers abort(403) and displays the custom 403 error page.
    """
    database.db.create_user("Alice", "alice@example.com", "alicepassword")
    database.db.create_user("Bob", "bob@example.com", "bobpassword")

    # Alice creates an expense
    conn = database.db.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (1, 75.0, "Transport", "2026-07-09", "Alice's cab"),
    )
    conn.commit()
    expense_id = conn.execute("SELECT id FROM expenses WHERE user_id = 1").fetchone()[
        "id"
    ]
    conn.close()

    # Bob logs in
    client.post("/login", data={"email": "bob@example.com", "password": "bobpassword"})

    # Bob attempts to POST update to Alice's expense
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={
            "amount": "90.00",
            "category": "Transport",
            "date": "2026-07-09",
            "description": "Bob trying to update Alice's expense",
        },
    )
    assert response.status_code == 403
    html = response.data.decode("utf-8")
    assert "Access Denied" in html


def test_403_forbidden_authenticated_ownership_violation_delete_get(client):
    """
    Verify that an authenticated user attempting to GET another user's expense delete page
    triggers abort(403) and displays the custom 403 error page.
    """
    database.db.create_user("Alice", "alice@example.com", "alicepassword")
    database.db.create_user("Bob", "bob@example.com", "bobpassword")

    # Alice creates an expense
    conn = database.db.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (1, 150.0, "Bills", "2026-07-09", "Alice's bill"),
    )
    conn.commit()
    expense_id = conn.execute("SELECT id FROM expenses WHERE user_id = 1").fetchone()[
        "id"
    ]
    conn.close()

    # Bob logs in
    client.post("/login", data={"email": "bob@example.com", "password": "bobpassword"})

    # Bob attempts to GET delete Alice's expense
    response = client.get(f"/expenses/{expense_id}/delete")
    assert response.status_code == 403
    html = response.data.decode("utf-8")
    assert "Access Denied" in html


def test_403_forbidden_authenticated_ownership_violation_delete_post(client):
    """
    Verify that an authenticated user attempting to POST delete another user's expense
    triggers abort(403) and displays the custom 403 error page.
    """
    database.db.create_user("Alice", "alice@example.com", "alicepassword")
    database.db.create_user("Bob", "bob@example.com", "bobpassword")

    # Alice creates an expense
    conn = database.db.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (1, 20.0, "Shopping", "2026-07-09", "Alice's shopping"),
    )
    conn.commit()
    expense_id = conn.execute("SELECT id FROM expenses WHERE user_id = 1").fetchone()[
        "id"
    ]
    conn.close()

    # Bob logs in
    client.post("/login", data={"email": "bob@example.com", "password": "bobpassword"})

    # Bob attempts to POST delete Alice's expense
    response = client.post(f"/expenses/{expense_id}/delete")
    assert response.status_code == 403
    html = response.data.decode("utf-8")
    assert "Access Denied" in html


def test_500_internal_server_error_unauthenticated(client):
    """
    Verify that triggering a 500 error page when unauthenticated returns 500,
    renders the custom 500 page extending base.html, links to static/css/errors.css,
    displays the correct details/icon, and provides a button to return to the Home page.
    """
    response = client.get("/trigger-500")
    assert response.status_code == 500
    html = response.data.decode("utf-8")

    # Verify custom 500 template indicators
    assert "500" in html
    assert "Something went wrong" in html
    assert "An internal server error occurred. We are looking into this." in html
    assert "⚡" in html  # Lightning icon

    # Verify extending base.html
    assert "Spendly" in html
    assert "navbar" in html
    assert "footer" in html

    # Verify return to Home button for unauthenticated users
    assert 'href="/"' in html or "Go to Home" in html
    assert "Go to Dashboard" not in html


def test_500_internal_server_error_authenticated(client):
    """
    Verify that triggering a 500 error page when authenticated returns 500,
    and provides a button/link to return to the Dashboard (/profile).
    """
    # Create and login user
    database.db.create_user("Alice", "alice@example.com", "alicepassword")
    client.post(
        "/login", data={"email": "alice@example.com", "password": "alicepassword"}
    )

    response = client.get("/trigger-500")
    assert response.status_code == 500
    html = response.data.decode("utf-8")

    # Verify custom 500 indicators
    assert "Something went wrong" in html

    # Verify return to Dashboard button for authenticated users
    assert 'href="/profile"' in html or "Go to Dashboard" in html
    assert "Go to Home" not in html


def test_errors_css_availability(client):
    """
    Verify that static/css/errors.css is served successfully and contains the correct classes.
    """
    response = client.get("/static/css/errors.css")
    assert response.status_code == 200
    css = response.data.decode("utf-8")
    assert ".error-container" in css
    assert ".error-card" in css
    assert ".error-icon" in css
    assert ".error-code" in css
    assert ".error-title" in css
    assert ".error-message" in css
    assert ".error-btn" in css
    assert "var(--" in css  # Strictly uses CSS variables


def test_db_side_effects_on_errors(client, monkeypatch):
    """
    Verify that accessing error routes (404, 403, 500) has no adverse DB side effects.
    Also ensures that database read/write queries can still be executed successfully
    before and after encountering errors, verifying no leaked connections or table locks.
    """
    # 1. Register and login a user, and insert an expense
    database.db.create_user("Alice", "alice@example.com", "alicepassword")
    client.post(
        "/login", data={"email": "alice@example.com", "password": "alicepassword"}
    )

    # Check we can read successfully from DB before errors
    user = get_user_by_id(1)
    assert user["name"] == "Alice"

    conn = database.db.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (1, 10.0, "Food", "2026-07-09", "Pre-error lunch"),
    )
    conn.commit()
    conn.close()

    # 2. Trigger various error pages
    # Trigger 404
    client.get("/nonexistent-page-url")

    # Trigger 403 by monkeypatching
    from app import app as flask_app
    from flask import abort

    monkeypatch.setitem(flask_app.view_functions, "terms", lambda: abort(403))
    client.get("/terms")

    # Trigger 500
    client.get("/trigger-500")

    # 3. Check we can still read and write successfully to DB after errors
    # Retrieve user
    user_after = get_user_by_id(1)
    assert user_after["name"] == "Alice"

    # Insert a new expense
    conn = database.db.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (1, 20.0, "Transport", "2026-07-09", "Post-error cab"),
    )
    conn.commit()

    # Verify counts
    cursor = conn.execute("SELECT COUNT(*) FROM expenses WHERE user_id = 1")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 2
