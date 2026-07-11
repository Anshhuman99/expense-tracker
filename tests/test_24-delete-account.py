"""
Tests for Step 24 — Delete Account
Covers: GET /account/delete, POST /account/delete
"""

import pytest
import sqlite3
import database.db
from werkzeug.security import check_password_hash, generate_password_hash

# ------------------------------------------------------------------ #
# Fixtures                                                             #
# ------------------------------------------------------------------ #


@pytest.fixture
def client(monkeypatch, tmp_path):
    """
    Isolated Flask test client with a clean in-memory-style SQLite DB.
    Monkeypatches DB_PATH so spendly.db is never touched.
    """
    db_path = str(tmp_path / "test_delete_account.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)

    from app import app as flask_app

    flask_app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret",
        }
    )

    database.db.init_db(db_path)

    with flask_app.test_client() as test_client:
        yield test_client


# ------------------------------------------------------------------ #
# Helpers                                                              #
# ------------------------------------------------------------------ #


def _create_user(name="Alice", email="alice@example.com", password="Password1!"):
    database.db.create_user(name, email, password)


def _login(client, email="alice@example.com", password="Password1!"):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=False,
    )


def _create_and_login(
    client, name="Alice", email="alice@example.com", password="Password1!"
):
    _create_user(name, email, password)
    _login(client, email, password)


def _get_db_user(email):
    conn = database.db.get_db(database.db.DB_PATH)
    try:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()


def _get_db_user_count():
    conn = database.db.get_db(database.db.DB_PATH)
    try:
        return conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    finally:
        conn.close()


def _get_db_expense_count(user_id):
    conn = database.db.get_db(database.db.DB_PATH)
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
    finally:
        conn.close()


def _get_db_budget_count(user_id):
    conn = database.db.get_db(database.db.DB_PATH)
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM budgets WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
    finally:
        conn.close()


# ------------------------------------------------------------------ #
# Auth guard tests                                                     #
# ------------------------------------------------------------------ #


class TestAuthGuards:
    def test_get_delete_account_redirects_unauthenticated(self, client):
        """GET /account/delete redirects to /login when not logged in."""
        response = client.get("/account/delete", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_post_delete_account_redirects_unauthenticated(self, client):
        """POST /account/delete redirects to /login when not logged in."""
        response = client.post(
            "/account/delete",
            data={"password": "Password1!"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


# ------------------------------------------------------------------ #
# GET /account/delete                                                  #
# ------------------------------------------------------------------ #


class TestGetDeleteAccount:
    def test_delete_confirmation_page_loads(self, client):
        """GET /account/delete returns 200 for authenticated users."""
        _create_and_login(client)
        response = client.get("/account/delete")
        assert response.status_code == 200
        html = response.data.decode()
        assert "Permanently Delete Account" in html
        assert "Verify Password to Confirm" in html


# ------------------------------------------------------------------ #
# POST /account/delete                                                 #
# ------------------------------------------------------------------ #


class TestPostDeleteAccount:
    def test_delete_account_incorrect_password(self, client):
        """POST /account/delete with incorrect password fails and does not delete user."""
        _create_and_login(client, email="alice@example.com", password="Password1!")
        response = client.post(
            "/account/delete",
            data={"password": "WrongPassword!"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert (
            b"Incorrect password" in response.data or b"error" in response.data.lower()
        )

        # Verify user still exists in DB
        user = _get_db_user("alice@example.com")
        assert user is not None
        assert _get_db_user_count() > 0

    def test_delete_account_success(self, client):
        """POST /account/delete with correct password succeeds, deletes user, clears session."""
        _create_and_login(client, email="alice@example.com", password="Password1!")

        user = _get_db_user("alice@example.com")
        user_id = user["id"]

        # Insert dummy expenses and budgets to verify cascades
        conn = database.db.get_db(database.db.DB_PATH)
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (user_id, 10.0, "Food", "2026-07-11", "Test expense"),
        )
        # Check if budgets table has a budget schema
        conn.execute(
            "INSERT INTO budgets (user_id, category, amount, month) VALUES (?, ?, ?, ?)",
            (user_id, "Food", 100.0, "2026-07"),
        )
        conn.commit()
        conn.close()

        assert _get_db_expense_count(user_id) == 1
        assert _get_db_budget_count(user_id) == 1

        response = client.post(
            "/account/delete",
            data={"password": "Password1!"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert (
            b"permanently deleted" in response.data
            or b"deleted" in response.data.lower()
        )

        # User must be deleted from DB
        assert _get_db_user("alice@example.com") is None

        # Associated records must be deleted
        assert _get_db_expense_count(user_id) == 0
        assert _get_db_budget_count(user_id) == 0

        # Session should be cleared (meaning GET /settings will redirect to /login)
        settings_response = client.get("/settings", follow_redirects=False)
        assert settings_response.status_code == 302
        assert "/login" in settings_response.headers["Location"]
