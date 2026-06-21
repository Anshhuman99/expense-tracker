import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spendly.db")


def get_db(path=None):
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path=None):
    conn = get_db(path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT    NOT NULL,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            created_at    TEXT    DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL    NOT NULL,
            category    TEXT    NOT NULL,
            date        TEXT    NOT NULL,
            description TEXT,
            created_at  TEXT    DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()


def create_user(name, email, password, path=None):
    conn = get_db(path)
    try:
        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
    finally:
        conn.close()


def seed_db(path=None):
    conn = get_db(path)
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        conn.close()
        return
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
    )
    user_id = cur.lastrowid
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
    cur.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
    )
    conn.commit()
    conn.close()


def get_user_by_email(email, path=None):
    conn = get_db(path)
    try:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return user
    finally:
        conn.close()


def get_user_expense_stats(user_id, path=None):
    import datetime
    conn = get_db(path)
    try:
        total_spent = conn.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ?", (user_id,)).fetchone()[0] or 0.0
        total_count = conn.execute("SELECT COUNT(*) FROM expenses WHERE user_id = ?", (user_id,)).fetchone()[0] or 0
        current_month = datetime.date.today().strftime("%Y-%m")
        month_spent = conn.execute("SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date LIKE ?", (user_id, f"{current_month}%")).fetchone()[0] or 0.0
        return {
            "total_spent": total_spent,
            "total_count": total_count,
            "month_spent": month_spent
        }
    finally:
        conn.close()


def get_user_category_breakdown(user_id, path=None):
    conn = get_db(path)
    try:
        rows = conn.execute(
            "SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ? GROUP BY category ORDER BY total DESC",
            (user_id,)
        ).fetchall()
        total_spent = sum(row['total'] for row in rows)
        breakdown = []
        for row in rows:
            percentage = (row['total'] / total_spent * 100) if total_spent > 0 else 0
            breakdown.append({
                "category": row["category"],
                "total": row["total"],
                "percentage": round(percentage, 1)
            })
        return breakdown
    finally:
        conn.close()


def get_user_recent_expenses(user_id, limit=5, path=None):
    conn = get_db(path)
    try:
        rows = conn.execute(
            "SELECT id, amount, category, date, description FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT ?",
            (user_id, limit)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


