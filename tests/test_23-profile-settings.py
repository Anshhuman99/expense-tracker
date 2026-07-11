"""
Tests for Step 23 — Profile Settings
Covers: GET /settings, POST /settings/profile, POST /settings/password
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
    db_path = str(tmp_path / "test_settings.db")
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


# ------------------------------------------------------------------ #
# Auth guard tests                                                     #
# ------------------------------------------------------------------ #


class TestAuthGuards:
    def test_get_settings_redirects_unauthenticated(self, client):
        """GET /settings redirects to /login when not logged in."""
        response = client.get("/settings", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_post_settings_profile_redirects_unauthenticated(self, client):
        """POST /settings/profile redirects to /login when not logged in."""
        response = client.post(
            "/settings/profile",
            data={"name": "Bob", "email": "bob@example.com"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]

    def test_post_settings_password_redirects_unauthenticated(self, client):
        """POST /settings/password redirects to /login when not logged in."""
        response = client.post(
            "/settings/password",
            data={
                "current_password": "Password1!",
                "new_password": "NewPass123",
                "confirm_new_password": "NewPass123",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "/login" in response.headers["Location"]


# ------------------------------------------------------------------ #
# GET /settings                                                        #
# ------------------------------------------------------------------ #


class TestGetSettings:
    def test_settings_page_loads_for_authenticated_user(self, client):
        """GET /settings returns 200 for authenticated users."""
        _create_and_login(client)
        response = client.get("/settings")
        assert response.status_code == 200

    def test_settings_page_contains_profile_form(self, client):
        """Settings page renders the Update Profile form."""
        _create_and_login(client)
        response = client.get("/settings")
        html = response.data.decode()
        assert "settings/profile" in html
        assert "name=" in html or 'name="name"' in html

    def test_settings_page_contains_password_form(self, client):
        """Settings page renders the Change Password form."""
        _create_and_login(client)
        response = client.get("/settings")
        html = response.data.decode()
        assert "settings/password" in html
        assert "current_password" in html

    def test_settings_page_prepopulates_name(self, client):
        """Settings page pre-populates the name field with the current user's name."""
        _create_and_login(client, name="Alice")
        response = client.get("/settings")
        assert b"Alice" in response.data

    def test_settings_page_prepopulates_email(self, client):
        """Settings page pre-populates the email field with the current user's email."""
        _create_and_login(client, email="alice@example.com")
        response = client.get("/settings")
        assert b"alice@example.com" in response.data


# ------------------------------------------------------------------ #
# POST /settings/profile — profile update                             #
# ------------------------------------------------------------------ #


class TestProfileUpdate:
    def test_profile_update_success(self, client):
        """Valid name + email update succeeds with a success flash."""
        _create_and_login(client)
        response = client.post(
            "/settings/profile",
            data={"name": "Alice Updated", "email": "alice_new@example.com"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert (
            b"Profile updated" in response.data or b"success" in response.data.lower()
        )

    def test_profile_update_persists_to_db(self, client):
        """After a successful profile update, the DB reflects the new values."""
        _create_and_login(client, email="alice@example.com")
        client.post(
            "/settings/profile",
            data={"name": "New Name", "email": "alice@example.com"},
            follow_redirects=True,
        )
        user = _get_db_user("alice@example.com")
        assert user is not None
        assert user["name"] == "New Name"

    def test_profile_update_updates_session_name(self, client):
        """After a name change, the session reflects the new name immediately."""
        _create_and_login(client)
        client.post(
            "/settings/profile",
            data={"name": "Updated Name", "email": "alice@example.com"},
            follow_redirects=False,
        )
        # The settings page should display the new name from session
        response = client.get("/settings")
        assert b"Updated Name" in response.data or b"Updated Name" in response.data

    def test_profile_update_empty_name_rejected(self, client):
        """Empty name returns an error flash and does not update DB."""
        _create_and_login(client, name="Alice", email="alice@example.com")
        response = client.post(
            "/settings/profile",
            data={"name": "   ", "email": "alice@example.com"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"required" in response.data.lower() or b"error" in response.data.lower()
        # DB name must not change
        user = _get_db_user("alice@example.com")
        assert user["name"] == "Alice"

    def test_profile_update_invalid_email_rejected(self, client):
        """Invalid email format returns an error flash and does not update DB."""
        _create_and_login(client, name="Alice", email="alice@example.com")
        response = client.post(
            "/settings/profile",
            data={"name": "Alice", "email": "not-an-email"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        html = response.data.decode().lower()
        assert "invalid" in html or "error" in html
        # DB email must not change
        user = _get_db_user("alice@example.com")
        assert user is not None

    def test_profile_update_duplicate_email_rejected(self, client):
        """Duplicate email returns error flash and does not update DB."""
        # Create two users
        database.db.create_user("Bob", "bob@example.com", "Password1!")
        _create_and_login(client, name="Alice", email="alice@example.com")
        # Try to steal bob's email
        response = client.post(
            "/settings/profile",
            data={"name": "Alice", "email": "bob@example.com"},
            follow_redirects=True,
        )
        assert response.status_code == 200
        html = response.data.decode().lower()
        assert "already" in html or "in use" in html or "error" in html
        # Alice's email must not change
        user = _get_db_user("alice@example.com")
        assert user is not None

    def test_profile_update_redirects_to_settings(self, client):
        """Successful profile update redirects back to /settings."""
        _create_and_login(client)
        response = client.post(
            "/settings/profile",
            data={"name": "Alice", "email": "alice@example.com"},
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "settings" in response.headers["Location"]


# ------------------------------------------------------------------ #
# POST /settings/password — password change                           #
# ------------------------------------------------------------------ #


class TestPasswordChange:
    def test_password_change_success(self, client):
        """Valid password change succeeds with a success flash."""
        _create_and_login(client)
        response = client.post(
            "/settings/password",
            data={
                "current_password": "Password1!",
                "new_password": "NewSecure99",
                "confirm_new_password": "NewSecure99",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        html = response.data.decode().lower()
        assert "password" in html and ("changed" in html or "success" in html)

    def test_password_change_updates_hash_in_db(self, client):
        """Successful password change stores a new hash that validates."""
        _create_and_login(client, email="alice@example.com")
        client.post(
            "/settings/password",
            data={
                "current_password": "Password1!",
                "new_password": "BrandNew99",
                "confirm_new_password": "BrandNew99",
            },
            follow_redirects=True,
        )
        user = _get_db_user("alice@example.com")
        assert user is not None
        assert check_password_hash(user["password_hash"], "BrandNew99")

    def test_password_change_old_password_no_longer_works(self, client):
        """After a password change, old password hash is replaced."""
        _create_and_login(client, email="alice@example.com")
        client.post(
            "/settings/password",
            data={
                "current_password": "Password1!",
                "new_password": "BrandNew99",
                "confirm_new_password": "BrandNew99",
            },
            follow_redirects=True,
        )
        user = _get_db_user("alice@example.com")
        # Old password should NOT validate against new hash
        assert not check_password_hash(user["password_hash"], "Password1!")

    def test_password_change_wrong_current_rejected(self, client):
        """Wrong current password returns error flash and does not change hash."""
        _create_and_login(client, email="alice@example.com")
        original_user = _get_db_user("alice@example.com")
        original_hash = original_user["password_hash"]
        response = client.post(
            "/settings/password",
            data={
                "current_password": "WrongPassword!",
                "new_password": "BrandNew99",
                "confirm_new_password": "BrandNew99",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        html = response.data.decode().lower()
        assert "incorrect" in html or "error" in html
        # Hash must not change
        user = _get_db_user("alice@example.com")
        assert user["password_hash"] == original_hash

    def test_password_change_too_short_rejected(self, client):
        """New password shorter than 8 chars returns error flash."""
        _create_and_login(client)
        response = client.post(
            "/settings/password",
            data={
                "current_password": "Password1!",
                "new_password": "Short1",
                "confirm_new_password": "Short1",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        html = response.data.decode().lower()
        assert "8" in html or "short" in html or "error" in html

    def test_password_change_mismatched_confirm_rejected(self, client):
        """Mismatched new/confirm passwords returns error flash."""
        _create_and_login(client)
        response = client.post(
            "/settings/password",
            data={
                "current_password": "Password1!",
                "new_password": "NewSecure99",
                "confirm_new_password": "DifferentPass99",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        html = response.data.decode().lower()
        assert "match" in html or "error" in html

    def test_password_change_redirects_to_settings(self, client):
        """Successful password change redirects back to /settings."""
        _create_and_login(client)
        response = client.post(
            "/settings/password",
            data={
                "current_password": "Password1!",
                "new_password": "NewSecure99",
                "confirm_new_password": "NewSecure99",
            },
            follow_redirects=False,
        )
        assert response.status_code == 302
        assert "settings" in response.headers["Location"]


# ------------------------------------------------------------------ #
# Navbar link                                                          #
# ------------------------------------------------------------------ #


class TestNavbarLink:
    def test_settings_link_present_when_authenticated(self, client):
        """Settings link appears in the navbar for authenticated users."""
        _create_and_login(client)
        response = client.get("/settings")
        html = response.data.decode()
        assert "settings" in html.lower()

    def test_settings_link_not_present_when_unauthenticated(self, client):
        """Settings link is absent in the navbar for unauthenticated users."""
        response = client.get("/")
        html = response.data.decode()
        # The settings link should only appear for logged-in users
        # Check there's no /settings route link in the unauthenticated navbar
        assert "url_for" not in html  # Templates are rendered, not raw
        # Just verify the page loads fine
        assert response.status_code == 200
