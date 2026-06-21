import pytest
import database.db
from flask import session

@pytest.fixture
def client(monkeypatch, tmp_path):
    # Set DB_PATH to a temporary location before importing app.py
    # to isolate tests from the production database.
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)
    
    # Import app now so that its module-level init_db/seed_db calls
    # run against the temporary test database.
    from app import app as flask_app
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False
    })
    
    # Force database initialization for each test run in case app is cached in sys.modules
    database.db.init_db(db_path)
    database.db.seed_db(db_path)
    
    with flask_app.test_client() as client:
        yield client

def test_login_page_loads(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Welcome back" in response.data
    assert b"action=\"/login\"" not in response.data  # Ensure url_for is used

def test_login_success(client):
    # Log in with the seeded demo user (demo@spendly.com / demo123)
    response = client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Logged in successfully." in response.data
    assert b"Welcome back" in response.data  # redirected to profile dashboard page
    
    # Verify session variables are set
    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None
        assert sess.get("user_name") == "Demo User"

def test_login_invalid_email(client):
    response = client.post("/login", data={
        "email": "nonexistent@spendly.com",
        "password": "password123"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data
    
    # Verify session is empty
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None

def test_login_wrong_password(client):
    response = client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "wrongpassword"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data
    
    # Verify session is empty
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None

def test_logout_clears_session(client):
    # Log in first
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    })
    
    # Log out
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Logged out successfully." in response.data
    assert b"Track every rupee" in response.data  # landing page loads
    
    # Verify session is cleared
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None

def test_profile_requires_login(client):
    # Get profile without logging in
    response = client.get("/profile", follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to login page and display error
    assert b"Please log in to access this page." in response.data
    assert b"Welcome back" in response.data

def test_profile_loads_when_logged_in(client):
    # Log in first
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    })
    
    # Get profile
    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Welcome back" in response.data


def test_login_redirect_if_logged_in(client):
    # Log in
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    })
    
    # Visit login page again
    response = client.get("/login", follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to profile/dashboard
    assert b"Welcome back" in response.data


def test_register_redirect_if_logged_in(client):
    # Log in
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    })
    
    # Visit register page
    response = client.get("/register", follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to profile/dashboard
    assert b"Welcome back" in response.data

