"""
Tests for Step 27: Spending Trends
Covers:
1. Happy path: Accessing GET `/trends` (logged in), verifying metrics are computed correctly, comparing month A and B correctly.
2. Validation: Requesting trends with an invalid month format flashes an error and redirects.
3. Edge case: Grassroots calculations with zero spending, new category spends, and check division by zero prevention.
4. Verify database queries: Check that `get_logged_months` returns month keys in descending order.
"""

import datetime
import pytest
import database.db
from database.queries import get_logged_months
from database.db import create_expense


@pytest.fixture
def client(monkeypatch, tmp_path):
    """
    Isolated Flask test client with a clean SQLite DB.
    """
    db_path = str(tmp_path / "test_trends.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)

    # Import app now so that its module-level init_db/seed_db calls
    # run against the temporary test database.
    from app import app as flask_app

    flask_app.config.update(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SECRET_KEY": "test-secret",
        }
    )

    database.db.init_db(db_path)
    database.db.seed_db(db_path)

    with flask_app.test_client() as test_client:
        yield test_client


def _create_user(name="Alice", email="alice@example.com", password="Password1!"):
    database.db.create_user(name, email, password)
    conn = database.db.get_db()
    try:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        return row["id"] if row else None
    finally:
        conn.close()


def _login(client, email="alice@example.com", password="Password1!"):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


def _create_and_login(
    client, name="Alice", email="alice@example.com", password="Password1!"
):
    user_id = _create_user(name, email, password)
    _login(client, email, password)
    return user_id


# ------------------------------------------------------------------ #
# Tests                                                              #
# ------------------------------------------------------------------ #


def test_trends_requires_login(client):
    """Accessing GET /trends without logging in redirects to /login."""
    response = client.get("/trends", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.location

    # Follow redirects to see flash message
    response = client.get("/trends", follow_redirects=True)
    assert b"Please log in to access this page." in response.data


def test_trends_happy_path(client):
    """Accessing GET /trends logged in returns correct page, params, and diffs."""
    user_id = _create_and_login(client)

    # Create expenses for two months: May 2026 and June 2026
    # Month A (May 2026): Food 100.0, Bills 200.0. Total = 300.0
    create_expense(
        user_id, 100.0, "Food", "2026-05-10", "Groceries", path=database.db.DB_PATH
    )
    create_expense(
        user_id, 200.0, "Bills", "2026-05-15", "Electricity", path=database.db.DB_PATH
    )

    # Month B (June 2026): Food 150.0, Bills 100.0. Total = 250.0
    create_expense(
        user_id, 150.0, "Food", "2026-06-12", "Supermarket", path=database.db.DB_PATH
    )
    create_expense(
        user_id, 100.0, "Bills", "2026-06-20", "Water bill", path=database.db.DB_PATH
    )

    # Get comparison
    response = client.get("/trends?month_a=2026-05&month_b=2026-06")
    assert response.status_code == 200

    # Verify metrics totals
    assert b"Spent in 2026-05" in response.data
    assert b"Spent in 2026-06" in response.data
    assert b"\xe2\x82\xb9300.00" in response.data
    assert b"\xe2\x82\xb9250.00" in response.data

    # Total diff: -50.00, which is -16.666% (shows as Decreased by 16.7%)
    assert b"\xe2\x82\xb9-50.00" in response.data
    assert b"Decreased by 16.7%" in response.data

    # Food diff: +50.00 (+50.0%)
    assert b"+\xe2\x82\xb950.00" in response.data
    assert b"+50.0%" in response.data

    # Bills diff: -100.00 (-50.0%)
    assert b"\xe2\x82\xb9-100.00" in response.data
    assert b"-50.0%" in response.data


def test_trends_validation_invalid_months(client):
    """Requesting trends with invalid month formats flashes error and redirects."""
    _create_and_login(client)

    # Invalid month_a
    response = client.get(
        "/trends?month_a=invalid&month_b=2026-06", follow_redirects=True
    )
    assert b"Invalid month format selected." in response.data

    # Invalid month_b
    response = client.get(
        "/trends?month_a=2026-05&month_b=2026/06", follow_redirects=True
    )
    assert b"Invalid month format selected." in response.data


def test_trends_edge_cases(client):
    """
    Edge case tests:
    - Zero spending in base month A.
    - Category present in only one month.
    - Division by zero prevention.
    """
    user_id = _create_and_login(client)

    # Scenario: Month A has zero spending (no expenses)
    # Month B has Food ($100)
    create_expense(
        user_id, 100.0, "Food", "2026-06-10", "Groceries", path=database.db.DB_PATH
    )

    response = client.get("/trends?month_a=2026-05&month_b=2026-06")
    assert response.status_code == 200
    assert b"\xe2\x82\xb90.00" in response.data  # Spent in base month
    assert b"\xe2\x82\xb9100.00" in response.data  # Spent in comparison month
    # Percentage change for total should be +100% since total_a was 0.0
    assert b"Increased by 100.0%" in response.data
    # Category Food should be marked as "New Category" since amount_a was 0.0 and amount_b > 0.0
    assert b"New Category" in response.data

    # Scenario: Category present in only one month
    # Let's seed Month A with Entertainment ($50.00) only
    # Month B has Food ($100.00) only (Food is not in Month A, Entertainment is not in Month B)
    # We clear expenses or just select different months. Let's compare Month A (July) and Month B (August)
    create_expense(
        user_id, 50.0, "Entertainment", "2026-07-05", "Cinema", path=database.db.DB_PATH
    )
    create_expense(
        user_id, 100.0, "Food", "2026-08-10", "Groceries", path=database.db.DB_PATH
    )

    response = client.get("/trends?month_a=2026-07&month_b=2026-08")
    assert response.status_code == 200
    # Total A: 50.00, Total B: 100.00 -> Diff +50.00 (+100.0%)
    assert b"\xe2\x82\xb950.00" in response.data
    assert b"\xe2\x82\xb9100.00" in response.data
    assert b"+\xe2\x82\xb950.00" in response.data
    assert b"Increased by 100.0%" in response.data

    # Food was only in B (amount_a = 0.0, amount_b = 100.0) -> New Category
    assert b"New Category" in response.data
    assert b"Food" in response.data

    # Entertainment was only in A (amount_a = 50.0, amount_b = 0.0) -> Diff -$50.00 (-100.0%)
    assert b"Entertainment" in response.data
    assert b"\xe2\x82\xb9-50.00" in response.data
    assert b"-100.0%" in response.data


def test_db_get_logged_months_descending(client):
    """Check that get_logged_months returns month keys in descending order."""
    user_id = _create_user()

    # Seed expenses out of order
    create_expense(user_id, 10.0, "Food", "2026-05-01", "A", path=database.db.DB_PATH)
    create_expense(user_id, 10.0, "Food", "2026-07-01", "B", path=database.db.DB_PATH)
    create_expense(user_id, 10.0, "Food", "2026-06-01", "C", path=database.db.DB_PATH)
    create_expense(
        user_id, 10.0, "Food", "2026-05-15", "D", path=database.db.DB_PATH
    )  # Same month, duplicate check

    months = get_logged_months(user_id, path=database.db.DB_PATH)
    # Should be sorted descending, and unique
    assert months == ["2026-07", "2026-06", "2026-05"]
