# Spec: Spending Insights

## Overview
Generate and present useful spending statistics and actionable insights from the user's logged expenses.
These insights will be shown on a dedicated section or sub-dashboard inside the application (under `GET /insights`) to highlight:
1. **Top Spending Categories**: The category with the highest total spend and its proportion of overall spending.
2. **Monthly Averages**: The average spending per month calculated across all logged months.
3. **Daily Averages**: The average spending per day for the current month.
4. **Spending Trends/Insights Cards**: Dynamic, rule-based text cards detailing:
   - *Month-over-Month Change*: Comparison of current month spending vs. previous month spending.
   - *Highest Single Expense*: Details of the largest single transaction.
   - *Category Warning*: A warning if any category has exceeded 70% of the total monthly spend, or warning if a category has increased by more than 20% compared to the previous month.

---

## Depends on
- Step 1: Database Setup
- Step 2: Registration
- Step 3: Login / Logout
- Step 4: Profile Page Design
- Step 5: Backend Route Profile Page
- Step 6: Data Filter for Profile Page
- Step 7: Add Expense
- Step 8: Edit Expense
- Step 9: Delete Expense
- Step 10: Custom Error Pages
- Step 11: Empty States
- Step 12: Better Flash Messages
- Step 13: Responsive Design
- Step 14: Monthly Budget System
- Step 15: Charts Dashboard

---

## Routes

### `GET /insights`
- Auth required. Redirects to `/login` if not authenticated.
- Queries:
  - Total lifetime spent and total count of transactions.
  - Category breakdown with percentages (reuse `get_category_breakdown`).
  - Monthly average spending.
  - Daily average spending for the current month.
  - Month-over-month comparison stats.
  - Highest single transaction (amount, category, date, description).
  - Category warnings (e.g. category spending exceeding 70% of current month or budget warning integration).
- Renders `templates/insights.html`.

---

## Database changes
No database changes are required. This feature computes insights from existing `expenses` and `budgets` data.

---

## Templates

### Create
- `templates/insights.html`
  - Extends `base.html`.
  - Header: "Spending Insights" with a descriptive sub-header.
  - Layout: Grid of metric cards/widgets.
    - **Overview Card**: Lifetime total spent, total transactions, and overall monthly average.
    - **Monthly Trend Card**: Month-over-month percentage difference.
    - **High Spender Card**: Details of the largest single transaction.
    - **Daily Run Rate Card**: Current month's daily average and projected total for the end of the month.
  - **Dynamic Insights & Tips Section**:
    - A collection of alert-style notification cards generating rule-based insights:
      - *MoM Increase/Decrease*: "Your spending this month is X% higher/lower than last month."
      - *Top Heavy Warning*: "Food accounts for 72% of your overall spending. Consider diversifying or budgeting."
      - *Single Big Purchase*: "Your purchase of [description] on [date] (₹[amount]) was your largest single expense."
  - Navigation: Add active class to "Analytics" or introduce a sub-navigation link or direct button to transition between Charts and Text Insights.
  - Empty State: If no transaction data exists, show an empty state illustration with a button to `/expenses/add`.

---

## Files to change
- `app.py`
  - Add `/insights` route handler. Enforce authentication and calculate or fetch the metrics.
- `database/queries.py`
  - Add `get_highest_expense(user_id)` to find the largest single transaction.
  - Add `get_monthly_averages(user_id)` or retrieve overall start/end months to calculate average monthly spend.
- `templates/base.html`
  - Add a link to the Insights sub-page next to or under Analytics.

---

## Files to create
- `templates/insights.html`
  - The spending insights interface.
- `static/css/insights.css`
  - Visual layout, metric cards, progress bars, and alert badges.

---

## New dependencies
No new dependencies.

---

## Rules for implementation
- No SQLAlchemy/ORMs.
- Parameterised queries only.
- Passwords hashed with werkzeug.
- CSS variables only.
- No hardcoded colours.
- All templates extend `base.html`.
- Round all currency values correctly to 2 decimal places.
- Use semantic HTML tags.

---

## Definition of done
- [ ] `GET /insights` requires auth and redirects unauthenticated users to `/login`.
- [ ] Nav link to "Insights" is present and active when on `/insights`.
- [ ] Displays Lifetime Total Spent, Monthly Average, Current Month Daily Average, and largest single transaction.
- [ ] Custom CSS style variables are used for dark/light mode compatibility.
- [ ] Page renders correctly on mobile, tablet, and desktop viewports.
- [ ] If no expenses exist, shows a clear empty state with a call-to-action to add an expense.
- [ ] All database queries are parameterised and reside in `database/queries.py`.
- [ ] Existing test suites pass successfully.
