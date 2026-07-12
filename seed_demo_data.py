import sqlite3
import os
import random
import datetime
import calendar
from werkzeug.security import generate_password_hash

DB_PATH = os.environ.get(
    "DATABASE_PATH",
    os.path.join(os.path.dirname(__file__), "spendly.db"),
)

CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]

# Descriptions for variety
DESCRIPTIONS = {
    "Food": [
        "Grocery Shopping",
        "Swiggy Delivery",
        "Zomato Dinner",
        "Coffee at Starbucks",
        "Lunch with colleagues",
        "Street food",
        "Tea/Snacks",
    ],
    "Transport": [
        "Uber ride",
        "Ola cab",
        "Auto rickshaw fare",
        "Metro smart card recharge",
        "Fuel / Petrol refill",
        "Train ticket",
        "Parking fee",
    ],
    "Bills": [
        "Electricity bill",
        "Mobile recharge",
        "Wi-Fi internet bill",
        "Water bill",
        "Gas refill",
        "Maintenance charges",
    ],
    "Health": [
        "Doctor consultation",
        "Pharmacy medicines",
        "Dental checkup",
        "Lab test",
        "Multi-vitamins",
        "Eye care checkup",
    ],
    "Entertainment": [
        "Movie ticket",
        "Netflix subscription",
        "Spotify premium",
        "Gaming arcade",
        "Concert ticket",
        "Weekend getaway entry",
    ],
    "Shopping": [
        "T-shirt & Jeans",
        "Shoes",
        "Home decor",
        "Electronics accessory",
        "Gift for friend",
        "Books",
        "Office stationery",
    ],
    "Other": [
        "Laundry",
        "Courier charges",
        "Donation",
        "Haircut / Salon",
        "Miscellaneous cash expense",
        "Repairs",
    ],
}


def seed():
    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    cur = conn.cursor()

    # 1. Clean existing expenses and recurring rules
    print("Clearing existing expenses and recurring rules...")
    cur.execute("DELETE FROM expenses")
    cur.execute("DELETE FROM recurring_rules")
    conn.commit()

    # 2. Check/create users
    users = cur.execute("SELECT id, name FROM users").fetchall()
    if not users:
        print("No users found. Creating a default Demo User...")
        cur.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", generate_password_hash("demo123")),
        )
        conn.commit()
        users = cur.execute("SELECT id, name FROM users").fetchall()

    today = datetime.date.today()

    # 3. For each user, seed 300 expenses and 10 recurring rules
    for user in users:
        user_id = user["id"]
        user_name = user["name"]
        print(f"Seeding data for user: {user_name} (ID: {user_id})...")

        # Seed 300 expenses
        expenses_to_insert = []
        for _ in range(300):
            category = random.choice(CATEGORIES)
            description = random.choice(DESCRIPTIONS[category])

            # Random amount based on category
            if category == "Food":
                amount = round(random.uniform(50.0, 800.0), 2)
            elif category == "Transport":
                amount = round(random.uniform(20.0, 500.0), 2)
            elif category == "Bills":
                amount = round(random.uniform(200.0, 3000.0), 2)
            elif category == "Health":
                amount = round(random.uniform(100.0, 2000.0), 2)
            elif category == "Entertainment":
                amount = round(random.uniform(100.0, 1500.0), 2)
            elif category == "Shopping":
                amount = round(random.uniform(200.0, 5000.0), 2)
            else:
                amount = round(random.uniform(50.0, 1000.0), 2)

            # Spread over the past year (365 days)
            days_ago = random.randint(0, 365)
            expense_date = today - datetime.timedelta(days=days_ago)

            expenses_to_insert.append(
                (
                    user_id,
                    amount,
                    category,
                    expense_date.strftime("%Y-%m-%d"),
                    description,
                )
            )

        cur.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            expenses_to_insert,
        )

        # Seed 10 recurring rules
        recurring_rules = [
            (
                15000.0,
                "Bills",
                "Apartment Rent",
                "monthly",
                today - datetime.timedelta(days=60),
            ),
            (
                1500.0,
                "Health",
                "Gym Membership",
                "monthly",
                today - datetime.timedelta(days=45),
            ),
            (
                199.0,
                "Entertainment",
                "Netflix Premium",
                "monthly",
                today - datetime.timedelta(days=30),
            ),
            (
                999.0,
                "Bills",
                "Broadband Internet",
                "monthly",
                today - datetime.timedelta(days=20),
            ),
            (
                50.0,
                "Food",
                "Daily Milk Delivery",
                "daily",
                today - datetime.timedelta(days=10),
            ),
            (
                5.0,
                "Other",
                "Daily Newspaper",
                "daily",
                today - datetime.timedelta(days=10),
            ),
            (
                1200.0,
                "Food",
                "Weekly Groceries",
                "weekly",
                today - datetime.timedelta(days=14),
            ),
            (
                300.0,
                "Transport",
                "Weekly Commute Pass",
                "weekly",
                today - datetime.timedelta(days=14),
            ),
            (
                499.0,
                "Other",
                "Software Subscription",
                "monthly",
                today - datetime.timedelta(days=15),
            ),
            (
                5000.0,
                "Health",
                "Annual Health Insurance",
                "yearly",
                today - datetime.timedelta(days=180),
            ),
        ]

        for amount, category, description, frequency, start_date in recurring_rules:
            cur.execute(
                """
                INSERT INTO recurring_rules (user_id, amount, category, description, frequency, start_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    amount,
                    category,
                    description,
                    frequency,
                    start_date.strftime("%Y-%m-%d"),
                ),
            )

        print(
            f"Successfully seeded 300 expenses and 10 recurring rules for {user_name}."
        )

    conn.commit()
    conn.close()
    print("Database seeding completed successfully.")


if __name__ == "__main__":
    seed()
