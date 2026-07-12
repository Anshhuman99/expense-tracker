# Spendly Codebase Architecture & /teamwork-preview Agent Orchestration Framework

This comprehensive report details the technical architecture of the **Spendly** personal expense tracking application and the coordination protocols of the **`/teamwork-preview`** multi-agent orchestration framework.

---

## Part 1: Spendly Codebase Architecture

Spendly is a lightweight personal finance web application built using Python, Flask, and SQLite. The design focuses on simplicity, readability, and a strict separation of concerns between route handlers, connection lifecycle management, and database query executions.

### 1. Technical Stack
* **Language & Runtime**: Python 3.10+
* **Web Framework**: Flask 3.1.3 (utilizing session-based authentication, cookie-based sessions, and dynamic route parsing).
* **Database Engine**: SQLite3 (accessed via Python's standard library `sqlite3` driver).
* **Frontend Layer**: Semantic HTML5 templates powered by the Jinja2 engine, styled with CSS3 variables supporting native Dark Theme and media queries for responsive layouts. Interaction is driven by vanilla modern client-side JavaScript.
* **Libraries & File Exports**:
  * `openpyxl`: Used to generate formatted Excel spreadsheets.
  * `reportlab`: Used for dynamic PDF document creation, implementing a two-pass page calculation.
  * `csv`: In-memory comma-separated values generation.

### 2. File Layout & Organization
The codebase maintains a clean flat-file layout:
```
expense-tracker/
├── app.py                    # Application entrypoint & all route handlers
├── requirements.txt          # Python dependencies (Flask, pytest, gunicorn, openpyxl, reportlab)
├── Procfile                  # Gunicorn entrypoint for production deployments
├── database/
│   ├── db.py                 # Connection lifecycle, initialization, schema setup
│   └── queries.py            # Data-fetching, aggregation, filters, and mutations
├── static/
│   ├── css/
│   │   ├── style.css         # Global styles, variables, typography, reset, components
│   │   └── *.css             # Page-specific styling (profile, analytics, budgets, errors, etc.)
│   └── js/
│       └── main.js           # Vanilla JavaScript for UI (theme switching, chart rendering)
├── templates/
│   ├── base.html             # Shared layout (navbar, alerts, footer, theme support)
│   ├── landing.html          # Unauthenticated landing page
│   ├── register.html         # User registration form
│   ├── login.html            # User login form
│   ├── profile.html          # Dashboard (main transaction tracker, filters, recent table)
│   ├── analytics.html        # Main analytics layout
│   ├── add_expense.html      # Expense creation form
│   ├── edit_expense.html     # Pre-populated expense editor
│   ├── delete_expense.html   # Delete confirmation screen
│   ├── errors/
│   │   ├── 404.html          # Custom Page Not Found page
│   │   └── 500.html          # Custom Server Error page
│   └── ...
└── tests/                    # pytest suite (unit, integration, routing, and schema verification)
```

---

### 3. Backend Architecture: Route Handlers (`app.py`)
All HTTP request routes are declared in `app.py`. The application strictly avoids Blueprints or nested directory routing to keep the control flow linear.

* **Authentication & Guards**:
  * `/register`: Validates user inputs (non-empty name, email syntax via regex, minimum 8-character passwords). Hashes password hashes using Werkzeug's `generate_password_hash` prior to insertion.
  * `/login`: Retrieves user by email, checks hash compatibility using `check_password_hash`, clears previous session data, sets `session["user_id"]` and `session["user_name"]`, and redirects to `/profile`.
  * `/logout`: Terminates user sessions.
  * *Session Guards*: Custom decorator checks check that `session["user_id"]` exists on authenticated routes. If absent, the user is redirected to `/login`.
* **Dashboard & Filtering (`/profile`)**:
  * Retrieves summary metrics (lifetime spent, transaction count, top category, breakdown percentages).
  * Automatically invokes the background recurring engine to generate any due scheduled expenses.
  * Supports parameterized database searching (category, date range, description keyword), sorting, and pagination.
* **Expense Management (`/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`)**:
  * Verifies ownership by confirming the expense `user_id` matches the active `session["user_id"]`.
  * Sanitizes inputs: verifies amounts are positive floats (rounded to two decimal places) and categories match the allowed list.
  * Handles receipt image uploads: validates file extension (JPG, PNG, PDF), size (capped at 5MB), and assigns a secure UUID-prefixed file name to save under `uploads/` (outside public paths).
* **Document Exports (`/expenses/export/csv`, `/expenses/export/excel`, `/expenses/export/pdf`)**:
  * **CSV Formula Injection Defense**: Implements value sanitization (`_sanitize_csv_value`). If an exported field begins with standard formula prefixes (`=`, `+`, `-`, `@`), a single quote (`'`) is prepended to prevent execution in client spreadsheet software.
  * **Dynamic PDF Generation**: reportlab builds tables dynamically and uses a custom `NumberedCanvas` class to perform a double-pass calculation to draw accurate "Page X of Y" counters in the footer.
* **Monthly Budget System (`/budgets`, `/budgets/add`, `/budgets/<id>/edit`, `/budgets/<id>/delete`)**:
  * Manages category-specific limits per month (YYYY-MM).
  * Calculates and displays remaining budget margins and alerts when spending exceeds 75% or 100%.
* **Recurring Expense Generation (`/recurring`, `/recurring/add`, `/recurring/<id>/delete`)**:
  * Allows creating rules for daily, weekly, monthly, or yearly transactions.
* **Account Settings & Deletion (`/settings`, `/settings/profile`, `/settings/password`, `/account/delete`)**:
  * Profile edits require valid unique emails.
  * Password changes require current password confirmation.
  * Account deletion performs a cascading file and database cleanup inside a database transaction block.

---

### 4. Connection Lifecycle & Schema (`database/db.py`)
This file is the single source of truth for the database connection lifecycle, table schema definition, and connection-level writes.

* **Connection Factory (`get_db`)**:
  * Connects to SQLite using the `sqlite3` driver.
  * Instantiates the custom row factory (`conn.row_factory = sqlite3.Row`) to support column access by name.
  * **Crucial Rule**: Forcefully runs `PRAGMA foreign_keys = ON` on every connection to maintain relational integrity.
* **Initialization & Migrations (`init_db`)**:
  * Sets up the core `users` and `expenses` tables.
  * Auto-reads and executes SQL migration scripts from the `database/migrations/` directory in alphanumeric sorted order.
  * Traps duplication errors (such as "duplicate column name") to ensure migrations are idempotent and additive.
* **Low-Level Mutations**:
  * Defines basic insert and delete functions (`create_user`, `create_expense`, `update_expense`, `delete_expense`) that handle connection closing safely within `try...finally` blocks.

---

### 5. Fetching and Aggregating Data (`database/queries.py`)
All SELECT queries, analytical aggregations, statistics, sorting, and search logic are isolated in `queries.py`.
* **Summary Statistics (`get_summary_stats`)**:
  * Computes total spent, transaction counts, and selects the top category using `GROUP BY category ORDER BY SUM(amount) DESC, category ASC LIMIT 1`.
* **Recent & Filtered Transactions (`get_recent_transactions`, `get_filtered_expenses`)**:
  * Dynamically compiles WHERE clauses based on category, date range, and search parameters.
  * **SQL Injection Prevention**: Safe sorting is accomplished by validating the user-provided sort columns against a hardcoded whitelist (`date`, `category`, `amount`).
  * Counts total records to provide accurate pagination.
* **Budget Tracking (`get_budgets_for_month`)**:
  * Aggregates expenses by month and joins them with budgets to compute the percentage spent.
* **Analytics and Trends (`get_monthly_spending_trend`, `get_category_spending_breakdown`, `get_highest_expense`)**:
  * Aggregates financial history across time periods to build graphs.
* **Account Erasure (`delete_user_account`)**:
  * Conducts data wiping across all related tables (`expenses`, `budgets`, `recurring_rules`, `users`) inside a strict database transaction.

---

### 6. Frontend Styling Architecture (`static/css/style.css`)
The visual language is defined by variables (design tokens) inside `style.css`.
* **CSS Custom Properties (Variables)**:
  * Colors: `--ink`, `--paper`, `--paper-card`, `--accent`, `--border`.
  * Theme Colors: `--success`, `--danger`, `--budget-ok`, `--budget-warning`, `--budget-exceeded`.
  * Category Badge Colors: Specific background and border colors for categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other).
  * Typography: Display and body font variables, spacing scale, border-radii.
* **Theme Support**:
  * Toggles design tokens under a `[data-theme="dark"]` selector.
  * Includes a `@media print` fallback block that forces light colors to save ink during print operations.
* **Global Rules**:
  * Standard box-sizing resets, typography sizing, navbar container layout, cards, layouts, utility classes, and buttons.
* **Page-Specific Refinements**:
  * Modules like `profile.css` (summary widgets, transaction lists), `analytics.css` (charts layout), `empty_states.css` (illustrated placeholders), and `flash_messages.css` (standardized alerts).

---

## Part 2: Database Schema & Relational Constraints

Spendly avoids ORMs, using raw SQLite parameters and explicit constraints to ensure safety and data consistency.

### 1. Database Table Diagrams & Rules
All database tables enforce column constraints, default values, and foreign keys.

#### A. Users Table (`users`)
```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    UNIQUE NOT NULL,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    DEFAULT (datetime('now'))
);
```
* **relational role**: Parent table. The `email` field is enforced unique to prevent multiple registrations under the same address.

#### B. Expenses Table (`expenses`)
```sql
CREATE TABLE expenses (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id            INTEGER NOT NULL REFERENCES users(id),
    amount             REAL    NOT NULL,
    category           TEXT    NOT NULL,
    date               TEXT    NOT NULL,
    description        TEXT,
    receipt_path       TEXT,
    recurring_rule_id  INTEGER REFERENCES recurring_rules(id) ON DELETE SET NULL,
    created_at         TEXT    DEFAULT (datetime('now'))
);
```
* **relational role**: Child table linking to `users` and `recurring_rules`. If a user is deleted, physical file triggers are processed before database cascading. If a recurring rule is deleted, related generated expenses persist (`ON DELETE SET NULL`).

#### C. Budgets Table (`budgets`)
```sql
CREATE TABLE budgets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id),
    category    TEXT    NOT NULL,
    amount      REAL    NOT NULL,
    month       TEXT    NOT NULL,
    created_at  TEXT    DEFAULT (datetime('now')),
    UNIQUE(user_id, category, month)
);
```
* **relational role**: Child table. The multi-column constraint `UNIQUE(user_id, category, month)` prevents duplicate budget allocations for the same category within the same month.

#### D. Recurring Rules Table (`recurring_rules`)
```sql
CREATE TABLE recurring_rules (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount         REAL    NOT NULL,
    category       TEXT    NOT NULL,
    description    TEXT,
    frequency      TEXT    NOT NULL,
    start_date     TEXT    NOT NULL,
    last_generated TEXT,
    created_at     TEXT    DEFAULT (datetime('now'))
);
```
* **relational role**: Child table representing scheduled tasks. Cascades deletions (`ON DELETE CASCADE`) to clean up rules when a user deletes their account.

### 2. Integrity and Arithmetic Rules
1. **No ORM Strategy**: Queries use parameterized values (`?`) only. Concatenating strings to assemble SQL expressions is prohibited.
2. **Precision Accounting**: Monetary `amount` is stored as a `REAL`. To prevent float arithmetic discrepancies (e.g. `0.1 + 0.2 != 0.3`), Python rounding is strictly applied:
   * Values are rounded to 2 decimal places (`round(value, 2)`) during database insertion, mathematical operations, and final template rendering.
3. **Time Formatting**:
   * Datetimes are recorded in UTC using ISO 8601 strings (`YYYY-MM-DD HH:MM:SS` or SQLite `datetime('now')`).
   * Dates are formatted strictly as `YYYY-MM-DD` and months as `YYYY-MM`.

---

## Part 3: `/teamwork-preview` Multi-Agent System

The `/teamwork-preview` framework is a collaborative multi-agent architecture built to coordinate task execution while preventing context collapse and maintaining high code standards.

```
                  +-----------------------------------+
                  |      Orchestrator Agent           |
                  |  (Coordinates, Plans, Dispatches) |
                  +-----------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                       |                       |
            v                       v                       v
  +------------------+    +------------------+    +------------------+
  |  Explorer Agent  |    |Worker/Implementer|    |  Reviewer Agent  |
  | (Inspects Code)  |    | (Writes Code/Fix)|    |  (Verifies Fix)  |
  +------------------+    +------------------+    +------------------+
            |                       |                       |
            +-----------------------+-----------------------+
                                    |
                                    v
                         +---------------------+
                         | Handoff to Parent   |
                         | (Successor Lifecycle|
                         |   & Retirement)     |
                         +---------------------+
```

### 1. Framework Principles
* **Dispatch-Only Orchestrator**: The central orchestrator manages tasks and monitors progress. It is strictly forbidden from editing code, running command scripts, or performing builds outside of the `.agents/` metadata folder. All edits and test verifications must be executed by worker/reviewer subagents.
* **Separation of Concerns**: Agent plans (`plan.md`), progress logs (`progress.md`), briefings (`BRIEFING.md`), and handoffs (`handoff.md`) are kept inside `.agents/` directories. Application source code, mock tests, and test suites must never reside under `.agents/`.
* **Flat Agent Registry**: Agent blueprints are stored as flat Markdown files directly in `.agents/agents/` (e.g. `.agents/agents/spendly-test-runner.md`) starting with YAML frontmatter. Nested folder configs or `agent.json` settings are invalid.
* **Immutable Lifespan**: Dispatched subagents exist for a single scope of work. Once they finish and submit a `handoff.md` report, their session is permanently retired. Re-runs require instantiating a fresh subagent.

---

### 2. Prompt Crafting Workflow Steps (1-9)
Dispatched worker agents follow these steps in order to guarantee liveness and accuracy:
1. **Initialize `ORIGINAL_REQUEST.md`**: Record the request verbatim under the agent's folder with a UTC timestamp header to maintain a clear history of expectations.
2. **Read/Create `BRIEFING.md`**: Establish a briefing index using a standard template. This preserves context markers and append-only constraints (🔒 Identity, 🔒 Constraints).
3. **Read `progress.md` & Recover State**: Check the step completion list to identify where the task currently stands and what remains.
4. **Start Heartbeat Timer/Cron**: Establish cron timers using scheduling tools to regularly update the `progress.md` timestamp during long compilation runs.
5. **Assess Complexity**: Establish boundaries, in-scope files, and success conditions.
6. **Create a Concrete Plan**: Detail specific milestones and verification steps inside `plan.md`.
7. **Dispatch Subtasks**: Decompose steps and spawn subagents (Explorer, Implementer, Worker, Reviewer) using messaging channels.
8. **Monitor Subagents**: Review and verify incoming files, check execution logs, and manage active timers.
9. **Synthesize Findings**: Compile outputs, resolve consensus/dissent, document gaps, and summarize results.

---

### 3. Integrity Modes
The framework operates under three strict environments: **Development**, **Testing**, and **Production**.

#### Development Mode Constraints:
* **No Mocking/Facades**: Real implementations must be built. Mocked classes or facade functions that simulate success without actual logic are forbidden.
* **No Hardcoded Test Verification**: Test suites must execute real assertions and verify live application code. Injecting hardcoded results to pass a checklist constitutes a critical failure of integrity.
* **No Fabricated Output**: All reports and handoffs must represent verified observations and code logic.
* **Victory Audit**: The agent must run a comprehensive validation audit (verifying constraints, code structures, tests, and configurations) before reporting milestone completion.

---

### 4. Delegation & Handoff Protocols
* **Directory Ownership**: Each agent owns exactly one folder under `.agents/` (e.g., `worker_writer_2/`). An agent has write permissions ONLY inside its designated directory, but has read-only access to all other directories.
* **Handoff Report (`handoff.md`)**: Handoffs require a structured 5-component report:
  1. **Observation**: Raw data, files, paths, line numbers, and exact errors.
  2. **Logic Chain**: Step-by-step logic connecting observations to findings.
  3. **Caveats**: Scope boundaries and assumptions.
  4. **Conclusion**: Summary and actionable assessments.
  5. **Verification Method**: Instructions to test and verify findings.
* **Permanent Retirement**: Once the handoff is delivered, the subagent conversation ID is retired.
* **Liveness Deadlines**: Heartbeat tracking must be updated regularly in `progress.md` (at least every 5 minutes during intensive processes). If an agent misses its deadline, the orchestrator triggers recovery.
* **Succession Protocol**: To prevent token limit/context window fatigue, agents must self-succeed after a set limit (e.g., 16 subagent spawns). The agent writes a detailed state report, spawns a successor, passes the context folder, and retires.
