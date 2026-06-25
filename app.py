from flask import Flask, render_template, request, redirect, url_for, flash, session, g, get_flashed_messages
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email
from database.queries import get_user_by_id, get_summary_stats, get_recent_transactions, get_category_breakdown, get_categories, get_filtered_expenses
from werkzeug.security import check_password_hash
import sqlite3
import re
import datetime

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
    
    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        flash("User session invalid. Please log in again.", "error")
        return redirect(url_for("login"))
        
    # Get active filters from URL query parameters
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()
    
    active_filters = {
        "q": q,
        "category": category,
        "start_date": start_date,
        "end_date": end_date
    }
    
    is_filtered = any([q, category, start_date, end_date])
    
    # Retrieve user's logged categories dynamically
    categories = get_categories(user_id)
    
    # Get live summary stats from database
    summary = get_summary_stats(user_id)
    
    # Calculate current month's spent amount dynamically
    current_month = datetime.date.today().strftime("%Y-%m")
    conn = get_db()
    month_spent_row = conn.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date LIKE ?",
        (user_id, f"{current_month}%")
    ).fetchone()
    month_spent = month_spent_row[0] if month_spent_row[0] is not None else 0.0
    conn.close()
    
    stats = {
        "total_spent": summary["total_spent"],
        "month_spent": month_spent,
        "total_count": summary["transaction_count"],
        "top_category": summary["top_category"]
    }
    
    # Retrieve real category breakdown from database
    db_breakdown = get_category_breakdown(user_id)
    breakdown = [
        {
            "category": item["name"],
            "total": item["amount"],
            "percentage": item["pct"]
        }
        for item in db_breakdown
    ]
    
    # Retrieve real expenses (filtered up to 100 vs default 10 recent)
    if is_filtered:
        recent_expenses = get_filtered_expenses(
            user_id=user_id,
            category=category,
            start_date=start_date,
            end_date=end_date,
            search_query=q,
            limit=100
        )
    else:
        recent_expenses = get_recent_transactions(user_id, limit=10)
        
    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        breakdown=breakdown,
        recent_expenses=recent_expenses,
        categories=categories,
        active_filters=active_filters,
        is_filtered=is_filtered
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
