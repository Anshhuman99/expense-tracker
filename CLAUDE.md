# CLAUDE.md

# Project Overview

Spendly is a lightweight personal expense tracker built with Flask and SQLite.

The project is intentionally simple, prioritising clean architecture, readability, maintainability, and fundamental web development concepts over unnecessary complexity.

---

# Architecture

Current structure:

```
expense-tracker/
├── app.py                    # All routes — single file, no blueprints
├── requirements.txt          # Pip dependencies
├── Procfile                  # Deployment entrypoint (Gunicorn)
├── spendly.db                # SQLite database — generated dynamically, never committed
├── database/
│   ├── db.py                 # Connection lifecycle & schema helpers only
│   └── queries.py            # All data-fetching / query functions
├── templates/
│   ├── base.html             # Shared layout (navbar, header, flash alerts, footer)
│   ├── landing.html
│   ├── register.html
│   ├── login.html
│   ├── profile.html          # Main dashboard (summary stats, filters, transactions)
│   ├── add_expense.html
│   ├── edit_expense.html
│   ├── delete_expense.html
│   ├── analytics.html        # Analytics teaser page
│   ├── terms.html
│   └── privacy.html
├── static/
│   ├── css/
│   │   ├── style.css
│   │   ├── profile.css
│   │   ├── analytics.css
│   │   ├── add_expense.css
│   │   ├── edit_expense.css
│   │   ├── delete_expense.css
│   │   └── *.css
│   └── js/
│       └── main.js
└── tests/
```

Planned, not yet created — do not assume these exist until the relevant roadmap step introduces them:

- `config.py` (centralised env-based secrets/config) — introduced when Security rules below are implemented
- `uploads/` (receipt storage, outside `static/`) — introduced in Step 25
- `database/migrations/` (numbered schema-change scripts) — introduced with the first new migration
- `templates/errors/` — introduced in Step 10

## Where things belong

- All routes belong inside `app.py`
- Database **connection lifecycle and schema** logic belongs inside `database/db.py`
- All **query functions** (fetching/aggregating data) belong inside `database/queries.py` — do not add new query logic to `db.py`, and do not duplicate a query that already exists in `queries.py`
- Never write SQL inside route functions
- Every page must have its own template
- Every template must extend `base.html`
- Page-specific styling belongs in its own CSS file
- Shared styling belongs in `style.css`
- Vanilla JavaScript only
- Secrets and environment-specific config belong in `config.py` once introduced, loaded from environment variables — never hardcoded

---

# Code Style

## Python

- Follow PEP 8
- Use snake_case everywhere
- Small single-responsibility functions
- Keep route handlers concise

## Templates

- Always use Jinja2
- Always use `url_for()`
- Never hardcode internal URLs
- Never duplicate navbar/footer

## Database

- SQLite only
- Parameterised queries only (`?`)
- Never build SQL using string formatting
- Connection/schema logic in `database/db.py`; query logic in `database/queries.py`
- `amount` is stored as `REAL`. Do not switch this to integer cents without an explicit, approved migration that converts existing production data. Until then, all money arithmetic in Python must use consistent rounding (round to 2 decimal places on every read, write, and calculation) — never rely on raw float math for sums or comparisons
- Store all datetimes in UTC internally; convert to local time only for display; `date` fields use `YYYY-MM-DD` text format

## Error Handling

- Use `abort()` where appropriate
- Never return raw HTML strings
- Flash meaningful error messages via Flask's `flash()` mechanism
- Custom error pages (Step 10) must extend `base.html`

---

# Tech Constraints

## Backend

- Flask only (currently pinned at 3.1.3)
- No Django
- No FastAPI
- No Blueprints

## Database

- SQLite only
- No PostgreSQL
- No MySQL
- No SQLAlchemy
- No ORM

## Frontend

- HTML
- CSS
- Vanilla JavaScript

Do NOT introduce

- React
- Vue
- Angular
- jQuery
- Bootstrap
- Tailwind

unless explicitly instructed.

## Dependencies

Currently approved: `Flask`, `pytest`, `pytest-flask`, `gunicorn`.

Do not install any other new Python package without explicit approval.

If a roadmap step requires a new dependency (e.g. Excel export, PDF generation, CSRF protection, scheduling for recurring expenses):

1. Stop before installing anything
2. State which package is needed and why
3. Wait for explicit confirmation
4. Only then install it and update `requirements.txt`

Keep `requirements.txt` synchronized whenever dependencies change.

Python 3.10+ is assumed.

---

# Current Database

Foreign key constraints are manually enforced on every connection (`PRAGMA foreign_keys = ON`).

## users

- `id` — integer primary key, autoincrement
- `name` — text, not null
- `email` — text, unique, not null
- `password_hash` — text, not null (Werkzeug `generate_password_hash`)
- `created_at` — text timestamp, default `CURRENT_TIMESTAMP`

## expenses

- `id` — integer primary key, autoincrement
- `user_id` — integer, foreign key → `users(id)`
- `amount` — real, not null, positive value (see Database code-style rule above on rounding)
- `category` — text, not null, must be one of the fixed enum below
- `date` — text, not null, `YYYY-MM-DD` format
- `description` — text, optional, max 250 characters
- `created_at` — text timestamp, default `CURRENT_TIMESTAMP`

Database rules

- Never remove existing tables
- Never rename existing columns
- Preserve existing user data
- All foreign keys must remain enabled
- Run `PRAGMA foreign_keys = ON` on every connection
- Any schema change ships as a new numbered file in `database/migrations/` (e.g. `001_add_budgets_table.sql`) — never edit a past migration once applied
- Migrations must be additive and non-destructive; never drop columns or tables that may contain user data
- `spendly.db` is generated dynamically and must never be committed to version control

---

# Validation Rules

These are already enforced in the app and must not be weakened or bypassed by future features:

- `email` — must pass format validation, must be unique
- `password` — minimum 8 characters
- `amount` — must be a positive number
- `category` — must be exactly one of: `Food`, `Transport`, `Bills`, `Health`, `Entertainment`, `Shopping`, `Other`
- `date` — must be a valid `YYYY-MM-DD` string
- `description` — optional, maximum 250 characters

All validation must be enforced server-side regardless of any client-side checks.

---

# Current Features

Implemented

- Landing page
- Registration (email format validation, 8+ character passwords)
- Login (`check_password_hash`)
- Logout / session management (session stores only `user_id` and `name` — never store password hash, email, or other sensitive data in the session)
- Route guards redirecting unauthenticated users to `/login`
- Dashboard (`/profile`): lifetime total, current month total, transaction count, top category, category breakdown with percentages normalised to sum to 100%, filtering by category/date range, recent transactions (10 by default, up to 100 when filters are active)
- Add expense (`/expenses/add`)
- Edit expense (`/expenses/<id>/edit`) — pre-populated, ownership-checked
- Delete expense (`/expenses/<id>/delete`) — confirmation screen before deletion
- Analytics teaser (`/analytics`)
- Terms of Service (`/terms`) and Privacy Policy (`/privacy`) — static, unauthenticated pages; do not add auth/ownership logic to these routes

---

# Planned Feature Roadmap

## Step 10 — Custom Error Pages

Replace Flask's default error pages with branded templates.
Create custom 404 and 500 pages that match Spendly's design, under `templates/errors/`.
Provide helpful navigation back to the application.

---

## Step 11 — Empty States

Display friendly messages when no data is available.
Show illustrations and call-to-action buttons instead of empty tables.
Handle empty dashboards, filters, and search results gracefully.

---

## Step 12 — Better Flash Messages

Standardize all success, warning, and error notifications.
Use consistent styling and clear user-friendly wording.
Ensure every important user action provides immediate feedback.

---

## Step 13 — Responsive Design

Optimize every page for desktop, tablet, and mobile devices.
Improve layouts, tables, forms, and navigation for smaller screens.
Eliminate horizontal scrolling and layout issues.
Verify colour contrast and keyboard navigation while making layout changes.

---

## Step 14 — Monthly Budget System

Allow users to create monthly spending budgets by category.
Display remaining budget and percentage spent using progress bars.
Warn users when spending approaches or exceeds the budget.
Requires a new `budgets` table via migration — do not alter `expenses` or `users`.

---

## Step 15 — Charts Dashboard

Visualize spending data using interactive charts.
Display category distribution, monthly trends, and comparisons.
Charts should reflect active dashboard filters — implement Steps 17–19 (search/sort/pagination) first, or build against current filters only and revisit once those primitives exist.

---

## Step 16 — Spending Insights

Generate useful spending statistics from user data.
Highlight highest spending categories, averages, and trends.
Present insights in a simple dashboard summary.

---

## Step 17 — Search Expenses

Allow users to quickly search their expenses.
Support searching by description and category.
Display matching results instantly and clearly.
Add search logic to `database/queries.py`, reusing existing filtering logic where possible.

---

## Step 18 — Sorting

Allow expenses to be sorted by multiple fields.
Support sorting by date, amount, category, and newest entries.
Provide ascending and descending ordering.

---

## Step 19 — Pagination

Improve performance for users with many expenses.
Display expenses in manageable pages with navigation controls.
Maintain active filters while changing pages.

---

## Step 20 — CSV Export

Allow users to download filtered expenses as CSV files.
Export all important transaction information.
Downloaded files should be spreadsheet compatible.

---

## Step 21 — Excel Export

Generate formatted Excel reports for expense data.
Preserve column headings and readable formatting.
Support exporting filtered results.
Requires a new dependency (e.g. `openpyxl`) — follow the Dependencies approval process before installing.

---

## Step 22 — PDF Reports

Generate printable expense reports in PDF format.
Include summaries, statistics, and transaction history.
Create clean reports suitable for sharing or printing.
Requires a new dependency (e.g. `reportlab` or `weasyprint`) — follow the Dependencies approval process before installing.

---

## Step 23 — Profile Settings

Allow users to manage their personal account.
Support updating profile information and changing passwords.
Require appropriate validation before saving changes, including current-password confirmation for password changes.

---

## Step 24 — Delete Account

Allow users to permanently remove their account.
Require password confirmation before deletion.
Delete all associated expense records safely (cascade via foreign keys, inside a transaction).

---

## Step 25 — Receipt Upload

Allow users to attach receipt images to expenses.
Store uploaded files securely and associate them with transactions.
Provide receipt preview functionality.

Requirements:
- Restrict to an explicit allow-list of file types (e.g. `.jpg`, `.jpeg`, `.png`, `.pdf`)
- Enforce a maximum file size
- Store files in `uploads/`, outside `static/`, never executed or served from a public path directly
- Sanitize filenames and generate internal storage names to prevent path traversal or collisions
- Serve receipts only through an authenticated, ownership-checked route

---

## Step 26 — Recurring Expenses

Support automatically recurring transactions.
Allow daily, weekly, monthly, or yearly recurrence.
Reduce repetitive manual expense entry.
If a scheduling library is needed, follow the Dependencies approval process first.

---

## Step 27 — Spending Trends

Compare spending across different time periods.
Highlight increases and decreases in categories.
Help users understand long-term spending behaviour.

---

## Step 28 — Savings Suggestions

Provide simple rule-based financial recommendations.
Identify overspending patterns and saving opportunities.
Display personalised suggestions on the dashboard.

---

## Step 29 — Dark Mode

Add an optional dark appearance for the application.
Allow users to switch themes from the interface.
Remember the selected preference between sessions.

---

## Step 30 — README Improvements

Create comprehensive project documentation.
Include screenshots, architecture diagrams, setup instructions, and feature overviews.
Prepare a polished GitHub repository suitable for recruiters and portfolio presentation.

---

# Feature Development Rules

For every roadmap step

- One feature per branch
- One spec per feature
- One pull request per feature
- Do not combine roadmap steps
- Reuse existing code whenever possible
- Avoid duplicated logic

If functionality already exists

Extend it.

Do not rewrite it.

---

# UI Rules

Every new page must

- Extend `base.html`
- Use semantic HTML
- Have its own CSS file if necessary
- Work on desktop
- Work on tablet
- Work on mobile
- Meet basic accessibility standards (sufficient colour contrast, keyboard-navigable forms and controls, meaningful labels/alt text)

Never

- Use inline CSS
- Use inline JavaScript
- Hardcode colours

Prefer CSS variables.

Maintain a consistent visual style throughout the application.

---

# Database Rules

Every schema change must

- Preserve existing data
- Ship as a new file in `database/migrations/`, never edited after being applied
- Use integer primary keys
- Use foreign keys where appropriate

Never

- Duplicate tables
- Duplicate data
- Remove production data
- Edit a migration that has already been applied

---

# Security Rules

Always

- Hash passwords with Werkzeug
- Validate all user input server-side (see Validation Rules)
- Authorize ownership before edit/delete
- Escape template output
- Parameterise every SQL query
- Protect authenticated routes
- Include CSRF protection on all state-changing forms (POST/PUT/DELETE) — requires an approved dependency; follow the Dependencies process
- Load `SECRET_KEY` and all other secrets from environment variables (via `config.py` once introduced) — never hardcoded, in dev or production
- Throttle repeated failed login attempts (e.g. simple per-account/IP attempt counter with cooldown)
- Validate uploaded files by type and size, and store them outside any publicly served directory
- Keep `debug=True` disabled in the production (Gunicorn/Procfile) entrypoint

Never

- Store plaintext passwords
- Trust client-side validation
- Expose other users' data
- Concatenate SQL strings
- Commit secrets, `.env` files, or `spendly.db` to version control
- Store sensitive data (password hash, email) in the session — session should hold only `user_id` and `name`

---

# Testing Rules

Each completed feature should include

- Happy path tests
- Validation tests
- Authorization tests (where applicable)
- Database tests (where applicable)

Test isolation

- Tests must run against a temporary/in-memory SQLite database, never `spendly.db`
- Each test run should start from a clean, known schema state

Before marking a feature complete

- Run pytest
- Resolve failures
- Ensure existing functionality still works

---

# Deployment

- Development: `python app.py`, runs on `http://localhost:5001`
- Production: served via Gunicorn per `Procfile`
- Both environments load secrets from environment variables — never hardcoded, never differing in security posture between dev and prod
- `debug=True` must never be enabled in the production entrypoint

---

# Definition of Done

A feature is complete only when

- Implementation finished
- UI complete
- Validation complete
- Error handling complete
- Tests passing
- No duplicated code
- Documentation updated if required
- No console errors
- No unnecessary dependencies introduced
- Any new dependency was explicitly approved and added to `requirements.txt`

---

# Naming Conventions

## Feature Branches

```
feature/<feature-name>
```

Example

```
feature/monthly-budget
```

## Spec Files

```
.ai/settings/specs/14-monthly-budget.md
```

## Migration Files

```
database/migrations/001_add_budgets_table.sql
```

## Templates

```
monthly_budget.html
```

## CSS

```
monthly_budget.css
```

## Functions

```
snake_case
```

## Variables

```
snake_case
```

---

# Subagent Policy

Always

- Use a builtin Explore subagent before implementing new features.
- Use a builtin Plan subagent while in Plan Mode.
- Delegate codebase research before presenting implementation plans.
- Use a verification subagent after implementation to validate results.

---

# Development Commands

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run (development)

```bash
python app.py
```

Application runs on

```
http://localhost:5001
```

## Run (production)

Served via Gunicorn per `Procfile`.

## Tests

Run all

```bash
pytest
```

Run one file

```bash
pytest tests/test_file.py
```

Run one test

```bash
pytest -k "test_name"
```

Verbose

```bash
pytest -s
```

---

# Warnings

Never

- Use SQLAlchemy
- Use an ORM
- Hardcode URLs
- Hardcode colours
- Put SQL inside route handlers
- Use inline CSS
- Use inline JavaScript
- Return raw HTML strings
- Install unnecessary packages
- Install any package without following the Dependencies approval process
- Introduce frontend frameworks
- Break existing functionality while implementing a new feature
- Edit an already-applied database migration
- Convert `amount` to a different type/column without an approved, explicit migration
- Use raw float math for money calculations — always round consistently
- Store or hardcode secrets in source files
- Commit `spendly.db` to version control

Always prefer extending the existing architecture instead of rewriting it.