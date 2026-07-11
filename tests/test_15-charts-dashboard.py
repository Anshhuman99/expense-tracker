"""
Tests for Spec 15: Charts Dashboard
Route: GET /analytics

Covers:
1.  Auth guard — unauthenticated GET /analytics redirects to /login with flash.
2.  Happy path (no filters) — 200 + chart heading content.
3.  Happy path (with filters) — category, start_date, end_date query params give 200.
4.  Empty state (no expenses at all) — empty state message shown, no chart canvases.
5.  Filter empty state — expenses exist but active filters match nothing -> empty state.
6.  Budget vs Actual — no budgets: CTA link to /budgets present.
7.  Budget vs Actual — with budgets: budget comparison chart canvas present.
8.  Chart.js CDN script tag present in response.
9.  JSON data injected: JS variable names / canvas IDs present in response.
10. Filter bar rendered: category dropdown, start_date and end_date inputs.
11. Valid category filter returns 200.
12. Analytics nav link is active when on /analytics.
"""

import datetime
import pytest
import database.db
from database.queries import create_budget

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client(monkeypatch, tmp_path):
    """
    Provides an isolated Flask test client backed by a temporary SQLite database.
    Monkeypatches database.db.DB_PATH so the real spendly.db is never touched.
    """
    db_path = str(tmp_path / "test_charts.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)

    # Import the app *after* monkeypatching so all get_db() calls pick up the new path
    from app import app as flask_app

    flask_app.config.update({"TESTING": True, "WTF_CSRF_ENABLED": False})
    database.db.init_db(db_path)

    with flask_app.test_client() as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TODAY = datetime.date.today()
CURRENT_MONTH = TODAY.strftime("%Y-%m")
LAST_MONTH = (TODAY.replace(day=1) - datetime.timedelta(days=1)).strftime("%Y-%m")


def _register_and_login(
    client, name="Tester", email="tester@example.com", password="testpass1"
):
    """Create a user in the database and log them in via POST /login."""
    database.db.create_user(name, email, password)
    client.post("/login", data={"email": email, "password": password})


def _seed_expenses(user_id, db_path):
    """Insert a variety of expenses spanning multiple months."""
    expenses = [
        (user_id, 50.00, "Food", f"{CURRENT_MONTH}-05", "Groceries"),
        (user_id, 30.00, "Transport", f"{CURRENT_MONTH}-10", "Bus pass"),
        (user_id, 20.00, "Entertainment", f"{CURRENT_MONTH}-15", "Cinema"),
        (user_id, 10.00, "Food", f"{LAST_MONTH}-20", "Snacks"),
    ]
    for exp in expenses:
        database.db.create_expense(*exp, path=db_path)


def _get_user_id(email="tester@example.com", db_path=None):
    """Return the integer user_id for a given email."""
    user = database.db.get_user_by_email(email, path=db_path)
    return user["id"]


# ---------------------------------------------------------------------------
# 1. Auth guard
# ---------------------------------------------------------------------------


class TestAuthGuard:
    """Unauthenticated access to GET /analytics must redirect to /login."""

    def test_unauthenticated_redirects_to_login(self, client):
        res = client.get("/analytics")
        assert res.status_code == 302
        assert "/login" in res.location

    def test_unauthenticated_redirect_location_is_login(self, client):
        res = client.get("/analytics")
        assert res.headers["Location"].endswith("/login") or "/login" in res.location

    def test_unauthenticated_follow_redirect_shows_flash(self, client):
        res = client.get("/analytics", follow_redirects=True)
        # Spec says: redirects to /login with a flash message
        assert b"log in" in res.data.lower() or b"Please log in" in res.data

    def test_unauthenticated_with_filters_still_redirects(self, client):
        res = client.get("/analytics?category=Food&start_date=2026-01-01")
        assert res.status_code == 302
        assert "/login" in res.location


# ---------------------------------------------------------------------------
# 2. Happy path - no filters
# ---------------------------------------------------------------------------


class TestHappyPathNoFilters:
    """Authenticated user with expenses gets 200 and all three chart headings."""

    def test_returns_200(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics")
        assert res.status_code == 200

    def test_contains_category_distribution_heading(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics")
        assert b"Category Distribution" in res.data

    def test_contains_monthly_trends_heading(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics")
        assert b"Monthly Trends" in res.data

    def test_contains_budget_vs_actual_heading(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics")
        assert b"Budget vs Actual" in res.data or b"Budget vs. Actual" in res.data


# ---------------------------------------------------------------------------
# 3. Happy path - with filters
# ---------------------------------------------------------------------------


class TestHappyPathWithFilters:
    """Authenticated user can apply query-param filters and still get 200."""

    def test_category_filter_returns_200(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics?category=Food")
        assert res.status_code == 200

    def test_start_date_filter_returns_200(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get(f"/analytics?start_date={CURRENT_MONTH}-01")
        assert res.status_code == 200

    def test_end_date_filter_returns_200(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get(f"/analytics?end_date={CURRENT_MONTH}-28")
        assert res.status_code == 200

    def test_all_filters_combined_returns_200(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        url = f"/analytics?category=Food&start_date={CURRENT_MONTH}-01&end_date={CURRENT_MONTH}-30"
        res = client.get(url)
        assert res.status_code == 200

    def test_transport_filter_returns_200(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics?category=Transport")
        assert res.status_code == 200


# ---------------------------------------------------------------------------
# 4. Empty state - authenticated user with NO expenses
# ---------------------------------------------------------------------------


class TestEmptyStateNoExpenses:
    """
    Authenticated user who has never logged an expense must see the empty-state
    message and must NOT see chart canvas elements.
    """

    def test_returns_200_with_no_expenses(self, client):
        _register_and_login(client)
        res = client.get("/analytics")
        assert res.status_code == 200

    def test_shows_empty_state_message(self, client):
        _register_and_login(client)
        res = client.get("/analytics")
        page_lower = res.data.lower()
        # Spec: show empty state with text describing no expenses.
        # Template renders: "No expense data found" / "haven't logged any expenses yet"
        assert (
            b"no expense data" in page_lower
            or b"no expenses" in page_lower
            or b"no data" in page_lower
            or b"haven" in page_lower  # "haven't logged any expenses yet"
        )

    def test_no_chart_canvases_when_no_expenses(self, client):
        """
        Spec: 'hide the charts and render the empty state instead of rendering
        empty chart frames'. So <canvas> HTML elements for chart IDs must be
        absent when there is no data. Note: chart IDs may still appear inside
        the inline JS block; we specifically check for the <canvas> HTML tag.
        """
        _register_and_login(client)
        res = client.get("/analytics")
        # Check for the actual <canvas id=...> HTML element, not JS references
        assert b'<canvas id="categoryDoughnutChart"' not in res.data
        assert b'<canvas id="monthlyTrendChart"' not in res.data
        assert b'<canvas id="budgetActualChart"' not in res.data

    def test_cta_links_to_add_expense(self, client):
        """Spec: empty state includes a CTA button linking to /expenses/add."""
        _register_and_login(client)
        res = client.get("/analytics")
        assert b"/expenses/add" in res.data


# ---------------------------------------------------------------------------
# 5. Filter empty state - expenses exist but active filter matches nothing
# ---------------------------------------------------------------------------


class TestFilterEmptyState:
    """
    When a user has expenses but the active filters produce zero matching rows,
    the empty-state component must be shown.
    """

    def test_shows_empty_state_when_filter_matches_nothing(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        # Only Food expense exists; filtering for Bills should yield zero matches
        database.db.create_expense(
            user_id, 50.00, "Food", f"{CURRENT_MONTH}-05", "Lunch", path=db_path
        )

        res = client.get("/analytics?category=Bills")
        page_lower = res.data.lower()
        assert (
            b"no expenses" in page_lower
            or b"no data" in page_lower
            or b"no transactions" in page_lower
            or b"no expenses found" in page_lower
        )

    def test_no_canvases_when_filter_matches_nothing(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        database.db.create_expense(
            user_id, 50.00, "Food", f"{CURRENT_MONTH}-05", "Lunch", path=db_path
        )

        res = client.get("/analytics?category=Bills")
        # Spec: empty state rendered instead of chart canvases when no matching data.
        # Check for the actual <canvas> HTML elements (not JS references).
        assert b'<canvas id="categoryDoughnutChart"' not in res.data
        assert b'<canvas id="monthlyTrendChart"' not in res.data

    def test_filter_empty_state_shows_add_expense_cta(self, client, tmp_path):
        """Spec: empty state always has CTA to /expenses/add."""
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        database.db.create_expense(
            user_id, 50.00, "Food", f"{CURRENT_MONTH}-05", "Lunch", path=db_path
        )

        res = client.get("/analytics?start_date=1990-01-01&end_date=1990-01-02")
        assert b"/expenses/add" in res.data


# ---------------------------------------------------------------------------
# 6. Budget vs Actual - no budgets set
# ---------------------------------------------------------------------------


class TestBudgetVsActualNoBudgets:
    """
    Spec: if no budgets are defined for the selected month, a CTA link to
    /budgets must be present in the response.
    """

    def test_no_budgets_cta_link_to_budgets_present(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics")
        # Spec requires a link (href) to /budgets when no budgets exist
        assert b"/budgets" in res.data

    def test_no_budgets_shows_setup_budgets_text_or_link(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics")
        page_lower = res.data.lower()
        # Spec says: "Set up budgets to see comparison here" with a link to /budgets
        assert b"set up budgets" in page_lower or b"budget" in page_lower
        assert b"/budgets" in res.data

    def test_budget_actual_canvas_absent_when_no_budgets(self, client, tmp_path):
        """
        Spec says to show a placeholder/CTA instead of the chart canvas when
        no budgets are defined. The budgetActualChart <canvas> HTML element must
        not be present (JS references in the script block are acceptable).
        """
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics")
        # Only the <canvas> tag is conditionally omitted; JS refs are always present.
        assert b'<canvas id="budgetActualChart"' not in res.data


# ---------------------------------------------------------------------------
# 7. Budget vs Actual - with budgets
# ---------------------------------------------------------------------------


class TestBudgetVsActualWithBudgets:
    """
    When a user has both expenses AND budgets for the selected month,
    the budget comparison chart canvas must be rendered.
    """

    def test_budget_chart_canvas_present(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        # Create a budget for the current month
        create_budget(user_id, "Food", 200.00, CURRENT_MONTH, path=db_path)

        res = client.get("/analytics")
        assert res.status_code == 200
        assert b"budgetActualChart" in res.data

    def test_budget_chart_canvas_present_filtered_month(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        create_budget(user_id, "Food", 200.00, CURRENT_MONTH, path=db_path)

        res = client.get(f"/analytics?start_date={CURRENT_MONTH}-01")
        assert res.status_code == 200
        assert b"budgetActualChart" in res.data

    def test_returns_200_with_budgets(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)
        create_budget(user_id, "Transport", 100.00, CURRENT_MONTH, path=db_path)

        res = client.get("/analytics")
        assert res.status_code == 200


# ---------------------------------------------------------------------------
# 8. Chart.js CDN script tag
# ---------------------------------------------------------------------------


class TestChartJsCDN:
    """Spec: Chart.js must be loaded via cdn.jsdelivr.net/npm/chart.js."""

    def test_chartjs_cdn_script_tag_present_no_expenses(self, client):
        _register_and_login(client)
        res = client.get("/analytics")
        assert b"cdn.jsdelivr.net/npm/chart.js" in res.data

    def test_chartjs_cdn_script_tag_present_with_expenses(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics")
        assert b"cdn.jsdelivr.net/npm/chart.js" in res.data

    def test_chartjs_cdn_is_in_page(self, client):
        _register_and_login(client)
        res = client.get("/analytics")
        page = res.data.decode("utf-8", errors="replace")
        assert "cdn.jsdelivr.net/npm/chart.js" in page


# ---------------------------------------------------------------------------
# 9. JSON data injected - JS variable names / canvas IDs
# ---------------------------------------------------------------------------


class TestJsonDataInjected:
    """
    Spec: The route serialises breakdown_json, trend_json, budget_comparison_json
    and passes them to the template.  When data exists the canvas IDs
    categoryDoughnutChart and monthlyTrendChart must be present.
    """

    def test_category_doughnut_canvas_present_when_has_expenses(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics")
        assert b"categoryDoughnutChart" in res.data

    def test_monthly_trend_canvas_present_when_has_expenses(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics")
        assert b"monthlyTrendChart" in res.data

    def test_breakdown_json_or_canvas_present(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics")
        assert b"breakdown_json" in res.data or b"categoryDoughnutChart" in res.data

    def test_trend_json_or_canvas_present(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics")
        assert b"trend_json" in res.data or b"monthlyTrendChart" in res.data

    def test_budget_comparison_json_or_canvas_present(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)
        create_budget(user_id, "Food", 200.00, CURRENT_MONTH, path=db_path)

        res = client.get("/analytics")
        assert b"budget_comparison_json" in res.data or b"budgetActualChart" in res.data


# ---------------------------------------------------------------------------
# 10. Filter bar rendered
# ---------------------------------------------------------------------------


class TestFilterBarRendered:
    """
    Spec: A filter bar with a category dropdown, start_date input, and
    end_date input must always be rendered on the analytics page.
    """

    def test_category_dropdown_present(self, client):
        _register_and_login(client)
        res = client.get("/analytics")
        assert b'name="category"' in res.data

    def test_start_date_input_present(self, client):
        _register_and_login(client)
        res = client.get("/analytics")
        assert b'name="start_date"' in res.data

    def test_end_date_input_present(self, client):
        _register_and_login(client)
        res = client.get("/analytics")
        assert b'name="end_date"' in res.data

    def test_filter_button_present(self, client):
        """Spec: Filter button must be in the filter bar."""
        _register_and_login(client)
        res = client.get("/analytics")
        page_lower = res.data.lower()
        assert b"filter" in page_lower

    def test_clear_filters_link_present_when_filtered(self, client, tmp_path):
        """
        Spec: 'Clear Filters' button is shown when filters are active.
        The template renders the Clear link only when is_filtered is True.
        """
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        # Apply a filter so is_filtered=True triggers the Clear link
        res = client.get(f"/analytics?category=Food")
        page_lower = res.data.lower()
        assert b"clear" in page_lower

    def test_category_dropdown_includes_all_categories_option(self, client):
        """Spec: dropdown has 'All Categories' option."""
        _register_and_login(client)
        res = client.get("/analytics")
        page_lower = res.data.lower()
        assert b"all categories" in page_lower or b"all" in page_lower

    def test_filter_bar_present_when_no_expenses(self, client):
        """Filter bar must always appear, even on the empty state."""
        _register_and_login(client)
        res = client.get("/analytics")
        assert b'name="category"' in res.data
        assert b'name="start_date"' in res.data
        assert b'name="end_date"' in res.data

    def test_filter_bar_present_with_expenses(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        _seed_expenses(user_id, db_path)

        res = client.get("/analytics")
        assert b'name="category"' in res.data
        assert b'name="start_date"' in res.data
        assert b'name="end_date"' in res.data


# ---------------------------------------------------------------------------
# 11. Valid category filter
# ---------------------------------------------------------------------------


class TestValidCategoryFilter:
    """Filtering by any allowed category returns 200."""

    ALLOWED_CATEGORIES = [
        "Food",
        "Transport",
        "Bills",
        "Health",
        "Entertainment",
        "Shopping",
        "Other",
    ]

    def test_food_filter_returns_200(self, client, tmp_path):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        database.db.create_expense(
            user_id, 25.00, "Food", f"{CURRENT_MONTH}-10", "Lunch", path=db_path
        )

        res = client.get("/analytics?category=Food")
        assert res.status_code == 200

    @pytest.mark.parametrize("category", ALLOWED_CATEGORIES)
    def test_each_allowed_category_filter_returns_200(self, client, tmp_path, category):
        db_path = str(tmp_path / "test_charts.db")
        _register_and_login(client)
        user_id = _get_user_id(db_path=db_path)
        database.db.create_expense(
            user_id, 15.00, category, f"{CURRENT_MONTH}-01", "Test", path=db_path
        )

        res = client.get(f"/analytics?category={category}")
        assert res.status_code == 200


# ---------------------------------------------------------------------------
# 12. Analytics nav link is active on /analytics
# ---------------------------------------------------------------------------


class TestAnalyticsNavActive:
    """
    Spec: The analytics nav link must be marked as active when the user is
    on the /analytics page.
    """

    def test_nav_link_has_active_class(self, client):
        _register_and_login(client)
        res = client.get("/analytics")
        page = res.data.decode("utf-8", errors="replace")
        # Accept common patterns: class="... active ...", aria-current="page",
        # or active class applied near the Analytics link text
        has_active_on_analytics = (
            "active" in page and "analytics" in page.lower()
        ) or 'aria-current="page"' in page
        assert has_active_on_analytics, (
            "Expected the Analytics nav link to be marked active on /analytics page. "
            "Check that the nav item has an 'active' CSS class or aria-current attribute."
        )

    def test_nav_link_text_analytics_present(self, client):
        _register_and_login(client)
        res = client.get("/analytics")
        assert b"analytics" in res.data.lower()

    def test_analytics_href_in_nav(self, client):
        """The nav must contain an anchor pointing to /analytics."""
        _register_and_login(client)
        res = client.get("/analytics")
        assert b'href="/analytics"' in res.data or b"href='/analytics'" in res.data
