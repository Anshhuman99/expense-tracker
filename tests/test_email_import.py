import pytest
import database.db
from flask import session


@pytest.fixture
def client(monkeypatch, tmp_path):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)

    from app import app as flask_app

    flask_app.config.update({"TESTING": True, "WTF_CSRF_ENABLED": False})

    database.db.init_db(db_path)

    with flask_app.test_client() as client:
        yield client


def test_email_import_guest_redirect(client):
    response = client.get("/email-import", follow_redirects=True)
    assert response.status_code == 200
    assert b"Please log in to access this page." in response.data


def test_email_import_loads_for_logged_in_user(client):
    # Create and log in a user
    database.db.create_user("Import User", "import@example.com", "password123")

    client.post(
        "/login", data={"email": "import@example.com", "password": "password123"}
    )

    response = client.get("/email-import")
    assert response.status_code == 200
    assert b"Email Import Sync" in response.data
    assert b"import@example.com" in response.data
    assert b"Delta Airlines" in response.data
