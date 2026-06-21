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
    # We do NOT seed by default in the fixture so we can test empty states,
    # but we can seed explicitly in individual tests.
    
    with flask_app.test_client() as client:
        yield client

def test_profile_guest_redirect(client):
    response = client.get("/profile", follow_redirects=True)
    assert response.status_code == 200
    assert b"Please log in to access this page." in response.data
    assert b"Welcome back" in response.data

def test_profile_loads_empty(client):
    # Create a user in the isolated DB but don't add any expenses
    database.db.create_user("New User", "new@example.com", "password123")
    
    # Log in
    client.post("/login", data={
        "email": "new@example.com",
        "password": "password123"
    })
    
    # Load profile
    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Welcome back, New User" in response.data
    assert b"new@example.com" in response.data
    assert b"Total Spent" in response.data
    assert "₹0.00".encode('utf-8') in response.data
    assert b"No expenses logged yet." in response.data
    assert b"No category data available yet." in response.data

def test_profile_loads_seeded_data(client):
    # Seed the database explicitly for this test
    database.db.seed_db()
    
    # Log in as the seeded demo user (demo@spendly.com / demo123)
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    })
    
    # Load profile
    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Welcome back, Demo User" in response.data
    assert b"demo@spendly.com" in response.data
    
    # Seeded data has 8 transactions.
    # Total spent: 12.50 + 45.00 + 120.00 + 30.00 + 60.00 + 85.00 + 20.00 + 18.75 = 391.25
    assert b"391.25" in response.data
    assert b"8" in response.data  # transaction count
    
    # Seeded categories include Food, Transport, Bills, Health, Entertainment, Shopping, Other
    assert b"Food" in response.data
    assert b"Transport" in response.data
    assert b"Bills" in response.data
    
    # Verify recent transaction list shows dinner and netflix (in top 5), etc.
    assert b"Dinner" in response.data
    assert b"Netflix" in response.data
