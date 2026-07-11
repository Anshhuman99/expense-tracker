import pytest
import re
import database.db
from database.queries import get_filtered_expenses, get_filtered_expenses_count


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


def parse_expenses_from_html(html_data):
    """
    Helper to extract descriptions and amounts from the HTML response.
    """
    text = html_data.decode("utf-8")
    pattern = r'<td data-label="Description">(.*?)</td>\s*<td data-label="Amount" class="amount">₹(.*?)</td>'
    matches = re.findall(pattern, text)
    return [
        {"description": m[0].strip(), "amount": float(m[1].replace(",", "").strip())}
        for m in matches
    ]


def test_pagination_default_page(client):
    """
    Test that the default profile view shows at most 10 expenses.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    # Check default dashboard
    response = client.get("/profile")
    assert response.status_code == 200

    # By default seed_db creates 8 expenses.
    # Let's seed 15 additional expenses to make a total of 23 expenses.
    conn = database.db.get_db()
    for i in range(15):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (1, 10.0, "Food", f"2026-06-{i+1:02d}", f"Extra expense {i+1}"),
        )
    conn.commit()
    conn.close()

    # Request default page 1
    response = client.get("/profile")
    assert response.status_code == 200
    expenses = parse_expenses_from_html(response.data)
    assert len(expenses) == 10
    assert b"Showing 1\xe2\x80\x9310 of 23 expenses" in response.data


def test_pagination_next_page(client):
    """
    Test navigating to page 2 and page 3.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    # Seed 15 additional expenses so total is 23 (seeded) + 8 (original) = 23.
    conn = database.db.get_db()
    for i in range(15):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (1, 10.0, "Food", f"2026-06-{i+1:02d}", f"Extra expense {i+1}"),
        )
    conn.commit()
    conn.close()

    # Page 2
    response = client.get("/profile?page=2")
    assert response.status_code == 200
    expenses = parse_expenses_from_html(response.data)
    assert len(expenses) == 10
    assert b"Showing 11\xe2\x80\x9320 of 23 expenses" in response.data

    # Page 3
    response = client.get("/profile?page=3")
    assert response.status_code == 200
    expenses = parse_expenses_from_html(response.data)
    assert len(expenses) == 3
    assert b"Showing 21\xe2\x80\x9323 of 23 expenses" in response.data


def test_pagination_out_of_bounds(client):
    """
    Test out of bounds page numbers fallback gracefully.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    # Seed 5 expenses, total 13
    conn = database.db.get_db()
    for i in range(5):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (1, 10.0, "Food", f"2026-06-{i+1:02d}", f"Extra expense {i+1}"),
        )
    conn.commit()
    conn.close()

    # Page 0 should fallback to 1
    response = client.get("/profile?page=0")
    assert response.status_code == 200
    assert b"Showing 1\xe2\x80\x9310 of 13 expenses" in response.data

    # Page 9999 should cap to last page (page 2)
    response = client.get("/profile?page=9999")
    assert response.status_code == 200
    assert b"Showing 11\xe2\x80\x9313 of 13 expenses" in response.data

    # Invalid page parameter should fallback to 1
    response = client.get("/profile?page=invalid")
    assert response.status_code == 200
    assert b"Showing 1\xe2\x80\x9310 of 13 expenses" in response.data


def test_pagination_preserves_filters(client):
    """
    Test that filters are maintained when clicking pagination links.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    # Seed 15 extra Food expenses
    conn = database.db.get_db()
    for i in range(15):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (1, 10.0, "Food", f"2026-06-{i+1:02d}", f"Extra Food {i+1}"),
        )
    # Seed 5 extra Bills expenses (won't match Food category filter)
    for i in range(5):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (1, 20.0, "Bills", f"2026-06-{i+1:02d}", f"Extra Bills {i+1}"),
        )
    conn.commit()
    conn.close()

    # Filter by category Food (original 2 Food + 15 extra = 17)
    response = client.get("/profile?category=Food&page=2")
    assert response.status_code == 200

    # Verify page contains correct elements and pagination links preserve filter parameters
    assert b"Showing 11\xe2\x80\x9317 of 17 expenses" in response.data
    # Link for page 1 should contain category=Food
    assert b"category=Food" in response.data
    assert b"page=1" in response.data
