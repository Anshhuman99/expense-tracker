# Spec: Spending Trends

## Overview

Allow users to compare their spending across different time periods. Specifically, users will be able to select two months (e.g. Month A and Month B) and view a detailed comparison of expenses by category, highlighting absolute and percentage increases or decreases. This helps users understand long-term spending patterns and see where they are increasing or decreasing their expenses.

## Depends on

- Step 15 (Charts Dashboard) — Reuses category aggregations.
- Step 16 (Spending Insights) — Complements general spending statistics.

## Routes

| Method | Path | Description |
|--------|------|-------------|
| GET    | `/trends` | View spending comparison page with selection forms for two months and comparative tables/metrics |

## Database changes

No new database changes or migrations are needed. We can query the `expenses` table directly using existing queries or lightweight parameterized queries to group by category for specific months.

## Templates

### Create
- `templates/trends.html` — Month-over-month comparison page. Contains:
  - Selector forms for Month A (Base Month) and Month B (Comparison Month), defaulting to the previous month and current month respectively.
  - Summary metrics: Total Spent A, Total Spent B, absolute difference, and percentage change.
  - Category breakdown comparison table: Category, Spent in Month A, Spent in Month B, Difference (+$ / -$ and percentage).
  - Visualization: Simple CSS-based bar comparisons or inline percentage difference badges (e.g. green for decrease, red for increase).

### Modify
- `templates/base.html` — Add a link to the spending trends page in the navbar (e.g. "Trends").

## Files to change

- `app.py` — Add `/trends` route. Calculate total spending and category spending for Month A and Month B, compute diffs (percentage and absolute), and send to template.
- `templates/base.html` — Add navigation link.

## Files to create

- `templates/trends.html`
- `static/css/trends.css`

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy / ORMs
- Parameterised queries only
- Handle edge cases: division by zero (when Month A spending in a category is $0), categories present in only one of the months.
- HSL tailored colors for visual indicators (increases/decreases).
- All templates extend `base.html`

## Definition of done

- [ ] User can view `/trends` page
- [ ] User can select any two months to compare using standard selectors
- [ ] Metrics show comparison between the two months (Totals, Category Diffs, Percentages)
- [ ] Handle $0 spending gracefully (e.g., show "N/A" or "+100%" for new category spend)
- [ ] Test cases verify comparison calculations and view rendering
- [ ] All tests pass
