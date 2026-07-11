import pytest
import io
import database.db


@pytest.fixture
def client(monkeypatch, tmp_path):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)

    # Import app inside fixture so monkeypatching takes effect
    from app import app as flask_app

    flask_app.config.update({"TESTING": True, "WTF_CSRF_ENABLED": False})

    database.db.init_db(db_path)
    database.db.seed_db(db_path)

    with flask_app.test_client() as client:
        yield client


def test_export_pdf_auth_guard(client):
    """
    Test that unauthenticated requests to export PDF redirect to login.
    """
    response = client.get("/expenses/export/pdf")
    assert response.status_code == 302
    assert "login" in response.headers["Location"]


def test_export_pdf_metadata_and_headers(client):
    """
    Test that exporting PDF returns correct mimetype, headers, and filename.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    response = client.get("/expenses/export/pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"

    disposition = response.headers.get("Content-Disposition", "")
    assert "attachment" in disposition
    assert 'filename="spendly_report_' in disposition
    assert disposition.endswith('.pdf"')


def test_export_pdf_header_signature(client):
    """
    Test that the returned data is a valid PDF starting with %PDF- header.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    response = client.get("/expenses/export/pdf")
    assert response.status_code == 200

    # PDF files start with %PDF-
    assert response.data.startswith(b"%PDF-")


def test_export_pdf_with_filtering(client):
    """
    Test that active filters successfully return a valid PDF response.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.get("/expenses/export/pdf?category=Food")
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF-")


def test_export_pdf_empty_results(client):
    """
    Test that exporting PDF with filters matching no results returns a valid PDF page.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    response = client.get("/expenses/export/pdf?category=Bills&start_date=2099-01-01")
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF-")


def test_export_pdf_escaping(client):
    """
    Test that PDF generation correctly escapes HTML/XML characters (like <, >, &)
    to prevent ReportLab SAX parsing crashes.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    # Insert an expense with HTML characters in description
    conn = database.db.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (1, 45.50, "Shopping", "2026-06-25", "Books & <stuff>"),
    )
    conn.commit()
    conn.close()

    # If not properly escaped, this will crash with a ReportLab XML parsing exception (HTTP 500)
    response = client.get("/expenses/export/pdf?search_query=stuff")
    assert response.status_code == 200
    assert response.data.startswith(b"%PDF-")
