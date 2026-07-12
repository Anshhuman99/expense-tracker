"""
Tests for Step 26: Recurring Expenses
Covers:
1. Happy path: Creating, listing, and deleting a recurring rule.
2. Validation: Rejects invalid frequency, invalid category, negative amount, and invalid start date.
3. Authorization: A logged-in user cannot delete another user's recurring rules.
4. Auto-generation: Simulates date transitions to verify that visiting the profile dashboard
   creates standard expenses in the `expenses` table for daily/weekly/monthly/yearly rules,
   and updates the rule's `last_generated` column correctly.
5. Database connection and query helpers verification.
"""

import datetime
import sys
import pytest
import database.db
from database.queries import (
    get_recurring_rules,
    get_recurring_rule,
    create_recurring_rule,
    delete_recurring_rule,
    update_recurring_rule_last_generated,
)

# ------------------------------------------------------------------ #
# Mock datetime module for date transitions                           #
# ------------------------------------------------------------------ #

_original_date = datetime.date


class MockDate(datetime.date):
    _mock_today = None

    @classmethod
    def today(cls):
        if cls._mock_today is not None:
            return cls._mock_today
        return _original_date.today()


_original_datetime = datetime


class MockDatetimeModule:
    def __init__(self):
        self.date = MockDate

    def __getattr__(self, name):
        return getattr(_original_datetime, name)


# Inject the mock datetime module into sys.modules
mock_datetime_instance = MockDatetimeModule()
sys.modules["datetime"] = mock_datetime_instance


@pytest.fixture(autouse=True)
def reset_mock_today():
    """Ensure mock today is cleared before/after each test."""
    MockDate._mock_today = None
    yield
    MockDate._mock_today = None


# ------------------------------------------------------------------ #
# Fixtures                                                           #
# ------------------------------------------------------------------ #


@pytest.fixture
def client(monkeypatch, tmp_path):
    """
    Isolated Flask test client with a clean SQLite DB.
    """
    db_path = str(tmp_path / "test_recurring.db")
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


# ------------------------------------------------------------------ #
# Helpers                                                           #
# ------------------------------------------------------------------ #


def _create_user(name="Alice", email="alice@example.com", password="Password1!"):
    database.db.create_user(name, email, password)
    # Get the created user ID
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
# 1. DB connection and query helpers verification                    #
# ------------------------------------------------------------------ #


def test_query_helpers(client):
    """Verify the DB connections and query helpers behave as expected."""
    user_id = _create_user("Bob", "bob@example.com")

    # 1. Create a rule
    create_recurring_rule(
        user_id=user_id,
        amount=99.99,
        category="Bills",
        frequency="monthly",
        start_date="2026-07-01",
        description="Netflix Subscription",
        path=database.db.DB_PATH,
    )

    # 2. Get list of rules
    rules = get_recurring_rules(user_id, path=database.db.DB_PATH)
    assert len(rules) == 1
    rule = rules[0]
    assert rule["amount"] == 99.99
    assert rule["category"] == "Bills"
    assert rule["frequency"] == "monthly"
    assert rule["start_date"] == "2026-07-01"
    assert rule["description"] == "Netflix Subscription"
    assert rule["last_generated"] is None

    # 3. Get single rule
    rule_id = rule["id"]
    fetched_rule = get_recurring_rule(rule_id, path=database.db.DB_PATH)
    assert fetched_rule is not None
    assert fetched_rule["id"] == rule_id

    # 4. Update last generated
    update_recurring_rule_last_generated(
        rule_id, "2026-07-01", path=database.db.DB_PATH
    )
    fetched_rule = get_recurring_rule(rule_id, path=database.db.DB_PATH)
    assert fetched_rule["last_generated"] == "2026-07-01"

    # 5. Delete rule
    delete_recurring_rule(rule_id, path=database.db.DB_PATH)
    assert get_recurring_rule(rule_id, path=database.db.DB_PATH) is None


# ------------------------------------------------------------------ #
# 2. Happy Path Integration Tests                                    #
# ------------------------------------------------------------------ #


def test_recurring_happy_path(client):
    """Test creating, listing, and deleting a recurring rule via the web interface."""
    user_id = _create_and_login(client)

    # Create rule
    res = client.post(
        "/recurring/add",
        data={
            "amount": "1500.00",
            "category": "Bills",
            "frequency": "monthly",
            "start_date": "2026-07-10",
            "description": "House Rent",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert b"Recurring expense rule created successfully." in res.data

    # List rules
    res = client.get("/recurring")
    assert res.status_code == 200
    assert b"House Rent" in res.data
    assert b"Monthly" in res.data

    # Find the rule ID from database
    rules = get_recurring_rules(user_id)
    assert len(rules) == 1
    rule_id = rules[0]["id"]

    # Delete rule
    res = client.post(f"/recurring/{rule_id}/delete", follow_redirects=True)
    assert res.status_code == 200
    assert b"Recurring expense rule deleted successfully." in res.data

    # Verify not listed anymore
    res = client.get("/recurring")
    assert b"House Rent" not in res.data


# ------------------------------------------------------------------ #
# 3. Input Validation Tests                                          #
# ------------------------------------------------------------------ #


def test_recurring_validation(client):
    """Test validation constraints on recurring rule creation form."""
    _create_and_login(client)

    # Helper function to submit data and assert error
    def assert_error(data, expected_error):
        res = client.post("/recurring/add", data=data, follow_redirects=True)
        assert res.status_code == 200
        assert expected_error.encode() in res.data

    # Invalid category
    assert_error(
        {
            "amount": "50.00",
            "category": "InvalidCat",
            "frequency": "daily",
            "start_date": "2026-07-10",
        },
        "Invalid category selected.",
    )

    # Invalid frequency
    assert_error(
        {
            "amount": "50.00",
            "category": "Food",
            "frequency": "hourly",
            "start_date": "2026-07-10",
        },
        "Invalid frequency selected.",
    )

    # Negative amount
    assert_error(
        {
            "amount": "-50.00",
            "category": "Food",
            "frequency": "daily",
            "start_date": "2026-07-10",
        },
        "Amount must be positive.",
    )

    # Zero amount
    assert_error(
        {
            "amount": "0",
            "category": "Food",
            "frequency": "daily",
            "start_date": "2026-07-10",
        },
        "Amount must be positive.",
    )

    # Non-numeric amount
    assert_error(
        {
            "amount": "abc",
            "category": "Food",
            "frequency": "daily",
            "start_date": "2026-07-10",
        },
        "Amount must be a number.",
    )

    # Invalid start date format
    assert_error(
        {
            "amount": "50.00",
            "category": "Food",
            "frequency": "daily",
            "start_date": "10/07/2026",
        },
        "Start date must be in YYYY-MM-DD format.",
    )


# ------------------------------------------------------------------ #
# 4. Authorization / Ownership Guards                                #
# ------------------------------------------------------------------ #


def test_recurring_authorization(client):
    """Logged in user cannot delete another user's recurring rules."""
    user1_id = _create_user("UserOne", "one@example.com")
    user2_id = _create_user("UserTwo", "two@example.com")

    # Create a rule for UserOne
    create_recurring_rule(
        user_id=user1_id,
        amount=100.00,
        category="Transport",
        frequency="weekly",
        start_date="2026-07-01",
        description="UserOne Commute",
    )
    rules = get_recurring_rules(user1_id)
    assert len(rules) == 1
    rule_id = rules[0]["id"]

    # Log in as UserTwo
    _login(client, "two@example.com")

    # Attempt to delete UserOne's rule
    res = client.post(f"/recurring/{rule_id}/delete")
    assert res.status_code == 403

    # Verify rule still exists
    assert get_recurring_rule(rule_id) is not None


# ------------------------------------------------------------------ #
# 5. Auto-generation Tests                                           #
# ------------------------------------------------------------------ #


def test_auto_generation_date_transitions(client):
    """
    Simulates date transitions to verify that visiting the profile dashboard creates standard expenses
    in the `expenses` table for daily/weekly/monthly/yearly rules, and updates the rule's `last_generated`.
    """
    user_id = _create_and_login(client)

    # Create recurring rules:
    # 1. Daily rule starting 2026-07-01
    create_recurring_rule(
        user_id=user_id,
        amount=10.00,
        category="Food",
        frequency="daily",
        start_date="2026-07-01",
        description="Daily Coffee",
    )
    # 2. Weekly rule starting 2026-07-01
    create_recurring_rule(
        user_id=user_id,
        amount=50.00,
        category="Transport",
        frequency="weekly",
        start_date="2026-07-01",
        description="Weekly Petrol",
    )
    # 3. Monthly rule starting 2026-07-01
    create_recurring_rule(
        user_id=user_id,
        amount=200.00,
        category="Bills",
        frequency="monthly",
        start_date="2026-07-01",
        description="Monthly Internet",
    )
    # 4. Yearly rule starting 2026-07-01
    create_recurring_rule(
        user_id=user_id,
        amount=1200.00,
        category="Other",
        frequency="yearly",
        start_date="2026-07-01",
        description="Yearly Insurance",
    )

    # Let's count expenses before processing
    conn = database.db.get_db()
    try:
        initial_expenses_count = conn.execute(
            "SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_id,)
        ).fetchone()[0]
    finally:
        conn.close()

    # -- Transition 1: Set today to 2026-07-01 --
    # On start date, all rules should trigger for the first time.
    MockDate._mock_today = datetime.date(2026, 7, 1)

    # Load profile dashboard to trigger auto-generation
    res = client.get("/profile")
    assert res.status_code == 200

    conn = database.db.get_db()
    try:
        expenses = conn.execute(
            "SELECT * FROM expenses WHERE user_id = ? ORDER BY date ASC", (user_id,)
        ).fetchall()
        # Verify 4 expenses generated (Daily Coffee, Weekly Petrol, Monthly Internet, Yearly Insurance)
        assert len(expenses) - initial_expenses_count == 4
        for exp in expenses[initial_expenses_count:]:
            assert exp["date"] == "2026-07-01"
            assert exp["amount"] in [10.0, 50.0, 200.0, 1200.0]

        # Verify last_generated is updated
        rules = conn.execute(
            "SELECT * FROM recurring_rules WHERE user_id = ?", (user_id,)
        ).fetchall()
        for r in rules:
            assert r["last_generated"] == "2026-07-01"
    finally:
        conn.close()

    # -- Transition 2: Set today to 2026-07-03 --
    # Only daily rule should trigger for 2026-07-02 and 2026-07-03 (2 occurrences)
    MockDate._mock_today = datetime.date(2026, 7, 3)

    res = client.get("/profile")
    assert res.status_code == 200

    conn = database.db.get_db()
    try:
        daily_expenses = conn.execute(
            "SELECT * FROM expenses WHERE user_id = ? AND category = 'Food' ORDER BY date ASC",
            (user_id,),
        ).fetchall()
        # Initial 1 coffee (2026-07-01) + 2 new ones (2026-07-02, 2026-07-03)
        assert len(daily_expenses) == 3
        assert daily_expenses[1]["date"] == "2026-07-02"
        assert daily_expenses[2]["date"] == "2026-07-03"

        # Check last_generated for the daily rule
        daily_rule = conn.execute(
            "SELECT last_generated FROM recurring_rules WHERE frequency = 'daily' AND user_id = ?",
            (user_id,),
        ).fetchone()
        assert daily_rule["last_generated"] == "2026-07-03"
    finally:
        conn.close()

    # -- Transition 3: Set today to 2026-07-08 --
    # Weekly rule triggers for 2026-07-08 (start_date 2026-07-01 + 7 days)
    # Daily rule triggers for 2026-07-04, 05, 06, 07, 08 (5 occurrences)
    MockDate._mock_today = datetime.date(2026, 7, 8)

    res = client.get("/profile")
    assert res.status_code == 200

    conn = database.db.get_db()
    try:
        weekly_expenses = conn.execute(
            "SELECT * FROM expenses WHERE user_id = ? AND category = 'Transport' ORDER BY date ASC",
            (user_id,),
        ).fetchall()
        # 2026-07-01 and 2026-07-08
        assert len(weekly_expenses) == 2
        assert weekly_expenses[1]["date"] == "2026-07-08"

        weekly_rule = conn.execute(
            "SELECT last_generated FROM recurring_rules WHERE frequency = 'weekly' AND user_id = ?",
            (user_id,),
        ).fetchone()
        assert weekly_rule["last_generated"] == "2026-07-08"
    finally:
        conn.close()
