import pytest
import datetime
import database.db
from database.queries import get_expense_by_id


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


def test_guest_redirect(client):
    """
    1. Guest redirect:
       Verify that accessing the edit expense page (via GET or POST)
       redirects unauthenticated users to the /login page.
    """
    # Test GET redirect
    response_get = client.get("/expenses/1/edit")
    assert response_get.status_code == 302
    assert "/login" in response_get.location

    # Test GET redirect followed to login page
    response_get_followed = client.get("/expenses/1/edit", follow_redirects=True)
    assert response_get_followed.status_code == 200
    assert b"Please log in to access this page." in response_get_followed.data

    # Test POST redirect
    response_post = client.post(
        "/expenses/1/edit",
        data={
            "amount": "100.00",
            "category": "Food",
            "date": "2026-06-25",
            "description": "Unauthorized attempt",
        },
    )
    assert response_post.status_code == 302
    assert "/login" in response_post.location


def test_owner_authorization(client):
    """
    2. Owner authorization check:
       Verify that a logged-in user cannot edit an expense belonging to another user.
       Should return 403 Forbidden.
    """
    # Create Alice (user_id=1)
    database.db.create_user("Alice", "alice@example.com", "passalice")

    # Create Bob (user_id=2)
    database.db.create_user("Bob", "bob@example.com", "passbob")

    # Alice logs in and creates an expense
    conn = database.db.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (1, 50.0, "Food", "2026-06-20", "Alice's lunch"),
    )
    conn.commit()
    expense_id = conn.execute("SELECT id FROM expenses WHERE user_id = 1").fetchone()[
        "id"
    ]
    conn.close()

    # Bob logs in
    client.post("/login", data={"email": "bob@example.com", "password": "passbob"})

    # Bob tries to access Alice's expense edit page
    response_get = client.get(f"/expenses/{expense_id}/edit")
    assert response_get.status_code == 403

    # Bob tries to POST update to Alice's expense
    response_post = client.post(
        f"/expenses/{expense_id}/edit",
        data={
            "amount": "100.00",
            "category": "Bills",
            "date": "2026-06-20",
            "description": "Bob trying to hijack",
        },
    )
    assert response_post.status_code == 403


def test_nonexistent_expense(client):
    """
    3. Nonexistent expense check:
       Verify that attempting to edit a non-existent expense ID returns a 404 Not Found.
    """
    # Create user and log in
    database.db.create_user("Alice", "alice@example.com", "passalice")
    client.post("/login", data={"email": "alice@example.com", "password": "passalice"})

    # GET nonexistent expense ID (e.g. 9999)
    response_get = client.get("/expenses/9999/edit")
    assert response_get.status_code == 404

    # POST nonexistent expense ID
    response_post = client.post(
        "/expenses/9999/edit",
        data={
            "amount": "50.00",
            "category": "Food",
            "date": "2026-06-20",
            "description": "Nonexistent",
        },
    )
    assert response_post.status_code == 404


def test_normal_page_load(client):
    """
    4. Normal page load:
       Verify that GET /expenses/<id>/edit when logged in loads the edit expense form
       pre-populated with current values and a cancel button pointing to /profile.
    """
    # Create user and log in
    database.db.create_user("Alice", "alice@example.com", "passalice")
    client.post("/login", data={"email": "alice@example.com", "password": "passalice"})

    # Insert Alice's expense
    conn = database.db.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (1, 45.99, "Transport", "2026-06-21", "Train ticket"),
    )
    conn.commit()
    expense_id = conn.execute("SELECT id FROM expenses").fetchone()["id"]
    conn.close()

    # Request the edit page
    response = client.get(f"/expenses/{expense_id}/edit")
    assert response.status_code == 200
    assert b"Edit Expense" in response.data
    assert b'value="45.99"' in response.data
    assert b'value="2026-06-21"' in response.data
    assert b'value="Train ticket"' in response.data
    assert b'value="Transport" selected' in response.data
    assert b'href="/profile"' in response.data


def test_validation_errors_and_retention(client):
    """
    5. Validation errors:
       Verify that submitting invalid inputs flashes validation error messages
       and retains the invalid inputs in the HTML.
    """
    # Create user and log in
    database.db.create_user("Alice", "alice@example.com", "passalice")
    client.post("/login", data={"email": "alice@example.com", "password": "passalice"})

    # Insert expense
    conn = database.db.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (1, 45.99, "Transport", "2026-06-21", "Train ticket"),
    )
    conn.commit()
    expense_id = conn.execute("SELECT id FROM expenses").fetchone()["id"]
    conn.close()

    # Case A: Negative amount
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={
            "amount": "-10.00",
            "category": "Transport",
            "date": "2026-06-21",
            "description": "Train ticket",
        },
    )
    assert response.status_code == 200
    assert b"Amount must be a positive number." in response.data
    assert b'value="-10.00"' in response.data

    # Case B: Invalid category
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={
            "amount": "45.99",
            "category": "InvalidCat",
            "date": "2026-06-21",
            "description": "Train ticket",
        },
    )
    assert response.status_code == 200
    assert b"Invalid category selected." in response.data

    # Case C: Invalid date format
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={
            "amount": "45.99",
            "category": "Transport",
            "date": "2026/06/21",
            "description": "Train ticket",
        },
    )
    assert response.status_code == 200
    assert b"Invalid date format. Use YYYY-MM-DD." in response.data
    assert b'value="2026/06/21"' in response.data


def test_success_path_and_stats_update(client):
    """
    6. Success path:
       Verify that submitting valid changes updates the database, redirects to /profile,
       shows a success message, and correctly updates dashboard statistics.
    """
    # Create user and log in
    database.db.create_user("Alice", "alice@example.com", "passalice")
    client.post("/login", data={"email": "alice@example.com", "password": "passalice"})

    # Insert expense
    conn = database.db.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (1, 100.00, "Bills", "2026-06-01", "Initial electricity bill"),
    )
    conn.commit()
    expense_id = conn.execute("SELECT id FROM expenses").fetchone()["id"]
    conn.close()

    # Check initial profile rendering has ₹100.00
    profile_initial = client.get("/profile")
    assert b"100.00" in profile_initial.data
    assert b"Initial electricity bill" in profile_initial.data

    # Edit the expense
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={
            "amount": "150.50",
            "category": "Bills",
            "date": "2026-06-01",
            "description": "Updated electricity bill",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Expense updated successfully!" in response.data
    assert b"Updated electricity bill" in response.data
    assert b"150.50" in response.data
    assert b"100.00" not in response.data  # Old amount should be gone

    # Verify database updates
    updated = get_expense_by_id(expense_id)
    assert updated is not None
    assert updated["amount"] == 150.50
    assert updated["description"] == "Updated electricity bill"
