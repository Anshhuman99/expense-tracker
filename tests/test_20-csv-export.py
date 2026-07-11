import pytest
import csv
import io
import re
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


def test_export_csv_auth_guard(client):
    """
    Test that unauthenticated requests to export CSV redirect to login.
    """
    response = client.get("/expenses/export/csv")
    assert response.status_code == 302
    assert "login" in response.headers["Location"]


def test_export_csv_metadata_and_headers(client):
    """
    Test that exporting CSV returns correct mimetype, headers, and filename.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    response = client.get("/expenses/export/csv")
    assert response.status_code == 200
    assert response.mimetype == "text/csv"

    disposition = response.headers.get("Content-Disposition", "")
    assert "attachment" in disposition
    assert "filename=spendly_expenses_" in disposition
    assert disposition.endswith(".csv")


def test_export_csv_content(client):
    """
    Test that the CSV content contains correct headers and transaction rows.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    response = client.get("/expenses/export/csv")
    assert response.status_code == 200

    csv_file = io.StringIO(response.data.decode("utf-8"))
    reader = csv.reader(csv_file)
    rows = list(reader)

    # Verify header row
    assert rows[0] == ["Date", "Category", "Description", "Amount"]

    # Verify that we have some data rows (default seed_db inserts 8 expenses for demo user)
    assert len(rows) == 9  # 1 header + 8 data rows

    # Verify formatting of amounts
    for row in rows[1:]:
        amount_str = row[3]
        assert re.match(r"^\d+\.\d{2}$", amount_str)


def test_export_csv_with_filtering(client):
    """
    Test that active filters are respected in the CSV output.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    # Filter by category Food (original seed has exactly 2 Food expenses)
    response = client.get("/expenses/export/csv?category=Food")
    assert response.status_code == 200

    csv_file = io.StringIO(response.data.decode("utf-8"))
    reader = csv.reader(csv_file)
    rows = list(reader)

    assert rows[0] == ["Date", "Category", "Description", "Amount"]
    assert len(rows) == 3  # 1 header + 2 Food expenses
    for row in rows[1:]:
        assert row[1] == "Food"


def test_export_csv_empty_results(client):
    """
    Test that export returns a valid CSV with just headers when there are no matches.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    # Filter for non-existent category
    response = client.get("/expenses/export/csv?category=Bills&start_date=2099-01-01")
    assert response.status_code == 200

    csv_file = io.StringIO(response.data.decode("utf-8"))
    reader = csv.reader(csv_file)
    rows = list(reader)

    assert len(rows) == 1
    assert rows[0] == ["Date", "Category", "Description", "Amount"]


def test_export_csv_injection_protection(client):
    """
    Test that CSV Export sanitizes values that could trigger Formula Injection.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    # Seed an expense with a formula-triggering description
    conn = database.db.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (1, 15.0, "Food", "2026-06-20", "=1+1 cmd"),
    )
    conn.commit()
    conn.close()

    response = client.get("/expenses/export/csv")
    assert response.status_code == 200

    csv_file = io.StringIO(response.data.decode("utf-8"))
    reader = csv.reader(csv_file)
    rows = list(reader)

    found = False
    for row in rows[1:]:
        if "=1+1 cmd" in row[2] or "'=1+1 cmd" in row[2]:
            assert row[2] == "'=1+1 cmd"
            found = True
            break
    assert found
