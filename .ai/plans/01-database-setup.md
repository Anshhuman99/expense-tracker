# Implementation Plan — Database Setup (Step 01)

## Problem Statement
`database/db.py` is a stub. Spendly needs a working SQLite data layer (`get_db`, `init_db`, `seed_db`) that creates `users` and `expenses` tables, seeds demo data once, and initializes on app startup.

## Decisions
- DB filename: `spendly.db` (project root)
- Testing: `tests/test_db.py` with TDD-style tests
- `spendly.db` added to `.gitignore`

## Constraints
- No ORMs; parameterized queries only
- `PRAGMA foreign_keys = ON` on every connection
- Passwords: `werkzeug.security.generate_password_hash`
- `amount` as REAL; dates as `YYYY-MM-DD`
- `seed_db()` idempotent
- Categories: Food, Transport, Bills, Health, Entertainment, Shopping, Other

## Tasks

- [ ] **Task 1** — Save plan to `.claude/plans/01-database-setup.md`
- [ ] **Task 2** — Implement `get_db()` + test scaffolding (`tests/__init__.py`, `tests/test_db.py`)
- [ ] **Task 3** — Implement `init_db()` with schema + tests
- [ ] **Task 4** — Implement `seed_db()` with demo data + tests
- [ ] **Task 5** — Wire `init_db`/`seed_db` into `app.py`
- [ ] **Task 6** — Add `spendly.db` to `.gitignore` and run full test suite
