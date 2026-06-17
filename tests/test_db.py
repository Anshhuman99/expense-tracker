import pytest
import tempfile
import os
from werkzeug.security import check_password_hash
from database.db import get_db, init_db, seed_db


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


# ── get_db ────────────────────────────────────────────────────────────────────

def test_get_db_returns_connection(db_path):
    conn = get_db(db_path)
    assert conn is not None
    conn.close()


def test_get_db_foreign_keys_on(db_path):
    conn = get_db(db_path)
    result = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    conn.close()
    assert result == 1


def test_get_db_row_factory(db_path):
    conn = get_db(db_path)
    init_db(db_path)
    conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                 ("Test", "t@t.com", "hash"))
    conn.commit()
    row = conn.execute("SELECT name FROM users").fetchone()
    conn.close()
    assert row["name"] == "Test"


# ── init_db ───────────────────────────────────────────────────────────────────

def test_init_db_creates_tables(db_path):
    init_db(db_path)
    conn = get_db(db_path)
    tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    conn.close()
    assert {"users", "expenses"} <= tables


def test_init_db_idempotent(db_path):
    init_db(db_path)
    init_db(db_path)  # must not raise


def test_init_db_unique_email_enforced(db_path):
    import sqlite3
    init_db(db_path)
    conn = get_db(db_path)
    conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", ("A", "a@a.com", "h"))
    conn.commit()
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", ("B", "a@a.com", "h"))
    conn.close()


def test_init_db_foreign_key_enforced(db_path):
    import sqlite3
    init_db(db_path)
    conn = get_db(db_path)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date) VALUES (?, ?, ?, ?)",
            (9999, 10.0, "Food", "2026-06-01")
        )
        conn.commit()
    conn.close()


# ── seed_db ───────────────────────────────────────────────────────────────────

def test_seed_db_inserts_demo_user(db_path):
    init_db(db_path)
    seed_db(db_path)
    conn = get_db(db_path)
    user = conn.execute("SELECT * FROM users WHERE email = ?", ("demo@spendly.com",)).fetchone()
    conn.close()
    assert user is not None
    assert user["name"] == "Demo User"


def test_seed_db_password_is_hashed(db_path):
    init_db(db_path)
    seed_db(db_path)
    conn = get_db(db_path)
    user = conn.execute("SELECT password_hash FROM users").fetchone()
    conn.close()
    assert user["password_hash"] != "demo123"
    assert check_password_hash(user["password_hash"], "demo123")


def test_seed_db_eight_expenses(db_path):
    init_db(db_path)
    seed_db(db_path)
    conn = get_db(db_path)
    count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    conn.close()
    assert count == 8


def test_seed_db_all_categories_present(db_path):
    init_db(db_path)
    seed_db(db_path)
    conn = get_db(db_path)
    cats = {r["category"] for r in conn.execute("SELECT DISTINCT category FROM expenses").fetchall()}
    conn.close()
    assert cats == {"Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"}


def test_seed_db_dates_format(db_path):
    import re
    init_db(db_path)
    seed_db(db_path)
    conn = get_db(db_path)
    dates = [r["date"] for r in conn.execute("SELECT date FROM expenses").fetchall()]
    conn.close()
    pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    assert all(pattern.match(d) for d in dates)


def test_seed_db_idempotent(db_path):
    init_db(db_path)
    seed_db(db_path)
    seed_db(db_path)  # second call must not insert duplicates
    conn = get_db(db_path)
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    expense_count = conn.execute("SELECT COUNT(*) FROM expenses").fetchone()[0]
    conn.close()
    assert user_count == 1
    assert expense_count == 8
