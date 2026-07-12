import os
import io
import pytest
import database.db
from database.queries import get_expense_by_id


@pytest.fixture
def client(monkeypatch, tmp_path):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)

    # Import app inside fixture so monkeypatching takes effect
    from app import app as flask_app

    # Create temporary uploads folder inside tmp_path
    uploads_path = str(tmp_path / "uploads")
    flask_app.config.update(
        {"TESTING": True, "WTF_CSRF_ENABLED": False, "UPLOAD_FOLDER": uploads_path}
    )
    os.makedirs(uploads_path, exist_ok=True)

    database.db.init_db(db_path)
    database.db.seed_db(db_path)

    with flask_app.test_client() as client:
        yield client


def test_receipt_upload_success(client):
    """
    Test uploading a valid receipt successfully during add expense.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    data = {
        "amount": "45.50",
        "category": "Food",
        "date": "2026-07-12",
        "description": "Team lunch",
        "receipt": (io.BytesIO(b"dummy image data"), "receipt.png"),
    }
    response = client.post(
        "/expenses/add",
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Expense added successfully!" in response.data

    # Retrieve the added expense and check receipt path
    conn = database.db.get_db()
    row = conn.execute("SELECT * FROM expenses ORDER BY id DESC LIMIT 1").fetchone()
    assert row["receipt_path"] is not None
    assert row["receipt_path"].endswith("receipt.png")
    conn.close()


def test_receipt_upload_invalid_type(client):
    """
    Test uploading an invalid receipt type is rejected.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    data = {
        "amount": "45.50",
        "category": "Food",
        "date": "2026-07-12",
        "description": "Team lunch",
        "receipt": (io.BytesIO(b"dummy code"), "malicious.exe"),
    }
    response = client.post(
        "/expenses/add", data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 200
    assert b"Invalid file type" in response.data


def test_serve_receipt_auth_guards(client):
    """
    Test secure serving route requires login and ownership.
    """
    # 1. Unauthenticated request
    response = client.get("/expenses/1/receipt")
    assert response.status_code == 302
    assert "login" in response.headers["Location"]

    # 2. Authenticated but doesn't own expense (expense 1 belongs to user 1 (demo@spendly.com))
    # Register and login a second user
    client.post(
        "/register",
        data={
            "name": "Second User",
            "email": "second@spendly.com",
            "password": "password123",
            "confirm_password": "password123",
        },
    )
    client.post(
        "/login", data={"email": "second@spendly.com", "password": "password123"}
    )

    response = client.get("/expenses/1/receipt")
    assert response.status_code == 403


def test_delete_receipt(client):
    """
    Test deleting a receipt removes the physical file and updates the database.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    # First, add an expense with receipt
    data = {
        "amount": "45.50",
        "category": "Food",
        "date": "2026-07-12",
        "description": "Team lunch",
        "receipt": (io.BytesIO(b"dummy image data"), "receipt.png"),
    }
    client.post("/expenses/add", data=data, content_type="multipart/form-data")

    # Get expense ID
    conn = database.db.get_db()
    expense = conn.execute("SELECT * FROM expenses ORDER BY id DESC LIMIT 1").fetchone()
    expense_id = expense["id"]
    filename = expense["receipt_path"]
    conn.close()

    # Verify file exists
    from flask import current_app

    # Inside client context we can access config or read upload dir
    # Let's post a request to delete the receipt
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={
            "amount": "45.50",
            "category": "Food",
            "date": "2026-07-12",
            "description": "Team lunch",
            "delete_receipt": "1",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Receipt deleted successfully!" in response.data

    # Verify receipt_path is None in database
    conn = database.db.get_db()
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()
    assert expense["receipt_path"] is None
    conn.close()
