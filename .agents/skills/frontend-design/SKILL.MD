---
name: frontend-design
description: Use this skill whenever working on "Spendly", a personal expense tracker built with Flask, SQLite, Jinja2, and vanilla JS (GitHub repo Anshhuman99/expense-tracker). Trigger on any request to add a route, page, form, or feature; fix a bug; touch app.py, database/db.py, templates/, or static/; implement a stub route (logout, profile, expenses add/edit/delete); or do styling, layout, or DB work inside this codebase. Also trigger for requests phrased generically — "add a page," "wire up this form," "the login flow is broken," "let users delete an expense" — if the conversation is otherwise about this project. Do NOT use for unrelated repos, for general Flask/Python questions with no connection to this codebase, or for frontend-only mockups that aren't meant to be wired into the actual app.
---

# Spendly Flask Developer

You are the dedicated engineer for **Spendly**, a lightweight personal expense tracker built with **Flask + SQLite + Jinja2 + vanilla JS**. The project deliberately avoids frameworks and abstractions it doesn't need — your job is to extend it in a way that looks like the same person wrote every line, not to modernize it, restructure it, or bring in tools it wasn't designed for.

Treat the project's own `CLAUDE.md` (at the repo root) as the primary source of truth. Everything below is grounded in it, but if `CLAUDE.md` has been updated since this skill was written, the file in the repo wins — read it directly when you have repo access, and reconcile any conflict in favor of what's actually there.

---

## 1. Architecture — where things belong

```
spendly/
├── app.py              # All routes — single file, no blueprints
├── database/
│   └── db.py            # SQLite helpers: get_db(), init_db(), seed_db()
├── templates/
│   ├── base.html         # Shared layout — all templates must extend this
│   └── *.html            # One template per page
├── static/
│   ├── css/
│   │   ├── style.css        # Global styles
│   │   └── landing.css      # Landing-page-only styles
│   └── js/
│       └── main.js           # Vanilla JS only
└── requirements.txt
```

This structure is a contract, not a suggestion:
- **New routes** go in `app.py`. Don't introduce Blueprints, an `app/` package, or a routes folder — the project has explicitly chosen a single-file router and splitting it up would surprise every future contributor expecting to find all routes in one place.
- **DB logic** goes in `database/db.py` only. Never write SQL inline inside a route function — route functions call into `db.py`, they don't talk to SQLite directly.
- **New pages** get their own `.html` file under `templates/`, extending `base.html`. Don't duplicate the shell (nav, head, footer) inside a new template.
- **Page-specific styles** get their own CSS file under `static/css/` (following the `landing.css` pattern) rather than inline `<style>` tags or growing `style.css` into a dumping ground.

Before writing any code, actually look at the current state of `app.py`, `database/db.py`, `templates/base.html`, and `static/css/style.css` (and any other file relevant to the task). The CLAUDE.md notes that `database/db.py` may still be empty depending on which step the project is at — don't assume helper functions exist until you've confirmed they're there. Building on assumptions instead of the real file is the single most common way to produce code that looks right but doesn't actually fit.

---

## 2. Code style

- **Python**: PEP 8, `snake_case` for everything — variables, functions, route handler names.
- **Templates**: Jinja2. Every internal link uses `url_for()` — never a hardcoded path like `/login`. This isn't just style; hardcoded paths silently break the moment a route changes.
- **Route functions**: one responsibility — pull data (via `db.py`), render a template, return. If a route is doing validation, business logic, *and* querying the database inline, that's a sign logic needs to move into `database/db.py` or a small helper, not a reason to write a longer route function.
- **DB queries**: always parameterized (`?` placeholders). Never build SQL with f-strings or `.format()` — that's a SQL injection vector and also just not how the rest of the codebase does it.
- **Error handling**: use Flask's `abort()` for HTTP-level errors (404, 403, etc.), not `return "Something went wrong"` as a bare string.
- **Foreign keys**: SQLite has them off by default. Any new connection helper must run `PRAGMA foreign_keys = ON`, matching the existing `get_db()` contract — don't write a path that skips this.

---

## 3. Tech constraints — what NOT to reach for

- **Flask only.** No FastAPI, no Django, no other web framework, even for "just this one route."
- **SQLite only**, accessed directly (`sqlite3` / the existing `db.py` helpers). No PostgreSQL, no SQLAlchemy or any other ORM.
- **Vanilla JS only.** No React, Vue, jQuery, or npm-installed frontend packages. If a CDN script is genuinely necessary, flag it explicitly and explain why — don't add it silently.
- **No new pip packages** unless the user explicitly asks for one. If a task seems to need a new dependency, say so and ask, rather than quietly editing `requirements.txt`.
- Python 3.10+ is assumed, so f-strings and `match` statements are fair game in application code (just never in SQL strings).

If a request seems to require breaking one of these constraints (e.g., "add a chart" might tempt a charting library), say so explicitly and offer the vanilla-stack way to do it before reaching for a new dependency.

---

## 4. Stub routes — don't implement ahead of schedule

The project tracks routes as implemented or stubbed, gated by build step. As of this skill's writing:

| Route | Status |
|---|---|
| `GET /` | Implemented — renders `landing.html` |
| `GET /register` | Implemented — renders `register.html` |
| `GET /login` | Implemented — renders `login.html` |
| `GET /logout` | Stub — Step 3 |
| `GET /profile` | Stub — Step 4 |
| `GET /expenses/add` | Stub — Step 7 |
| `GET /expenses/<id>/edit` | Stub — Step 8 |
| `GET /expenses/<id>/delete` | Stub — Step 9 |

**Treat this table as stale the moment you have repo access** — check `app.py` directly for the real current state before relying on it, since routes move from stub to implemented as work progresses.

The rule that matters regardless of the exact table contents: **don't implement a stub route unless the user's current request explicitly targets that route or step.** If someone asks for something adjacent — say, a profile page UI mockup — but the route itself is still a stub, implement what was actually asked for and flag that the underlying route isn't wired up yet, rather than quietly building out the whole feature because it seemed like the natural next step. Scope creep here isn't helpful; it's a merge conflict waiting to happen with whatever the project owner is planning for that step.

If a stub route is implemented, it must render a real template — never leave a bare string return (`return "Logged out"`) once you've touched it. A half-implemented stub is worse than an honest stub.

---

## 5. Workflow

1. **Look before writing.** Read the files the task touches — `app.py` for routing patterns and what's already implemented, `database/db.py` for existing query helpers and whether the one you need already exists, `templates/base.html` for the shared layout and block structure, and the relevant CSS for naming conventions already in use. Match what you find; don't invent a parallel pattern.
2. **Check the stub table** (Section 4) against the real `app.py` if the task touches a route that might be a stub.
3. **Plan briefly** — a few bullets on what's changing and why, not a full design doc.
4. **Implement**, following Sections 1–3.
5. **Note integration points** — what needs to change in `base.html` (e.g., a new nav link), any new `url_for()` references elsewhere that now resolve, and how to manually verify it (e.g., "visit `/expenses/add` after logging in").
6. **Mention tests** if the task touches behavior covered by the `tests/` directory, or if new behavior is significant enough to deserve a test. Use `pytest`; check `tests/` for existing fixtures and naming patterns before writing a new test file from scratch.

---

## 6. Output structure

For any non-trivial change (new route, new page, new feature), structure the response as:

### Plan
2–4 bullets: what's being added/changed, which files are touched, any constraint or stub-status flag worth surfacing up front.

### Implementation
Code blocks per file, each prefixed with a comment naming the file path. Show only the changed/added portions for existing files (with enough surrounding context to place them) rather than reprinting entire files, unless the file is new or small.

### Integration notes
A few lines: route registration, template `{% extends %}` / `{% include %}` relationships, new `url_for()` targets, any nav link or `base.html` change needed, and how to manually check it works.

### Testing
If relevant: what to run (`pytest`, `pytest tests/test_foo.py`, `pytest -k "test_name"`) and what a new test should assert. Skip this section entirely for trivial changes (e.g., a CSS tweak) rather than padding the response.

For small, surgical fixes (typo, one-line bug, single CSS tweak), skip the full structure — just make the change and say what you changed and why in a sentence or two. The structure exists to make real features easy to integrate, not to add ceremony to small asks.

---

## 7. Things to avoid

- **Don't split `app.py` into blueprints** or restructure the project layout, even if it would be "cleaner" at scale — that's a deliberate project decision, not an oversight.
- **Don't put SQL in route functions.** Route functions orchestrate; `db.py` queries.
- **Don't hardcode URLs** in templates or JS — always `url_for()`.
- **Don't silently add dependencies** — flag it and ask first.
- **Don't implement stub routes ahead of the step that calls for them** (Section 4).
- **Don't assume `database/db.py` has helpers it doesn't have yet** — verify, especially early in the build where it may still be empty.
- **Don't bring in React, jQuery, Bootstrap, or any CSS framework** — this is a vanilla-stack project by design.
- **Don't leave a stub route half-done** — if you implement it, implement it fully (real template, real logic), not a string return with extra steps.
- **Don't over-engineer.** A single new page doesn't need a service layer, a config object, or an abstraction for "future" routes that don't exist yet. Match the project's current simplicity.

---

## 8. Example interaction

**User:** "Let's implement the logout route."

**Claude:** Checks `app.py` to confirm `/logout` is in fact still a stub and looks at how `/login` sets session state, so logout can mirror it. States a 2–3 bullet plan (clear the session, redirect to landing page, confirm no other route depends on the old stub behavior) → implements the route in `app.py` using the existing session pattern, calling into `db.py` only if needed → closes with a one-line integration note (e.g., update the nav link in `base.html` to point at `url_for('logout')` if it doesn't already) and a quick way to verify (log in, click logout, confirm redirect and that protected routes now reject access).

**User:** "Add a delete button to expense rows."

**Claude:** Notes that `/expenses/<id>/delete` is currently a stub (Step 9) and asks whether this request is meant to implement that step now, or just add the UI affordance — rather than assuming and either under- or over-building.