import pytest
import database.db
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown
)

@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    db_path = str(tmp_path / "test.db")
    monkeypatch.setattr(database.db, "DB_PATH", db_path)
    database.db.init_db(db_path)
    yield db_path


def test_get_user_by_id(isolated_db):
    # Test non-existent id
    assert get_user_by_id(999, path=isolated_db) is None
    
    # Create user
    database.db.create_user("Test User", "test@example.com", "pass1234", path=isolated_db)
    conn = database.db.get_db(isolated_db)
    user_id = conn.execute("SELECT id FROM users WHERE email = ?", ("test@example.com",)).fetchone()["id"]
    conn.close()
    
    # Test valid user
    user = get_user_by_id(user_id, path=isolated_db)
    assert user is not None
    assert user["name"] == "Test User"
    assert user["email"] == "test@example.com"
    # Format should be "Month YYYY", e.g. June 2026
    import datetime
    current_month_year = datetime.date.today().strftime("%B %Y")
    assert user["member_since"] == current_month_year


def test_get_summary_stats_empty(isolated_db):
    database.db.create_user("Test User", "test@example.com", "pass1234", path=isolated_db)
    conn = database.db.get_db(isolated_db)
    user_id = conn.execute("SELECT id FROM users WHERE email = ?", ("test@example.com",)).fetchone()["id"]
    conn.close()
    
    # Test summary stats with no expenses
    stats = get_summary_stats(user_id, path=isolated_db)
    assert stats["total_spent"] == 0
    assert stats["transaction_count"] == 0
    assert stats["top_category"] == "—"


def test_get_summary_stats_populated(isolated_db):
    database.db.create_user("Test User", "test@example.com", "pass1234", path=isolated_db)
    conn = database.db.get_db(isolated_db)
    user_id = conn.execute("SELECT id FROM users WHERE email = ?", ("test@example.com",)).fetchone()["id"]
    
    # Add expenses
    conn.execute("INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                 (user_id, 50.0, "Food", "2026-06-01", "Lunch"))
    conn.execute("INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                 (user_id, 100.0, "Bills", "2026-06-02", "Electric"))
    conn.execute("INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                 (user_id, 50.0, "Food", "2026-06-03", "Dinner"))
    conn.commit()
    conn.close()
    
    stats = get_summary_stats(user_id, path=isolated_db)
    assert stats["total_spent"] == 200.0
    assert stats["transaction_count"] == 3
    assert stats["top_category"] == "Bills"  # Bills (100) vs Food (100), Bills is alphabetically first


def test_get_recent_transactions(isolated_db):
    database.db.create_user("Test User", "test@example.com", "pass1234", path=isolated_db)
    conn = database.db.get_db(isolated_db)
    user_id = conn.execute("SELECT id FROM users WHERE email = ?", ("test@example.com",)).fetchone()["id"]
    
    # Empty case
    assert get_recent_transactions(user_id, path=isolated_db) == []
    
    # Add expenses
    conn.execute("INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                 (user_id, 10.0, "Food", "2026-06-01", "Lunch"))
    conn.execute("INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                 (user_id, 20.0, "Bills", "2026-06-03", "Electric"))
    conn.execute("INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
                 (user_id, 15.0, "Food", "2026-06-02", "Dinner"))
    conn.commit()
    conn.close()
    
    recent = get_recent_transactions(user_id, limit=2, path=isolated_db)
    assert len(recent) == 2
    # Ordered by date DESC, id DESC -> Electric (June 3), Dinner (June 2)
    assert recent[0]["date"] == "2026-06-03"
    assert recent[0]["amount"] == 20.0
    assert recent[1]["date"] == "2026-06-02"
    assert recent[1]["amount"] == 15.0


def test_get_category_breakdown(isolated_db):
    database.db.create_user("Test User", "test@example.com", "pass1234", path=isolated_db)
    conn = database.db.get_db(isolated_db)
    user_id = conn.execute("SELECT id FROM users WHERE email = ?", ("test@example.com",)).fetchone()["id"]
    
    # Empty case
    assert get_category_breakdown(user_id, path=isolated_db) == []
    
    # Add expenses that require rounding adjustment to sum to 100%
    # Food: 31.25, Bills: 120.00, Transport: 45.00, Health: 30.00, Entertainment: 60.00, Shopping: 85.00, Other: 20.00
    # Total: 391.25
    expenses = [
        (user_id, 12.50,  "Food",          "2026-06-01", "Lunch"),
        (user_id, 45.00,  "Transport",     "2026-06-03", "Uber"),
        (user_id, 120.00, "Bills",         "2026-06-05", "Electricity"),
        (user_id, 30.00,  "Health",        "2026-06-08", "Pharmacy"),
        (user_id, 60.00,  "Entertainment", "2026-06-10", "Netflix + cinema"),
        (user_id, 85.00,  "Shopping",      "2026-06-12", "Clothes"),
        (user_id, 20.00,  "Other",         "2026-06-15", "Miscellaneous"),
        (user_id, 18.75,  "Food",          "2026-06-17", "Dinner"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses
    )
    conn.commit()
    conn.close()
    
    breakdown = get_category_breakdown(user_id, path=isolated_db)
    assert len(breakdown) == 7
    # Ordered by amount desc
    assert breakdown[0]["name"] == "Bills"
    assert breakdown[0]["amount"] == 120.00
    
    # Check that sum of percentages is exactly 100
    pct_sum = sum(item["pct"] for item in breakdown)
    assert pct_sum == 100
    
    # Check specific rounded pct
    # Bills expected: 30% (originally 31% before remainder adjustment)
    assert breakdown[0]["pct"] == 30
