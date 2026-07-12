# Spec: Saving Suggestions

## Overview

Provide simple rule-based financial recommendations and saving suggestions for users.
The application will analyze the user's spending habits (such as highest spending category, month-over-month increases, or category spending exceeding 30% of total spending) and generate personalized suggestions to help them save money.
Suggestions will be shown on a dedicated suggestions section/page, and optionally highlighted on the dashboard.

## Depends on

- Step 05 (Backend Route Profile Page) — Reads user expense totals.
- Step 16 (Spending Insights) — Uses general statistical insights.

## Routes

| Method | Path | Description |
|--------|------|-------------|
| GET    | `/suggestions` | Displays personalized rule-based financial saving suggestions |

## Database changes

No new database changes or migrations are needed. We will write queries to analyze expense proportions.

## Templates

### Create
- `templates/suggestions.html` — Personalized recommendations page.
  - Displays a clean layout with suggestion cards.
  - Suggestion Rules to implement:
    1. **High Dining Spend**: If Food spending exceeds 30% of the total monthly spending: suggest cooking at home, packing lunches, and reducing restaurant/delivery orders.
    2. **Over-budget Alert**: If a user's category spend is close to or exceeds their budget (e.g. 90% or more): alert them and suggest specific budget controls.
    3. **MoM Increase Alert**: If category spending in the current month has increased by more than 20% compared to the previous month: flag this category and suggest review.
    4. **Top Category Focus**: Always identify the user's highest spending category and suggest a targeted action.
  - If no expenses exist, display a friendly empty state prompting the user to add expenses to start receiving insights.

### Modify
- `templates/base.html` — Add a link to the savings suggestions page in the navbar (e.g. "Suggestions").
- `templates/profile.html` — (Optional/Recommended) Display a summary teaser or callout highlighting that new saving suggestions are available.

## Files to change

- `app.py` — Add `/suggestions` route. Run analytics rules over database queries and compile a list of suggestions.
- `templates/base.html` — Add navigation link.
- `templates/profile.html` — Link to suggestions dashboard.

## Files to create

- `templates/suggestions.html`
- `static/css/suggestions.css`

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy / ORMs
- Parameterised queries only
- CSS variables only
- All templates extend `base.html`

## Definition of done

- [ ] User can view `/suggestions` page
- [ ] Suggestions are dynamically calculated based on actual user expense data
- [ ] Rules are evaluated correctly (high food spend, top spend category, MoM increases)
- [ ] Empty state handles new users with no expenses safely
- [ ] Test cases verify suggestion calculation rules
- [ ] All tests pass
