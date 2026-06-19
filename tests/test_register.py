import pytest
import sqlite3
import database.db

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

def test_register_page_loads(client):
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Create your account" in response.data
    assert b"action=\"/register\"" not in response.data  # Ensure url_for is used
    assert b"action=\"/login\"" not in response.data

def test_register_success(client):
    # Register a new user
    response = client.post("/register", data={
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Should redirect to login page and display success flash message
    assert b"Account created! Please log in." in response.data
    assert b"Welcome back" in response.data  # verify login page loads

    # Check database to ensure user was created
    conn = database.db.get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", ("test@example.com",)).fetchone()
    conn.close()
    
    assert user is not None
    assert user["name"] == "Test User"
    assert user["password_hash"] != "password123"  # password must be hashed

def test_register_duplicate_email(client):
    # Register first user
    client.post("/register", data={
        "name": "First User",
        "email": "duplicate@example.com",
        "password": "password123",
        "confirm_password": "password123"
    })
    
    # Attempt to register second user with same email
    response = client.post("/register", data={
        "name": "Second User",
        "email": "duplicate@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Email already registered." in response.data

def test_register_empty_name(client):
    # Empty name check
    response = client.post("/register", data={
        "name": "   ",
        "email": "valid@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Name is required." in response.data

def test_register_missing_fields(client):
    # Missing name
    response = client.post("/register", data={
        "email": "valid@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)
    assert b"Name is required." in response.data

    # Missing email
    response = client.post("/register", data={
        "name": "Valid Name",
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)
    assert b"Invalid email address." in response.data

def test_register_invalid_email(client):
    invalid_emails = [
        "plainaddress",
        "#@%^%#$@#$@#.com",
        "@example.com",
        "Joe Smith <email@example.com>",
        "email.example.com",
        "email@example@example.com",
        "email@example",
    ]
    
    for email in invalid_emails:
        response = client.post("/register", data={
            "name": "Valid Name",
            "email": email,
            "password": "password123",
            "confirm_password": "password123"
        }, follow_redirects=True)
        assert b"Invalid email address." in response.data

def test_register_short_password(client):
    response = client.post("/register", data={
        "name": "Valid Name",
        "email": "valid@example.com",
        "password": "short",
        "confirm_password": "short"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Password must be at least 8 characters long." in response.data

def test_register_mismatched_passwords(client):
    response = client.post("/register", data={
        "name": "Valid Name",
        "email": "valid@example.com",
        "password": "password123",
        "confirm_password": "differentpassword"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Passwords do not match." in response.data
