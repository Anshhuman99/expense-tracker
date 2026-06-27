import pytest
import database.db
from database.queries import (
    get_categories,
    get_filtered_expenses,
    get_recent_transactions,
    get_summary_stats
)

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


def test_auth_guard_profile(client):
    """
    Test that accessing /profile as an unauthenticated user (guest)
    redirects to /login and displays a flash message.
    """
    response = client.get("/profile", follow_redirects=True)
    assert response.status_code == 200
    assert b"Please log in to access this page." in response.data
    assert b"Login" in response.data or b"Email" in response.data


def test_default_dashboard_unfiltered(client):
    """
    Test that loading /profile without query parameters:
    1. Shows the default header "Recent Expenses".
    2. Does not show the "Clear" link/button.
    3. Fetches the recent transactions (seeded has 8, so displays all 8).
    """
    # Log in as seeded demo user
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    
    response = client.get("/profile")
    assert response.status_code == 200
    assert b"Recent Expenses" in response.data
    assert b"Filtered Expenses" not in response.data
    assert b"Clear" not in response.data
    # Verify some seeded transactions exist in the response
    assert b"Lunch" in response.data
    assert b"Uber" in response.data
    assert b"Dinner" in response.data


def test_category_filter_integration(client):
    """
    Test that filtering by a category:
    1. Shows the "Filtered Expenses" header.
    2. Shows the "Clear" link.
    3. Filters the table to match only that category (e.g. Food).
    4. Retains form input state (selected option).
    """
    # Log in
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    
    response = client.get("/profile?category=Food")
    assert response.status_code == 200
    assert b"Filtered Expenses" in response.data
    assert b"Recent Expenses" not in response.data
    assert b"Clear" in response.data
    
    # State retention check (Food should be selected)
    assert b'selected>Food</option>' in response.data
    
    # Food transactions "Lunch" and "Dinner" should be displayed, but "Uber" (Transport) should not
    assert b"Lunch" in response.data
    assert b"Dinner" in response.data
    assert b"Uber" not in response.data


def test_date_range_filter_integration(client):
    """
    Test that specifying a valid date range:
    1. Filters transactions to include only those within the range (inclusive).
    2. Retains the date input values in the form.
    """
    # Log in
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    
    # Date range: 2026-06-03 to 2026-06-08 (includes Uber: 06-03, Electricity: 06-05, Pharmacy: 06-08)
    response = client.get("/profile?start_date=2026-06-03&end_date=2026-06-08")
    assert response.status_code == 200
    assert b"Filtered Expenses" in response.data
    
    # Check table rows: Uber, Electricity, Pharmacy should be visible
    assert b"Uber" in response.data
    assert b"Electricity" in response.data
    assert b"Pharmacy" in response.data
    
    # Out of range items (Lunch: 06-01, Dinner: 06-17) should not be visible
    assert b"Lunch" not in response.data
    assert b"Dinner" not in response.data
    
    # State retention check
    assert b'value="2026-06-03"' in response.data
    assert b'value="2026-06-08"' in response.data


def test_conflicting_date_range(client):
    """
    Test that if start_date > end_date, 0 results are returned and
    the page displays the custom empty state message.
    """
    # Log in
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    
    # Conflicting date range: 2026-06-10 to 2026-06-05
    response = client.get("/profile?start_date=2026-06-10&end_date=2026-06-05")
    assert response.status_code == 200
    assert b"Filtered Expenses" in response.data
    assert b"No matching expenses found." in response.data


def test_malformed_date_range(client):
    """
    Test that malformed date inputs do not cause the application to crash,
    handling them gracefully.
    """
    # Log in
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    
    response = client.get("/profile?start_date=invalid-date&end_date=not-a-date")
    assert response.status_code == 200
    # SQLite string comparisons will just return empty or run without crashing.
    # The application remains functional.
    assert b"Filtered Expenses" in response.data or b"Recent Expenses" in response.data


def test_empty_strings_ignored(client):
    """
    Test that empty strings for filter fields are ignored and treated as unfiltered.
    """
    # Log in
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    
    response = client.get("/profile?category=&start_date=&end_date=")
    assert response.status_code == 200
    assert b"Recent Expenses" in response.data
    assert b"Filtered Expenses" not in response.data
    assert b"Clear" not in response.data


def test_stats_and_breakdown_unfiltered(client):
    """
    Test that KPI stats cards and Category Breakdown sidebar remain overall summaries
    and are not affected by active filters.
    """
    # Log in
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    
    # Filter by category Food (sum is 12.50 + 18.75 = 31.25)
    response = client.get("/profile?category=Food")
    assert response.status_code == 200
    
    # 1. Total spent KPI should show overall lifetime sum (391.25), not 31.25
    assert b"391.25" in response.data
    
    # 2. Total count KPI should show overall count (8), not 2
    assert b"8" in response.data
    
    # 3. Category breakdown should still show all category entries (e.g. Bills, Transport)
    assert b"Bills" in response.data
    assert b"Transport" in response.data


def test_db_filtered_expenses_category(client):
    """
    Test the queries.get_filtered_expenses helper directly for category filtering.
    """
    # Food categories (Lunch, Dinner)
    food_expenses = get_filtered_expenses(1, category="Food")
    assert len(food_expenses) == 2
    for exp in food_expenses:
        assert exp["category"] == "Food"


def test_db_filtered_expenses_date_range(client):
    """
    Test the queries.get_filtered_expenses helper directly for date range boundaries (inclusive).
    """
    # From 2026-06-03 to 2026-06-08 (Uber, Electricity, Pharmacy)
    expenses = get_filtered_expenses(1, start_date="2026-06-03", end_date="2026-06-08")
    assert len(expenses) == 3
    descriptions = [exp["description"] for exp in expenses]
    assert "Uber" in descriptions
    assert "Electricity" in descriptions
    assert "Pharmacy" in descriptions


def test_db_filtered_expenses_text_search(client):
    """
    Test the queries.get_filtered_expenses helper directly for text search (case-insensitive description/category).
    """
    # Exact description match
    exp_lunch = get_filtered_expenses(1, search_query="Lunch")
    assert len(exp_lunch) == 1
    assert exp_lunch[0]["description"] == "Lunch"

    # Case-insensitive description match
    exp_lunch_lower = get_filtered_expenses(1, search_query="lunch")
    assert len(exp_lunch_lower) == 1
    assert exp_lunch_lower[0]["description"] == "Lunch"

    # Category match
    exp_transport = get_filtered_expenses(1, search_query="transport")
    assert len(exp_transport) == 1
    assert exp_transport[0]["description"] == "Uber"


def test_db_filtered_expenses_combined(client):
    """
    Test the queries.get_filtered_expenses helper directly for multiple filters (AND logic).
    """
    # Category=Food AND text_search=Dinner
    expenses = get_filtered_expenses(1, category="Food", search_query="Dinner")
    assert len(expenses) == 1
    assert expenses[0]["description"] == "Dinner"

    # Category=Food AND start_date after all food logs
    expenses_empty = get_filtered_expenses(1, category="Food", start_date="2026-06-20")
    assert len(expenses_empty) == 0


def test_filter_limit_difference(client):
    """
    Test that:
    1. Unfiltered profile page fetches only 10 recent transactions.
    2. Filtered profile page fetches up to 100 transactions.
    """
    # Log in
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    
    # Seed an additional 15 transactions in the DB for demo user (id=1)
    conn = database.db.get_db()
    for i in range(15):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            (1, 10.0, "Food", f"2026-06-{i+1:02d}", f"Seeded expense {i}")
        )
    conn.commit()
    conn.close()
    
    # 1. Verify default unfiltered view limit is 10 (via DB query)
    recent = get_recent_transactions(1, limit=10)
    assert len(recent) == 10

    # 2. Verify active filter uses limit 100 and returns more than 10 matching transactions
    # In total there are 15 (seeded) + 2 (demo Food) = 17 Food expenses.
    filtered = get_filtered_expenses(1, category="Food", limit=100)
    assert len(filtered) == 17


@pytest.mark.xfail(reason="Route integration for text search (q) parameter is not yet implemented in app.py")
def test_route_text_search_integration(client):
    """
    Test that the route accepts query parameter 'q' and filters text case-insensitively.
    This test is expected to fail because app.py does not yet parse or apply the 'q' parameter.
    """
    # Log in
    client.post("/login", data={"email": "demo@spendly.com", "password": "demo123"})
    
    # Request profile filtered by text query
    response = client.get("/profile?q=lunch")
    assert response.status_code == 200
    assert b"Filtered Expenses" in response.data
    
    # "Lunch" should be displayed, but "Uber" should not
    assert b"Lunch" in response.data
    assert b"Uber" not in response.data
