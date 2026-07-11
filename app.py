from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    g,
    get_flashed_messages,
    abort,
)
import json
from database.db import (
    get_db,
    init_db,
    seed_db,
    create_user,
    get_user_by_email,
    create_expense,
    update_expense,
    delete_expense as db_delete_expense,
)
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
    get_categories,
    get_filtered_expenses,
    get_expense_by_id,
    create_budget,
    get_budget_by_id,
    get_budgets_for_month,
    update_budget,
    delete_budget as db_delete_budget,
    get_month_category_spending,
    get_monthly_spending_trend,
    get_category_spending_breakdown,
)
from werkzeug.security import check_password_hash
import sqlite3
import re
import datetime
import math

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
ALLOWED_CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]

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

        session.clear()
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
    category = request.args.get("category", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    active_filters = {
        "category": category,
        "start_date": start_date,
        "end_date": end_date,
    }

    is_filtered = any([category, start_date, end_date])

    # Retrieve user's logged categories dynamically
    categories = get_categories(user_id)

    # Get live summary stats from database
    summary = get_summary_stats(user_id)

    # Calculate current month's spent amount dynamically
    current_month = datetime.date.today().strftime("%Y-%m")
    conn = get_db()
    month_spent_row = conn.execute(
        "SELECT SUM(amount) FROM expenses WHERE user_id = ? AND date LIKE ?",
        (user_id, f"{current_month}%"),
    ).fetchone()
    month_spent = month_spent_row[0] if month_spent_row[0] is not None else 0.0
    conn.close()

    stats = {
        "total_spent": summary["total_spent"],
        "month_spent": month_spent,
        "total_count": summary["transaction_count"],
        "top_category": summary["top_category"],
    }

    # Retrieve real category breakdown from database
    db_breakdown = get_category_breakdown(user_id)
    breakdown = [
        {"category": item["name"], "total": item["amount"], "percentage": item["pct"]}
        for item in db_breakdown
    ]

    # Retrieve real expenses (filtered up to 100 vs default 10 recent)
    if is_filtered:
        recent_expenses = get_filtered_expenses(
            user_id=user_id,
            category=category,
            start_date=start_date,
            end_date=end_date,
            limit=100,
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
        is_filtered=is_filtered,
    )


@app.route("/analytics")
def analytics():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    # Parse filter parameters
    category = request.args.get("category", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    # Validate date formats if provided
    if start_date:
        try:
            datetime.datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            flash("Invalid start date format. Expected YYYY-MM-DD.", "error")
            start_date = ""
    if end_date:
        try:
            datetime.datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            flash("Invalid end date format. Expected YYYY-MM-DD.", "error")
            end_date = ""

    active_filters = {
        "category": category,
        "start_date": start_date,
        "end_date": end_date,
    }
    is_filtered = any([category, start_date, end_date])

    # Categories for dropdown
    categories = get_categories(user_id)

    # Fetch filtered expenses to check if overall data exists (empty states)
    filtered_expenses = get_filtered_expenses(
        user_id=user_id,
        category=category,
        start_date=start_date,
        end_date=end_date,
    )

    # Use the helper function to query aggregated category totals
    breakdown_data = get_category_spending_breakdown(
        user_id=user_id,
        category=category if category else None,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None,
    )

    # Monthly spending trend
    trend_data = get_monthly_spending_trend(
        user_id=user_id,
        category=category if category else None,
        start_date=start_date if start_date else None,
        end_date=end_date if end_date else None,
    )

    # Budget vs actual: use start_date month or current month
    if start_date:
        try:
            budget_month = datetime.datetime.strptime(start_date, "%Y-%m-%d").strftime(
                "%Y-%m"
            )
        except ValueError:
            budget_month = datetime.date.today().strftime("%Y-%m")
    else:
        budget_month = datetime.date.today().strftime("%Y-%m")

    budgets_for_month = get_budgets_for_month(user_id, budget_month)
    actual_spending = get_month_category_spending(user_id, budget_month)
    budget_comparison = [
        {
            "category": b["category"],
            "budget": round(b["amount"], 2),
            "actual": actual_spending.get(b["category"], 0.0),
        }
        for b in budgets_for_month
    ]

    return render_template(
        "analytics.html",
        categories=categories,
        active_filters=active_filters,
        is_filtered=is_filtered,
        has_data=len(filtered_expenses) > 0,
        breakdown_data=breakdown_data,
        trend_data=trend_data,
        budget_comparison=budget_comparison,
        has_budgets=len(budgets_for_month) > 0,
        budget_month=budget_month,
    )


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    if request.method == "POST":
        amount_str = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date_str = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        has_error = False
        amount = None

        if not amount_str:
            flash("Amount is required.", "error")
            has_error = True
        else:
            try:
                amount = float(amount_str)
                if not math.isfinite(amount) or amount <= 0:
                    flash("Amount must be a positive number.", "error")
                    has_error = True
            except ValueError:
                flash("Amount must be a valid number.", "error")
                has_error = True

        if not category:
            flash("Category is required.", "error")
            has_error = True
        elif category not in ALLOWED_CATEGORIES:
            flash("Invalid category selected.", "error")
            has_error = True

        if not date_str:
            flash("Date is required.", "error")
            has_error = True
        else:
            try:
                datetime.datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                flash("Invalid date format. Use YYYY-MM-DD.", "error")
                has_error = True

        if len(description) > 250:
            flash("Description cannot exceed 250 characters.", "error")
            has_error = True

        if has_error:
            return render_template(
                "add_expense.html",
                amount=amount_str,
                category=category,
                date=date_str,
                description=description,
                categories=ALLOWED_CATEGORIES,
            )

        create_expense(user_id, amount, category, date_str, description)
        flash("Expense added successfully!", "success")
        return redirect(url_for("profile"))

    # GET request
    default_date = datetime.date.today().strftime("%Y-%m-%d")
    return render_template(
        "add_expense.html",
        amount="",
        category="",
        date=default_date,
        description="",
        categories=ALLOWED_CATEGORIES,
    )


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        flash("User session invalid. Please log in again.", "error")
        return redirect(url_for("login"))

    # Fetch the expense
    expense = get_expense_by_id(id)
    if not expense:
        abort(404)

    # Ownership check
    if expense["user_id"] != user_id:
        abort(403)

    if request.method == "POST":
        amount_str = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date_str = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        has_error = False
        amount = None

        if not amount_str:
            flash("Amount is required.", "error")
            has_error = True
        else:
            try:
                amount = float(amount_str)
                if not math.isfinite(amount) or amount <= 0:
                    flash("Amount must be a positive number.", "error")
                    has_error = True
            except ValueError:
                flash("Amount must be a valid number.", "error")
                has_error = True

        if not category:
            flash("Category is required.", "error")
            has_error = True
        elif category not in ALLOWED_CATEGORIES:
            flash("Invalid category selected.", "error")
            has_error = True

        if not date_str:
            flash("Date is required.", "error")
            has_error = True
        else:
            try:
                datetime.datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                flash("Invalid date format. Use YYYY-MM-DD.", "error")
                has_error = True

        if len(description) > 250:
            flash("Description cannot exceed 250 characters.", "error")
            has_error = True

        if has_error:
            return render_template(
                "edit_expense.html",
                expense=expense,
                amount=amount_str,
                category=category,
                date=date_str,
                description=description,
                categories=ALLOWED_CATEGORIES,
            )

        update_expense(id, amount, category, date_str, description)
        flash("Expense updated successfully!", "success")
        return redirect(url_for("profile"))

    # GET request: Load existing values
    return render_template(
        "edit_expense.html",
        expense=expense,
        amount=expense["amount"],
        category=expense["category"],
        date=expense["date"],
        description=expense["description"],
        categories=ALLOWED_CATEGORIES,
    )


@app.route("/expenses/<int:id>/delete", methods=["GET", "POST"])
def delete_expense(id):
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        flash("User session invalid. Please log in again.", "error")
        return redirect(url_for("login"))

    expense = get_expense_by_id(id)
    if not expense:
        abort(404)

    if expense["user_id"] != user_id:
        abort(403)

    if request.method == "POST":
        db_delete_expense(id)
        flash("Expense deleted successfully!", "success")
        return redirect(url_for("profile"))

    # GET request
    return render_template(
        "delete_expense.html",
        expense=expense,
    )


# ------------------------------------------------------------------ #
# Budget Routes & Helpers                                            #
# ------------------------------------------------------------------ #


def validate_budget_data(category, amount_str, month_str):
    """
    Validates category, amount, and month for budget creation/updates.
    Returns (amount, error_messages_list).
    """
    errors = []
    amount = None

    if not category or category not in ALLOWED_CATEGORIES:
        errors.append("Please select a valid category.")

    if not amount_str:
        errors.append("Amount is required.")
    else:
        try:
            amount = float(amount_str)
            if not math.isfinite(amount) or amount <= 0:
                errors.append("Amount must be a positive number.")
        except ValueError:
            errors.append("Amount must be a valid number.")

    if not month_str:
        errors.append("Month is required.")
    else:
        try:
            datetime.datetime.strptime(month_str, "%Y-%m")
        except ValueError:
            errors.append("Invalid month format. Use YYYY-MM.")

    return amount, errors


@app.route("/budgets")
def budgets():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    # Determine selected month (default: current month)
    month = request.args.get("month", "").strip()
    if month:
        # Validate month format; fall back to current month on bad input
        try:
            month_date = datetime.datetime.strptime(month, "%Y-%m")
        except ValueError:
            month_date = datetime.datetime.today()
            month = month_date.strftime("%Y-%m")
    else:
        month_date = datetime.datetime.today()
        month = month_date.strftime("%Y-%m")

    # Calculate previous and next months for navigation links
    if month_date.month == 1:
        prev_month = f"{month_date.year - 1}-12"
    else:
        prev_month = f"{month_date.year}-{month_date.month - 1:02d}"

    if month_date.month == 12:
        next_month = f"{month_date.year + 1}-01"
    else:
        next_month = f"{month_date.year}-{month_date.month + 1:02d}"

    month_label = month_date.strftime("%B %Y")

    # Fetch budgets for this month and actual spending from expenses
    budget_list = get_budgets_for_month(user_id, month)
    spending = get_month_category_spending(user_id, month)

    # Enrich each budget dict with spent amount, percentage, and status
    for b in budget_list:
        spent = spending.get(b["category"], 0.0)
        b["spent"] = round(spent, 2)
        b["percentage"] = (
            round((spent / b["amount"]) * 100, 1) if b["amount"] > 0 else 0.0
        )
        if b["percentage"] > 100:
            b["status"] = "exceeded"
        elif b["percentage"] > 75:
            b["status"] = "warning"
        else:
            b["status"] = "ok"

    return render_template(
        "budgets.html",
        budgets=budget_list,
        month=month,
        month_label=month_label,
        prev_month=prev_month,
        next_month=next_month,
    )


@app.route("/budgets/add", methods=["GET", "POST"])
def add_budget():
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    default_month = datetime.date.today().strftime("%Y-%m")

    if request.method == "POST":
        category = request.form.get("category", "").strip()
        amount_str = request.form.get("amount", "").strip()
        month = request.form.get("month", "").strip()

        amount, errors = validate_budget_data(category, amount_str, month)

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "add_budget.html",
                categories=ALLOWED_CATEGORIES,
                category=category,
                amount=amount_str,
                month=month or default_month,
            )

        try:
            create_budget(user_id, category, amount, month)
            flash("Budget created successfully!", "success")
            return redirect(url_for("budgets", month=month))
        except sqlite3.IntegrityError:
            flash("A budget for this category and month already exists.", "error")
            return render_template(
                "add_budget.html",
                categories=ALLOWED_CATEGORIES,
                category=category,
                amount=amount_str,
                month=month,
            )

    return render_template(
        "add_budget.html",
        categories=ALLOWED_CATEGORIES,
        category="",
        amount="",
        month=default_month,
    )


@app.route("/budgets/<int:id>/edit", methods=["GET", "POST"])
def edit_budget(id):
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    budget = get_budget_by_id(id)
    if not budget:
        abort(404)
    if budget["user_id"] != user_id:
        abort(403)

    if request.method == "POST":
        category = request.form.get("category", "").strip()
        amount_str = request.form.get("amount", "").strip()
        month = request.form.get("month", "").strip()

        amount, errors = validate_budget_data(category, amount_str, month)

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "edit_budget.html",
                budget=budget,
                categories=ALLOWED_CATEGORIES,
                category=category,
                amount=amount_str,
                month=month,
            )

        try:
            update_budget(id, category, amount, month)
            flash("Budget updated successfully!", "success")
            return redirect(url_for("budgets", month=month))
        except sqlite3.IntegrityError:
            flash("A budget for this category and month already exists.", "error")
            return render_template(
                "edit_budget.html",
                budget=budget,
                categories=ALLOWED_CATEGORIES,
                category=category,
                amount=amount_str,
                month=month,
            )

    return render_template(
        "edit_budget.html",
        budget=budget,
        categories=ALLOWED_CATEGORIES,
        category=budget["category"],
        amount=budget["amount"],
        month=budget["month"],
    )


@app.route("/budgets/<int:id>/delete", methods=["GET", "POST"])
def delete_budget_route(id):
    user_id = session.get("user_id")
    if not user_id:
        flash("Please log in to access this page.", "error")
        return redirect(url_for("login"))

    budget = get_budget_by_id(id)
    if not budget:
        abort(404)
    if budget["user_id"] != user_id:
        abort(403)

    if request.method == "POST":
        db_delete_budget(id)
        flash("Budget deleted successfully!", "success")
        return redirect(url_for("budgets", month=budget["month"]))

    return render_template("delete_budget.html", budget=budget)


# ------------------------------------------------------------------ #
# Error Handlers & Testing Routes                                    #
# ------------------------------------------------------------------ #


@app.errorhandler(403)
def forbidden_error(error):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template("errors/500.html"), 500


@app.route("/trigger-500")
def trigger_500():
    if not (app.config.get("TESTING") or app.debug):
        abort(404)
    abort(500)


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
