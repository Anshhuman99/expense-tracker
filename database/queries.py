import datetime
from database.db import get_db

def get_user_by_id(user_id, path=None):
    """
    Retrieve user information by user ID.
    Returns a dict with keys: name, email, member_since (formatted as "Month YYYY")
    or None if user does not exist.
    """
    conn = get_db(path)
    try:
        row = conn.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
        if not row:
            return None
        
        # Parse created_at to format as "Month YYYY" (e.g. "June 2026")
        created_str = row["created_at"]
        try:
            date_part = created_str.split()[0]
            dt = datetime.datetime.strptime(date_part, "%Y-%m-%d")
            member_since = dt.strftime("%B %Y")
        except Exception:
            member_since = "Unknown"
            
        return {
            "name": row["name"],
            "email": row["email"],
            "member_since": member_since
        }
    finally:
        conn.close()


def get_summary_stats(user_id, path=None):
    """
    Retrieves summary stats for a given user.
    Returns a dict with:
      - total_spent (float/int): Sum of all expense amounts, default 0
      - transaction_count (int): Total number of expenses, default 0
      - top_category (str): Category with highest total spent, default "—" (U+2014 EM DASH)
    """
    conn = get_db(path)
    try:
        # Query total spent and transaction count
        summary_row = conn.execute(
            "SELECT SUM(amount) as total_spent, COUNT(*) as transaction_count FROM expenses WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        total_spent = summary_row["total_spent"] if summary_row["total_spent"] is not None else 0.0
        transaction_count = summary_row["transaction_count"] if summary_row["transaction_count"] is not None else 0
        
        # Query top category (highest sum of amount spent). Break ties alphabetically.
        top_cat_row = conn.execute(
            """
            SELECT category, SUM(amount) as cat_total 
            FROM expenses 
            WHERE user_id = ? 
            GROUP BY category 
            ORDER BY cat_total DESC, category ASC 
            LIMIT 1
            """,
            (user_id,)
        ).fetchone()
        
        top_category = top_cat_row["category"] if top_cat_row else "—"
        
        return {
            "total_spent": total_spent,
            "transaction_count": transaction_count,
            "top_category": top_category
        }
    finally:
        conn.close()


def get_recent_transactions(user_id, limit=10, path=None):
    """
    Retrieve the most recent transactions (expenses) for a specific user,
    ordered from newest to oldest.
    
    Args:
        user_id (int): The ID of the user.
        limit (int): The maximum number of transactions to return. Default is 10.
        path (str, optional): Custom database file path.
        
    Returns:
        list of dict: A list of transactions containing keys: date, description, category, amount.
    """
    conn = get_db(path)
    try:
        rows = conn.execute(
            """
            SELECT date, description, category, amount 
            FROM expenses 
            WHERE user_id = ? 
            ORDER BY date DESC, id DESC 
            LIMIT ?
            """,
            (user_id, limit)
        ).fetchall()
        
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_category_breakdown(user_id, path=None):
    """
    Retrieves the category breakdown of expenses for a given user.
    Returns a list of dicts, each containing:
      - name: category name
      - amount: total amount spent in this category
      - pct: percentage of total spent, rounded to nearest integer,
             summing to exactly 100% by adjusting the largest category.
    Ordered by amount DESC.
    """
    conn = get_db(path)
    try:
        rows = conn.execute(
            """
            SELECT category AS name, SUM(amount) AS amount
            FROM expenses
            WHERE user_id = ?
            GROUP BY category
            ORDER BY amount DESC
            """,
            (user_id,)
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        return []

    breakdown = [{"name": row["name"], "amount": row["amount"]} for row in rows]
    total_amount = sum(item["amount"] for item in breakdown)
    
    if total_amount > 0:
        # Calculate rounded percentages
        for item in breakdown:
            item["pct"] = int((item["amount"] / total_amount) * 100 + 0.5)
        
        # Adjust for rounding remainder using the largest category (breakdown[0])
        pct_sum = sum(item["pct"] for item in breakdown)
        remainder = 100 - pct_sum
        breakdown[0]["pct"] += remainder
    else:
        for item in breakdown:
            item["pct"] = 0
            
    return breakdown


def get_categories(user_id, path=None):
    """
    Retrieve all unique categories logged by a specific user, sorted alphabetically.
    Returns a list of strings.
    """
    conn = get_db(path)
    try:
        rows = conn.execute(
            "SELECT DISTINCT category FROM expenses WHERE user_id = ? ORDER BY category ASC",
            (user_id,)
        ).fetchall()
        return [row["category"] for row in rows]
    finally:
        conn.close()


def get_filtered_expenses(user_id, category=None, start_date=None, end_date=None, search_query=None, limit=None, path=None):
    """
    Retrieve expenses for a specific user filtered by category, date range, and search text.
    """
    conn = get_db(path)
    try:
        query = "SELECT id, amount, category, date, description FROM expenses WHERE user_id = ?"
        params = [user_id]
        
        if category:
            query += " AND category = ?"
            params.append(category)
            
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
            
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
            
        if search_query:
            query += " AND (description LIKE ? OR category LIKE ?)"
            search_param = f"%{search_query}%"
            params.extend([search_param, search_param])
            
        query += " ORDER BY date DESC, id DESC"
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
            
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

