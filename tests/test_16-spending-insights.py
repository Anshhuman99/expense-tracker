"""
Tests for Spec 16: Spending Insights
Route: GET /insights

Covers:
1. Auth guard: Unauthenticated users are redirected to /login with flash.
2. Nav Link: Verification that active 'Insights' links are in layout base.html.
3. Happy path: Calculations (lifetime metrics, MoM percentage changes, daily average spending, projecting month-end) and custom alert badges display correctly.
4. Edge case: Empty state handles no expense data gracefully with clean illustrations and CTA.
"""

import datetime
import calendar
import pytest
import database.db
from database.queries import create_budget


@pytest.fixture
def client(monkeypatch, tmp_path):
    """
    Provides an isolated Flask test client backed by a temporary SQLite database.
    Monkeypatches database.db.DB_PATH so the real database is never touched.
    """
    db_path = str(tmp_path / "test_insights.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)

    # Import the app *after* monkeypatching so all get_db() calls pick up the new path
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


class TestAuthGuard:
    """Unauthenticated access to GET /insights must redirect to /login."""

    def test_unauthenticated_redirects_to_login(self, client):
        res = client.get("/insights")
        assert res.status_code == 302
        assert "/login" in res.location

    def test_unauthenticated_follow_redirect_shows_flash(self, client):
        res = client.get("/insights", follow_redirects=True)
        assert b"log in" in res.data.lower() or b"please log in" in res.data.lower()


# ---------------------------------------------------------------------------
# 2. Nav Link
# ---------------------------------------------------------------------------


class TestNavLink:
    """Verification that active 'Insights' links are in layout base.html when on /insights."""

    def test_nav_link_present_and_active(self, client, tmp_path):
        db_path = str(tmp_path / "test_insights.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)

        res = client.get("/insights")
        assert res.status_code == 200
        # Check for Insights link in response
        assert b"Insights" in res.data
        # Ensure active class is applied to the Insights link/element
        # Layout template: class="{% if request.endpoint == 'insights' %}active{% endif %}"
        assert b"active" in res.data


# ---------------------------------------------------------------------------
# 3. Happy Path: Calculations & Alerts
# ---------------------------------------------------------------------------


class TestHappyPathCalculations:
    """
    Validates calculations (lifetime metrics, MoM percentage changes, daily average spending, projecting month-end)
    and check that custom alert badges / insight alerts display correctly.
    """

    def test_calculations_and_metric_cards(self, client, tmp_path):
        db_path = str(tmp_path / "test_insights.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)

        today = datetime.date.today()
        current_month = today.strftime("%Y-%m")
        prev_month_date = today.replace(day=1) - datetime.timedelta(days=1)
        prev_month = prev_month_date.strftime("%Y-%m")

        # Let's seed expenses
        # Current month: 2 transactions (total = 600.00)
        # Prev month: 2 transactions (total = 400.00)
        # Lifetime: 4 transactions (total = 1000.00), 2 months
        database.db.create_expense(
            user_id, 200.00, "Food", f"{current_month}-01", "Groceries", path=db_path
        )
        database.db.create_expense(
            user_id, 400.00, "Rent", f"{current_month}-05", "Monthly Rent", path=db_path
        )
        database.db.create_expense(
            user_id, 300.00, "Food", f"{prev_month}-10", "Eating Out", path=db_path
        )
        database.db.create_expense(
            user_id, 100.00, "Transport", f"{prev_month}-15", "Taxi", path=db_path
        )

        res = client.get("/insights")
        assert res.status_code == 200

        # 1. Lifetime metrics assertions
        # Lifetime Total Spent: ₹1,000.00
        assert b"1,000.00" in res.data or b"1000.00" in res.data
        assert b"4 transactions" in res.data

        # 2. Monthly Average: 1000.00 / 2 = ₹500.00
        assert b"500.00" in res.data

        # 3. Daily Average (This month): 600.00 / today.day
        daily_average = 600.00 / today.day
        daily_average_str = f"{daily_average:.2f}"
        assert daily_average_str.encode() in res.data

        # 4. Projected month end: daily_average * total_days_in_month
        _, total_days = calendar.monthrange(today.year, today.month)
        projected = daily_average * total_days
        projected_str = f"{projected:,.2f}"
        # Strip commas or match parts just in case of formatting
        projected_stripped = f"{projected:.2f}"
        assert (
            projected_stripped.encode() in res.data
            or projected_str.encode() in res.data
        )

        # 5. Largest single expense: Rent (400.00)
        assert b"Largest Expense" in res.data or b"Largest Single Expense" in res.data
        assert b"400.00" in res.data
        assert b"Rent" in res.data

    def test_spending_surge_mom_alert(self, client, tmp_path):
        db_path = str(tmp_path / "test_insights.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)

        today = datetime.date.today()
        current_month = today.strftime("%Y-%m")
        prev_month_date = today.replace(day=1) - datetime.timedelta(days=1)
        prev_month = prev_month_date.strftime("%Y-%m")

        # Current month total: 500
        # Prev month total: 300
        # MoM change: (500 - 300)/300 = 66.7% increase (> 10% threshold for Spending Surge warning)
        database.db.create_expense(
            user_id, 500.00, "Food", f"{current_month}-01", "Groceries", path=db_path
        )
        database.db.create_expense(
            user_id, 300.00, "Food", f"{prev_month}-10", "Eating Out", path=db_path
        )

        res = client.get("/insights")
        assert res.status_code == 200
        assert b"Spending Surge" in res.data
        assert b"higher than last month" in res.data

    def test_great_savings_mom_alert(self, client, tmp_path):
        db_path = str(tmp_path / "test_insights.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)

        today = datetime.date.today()
        current_month = today.strftime("%Y-%m")
        prev_month_date = today.replace(day=1) - datetime.timedelta(days=1)
        prev_month = prev_month_date.strftime("%Y-%m")

        # Current month total: 100
        # Prev month total: 500
        # MoM change: (100 - 500)/500 = -80% decrease (< -10% threshold for Great Savings success card)
        database.db.create_expense(
            user_id, 100.00, "Food", f"{current_month}-01", "Groceries", path=db_path
        )
        database.db.create_expense(
            user_id, 500.00, "Food", f"{prev_month}-10", "Eating Out", path=db_path
        )

        res = client.get("/insights")
        assert res.status_code == 200
        assert b"Great Savings" in res.data or b"Great Savings!" in res.data
        assert b"lower than last month" in res.data

    def test_stable_spending_mom_alert(self, client, tmp_path):
        db_path = str(tmp_path / "test_insights.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)

        today = datetime.date.today()
        current_month = today.strftime("%Y-%m")
        prev_month_date = today.replace(day=1) - datetime.timedelta(days=1)
        prev_month = prev_month_date.strftime("%Y-%m")

        # Current month total: 102
        # Prev month total: 100
        # MoM change: 2% (within -10% to 10% threshold for Stable Spending info card)
        database.db.create_expense(
            user_id, 102.00, "Food", f"{current_month}-01", "Groceries", path=db_path
        )
        database.db.create_expense(
            user_id, 100.00, "Food", f"{prev_month}-10", "Eating Out", path=db_path
        )

        res = client.get("/insights")
        assert res.status_code == 200
        assert b"Stable Spending" in res.data
        assert b"stable compared to last month" in res.data

    def test_dominant_category_warning_alert(self, client, tmp_path):
        db_path = str(tmp_path / "test_insights.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)

        today = datetime.date.today()
        current_month = today.strftime("%Y-%m")

        # Create one category with huge chunk: Food (90.00) vs Travel (10.00). Food accounts for 90% (> 50% threshold)
        database.db.create_expense(
            user_id, 90.00, "Food", f"{current_month}-01", "Groceries", path=db_path
        )
        database.db.create_expense(
            user_id, 10.00, "Travel", f"{current_month}-02", "Bus", path=db_path
        )

        res = client.get("/insights")
        assert res.status_code == 200
        assert b"Dominant Category" in res.data
        assert b"Food" in res.data
        assert b"accounts for" in res.data

    def test_budget_warnings(self, client, tmp_path):
        db_path = str(tmp_path / "test_insights.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)

        today = datetime.date.today()
        current_month = today.strftime("%Y-%m")

        # Budget exceeded: Limit = 100, Spend = 120
        create_budget(user_id, "Food", 100.00, current_month, path=db_path)
        database.db.create_expense(
            user_id, 120.00, "Food", f"{current_month}-01", "Groceries", path=db_path
        )

        # Budget alert (near limit: >80% and <=100%): Limit = 200, Spend = 170 (85%)
        create_budget(user_id, "Entertainment", 200.00, current_month, path=db_path)
        database.db.create_expense(
            user_id,
            170.00,
            "Entertainment",
            f"{current_month}-02",
            "Movies",
            path=db_path,
        )

        res = client.get("/insights")
        assert res.status_code == 200
        # Exceeded alert
        assert b"Budget Exceeded" in res.data or b"exceeding your budget" in res.data
        assert b"Food" in res.data
        # Alert warning
        assert b"Budget Alert" in res.data or b"of your budget limit" in res.data
        assert b"Entertainment" in res.data


# ---------------------------------------------------------------------------
# 4. Edge Case: Empty State
# ---------------------------------------------------------------------------


class TestEmptyState:
    """Empty state handles no expense data gracefully with clean illustrations and CTA."""

    def test_empty_state_rendered_correctly(self, client, tmp_path):
        db_path = str(tmp_path / "test_insights.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)

        res = client.get("/insights")
        assert res.status_code == 200
        # Assert empty state headings and copy are displayed
        assert b"No Insights Available" in res.data
        assert b"Start logging your daily expenses" in res.data
        # Assert clean CTA to add expense is present
        assert b"Add Your First Expense" in res.data
        assert b"/expenses/add" in res.data
        # Make sure metrics grid or metric cards are NOT rendered
        assert b"Lifetime Spent" not in res.data
        assert b"Monthly Average" not in res.data
        assert b"Daily Avg (This Month)" not in res.data
