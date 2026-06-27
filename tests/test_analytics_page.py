import pytest
import database.db
from flask import session

@pytest.fixture
def client(monkeypatch, tmp_path):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)
    
    from app import app as flask_app
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False
    })
    
    database.db.init_db(db_path)
    
    with flask_app.test_client() as client:
        yield client

def test_analytics_guest_redirect(client):
    response = client.get("/analytics", follow_redirects=True)
    assert response.status_code == 200
    assert b"Please log in to access this page." in response.data
    # Verify redirected to sign in / login page
    assert b"Sign in to Spendly" in response.data or b"password" in response.data

def test_analytics_loads_for_logged_in_user(client):
    # Create and log in a user
    database.db.create_user("Analytics User", "analytics@example.com", "password123")
    
    client.post("/login", data={
        "email": "analytics@example.com",
        "password": "password123"
    })
    
    response = client.get("/analytics")
    assert response.status_code == 200
    assert b"Analytics: Deep Dive into Your" in response.data
    assert b"Interactive Dashboards" in response.data
    assert b"Trend Analysis" in response.data
    assert b"Automated Insights" in response.data

def test_navbar_active_states(client):
    # Create and log in a user
    database.db.create_user("Active States User", "active@example.com", "password123")
    
    client.post("/login", data={
        "email": "active@example.com",
        "password": "password123"
    })
    
    # Check Profile page active state
    profile_response = client.get("/profile")
    assert profile_response.status_code == 200
    assert b'class="active">Profile</a>' in profile_response.data
    assert b'class="">Analytics</a>' in profile_response.data or b'class="active">Analytics</a>' not in profile_response.data
    
    # Check Analytics page active state
    analytics_response = client.get("/analytics")
    assert analytics_response.status_code == 200
    assert b'class="active">Analytics</a>' in analytics_response.data
    assert b'class="">Profile</a>' in analytics_response.data or b'class="active">Profile</a>' not in analytics_response.data
