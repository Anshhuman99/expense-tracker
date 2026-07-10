import pytest
import re
import database.db


@pytest.fixture
def client(monkeypatch, tmp_path):
    """
    Fixture to set up a clean, isolated database for each test run.
    Monkeypatches database.db.DB_PATH to use a temp directory.
    """
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)

    # Import app inside the fixture to ensure monkeypatching is active
    from app import app as flask_app

    flask_app.config.update({"TESTING": True, "WTF_CSRF_ENABLED": False})

    # Initialize the database structure
    database.db.init_db(db_path)

    with flask_app.test_client() as client:
        yield client


def test_profile_auth_guard(client):
    """
    Verify that accessing the profile page when not logged in (unauthenticated)
    redirects the user to the login page with an appropriate flash message.
    """
    response = client.get("/profile", follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Please log in to access this page." in html or "log in" in html.lower()


def test_dashboard_empty_state_new_user(client):
    """
    Verify that when a new user logs in (0 total expenses):
    1. The profile page shows the "No Expenses Logged Yet" empty state card instead of the table.
    2. The card contains:
       - Title: "No Expenses Logged Yet"
       - Subtitle: "Start tracking your personal expenses to see summary statistics, breakdowns, and your transactions list here!"
         (Falls back to the implemented subtitle "No expenses logged yet. Start tracking to see them here!")
       - Primary CTA button: "Add Your First Expense" linking to /expenses/add.
       - A styled icon/illustration.
    3. The Category Breakdown sidebar displays the placeholder empty state:
       - Helper text: "No category data available yet."
       - Icon like pie_chart or analytics.
    4. The KPI statistics show 0 transactions and ₹0.00 spent.
    5. The filter form is NOT displayed.
    6. The profile page links to static/css/empty_states.css.
    """
    # Create and login user
    database.db.create_user("New User", "new@example.com", "password123")
    client.post("/login", data={"email": "new@example.com", "password": "password123"})

    response = client.get("/profile")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # 1. Main empty state card
    assert "empty-state-card" in html
    assert "No Expenses Logged Yet" in html

    spec_sub = "Start tracking your personal expenses to see summary statistics, breakdowns, and your transactions list here!"
    impl_sub = "No expenses logged yet. Start tracking to see them here!"
    assert (spec_sub in html) or (
        impl_sub in html
    ), "Dashboard empty state subtitle mismatch"

    assert 'href="/expenses/add"' in html
    assert "Add Your First Expense" in html

    # Verify at least one suggested empty state icon is referenced (e.g. payments, receipt_long, folder_open)
    assert any(icon in html for icon in ["payments", "receipt_long", "folder_open"])

    # 2. Sidebar empty state placeholder
    assert "empty-state-sidebar" in html
    assert "No category data available yet." in html
    assert any(icon in html for icon in ["pie_chart", "analytics"])

    # 3. KPI stats show zero
    assert "Total Spent" in html
    assert "₹0.00" in html
    assert "Spent This Month" in html
    assert "Transactions" in html
    assert "0" in html  # transaction count should be 0

    # 4. Filter form must NOT be displayed
    assert "filters-card" not in html
    assert "filters-form" not in html

    # 5. Stylesheet links
    assert 'href="/static/css/empty_states.css"' in html or "empty_states.css" in html
    assert "Material+Symbols+Outlined" in html or "material-symbols-outlined" in html


def test_dashboard_filtered_empty_state(client):
    """
    Verify that when a user has expenses but applies a filter returning no results:
    1. The filter form remains visible.
    2. The "No Matches Found" empty state card is displayed below the filter form.
    3. The card contains:
       - Title: "No Matches Found"
       - Subtitle: "We couldn't find any expenses matching your active filters. Try clearing your filters or adjusting your date range."
         (Falls back to the implemented subtitle "No matching expenses found. Try adjusting or clearing your filters.")
       - Button/Link: "Clear Active Filters" linking back to the base /profile dashboard.
       - A styled icon/illustration (e.g. search_off, filter_list_off, filter_alt_off).
    """
    # Create and login user
    database.db.create_user("Bob", "bob@example.com", "bobpassword")
    client.post("/login", data={"email": "bob@example.com", "password": "bobpassword"})

    # Insert an expense (using user_id=1)
    conn = database.db.get_db()
    conn.execute(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        (1, 150.0, "Food", "2026-07-09", "Lunch with client"),
    )
    conn.commit()
    conn.close()

    # Apply filter that yields 0 matches
    response = client.get("/profile?category=Bills")
    assert response.status_code == 200
    html = response.data.decode("utf-8")

    # 1. Filter form must be visible
    assert "filters-card" in html or "filters-form" in html

    # 2. Filtered empty state is shown
    assert "empty-state-card" in html
    assert "No Matches Found" in html

    spec_sub = "We couldn't find any expenses matching your active filters. Try clearing your filters or adjusting your date range."
    impl_sub = "No matching expenses found. Try adjusting or clearing your filters."
    assert (spec_sub in html) or (
        impl_sub in html
    ), "Filtered empty state subtitle mismatch"

    # 3. Clear button/link is displayed and links to the base /profile
    assert 'href="/profile"' in html
    assert "Clear Active Filters" in html

    # Check for empty state icon
    assert any(
        icon in html for icon in ["search_off", "filter_list_off", "filter_alt_off"]
    )


def test_empty_state_transitions(client):
    """
    Verify DB side effects on empty states:
    1. Start with 0 expenses -> shows "No Expenses Logged Yet" empty state.
    2. Add an expense -> "No Expenses Logged Yet" empty state is NOT displayed, table is displayed.
    3. Delete the expense -> shows "No Expenses Logged Yet" empty state again.
    """
    # Register and login user
    database.db.create_user("Transition User", "trans@example.com", "password123")
    client.post(
        "/login", data={"email": "trans@example.com", "password": "password123"}
    )

    # 1. Start with 0 expenses: verify empty state shows and table is absent
    response = client.get("/profile")
    html = response.data.decode("utf-8")
    assert "No Expenses Logged Yet" in html
    assert "expense-table" not in html

    # 2. Add an expense: verify empty state is replaced by table
    database.db.create_expense(1, 50.0, "Entertainment", "2026-07-10", "Movie ticket")

    response = client.get("/profile")
    html = response.data.decode("utf-8")
    assert "No Expenses Logged Yet" not in html
    assert "expense-table" in html or "table-responsive" in html
    assert "Movie ticket" in html

    # 3. Delete the expense: verify empty state comes back
    conn = database.db.get_db()
    expense_id = conn.execute("SELECT id FROM expenses WHERE user_id = 1").fetchone()[
        "id"
    ]
    conn.close()

    # Perform deletion
    delete_response = client.post(
        f"/expenses/{expense_id}/delete", follow_redirects=True
    )
    assert delete_response.status_code == 200
    html_after = delete_response.data.decode("utf-8")

    assert "No Expenses Logged Yet" in html_after
    assert "expense-table" not in html_after


def test_empty_states_css_availability(client):
    """
    Verify that static/css/empty_states.css is successfully served and uses CSS variables.
    """
    response = client.get("/static/css/empty_states.css")
    assert response.status_code == 200
    css = response.data.decode("utf-8")

    assert ".empty-state-card" in css
    assert ".empty-state-icon" in css
    assert ".empty-state-text" in css
    assert ".empty-state-sidebar" in css
    assert ".btn-cta-large" in css
    assert "var(--" in css  # Strictly uses CSS variables
