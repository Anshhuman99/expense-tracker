import pytest
import datetime
import sqlite3
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


def create_and_login_user(
    client, name="Alice", email="alice@example.com", password="securepassword"
):
    database.db.create_user(name, email, password)
    login_user(client, email, password)


def login_user(client, email="alice@example.com", password="securepassword"):
    client.post("/login", data={"email": email, "password": password})


def test_auth_guards(client):
    """
    Verify that unauthenticated users are redirected to /login for all budget routes.
    """
    routes = [
        ("/budgets", "GET", None),
        ("/budgets/add", "GET", None),
        (
            "/budgets/add",
            "POST",
            {"category": "Food", "amount": "100.00", "month": "2026-07"},
        ),
        ("/budgets/1/edit", "GET", None),
        (
            "/budgets/1/edit",
            "POST",
            {"category": "Food", "amount": "120.00", "month": "2026-07"},
        ),
        ("/budgets/1/delete", "GET", None),
        ("/budgets/1/delete", "POST", None),
    ]

    for route, method, data in routes:
        if method == "GET":
            res = client.get(route)
        else:
            res = client.post(route, data=data)

        assert res.status_code == 302, f"Route {route} [{method}] did not redirect"
        assert (
            "/login" in res.location
        ), f"Route {route} [{method}] did not redirect to /login"

        # Check followed redirect contains the auth guard flash message
        if method == "GET":
            res_followed = client.get(route, follow_redirects=True)
        else:
            res_followed = client.post(route, data=data, follow_redirects=True)

        assert b"Please log in to access this page." in res_followed.data


def test_get_add_budget_page(client):
    """
    Verify that GET /budgets/add loads correctly for authenticated users
    and pre-populates category options and the current month.
    """
    create_and_login_user(client)

    res = client.get("/budgets/add")
    assert res.status_code == 200

    # Renders forms and fields
    assert b'name="category"' in res.data
    assert b'name="amount"' in res.data
    assert b'name="month"' in res.data

    # Defaults month to current month YYYY-MM
    current_month_str = datetime.date.today().strftime("%Y-%m")
    assert f'value="{current_month_str}"'.encode() in res.data

    # Renders the allowed category options
    from app import ALLOWED_CATEGORIES

    for cat in ALLOWED_CATEGORIES:
        assert f'value="{cat}"'.encode() in res.data


def test_add_budget_validation_failures(client):
    """
    Verify that invalid inputs to POST /budgets/add show flash errors and retain values.
    """
    create_and_login_user(client)

    # 1. Invalid Category
    res = client.post(
        "/budgets/add",
        data={"category": "InvalidCategory", "amount": "100.00", "month": "2026-07"},
    )
    assert res.status_code == 200
    assert b"Please select a valid category." in res.data
    assert b'value="100.00"' in res.data
    assert b'value="2026-07"' in res.data

    # 2. Missing Amount
    res = client.post(
        "/budgets/add", data={"category": "Food", "amount": "", "month": "2026-07"}
    )
    assert res.status_code == 200
    assert b"Amount is required." in res.data
    assert b'value="Food" selected' in res.data or b'value="Food"' in res.data
    assert b'value="2026-07"' in res.data

    # 3. Invalid Amount (non-numeric)
    res = client.post(
        "/budgets/add",
        data={"category": "Food", "amount": "not-a-number", "month": "2026-07"},
    )
    assert res.status_code == 200
    assert b"Amount must be a valid number." in res.data
    assert b'value="not-a-number"' in res.data

    # 4. Non-positive Amount (negative)
    res = client.post(
        "/budgets/add",
        data={"category": "Food", "amount": "-50.00", "month": "2026-07"},
    )
    assert res.status_code == 200
    assert b"Amount must be a positive number." in res.data
    assert b'value="-50.00"' in res.data

    # 5. Non-positive Amount (zero)
    res = client.post(
        "/budgets/add", data={"category": "Food", "amount": "0.00", "month": "2026-07"}
    )
    assert res.status_code == 200
    assert b"Amount must be a positive number." in res.data
    assert b'value="0.00"' in res.data

    # 6. Missing Month
    res = client.post(
        "/budgets/add", data={"category": "Food", "amount": "100.00", "month": ""}
    )
    assert res.status_code == 200
    assert b"Month is required." in res.data
    assert b'value="Food"' in res.data
    assert b'value="100.00"' in res.data

    # 7. Invalid Month Format
    res = client.post(
        "/budgets/add",
        data={"category": "Food", "amount": "100.00", "month": "2026/07"},
    )
    assert res.status_code == 200
    assert b"Invalid month format. Use YYYY-MM." in res.data
    assert b'value="2026/07"' in res.data


def test_add_budget_success(client):
    """
    Verify that a valid budget submission inserts into the db, rounds the amount,
    and redirects with a success flash message.
    """
    create_and_login_user(client)

    res = client.post(
        "/budgets/add",
        data={
            "category": "Food",
            "amount": "150.756",  # should round to 150.76
            "month": "2026-07",
        },
        follow_redirects=True,
    )

    assert res.status_code == 200
    assert b"Budget created successfully!" in res.data
    assert b"Food" in res.data
    assert b"150.76" in res.data

    # Verify db side effects
    conn = database.db.get_db()
    try:
        budget = conn.execute(
            "SELECT * FROM budgets WHERE category = ? AND month = ?",
            ("Food", "2026-07"),
        ).fetchone()
        assert budget is not None
        assert budget["amount"] == 150.76  # Rounded to 2 decimal places
        assert budget["month"] == "2026-07"
    finally:
        conn.close()


def test_add_budget_uniqueness_constraint(client):
    """
    Verify that duplicate budget entries (same user + category + month) are blocked
    with a user-friendly error message, while different users can have the same category+month.
    """
    # 1. Setup User A
    create_and_login_user(client, name="UserA", email="usera@example.com")

    # Add initial budget for User A
    res = client.post(
        "/budgets/add",
        data={"category": "Food", "amount": "100.00", "month": "2026-07"},
    )
    assert res.status_code == 302

    # Attempt to add duplicate budget for User A
    res_dup = client.post(
        "/budgets/add",
        data={"category": "Food", "amount": "200.00", "month": "2026-07"},
    )
    assert res_dup.status_code == 200
    assert b"A budget for this category and month already exists." in res_dup.data

    # Verify User A only has one budget in the database
    conn = database.db.get_db()
    try:
        budgets = conn.execute(
            "SELECT * FROM budgets WHERE category = ? AND month = ?",
            ("Food", "2026-07"),
        ).fetchall()
        assert len(budgets) == 1
        assert budgets[0]["amount"] == 100.00
    finally:
        conn.close()

    # Log out User A and log in User B
    client.get("/logout")
    create_and_login_user(client, name="UserB", email="userb@example.com")

    # Add the same category and month budget for User B (should succeed!)
    res_userb = client.post(
        "/budgets/add",
        data={"category": "Food", "amount": "150.00", "month": "2026-07"},
        follow_redirects=True,
    )
    assert res_userb.status_code == 200
    assert b"Budget created successfully!" in res_userb.data

    # Verify User B has their own budget
    conn = database.db.get_db()
    try:
        budgets_all = conn.execute(
            "SELECT * FROM budgets WHERE category = ? AND month = ?",
            ("Food", "2026-07"),
        ).fetchall()
        assert len(budgets_all) == 2
    finally:
        conn.close()


def test_list_budgets_empty_state(client):
    """
    Verify that if no budgets are set for the month, an empty state is shown.
    """
    create_and_login_user(client)

    # Check default month empty state
    res = client.get("/budgets")
    assert res.status_code == 200
    assert b"No Budgets Set" in res.data
    assert b"Create Your First Budget" in res.data
    assert b'href="/budgets/add"' in res.data


def test_list_budgets_calculations_and_styles(client):
    """
    Verify that budgets show actual spent amount vs limit, percentage, and are color-coded:
    - Normal (<= 75%): status 'ok' -> class 'budget-ok'
    - Warning (75% to 100%): status 'warning' -> class 'budget-warning'
    - Exceeded (> 100%): status 'exceeded' -> class 'budget-exceeded'
    Also verifies that expenses from other months or users are not counted.
    """
    # 1. Setup User A
    create_and_login_user(client, name="UserA", email="usera@example.com")

    # Log in as User A, insert 3 budgets
    client.post(
        "/budgets/add",
        data={"category": "Food", "amount": "100.00", "month": "2026-07"},
    )
    client.post(
        "/budgets/add",
        data={"category": "Transport", "amount": "100.00", "month": "2026-07"},
    )
    client.post(
        "/budgets/add",
        data={"category": "Bills", "amount": "100.00", "month": "2026-07"},
    )

    # Setup database helper for inserting expenses manually (associated with UserA)
    conn = database.db.get_db()
    try:
        user_row = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("usera@example.com",)
        ).fetchone()
        user_a_id = user_row["id"]
    finally:
        conn.close()

    # Insert expenses for User A:
    # 1. Food: 50.00 in 2026-07 -> 50% spent (Status OK)
    database.db.create_expense(user_a_id, 50.00, "Food", "2026-07-05", "Groceries")
    # 2. Transport: 80.00 in 2026-07 -> 80% spent (Status WARNING)
    database.db.create_expense(user_a_id, 80.00, "Transport", "2026-07-06", "Fuel")
    # 3. Bills: 120.00 in 2026-07 -> 120% spent (Status EXCEEDED)
    database.db.create_expense(user_a_id, 120.00, "Bills", "2026-07-07", "Electricity")

    # 4. Food expense in different month (should NOT be counted towards 2026-07 budget)
    database.db.create_expense(
        user_a_id, 40.00, "Food", "2026-08-01", "Later Groceries"
    )

    # 5. Food expense for different user (should NOT be counted)
    database.db.create_user("UserB", "userb@example.com", "securepassword")
    conn = database.db.get_db()
    try:
        user_b_row = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("userb@example.com",)
        ).fetchone()
        user_b_id = user_b_row["id"]
    finally:
        conn.close()
    database.db.create_expense(
        user_b_id, 30.00, "Food", "2026-07-05", "UserB Groceries"
    )

    # GET /budgets?month=2026-07
    res = client.get("/budgets?month=2026-07")
    assert res.status_code == 200

    # Verify category values and statuses
    # Food: 50% spent, status OK (<=75%)
    assert b"budget-ok" in res.data
    assert b"50.0% used" in res.data
    assert b"50.00 remaining" in res.data

    # Transport: 80% spent, status WARNING (75% to 100%)
    assert b"budget-warning" in res.data
    assert b"80.0% used" in res.data
    assert b"20.00 remaining" in res.data

    # Bills: 120% spent, status EXCEEDED (>100%)
    assert b"budget-exceeded" in res.data
    assert b"120.0% used" in res.data
    assert b"20.00 over budget" in res.data


def test_edit_budget_uniqueness_and_retention(client):
    """
    Verify editing a budget checks uniqueness of category + month (excluding the current record),
    validates fields, and retains inputs on validation failures.
    """
    create_and_login_user(client)

    # Add two budgets for test
    client.post(
        "/budgets/add",
        data={"category": "Food", "amount": "100.00", "month": "2026-07"},
    )
    client.post(
        "/budgets/add",
        data={"category": "Bills", "amount": "200.00", "month": "2026-07"},
    )

    conn = database.db.get_db()
    try:
        food_budget = conn.execute(
            "SELECT id FROM budgets WHERE category = ?", ("Food",)
        ).fetchone()
        food_id = food_budget["id"]
    finally:
        conn.close()

    # 1. Edit Food budget to category=Bills (clash with existing Bills budget for 2026-07)
    res_clash = client.post(
        f"/budgets/{food_id}/edit",
        data={"category": "Bills", "amount": "150.00", "month": "2026-07"},
    )
    assert res_clash.status_code == 200
    assert b"A budget for this category and month already exists." in res_clash.data
    # Check retention
    assert b'value="Bills"' in res_clash.data
    assert b'value="150.00"' in res_clash.data

    # 2. Edit Food budget, but keep category=Food, amount=120.00 (Self-exclusion from unique check)
    res_self = client.post(
        f"/budgets/{food_id}/edit",
        data={"category": "Food", "amount": "120.00", "month": "2026-07"},
        follow_redirects=True,
    )
    assert res_self.status_code == 200
    assert b"Budget updated successfully!" in res_self.data
    assert b"120.00" in res_self.data

    # Verify db was updated
    conn = database.db.get_db()
    try:
        budget = conn.execute(
            "SELECT * FROM budgets WHERE id = ?", (food_id,)
        ).fetchone()
        assert budget["amount"] == 120.00
    finally:
        conn.close()


def test_budget_ownership_authorization(client):
    """
    Verify ownership checks on GET and POST for both Edit and Delete routes.
    If a budget doesn't belong to the logged-in user, returns 403.
    Nonexistent budgets return 404.
    """
    # Create User A
    create_and_login_user(client, name="UserA", email="usera@example.com")
    client.post(
        "/budgets/add",
        data={"category": "Food", "amount": "100.00", "month": "2026-07"},
    )

    conn = database.db.get_db()
    try:
        budget = conn.execute(
            "SELECT id FROM budgets WHERE category = ?", ("Food",)
        ).fetchone()
        budget_id = budget["id"]
    finally:
        conn.close()

    # Log out User A and log in User B
    client.get("/logout")
    create_and_login_user(client, name="UserB", email="userb@example.com")

    # Verify User B gets 403 for User A's budget
    assert client.get(f"/budgets/{budget_id}/edit").status_code == 403
    assert (
        client.post(
            f"/budgets/{budget_id}/edit",
            data={"category": "Food", "amount": "150.00", "month": "2026-07"},
        ).status_code
        == 403
    )

    assert client.get(f"/budgets/{budget_id}/delete").status_code == 403
    assert client.post(f"/budgets/{budget_id}/delete").status_code == 403

    # Log out and log back in as User A to test nonexistent budgets (404)
    client.get("/logout")
    login_user(client, email="usera@example.com")

    assert client.get("/budgets/99999/edit").status_code == 404
    assert (
        client.post(
            "/budgets/99999/edit",
            data={"category": "Food", "amount": "150.00", "month": "2026-07"},
        ).status_code
        == 404
    )
    assert client.get("/budgets/99999/delete").status_code == 404
    assert client.post("/budgets/99999/delete").status_code == 404


def test_delete_budget(client):
    """
    Verify deletion of a budget works:
    - GET /budgets/<id>/delete renders confirmation.
    - POST /budgets/<id>/delete removes row, redirects, and flashes message.
    """
    create_and_login_user(client)
    client.post(
        "/budgets/add",
        data={"category": "Food", "amount": "100.00", "month": "2026-07"},
    )

    conn = database.db.get_db()
    try:
        budget = conn.execute(
            "SELECT id FROM budgets WHERE category = ?", ("Food",)
        ).fetchone()
        budget_id = budget["id"]
    finally:
        conn.close()

    # GET confirmation page
    res_get = client.get(f"/budgets/{budget_id}/delete")
    assert res_get.status_code == 200
    assert b"delete" in res_get.data.lower()

    # POST delete
    res_post = client.post(f"/budgets/{budget_id}/delete", follow_redirects=True)
    assert res_post.status_code == 200
    assert b"Budget deleted successfully!" in res_post.data

    # Verify deleted from DB
    conn = database.db.get_db()
    try:
        budget_del = conn.execute(
            "SELECT * FROM budgets WHERE id = ?", (budget_id,)
        ).fetchone()
        assert budget_del is None
    finally:
        conn.close()


def test_init_db_creates_budgets_table_and_constraints(tmp_path):
    """
    Verify that init_db() correctly runs the migrations to create the budgets table
    with all expected columns and UNIQUE constraints.
    """
    db_path = str(tmp_path / "migration_test.db")

    # Run database initialization
    database.db.init_db(db_path)

    conn = database.db.get_db(db_path)
    try:
        # Check budgets table exists
        table_check = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='budgets'"
        ).fetchone()
        assert table_check is not None

        # Check columns
        cursor = conn.execute("PRAGMA table_info(budgets)")
        columns = {col["name"]: col["type"] for col in cursor.fetchall()}

        assert "id" in columns
        assert "user_id" in columns
        assert "category" in columns
        assert "amount" in columns
        assert "month" in columns
        assert "created_at" in columns

        # Insert test users
        conn.execute(
            "INSERT INTO users (id, name, email, password_hash) VALUES (?, ?, ?, ?)",
            (1, "U1", "u1@e.com", "h"),
        )
        conn.execute(
            "INSERT INTO users (id, name, email, password_hash) VALUES (?, ?, ?, ?)",
            (2, "U2", "u2@e.com", "h"),
        )
        conn.commit()

        # Test unique constraint for user+category+month
        conn.execute(
            "INSERT INTO budgets (user_id, category, amount, month) VALUES (?, ?, ?, ?)",
            (1, "Food", 100.0, "2026-07"),
        )
        conn.commit()

        # Same user, category, month -> should fail
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO budgets (user_id, category, amount, month) VALUES (?, ?, ?, ?)",
                (1, "Food", 200.0, "2026-07"),
            )
            conn.commit()

        # Different category, same user, same month -> should succeed
        conn.execute(
            "INSERT INTO budgets (user_id, category, amount, month) VALUES (?, ?, ?, ?)",
            (1, "Bills", 150.0, "2026-07"),
        )

        # Different month, same user, same category -> should succeed
        conn.execute(
            "INSERT INTO budgets (user_id, category, amount, month) VALUES (?, ?, ?, ?)",
            (1, "Food", 100.0, "2026-08"),
        )

        # Different user, same category, same month -> should succeed
        conn.execute(
            "INSERT INTO budgets (user_id, category, amount, month) VALUES (?, ?, ?, ?)",
            (2, "Food", 120.0, "2026-07"),
        )
        conn.commit()

    finally:
        conn.close()
