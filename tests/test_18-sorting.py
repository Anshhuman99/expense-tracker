import pytest
import re
import database.db
from database.queries import get_filtered_expenses, get_recent_transactions


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


def test_auth_guard_profile_sorting(client):
    """
    Test that accessing /profile with sorting parameters as an unauthenticated user
    redirects to /login and displays a flash message.
    """
    response = client.get("/profile?sort_by=amount&order=ASC", follow_redirects=True)
    assert response.status_code == 200
    assert b"Please log in to access this page." in response.data
    assert b"Login" in response.data or b"Email" in response.data


def parse_expenses_from_html(html_data):
    """
    Helper to extract dates, categories, and amounts from the HTML response to verify order.
    """
    text = html_data.decode("utf-8")

    # Find all rows in the table body.
    # Each row is:
    # <td data-label="Date">2026-06-17</td>
    # <td data-label="Category"><span class="category-badge food">Food</span></td>
    # <td data-label="Description">Dinner</td>
    # <td data-label="Amount" class="amount">₹18.75</td>

    pattern = r'<td data-label="Date">(.*?)</td>\s*<td data-label="Category"><span[^>]*>(.*?)</span></td>\s*<td data-label="Description">(.*?)</td>\s*<td data-label="Amount" class="amount">₹(.*?)</td>'
    matches = re.findall(pattern, text)

    parsed = []
    for match in matches:
        date = match[0].strip()
        category = match[1].strip()
        description = match[2].strip()
        # Clean amount string (remove commas)
        amount_str = match[3].replace(",", "").strip()
        amount = float(amount_str)
        parsed.append(
            {
                "date": date,
                "category": category,
                "description": description,
                "amount": amount,
            }
        )
    return parsed


def test_sorting_by_date_asc(client):
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    response = client.get("/profile?sort_by=date&order=ASC")
    assert response.status_code == 200

    # Verify retention of select inputs
    assert b"selected>Date</option>" in response.data
    assert b"selected>Ascending</option>" in response.data

    expenses = parse_expenses_from_html(response.data)
    assert len(expenses) == 8

    # Verify sorted order by date ascending
    dates = [e["date"] for e in expenses]
    assert dates == sorted(dates)


def test_sorting_by_date_desc(client):
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    response = client.get("/profile?sort_by=date&order=DESC")
    assert response.status_code == 200

    # Verify retention of select inputs
    assert b"selected>Date</option>" in response.data
    assert b"selected>Descending</option>" in response.data

    expenses = parse_expenses_from_html(response.data)
    assert len(expenses) == 8

    dates = [e["date"] for e in expenses]
    assert dates == sorted(dates, reverse=True)


def test_sorting_by_amount_asc(client):
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    response = client.get("/profile?sort_by=amount&order=ASC")
    assert response.status_code == 200

    assert b"selected>Amount</option>" in response.data
    assert b"selected>Ascending</option>" in response.data

    expenses = parse_expenses_from_html(response.data)
    assert len(expenses) == 8

    amounts = [e["amount"] for e in expenses]
    assert amounts == sorted(amounts)


def test_sorting_by_amount_desc(client):
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    response = client.get("/profile?sort_by=amount&order=DESC")
    assert response.status_code == 200

    assert b"selected>Amount</option>" in response.data
    assert b"selected>Descending</option>" in response.data

    expenses = parse_expenses_from_html(response.data)
    assert len(expenses) == 8

    amounts = [e["amount"] for e in expenses]
    assert amounts == sorted(amounts, reverse=True)


def test_sorting_by_category_asc(client):
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    response = client.get("/profile?sort_by=category&order=ASC")
    assert response.status_code == 200

    assert b"selected>Category</option>" in response.data
    assert b"selected>Ascending</option>" in response.data

    expenses = parse_expenses_from_html(response.data)
    assert len(expenses) == 8

    categories = [e["category"] for e in expenses]
    assert categories == sorted(categories)


def test_sorting_by_category_desc(client):
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    response = client.get("/profile?sort_by=category&order=DESC")
    assert response.status_code == 200

    assert b"selected>Category</option>" in response.data
    assert b"selected>Descending</option>" in response.data

    expenses = parse_expenses_from_html(response.data)
    assert len(expenses) == 8

    categories = [e["category"] for e in expenses]
    assert categories == sorted(categories, reverse=True)


def test_sorting_with_invalid_params_fallback(client):
    """
    Test that invalid sort_by and order parameters fall back to defaults (date DESC).
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    response = client.get("/profile?sort_by=invalid&order=invalid")
    assert response.status_code == 200

    # Verify it defaults to date DESC.
    expenses = parse_expenses_from_html(response.data)
    assert len(expenses) == 8
    dates = [e["date"] for e in expenses]
    assert dates == sorted(dates, reverse=True)


def test_sorting_interaction_with_filters(client):
    """
    Test sorting works in unison with category filtering and text search.
    """
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})

    # 1. Category Filter "Food" + Sort by amount DESC
    response = client.get("/profile?category=Food&sort_by=amount&order=DESC")
    assert response.status_code == 200

    # Check that category state is retained
    assert b"selected>Food</option>" in response.data
    assert b"selected>Amount</option>" in response.data
    assert b"selected>Descending</option>" in response.data

    expenses = parse_expenses_from_html(response.data)
    assert len(expenses) == 2
    assert expenses[0]["description"] == "Dinner"  # 18.75
    assert expenses[1]["description"] == "Lunch"  # 12.50

    # 2. Text Search "er" (should match Uber, Dinner, etc) + Sort by amount ASC
    response = client.get("/profile?search_query=er&sort_by=amount&order=ASC")
    assert response.status_code == 200

    # Text input value for search_query check
    assert b'value="er"' in response.data
    assert b"selected>Amount</option>" in response.data
    assert b"selected>Ascending</option>" in response.data

    expenses = parse_expenses_from_html(response.data)
    # Validate amounts are ascending
    amounts = [e["amount"] for e in expenses]
    assert len(amounts) >= 2
    assert amounts == sorted(amounts)
