# Spec: Charts Dashboard

## Overview
Transform the placeholder Analytics page into an interactive, visually stunning Charts Dashboard. The dashboard will visualize the user's spending data using frontend interactive charts, reflecting the active dashboard filters (category, start date, and end date). It will display the category distribution, monthly spending trends, and budget vs. actual spending comparison.

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

---

## Routes

### `GET /analytics`
- Auth required. Redirects to `/login` if not authenticated.
- Accepts the following optional query parameters for filtering (identical to the dashboard filters):
  - `category`: Filter expenses by a specific category (Food, Transport, Bills, Health, Entertainment, Shopping, Other).
  - `start_date`: Filter expenses starting from this date (`YYYY-MM-DD`).
  - `end_date`: Filter expenses up to this date (`YYYY-MM-DD`).
- Queries:
  - Fetches the user's filtered expenses using the existing `get_filtered_expenses` helper.
  - Fetches monthly spending trends (aggregated total spent per month for the last 6 months, or for the range of months spanned by the filters if date parameters are present).
  - Fetches budget vs. actual spending for the current month (or the month containing the filter's `start_date` if provided).
- JSON Serialization:
  - Serializes data for the frontend charts into JSON variables passed to the Jinja template, or provides them as lists/dicts.
- Renders `templates/analytics.html`.

---

## Database changes
No database changes.

---

## Templates

### Modify
- `templates/analytics.html`
  - Remove the "Coming Soon" teaser hero section and card grid.
  - Add a Filter Bar at the top of the container matching the design of the Dashboard page filters:
    - Dropdown select for `category` (pre-populated with user's categories/allowed categories, option for "All Categories").
    - Date input for `start_date`.
    - Date input for `end_date`.
    - "Filter" button and "Clear Filters" button.
  - If no transactions exist for the user (or no transactions match the filters), show a clean empty state component with an illustration (Material Symbol) and text saying "No expenses found matching the active filters" or "No expenses logged yet" with a call-to-action button linking to `/expenses/add`.
  - Otherwise, display a grid layout containing three chart cards:
    1. **Category Distribution**: A Doughnut chart visualizing the total and percentage of spending in each category for the filtered dataset.
    2. **Monthly Trends**: A Bar or Line chart showing monthly total spending over the last 6 months (or the duration of the filter range).
    3. **Budget vs. Actual Spending**: A Horizontal Bar chart comparing the monthly budget limit against actual spending in each category for the selected month (using budget data from Step 14).
       - If no budgets are defined for that month, show a subtle placeholder card or tip inside the chart container suggesting the user to "Set up budgets to see comparison here" with a link to `/budgets`.
  - Include the Chart.js CDN script (`https://cdn.jsdelivr.net/npm/chart.js`) in the scripts block (or top header) to avoid installing Python packages.
  - Include inline/external Vanilla JS in `scripts` block to fetch the serialized JSON data and instantiate/render the charts.

---

## Files to change
- `app.py`
  - Modify `/analytics` route handler to enforce auth, parse request arguments, fetch aggregated chart data, and pass data to the template.
- `database/queries.py`
  - Add `get_monthly_spending_trend(user_id, start_date=None, end_date=None)` to aggregate totals grouped by month.
  - Add `get_budget_vs_actual(user_id, month)` to retrieve budget limits vs. actual spending per category for a given month.
- `templates/analytics.html`
  - Completely replace teaser HTML with the new filter form, chart canvas elements, empty states, and Chart.js script setup.
- `static/css/analytics.css`
  - Overhaul stylesheet to support the charts grid layout, filter form, chart card styling, responsive styling, and custom variables matching the design language.

---

## Files to create
No new files are created, since we modify the existing teaser templates/styles.

---

## New dependencies
No new dependencies. We will load `Chart.js` via a standard CDN `<script>` tag in the HTML template.

---

## Rules for implementation
- No SQLAlchemy/ORMs.
- Parameterised queries only.
- Passwords hashed with werkzeug.
- CSS variables only.
- No hardcoded colours.
- All templates extend `base.html`.
- Do not add any new Python packages to `requirements.txt`.
- Chart styling (colors, borders, fonts, tooltips) must be customized using Spendly's CSS theme variables to look premium and integrated, rather than Chart.js default colors.
- Handle empty states gracefully. If there is no expense data, hide the charts and render the empty state instead of rendering empty chart frames.
- Ensure the monthly trend chart sorts months chronologically (e.g. `2026-02`, `2026-03`, `2026-04`...) and handles gaps (months with zero spending) correctly.
- Ensure tooltips display amounts correctly formatted (e.g., currency symbols, rounded to 2 decimal places).
- The charts must dynamically scale and remain responsive on desktop, tablet, and mobile. Use `responsive: true` and `maintainAspectRatio: false` in Chart.js configurations.

---

## Definition of done
- [ ] The `/analytics` route is protected and redirects unauthenticated users to `/login`.
- [ ] The `/analytics` route accepts `category`, `start_date`, and `end_date` query parameters and filters chart data accordingly.
- [ ] Chart.js is loaded successfully via CDN in `templates/analytics.html`.
- [ ] Category Distribution Doughnut chart is rendered and correctly aggregates category totals from the filtered dataset.
- [ ] Monthly Trends chart is rendered and lists total monthly spending sorted chronologically.
- [ ] Budget vs. Actual Horizontal Bar chart is rendered for the selected month, comparing the budget limit to actual spending.
- [ ] A fallback/CTA link to `/budgets` is rendered if no budgets exist for the selected month.
- [ ] Empty state is displayed when no expenses match the active filters, with a CTA to add an expense.
- [ ] Chart tooltips and labels format currency values clearly (e.g., rounded to 2 decimal places).
- [ ] Chart colors and styles match the Spendly CSS design system (no generic default colors).
- [ ] Layout is responsive across mobile, tablet, and desktop (no horizontal scrollbars or distorted canvases).
- [ ] All database queries are parameterised and reside in `database/queries.py`.
- [ ] Existing tests still pass (`pytest`).
