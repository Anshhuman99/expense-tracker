"""
Tests for Spec 28: Saving Suggestions
Route: GET /suggestions

Covers:
1. Accessing GET /suggestions without logging in redirects to /login.
2. Accessing GET /suggestions logged in returns the page correctly, displaying suggestion cards.
3. Suggestion rules are evaluated correctly:
   - High dining spend rule trigger (Food category exceeds 30% of monthly total).
   - Over-budget warning (spend >= 90% of budget limit) and exceeded budget (spend >= 100% of budget limit).
   - MoM category spending increase of >= 20% compared to previous month (with base spending > $20).
   - Highest spending category triggers target advice optimization card.
4. Empty state is rendered correctly for users with no expenses.
"""

import datetime
import pytest
import database.db
from database.queries import create_budget


@pytest.fixture
def client(monkeypatch, tmp_path):
    """
    Provides an isolated Flask test client backed by a temporary SQLite database.
    Monkeypatches database.db.DB_PATH so the real database is never touched.
    """
    db_path = str(tmp_path / "test_suggestions.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)

    # Import the app *after* monkeypatching so all db calls pick up the new path
    from app import app as flask_app

    flask_app.config.update({"TESTING": True, "WTF_CSRF_ENABLED": False})
    database.db.init_db(db_path)

    with flask_app.test_client() as test_client:
        yield test_client


def _register_and_login(
    client, name="Tester", email="tester@example.com", password="testpass1"
):
    """Create a user in the database and log them in via POST /login."""
    database.db.create_user(name, email, password)
    client.post("/login", data={"email": email, "password": password})


def _get_user_id(email="tester@example.com", db_path=None):
    """Return the integer user_id for a given email."""
    user = database.db.get_user_by_email(email, path=db_path)
    return user["id"]


# ---------------------------------------------------------------------------
# 1. Auth Guard
# ---------------------------------------------------------------------------


def test_unauthenticated_redirects_to_login(client):
    """Verify accessing GET /suggestions without logging in redirects to /login."""
    res = client.get("/suggestions")
    assert res.status_code == 302
    assert "/login" in res.location


# ---------------------------------------------------------------------------
# 2. Authenticated Rendering & General Success
# ---------------------------------------------------------------------------


def test_authenticated_suggestions_page_renders(client, tmp_path):
    """Verify accessing GET /suggestions logged in renders the page and generates suggestions."""
    db_path = str(tmp_path / "test_suggestions.db")
    _register_and_login(client)
    user_id = _get_user_id(db_path=db_path)

    today = datetime.date.today()
    current_month = today.strftime("%Y-%m")

    # Seed some dummy expenses to generate generic top category suggestion
    database.db.create_expense(
        user_id, 50.00, "Transport", f"{current_month}-01", "Uber ride", path=db_path
    )

    res = client.get("/suggestions")
    assert res.status_code == 200
    assert b"Personalized Saving Suggestions" in res.data
    assert b"Transport" in res.data
    assert b"Optimize Top Category: Transport" in res.data


# ---------------------------------------------------------------------------
# 3. Rule Evaluation Behavior
# ---------------------------------------------------------------------------


def test_rule_high_dining_spend(client, tmp_path):
    """Verify that Food spend > 30% of total triggers the high dining spend card."""
    db_path = str(tmp_path / "test_suggestions.db")
    _register_and_login(client)
    user_id = _get_user_id(db_path=db_path)

    today = datetime.date.today()
    current_month = today.strftime("%Y-%m")

    # Total spend = 300.00
    # Food spend = 100.00 (which is 33.3%, > 30% threshold)
    # Transport spend = 200.00
    database.db.create_expense(
        user_id, 100.00, "Food", f"{current_month}-01", "Dinner out", path=db_path
    )
    database.db.create_expense(
        user_id, 200.00, "Transport", f"{current_month}-02", "Uber", path=db_path
    )

    res = client.get("/suggestions")
    assert res.status_code == 200
    assert b"High Food &amp; Dining Spend" in res.data
    assert b"Try preparing meals at home" in res.data


def test_rule_over_budget_warning_and_exceeded(client, tmp_path):
    """Verify that spend >= 90% of budget triggers warning and spend >= 100% triggers exceeded."""
    db_path = str(tmp_path / "test_suggestions.db")
    _register_and_login(client)
    user_id = _get_user_id(db_path=db_path)

    today = datetime.date.today()
    current_month = today.strftime("%Y-%m")

    # Set up budgets
    # Food budget: limit = 100.00. Spend = 92.00 (92%, triggers warning)
    # Shopping budget: limit = 100.00. Spend = 110.00 (110%, triggers exceeded)
    create_budget(user_id, "Food", 100.00, current_month, path=db_path)
    create_budget(user_id, "Shopping", 100.00, current_month, path=db_path)

    database.db.create_expense(
        user_id, 92.00, "Food", f"{current_month}-01", "Groceries", path=db_path
    )
    database.db.create_expense(
        user_id, 110.00, "Shopping", f"{current_month}-01", "Clothes", path=db_path
    )

    res = client.get("/suggestions")
    assert res.status_code == 200
    assert b"Approaching Food Budget Limit" in res.data
    assert b"Exceeded Shopping Budget" in res.data


def test_rule_mom_spending_spike(client, tmp_path):
    """Verify MoM category spending increase of >= 20% compared to previous month triggers spike card."""
    db_path = str(tmp_path / "test_suggestions.db")
    _register_and_login(client)
    user_id = _get_user_id(db_path=db_path)

    today = datetime.date.today()
    current_month = today.strftime("%Y-%m")

    first_day_current = today.replace(day=1)
    prev_month_val = first_day_current - datetime.timedelta(days=1)
    prev_month = prev_month_val.strftime("%Y-%m")

    # Transport spend:
    # Previous month = $50.00 (> $20 base threshold)
    # Current month = $75.00 (a 50% increase, >= 20% spike threshold)
    database.db.create_expense(
        user_id, 50.00, "Transport", f"{prev_month}-15", "Taxi last month", path=db_path
    )
    database.db.create_expense(
        user_id,
        75.00,
        "Transport",
        f"{current_month}-10",
        "Taxi this month",
        path=db_path,
    )

    res = client.get("/suggestions")
    assert res.status_code == 200
    assert b"Spike in Transport Spending" in res.data
    assert b"increased from \xe2\x82\xb950.00" in res.data


def test_rule_top_category_optimization_tip(client, tmp_path):
    """Verify that the highest spending category triggers target advice optimization card."""
    db_path = str(tmp_path / "test_suggestions.db")
    _register_and_login(client)
    user_id = _get_user_id(db_path=db_path)

    today = datetime.date.today()
    current_month = today.strftime("%Y-%m")

    # Shopping is top category: $150.00
    # Food: $50.00
    database.db.create_expense(
        user_id, 150.00, "Shopping", f"{current_month}-01", "Electronics", path=db_path
    )
    database.db.create_expense(
        user_id, 50.00, "Food", f"{current_month}-02", "Snacks", path=db_path
    )

    res = client.get("/suggestions")
    assert res.status_code == 200
    assert b"Optimize Top Category: Shopping" in res.data
    assert b"Implement a 48-hour cool-down rule" in res.data


# ---------------------------------------------------------------------------
# 4. Empty State Verification
# ---------------------------------------------------------------------------


def test_empty_state_for_no_expenses(client, tmp_path):
    """Verify empty state is rendered correctly and safely for users with no expenses."""
    db_path = str(tmp_path / "test_suggestions.db")
    _register_and_login(client)

    res = client.get("/suggestions")
    assert res.status_code == 200
    assert b"You're in great shape!" in res.data
    assert (
        b"Note: Start logging expenses for this month to receive personalized recommendations."
        in res.data
    )
