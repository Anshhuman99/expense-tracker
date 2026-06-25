import pytest
import database.db
from database.queries import get_categories, get_filtered_expenses

@pytest.fixture
def client(monkeypatch, tmp_path):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)
    
    # Import app inside fixture so monkeypatching takes effect
    from app import app as flask_app
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False
    })
    
    database.db.init_db(db_path)
    database.db.seed_db(db_path)
    
    with flask_app.test_client() as client:
        yield client


def test_get_categories(client):
    # Retrieve categories for demo user (id=1)
    categories = get_categories(1)
    assert len(categories) == 7
    assert "Food" in categories
    assert "Transport" in categories
    assert categories == sorted(categories)


def test_get_filtered_expenses_by_category(client):
    # Seeded Food items: Lunch (12.50), Dinner (18.75)
    food_expenses = get_filtered_expenses(1, category="Food")
    assert len(food_expenses) == 2
    for exp in food_expenses:
        assert exp["category"] == "Food"
    
    # Transport: Uber (45.00)
    transport_expenses = get_filtered_expenses(1, category="Transport")
    assert len(transport_expenses) == 1
    assert transport_expenses[0]["description"] == "Uber"


def test_get_filtered_expenses_by_date_range(client):
    # Seed date bounds: 2026-06-03 to 2026-06-08
    # Should match: Transport (06-03), Bills (06-05), Health (06-08)
    expenses = get_filtered_expenses(1, start_date="2026-06-03", end_date="2026-06-08")
    assert len(expenses) == 3
    descriptions = [exp["description"] for exp in expenses]
    assert "Uber" in descriptions
    assert "Electricity" in descriptions
    assert "Pharmacy" in descriptions


def test_get_filtered_expenses_by_text_search(client):
    # Match description (e.g. "Lunch")
    expenses_lunch = get_filtered_expenses(1, search_query="lunch")
    assert len(expenses_lunch) == 1
    assert expenses_lunch[0]["description"] == "Lunch"

    # Match description case-insensitively
    expenses_lunch_caps = get_filtered_expenses(1, search_query="LUNCH")
    assert len(expenses_lunch_caps) == 1
    assert expenses_lunch_caps[0]["description"] == "Lunch"

    # Match category (e.g. "Transport")
    expenses_transport = get_filtered_expenses(1, search_query="transport")
    assert len(expenses_transport) == 1
    assert expenses_transport[0]["description"] == "Uber"


def test_get_filtered_expenses_combined(client):
    # Category = Food, Text Search = dinner
    expenses = get_filtered_expenses(1, category="Food", search_query="dinner")
    assert len(expenses) == 1
    assert expenses[0]["description"] == "Dinner"

    # Outside date range
    expenses_out_of_date = get_filtered_expenses(1, category="Food", start_date="2026-06-20")
    assert len(expenses_out_of_date) == 0


def test_route_unfiltered_view(client):
    # Log in
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    
    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Recent Expenses" in response.data
    assert b"Filtered Expenses" not in response.data
    assert b"Lunch" in response.data
    assert b"Uber" in response.data
    assert b"Clear" not in response.data


def test_route_filtered_by_category(client):
    # Log in
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    
    response = client.get("/profile?category=Food")
    assert response.status_code == 200
    assert b"Filtered Expenses" in response.data
    assert b"Recent Expenses" not in response.data
    assert b"Lunch" in response.data
    assert b"Dinner" in response.data
    assert b"Uber" not in response.data
    assert b"Clear" in response.data
    
    # State retention check
    assert b'selected>Food</option>' in response.data


def test_route_filtered_by_text(client):
    # Log in
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    
    response = client.get("/profile?q=cinema")
    assert response.status_code == 200
    assert b"Filtered Expenses" in response.data
    assert b"Netflix + cinema" in response.data
    assert b"Lunch" not in response.data
    
    # State retention check
    assert b'value="cinema"' in response.data


def test_route_filtered_no_matches(client):
    # Log in
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    
    response = client.get("/profile?q=nonexistent")
    assert response.status_code == 200
    assert b"No matching expenses found." in response.data


def test_kpi_stats_unfiltered_during_active_filter(client):
    # Log in
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    
    # Filter by category Food (sum is 12.50 + 18.75 = 31.25)
    response = client.get("/profile?category=Food")
    assert response.status_code == 200
    
    # The stats grid must still show the total overall spent, which is 391.25 (unfiltered)
    assert b"391.25" in response.data
    # Total count in stats grid should still show overall count (8 transactions)
    assert b"8" in response.data
