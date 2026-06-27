import pytest
import datetime
import database.db
from flask import session

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
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False
    })
    
    # Initialize the database structure
    database.db.init_db(db_path)
    
    with flask_app.test_client() as client:
        yield client


def test_guest_redirect(client):
    """
    1. Guest redirect:
       Verify that accessing the add expense page (via GET or POST)
       redirects unauthenticated users to the /login page.
    """
    # Test GET redirect
    response_get = client.get("/expenses/add")
    assert response_get.status_code == 302
    assert "/login" in response_get.location

    # Test GET redirect with following redirects (verifying the warning flash message)
    response_get_followed = client.get("/expenses/add", follow_redirects=True)
    assert response_get_followed.status_code == 200
    assert b"Please log in to access this page." in response_get_followed.data

    # Test POST redirect
    response_post = client.post("/expenses/add", data={
        "amount": "100.00",
        "category": "Food",
        "date": "2026-06-25",
        "description": "Unauthorized attempt"
    })
    assert response_post.status_code == 302
    assert "/login" in response_post.location


def test_normal_page_load(client):
    """
    2. Normal page load:
       Verify that GET /expenses/add when logged in renders the add expense form
       with the current date pre-filled and a cancel button pointing to /profile.
    """
    # Create a user and log them in
    database.db.create_user("Alice", "alice@example.com", "securepassword")
    client.post("/login", data={
        "email": "alice@example.com",
        "password": "securepassword"
    })

    # GET the add expense page
    response = client.get("/expenses/add")
    assert response.status_code == 200

    # Verify form elements are rendered
    assert b"Add New Expense" in response.data
    assert b'name="amount"' in response.data
    assert b'name="category"' in response.data
    assert b'name="date"' in response.data
    assert b'name="description"' in response.data
    assert b'type="submit"' in response.data

    # Verify the date input is prefilled with today's date
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    assert f'value="{today_str}"'.encode() in response.data

    # Verify the cancel button points to the profile page
    assert b'href="/profile"' in response.data


def test_validation_errors_and_retention(client):
    """
    3. Validation errors:
       Verify that POSTing with invalid inputs (amount, category, date) shows
       appropriate flash errors and retains user inputs in the HTML.
    """
    # Create a user and log them in
    database.db.create_user("Alice", "alice@example.com", "securepassword")
    client.post("/login", data={
        "email": "alice@example.com",
        "password": "securepassword"
    })

    # Case A: Invalid amount (negative number)
    response_neg_amount = client.post("/expenses/add", data={
        "amount": "-15.50",
        "category": "Food",
        "date": "2026-06-25",
        "description": "Dinner with friends"
    })
    assert response_neg_amount.status_code == 200
    assert b"Amount must be a positive number." in response_neg_amount.data
    # Check retention
    assert b'value="-15.50"' in response_neg_amount.data
    assert b'value="2026-06-25"' in response_neg_amount.data
    assert b'value="Dinner with friends"' in response_neg_amount.data
    assert b'value="Food" selected' in response_neg_amount.data

    # Case B: Invalid amount (non-numeric)
    response_bad_amount = client.post("/expenses/add", data={
        "amount": "abc",
        "category": "Food",
        "date": "2026-06-25",
        "description": "Lunch"
    })
    assert response_bad_amount.status_code == 200
    assert b"Amount must be a valid number." in response_bad_amount.data
    assert b'value="abc"' in response_bad_amount.data

    # Case C: Empty amount
    response_empty_amount = client.post("/expenses/add", data={
        "amount": "",
        "category": "Food",
        "date": "2026-06-25",
        "description": "Lunch"
    })
    assert response_empty_amount.status_code == 200
    assert b"Amount is required." in response_empty_amount.data

    # Case D: Empty category
    response_empty_cat = client.post("/expenses/add", data={
        "amount": "50.00",
        "category": "",
        "date": "2026-06-25",
        "description": "Supplies"
    })
    assert response_empty_cat.status_code == 200
    assert b"Category is required." in response_empty_cat.data
    assert b'value="50.00"' in response_empty_cat.data
    assert b'value="2026-06-25"' in response_empty_cat.data
    assert b'value="Supplies"' in response_empty_cat.data

    # Case E: Invalid category option
    response_bad_cat = client.post("/expenses/add", data={
        "amount": "50.00",
        "category": "Luxury",  # Not in ALLOWED_CATEGORIES
        "date": "2026-06-25",
        "description": "Spa day"
    })
    assert response_bad_cat.status_code == 200
    assert b"Invalid category selected." in response_bad_cat.data
    assert b'value="50.00"' in response_bad_cat.data
    assert b'value="2026-06-25"' in response_bad_cat.data
    assert b'value="Spa day"' in response_bad_cat.data

    # Case F: Empty date
    response_empty_date = client.post("/expenses/add", data={
        "amount": "20.00",
        "category": "Shopping",
        "date": "",
        "description": "T-shirt"
    })
    assert response_empty_date.status_code == 200
    assert b"Date is required." in response_empty_date.data
    assert b'value="20.00"' in response_empty_date.data
    assert b'value=""' in response_empty_date.data or b'name="date" class="form-input" value=""' in response_empty_date.data
    assert b'value="T-shirt"' in response_empty_date.data
    assert b'value="Shopping" selected' in response_empty_date.data

    # Case G: Invalid date format
    response_bad_date = client.post("/expenses/add", data={
        "amount": "20.00",
        "category": "Shopping",
        "date": "25/06/2026",  # Not YYYY-MM-DD
        "description": "Shoes"
    })
    assert response_bad_date.status_code == 200
    assert b"Invalid date format. Use YYYY-MM-DD." in response_bad_date.data
    assert b'value="20.00"' in response_bad_date.data
    assert b'value="25/06/2026"' in response_bad_date.data
    assert b'value="Shoes"' in response_bad_date.data
    assert b'value="Shopping" selected' in response_bad_date.data


def test_success_path_and_stats_update(client):
    """
    4. Success path:
       Verify that posting valid data adds the expense to the database,
       redirects to /profile, shows a success flash message, and updates stats.
    """
    # Create a user and log them in
    database.db.create_user("Alice", "alice@example.com", "securepassword")
    client.post("/login", data={
        "email": "alice@example.com",
        "password": "securepassword"
    })

    # Verify initial stats (empty dashboard)
    profile_initial = client.get("/profile")
    assert profile_initial.status_code == 200
    assert "₹0.00".encode('utf-8') in profile_initial.data
    assert b"No expenses logged yet." in profile_initial.data

    # Today's date to count towards current month
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # Add first expense
    response_1 = client.post("/expenses/add", data={
        "amount": "120.50",
        "category": "Bills",
        "date": today_str,
        "description": "Internet bill"
    }, follow_redirects=True)

    assert response_1.status_code == 200
    assert b"Expense added successfully!" in response_1.data
    assert b"Internet bill" in response_1.data
    assert b"120.50" in response_1.data
    
    # Check that transaction count stats updated to 1
    # Check that total spent is 120.50
    assert b"1" in response_1.data  # transaction count
    assert b"120.50" in response_1.data  # total spent

    # Verify directly in the database
    conn = database.db.get_db()
    expense = conn.execute("SELECT * FROM expenses WHERE description = ?", ("Internet bill",)).fetchone()
    conn.close()
    assert expense is not None
    assert expense["amount"] == 120.50
    assert expense["category"] == "Bills"
    assert expense["date"] == today_str

    # Add second expense to ensure stats accumulate correctly
    response_2 = client.post("/expenses/add", data={
        "amount": "45.00",
        "category": "Food",
        "date": today_str,
        "description": "Office lunch"
    }, follow_redirects=True)

    assert response_2.status_code == 200
    assert b"Expense added successfully!" in response_2.data
    assert b"Office lunch" in response_2.data
    
    # Accumulated stats: Total Spent = 120.50 + 45.00 = 165.50
    # Transaction Count = 2
    assert b"165.50" in response_2.data
    assert b"2" in response_2.data
