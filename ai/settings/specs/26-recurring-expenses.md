# Spec: Recurring Expenses

## Overview

Allow users to define automatically recurring expenses (subscriptions, rent, bills, utility fees, etc.). Users can configure expenses to repeat on a regular schedule: daily, weekly, monthly, or yearly.
The application will periodically check for and generate recurring expenses that are due, automatically adding them to the user's list of expenses.
In the interface, users can see their active recurring expense rules, create new ones, and delete existing ones.

## Depends on

- Step 07 (Add Expense) — Recurring expense rules are structured similarly to standard expenses.
- Step 14 (Monthly Budget System) — Recurring expenses should count towards budgets once generated.

## Routes

| Method | Path | Description |
|--------|------|-------------|
| GET    | `/recurring` | List all active recurring expense rules for the logged-in user |
| GET    | `/recurring/add` | Form to create a new recurring expense rule |
| POST   | `/recurring/add` | Process creation of a new recurring expense rule |
| POST   | `/recurring/<int:rule_id>/delete` | Deletes a recurring expense rule (does not delete already generated expenses) |

## Database changes

Create a database migration file `database/migrations/003_add_recurring_rules_table.sql` to add a new table `recurring_rules`:
- `id` — INTEGER PRIMARY KEY AUTOINCREMENT
- `user_id` — INTEGER, NOT NULL, FOREIGN KEY -> `users(id)` ON DELETE CASCADE
- `amount` — REAL, NOT NULL (positive value)
- `category` — TEXT, NOT NULL (must be one of the standard categories)
- `description` — TEXT, max 250 characters
- `frequency` — TEXT, NOT NULL (one of: `daily`, `weekly`, `monthly`, `yearly`)
- `start_date` — TEXT, NOT NULL (`YYYY-MM-DD` format)
- `last_generated` — TEXT, nullable (`YYYY-MM-DD` format). Tracks when the expense was last created.
- `created_at` — TEXT, DEFAULT `CURRENT_TIMESTAMP`

Also, we can run a check function on user login or dashboard view to generate any due expenses. Generated expenses are inserted into the `expenses` table as standard expenses.
To track which standard expenses were created from recurring rules (optional but useful), we can add a nullable `recurring_rule_id` column to the `expenses` table, or just insert them as normal expenses with a description note. Let's keep it simple: insert them as normal expenses, and optionally store `recurring_rule_id` on the `expenses` table to link them.
Let's add `recurring_rule_id` — INTEGER, nullable, FOREIGN KEY -> `recurring_rules(id)` ON DELETE SET NULL to the `expenses` table in the migration.

## Templates

### Create
- `templates/recurring.html` — List existing recurring rules, showing amount, category, frequency, start date, next due date, and a delete button. Includes a link to add a new rule.
- `templates/add_recurring.html` — Form to create a recurring expense rule. Fields: amount, category, frequency (dropdown: Daily, Weekly, Monthly, Yearly), start date, description.

### Modify
- `templates/base.html` — Add a link to the recurring expenses manager in the navbar (e.g. "Recurring").

## Files to change

- `app.py` — Add `/recurring`, `/recurring/add`, and `/recurring/<id>/delete` routes. Add a helper function `process_due_recurring_expenses(user_id)` called on dashboard load (`/profile`) and other relevant entrypoints.
- `database/queries.py` — Add queries to create, list, and delete recurring rules. Add query to fetch due recurring rules and update `last_generated` date.
- `templates/base.html` — Add navigation link.

## Files to create

- `database/migrations/003_add_recurring_rules_table.sql`
- `templates/recurring.html`
- `templates/add_recurring.html`
- `static/css/recurring.css`

## New dependencies

No new dependencies. Standard Python libraries (`datetime`) will be used to calculate dates and due intervals.

## Rules for implementation

- No SQLAlchemy / ORMs
- Parameterised queries only
- Validate all inputs: frequency must be valid, category must be valid, amount must be positive, start_date must be a valid date
- CSS variables only
- All templates extend `base.html`

## Definition of done

- [ ] Migration runs and creates `recurring_rules` table and adds `recurring_rule_id` to `expenses`
- [ ] User can view their list of recurring rules on `/recurring`
- [ ] User can add a new recurring rule with input validation (amount, category, frequency, start_date)
- [ ] User can delete a recurring rule, which stops future generation but preserves already generated expenses
- [ ] The app automatically generates due expenses when the user logs in or visits the profile dashboard
- [ ] Test cases verify creation, listing, deletion, and auto-generation of recurring expenses
- [ ] All tests pass
