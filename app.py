from flask import Flask, render_template, request, redirect, url_for, flash, session, g, get_flashed_messages
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email
from werkzeug.security import check_password_hash
import sqlite3
import re

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

app = Flask(__name__)
app.secret_key = "dev-secret-key"

with app.app_context():
    init_db()
    seed_db()


@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        conn = get_db()
        g.user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name:
            flash("Name is required.", "error")
            return render_template("register.html")

        if not email or not EMAIL_REGEX.match(email):
            flash("Invalid email address.", "error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return render_template("register.html")

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")

        try:
            create_user(name, email, password)
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email already registered.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        user = get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid email or password.", "error")
            return render_template("login.html")

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        flash("Logged in successfully.", "success")
        return redirect(url_for("profile"))

    return render_template("login.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))
    
    # TODO (Subagent 2): Retrieve real summary stats from database using get_user_expense_stats
    stats = {
        "total_spent": 391.25,
        "month_spent": 120.00,
        "total_count": 8
    }
    
    # TODO (Subagent 3): Retrieve real category breakdown from database using get_user_category_breakdown
    breakdown = [
        {"category": "Food", "total": 31.25, "percentage": 8.0},
        {"category": "Bills", "total": 120.00, "percentage": 30.7},
        {"category": "Transport", "total": 45.00, "percentage": 11.5},
        {"category": "Entertainment", "total": 60.00, "percentage": 15.3},
        {"category": "Shopping", "total": 85.00, "percentage": 21.7},
        {"category": "Health", "total": 30.00, "percentage": 7.7},
        {"category": "Other", "total": 20.00, "percentage": 5.1}
    ]
    
    # TODO (Subagent 1): Retrieve real recent expenses from database using get_user_recent_expenses
    recent_expenses = [
        {"date": "2026-06-17", "category": "Food", "description": "Dinner", "amount": 18.75},
        {"date": "2026-06-15", "category": "Other", "description": "Miscellaneous", "amount": 20.00},
        {"date": "2026-06-12", "category": "Shopping", "description": "Clothes", "amount": 85.00},
        {"date": "2026-06-10", "category": "Entertainment", "description": "Netflix + cinema", "amount": 60.00},
        {"date": "2026-06-08", "category": "Health", "description": "Pharmacy", "amount": 30.00}
    ]
    
    return render_template(
        "profile.html",
        stats=stats,
        breakdown=breakdown,
        recent_expenses=recent_expenses
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
