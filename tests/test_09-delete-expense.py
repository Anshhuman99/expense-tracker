import pytest
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
       Verify that accessing the delete page or trying to POST delete
       redirects unauthenticated users to the /login page.
    """
    # Test GET redirect
    response_get = client.get("/expenses/1/delete")
    assert response_get.status_code == 302
    assert "/login" in response_get.location

    # Test GET redirect followed to login page
    response_get_followed = client.get("/expenses/1/delete", follow_redirects=True)
    assert response_get_followed.status_code == 200
    assert b"Please log in to access this page." in response_get_followed.data

    # Test POST redirect
    response_post = client.post("/expenses/1/delete")
    assert response_post.status_code == 302
    assert "/login" in response_post.location


def test_owner_authorization(client):
    """
    2. Owner authorization check:
       Verify that a logged-in user cannot delete an expense belonging to another user.
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

    # Bob tries to access Alice's expense delete confirmation page
    response_get = client.get(f"/expenses/{expense_id}/delete")
    assert response_get.status_code == 403

    # Bob tries to POST delete Alice's expense
    response_post = client.post(f"/expenses/{expense_id}/delete")
    assert response_post.status_code == 403


def test_nonexistent_expense(client):
    """
    3. Nonexistent expense check:
       Verify that attempting to delete a non-existent expense ID returns a 404 Not Found.
    """
    # Create user and log in
    database.db.create_user("Alice", "alice@example.com", "passalice")
    client.post("/login", data={"email": "alice@example.com", "password": "passalice"})

    # GET nonexistent expense ID (e.g. 9999)
    response_get = client.get("/expenses/9999/delete")
    assert response_get.status_code == 404

    # POST nonexistent expense ID
    response_post = client.post("/expenses/9999/delete")
    assert response_post.status_code == 404


def test_normal_page_load(client):
    """
    4. Normal page load:
       Verify that GET /expenses/<id>/delete when logged in loads the delete confirmation form
       with the details of the expense and a cancel button pointing to /profile.
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

    # Request the delete page
    response = client.get(f"/expenses/{expense_id}/delete")
    assert response.status_code == 200
    assert b"Delete Expense" in response.data
    assert b"Are you sure you want to delete this expense?" in response.data
    assert b"45.99" in response.data
    assert b"2026-06-21" in response.data
    assert b"Train ticket" in response.data
    assert b"Transport" in response.data
    assert b'href="/profile"' in response.data


def test_success_path_and_stats_update(client):
    """
    5. Success path:
       Verify that submitting the deletion form deletes the expense from the database,
       redirects to /profile, shows a success message, and correctly updates dashboard statistics.
    """
    # Create user and log in
    database.db.create_user("Alice", "alice@example.com", "passalice")
    client.post("/login", data={"email": "alice@example.com", "password": "passalice"})

    # Insert expense
    conn = database.db.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (1, 100.00, "Bills", "2026-06-01", "Electricity bill"),
    )
    conn.commit()
    expense_id = conn.execute("SELECT id FROM expenses").fetchone()["id"]
    conn.close()

    # Check initial profile rendering has ₹100.00
    profile_initial = client.get("/profile")
    assert b"100.00" in profile_initial.data
    assert b"Electricity bill" in profile_initial.data

    # POST delete the expense
    response = client.post(
        f"/expenses/{expense_id}/delete",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Expense deleted successfully!" in response.data
    assert b"Electricity bill" not in response.data  # Expense should be gone
    assert b"100.00" not in response.data  # Old amount should be gone

    # Verify database deletion
    deleted = get_expense_by_id(expense_id)
    assert deleted is None
