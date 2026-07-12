# ◈ Spendly

Spendly is a lightweight, high-performance personal expense tracker built with **Flask** and **SQLite**. 

The project prioritises clean architecture, readability, maintainability, and core web development principles over unnecessary framework overhead. It implements a zero-dependency frontend, server-side data validation, raw database parameterisation, and dynamic visualizations.

---

## 🌟 Key Features

### 1. Dashboard & Transactions
* **Overview KPI Stats:** View lifetime total, current month total, total transactions, and top category breakdown.
* **Smart Filter Bar:** Filter transactions instantly by category or custom date range.
* **CRUD Management:** Add, edit, or delete expenses with server-side validation.
* **Pagination & Sorting:** Navigate large transaction lists easily with persistent filters.

### 2. Budgets & Smart Insights
* **Monthly Budgets:** Create spending limits per category. Visual progress bars alert you when you approach or exceed limits.
* **Savings Suggestions:** Personalised suggestions derived from dining out frequencies, month-over-month spending spikes, and budget health.
* **Trends Analysis:** Compare spending across different months to spot changes in financial habits.

### 3. Preferences & Utilities
* **Dark Mode:** Persistence preference via `localStorage` with system preference fallbacks and inline blocker scripts to prevent Flash of Unstyled Content (FOUC).
* **Multi-Format Export:** Download filtered transaction logs instantly as CSV, Excel, or PDF reports.
* **Receipt Uploads:** Attach receipt images safely. Uploaded files are renamed, stored outside public directories, and accessed via authenticated, ownership-checked routes.
* **Recurring Transactions:** Automate monthly, weekly, or daily expenses with smart background auto-generation.

---

## 🛠️ Technology Stack & Architectural Constraints

Spendly is designed around strict development guidelines to maintain clean codebase patterns.

* **Backend:** Flask 3.x (Single-file routing in `app.py`, no blueprints)
* **Database:** SQLite 3 (Pure SQLite wrappers in `database/db.py` and query logic in `database/queries.py`)
  * **Rule:** No SQLAlchemy/ORMs are allowed. All database actions use parameterised SQL (`?`) to prevent injection.
* **Frontend:** Vanilla HTML5, Vanilla CSS3 (Custom design system utilizing CSS custom properties/variables), Vanilla JavaScript (No React, Vue, jQuery, Tailwind, or Bootstrap).
* **Security:** Password hashing via `werkzeug.security`, route guards, strict ownership authorization checks on resource edits/deletions, secure file uploads.

---

## 📁 Project Directory Structure

```
expense-tracker/
├── app.py                    # All routes and controller logic (single file)
├── requirements.txt          # Pip dependency manifest
├── Procfile                  # Gunicorn deployment configuration
├── spendly.db                # SQLite database (generated dynamically, git ignored)
├── database/
│   ├── db.py                 # Connection lifecycle, initialization & migration helpers
│   ├── queries.py            # All SQL data-fetching and query functions
│   └── migrations/           # Numbered SQL database migration files
├── templates/
│   ├── base.html             # Shared layout (navbar, header, toasts, footers)
│   ├── landing.html          # Clean marketing page
│   ├── profile.html          # Main user dashboard
│   ├── recurring.html        # Recurring rules management
│   ├── suggestions.html      # Saving suggestions panel
│   └── errors/               # Custom branded 404 and 500 error pages
├── static/
│   ├── css/                  # Module-specific styles extending main style.css variables
│   │   ├── style.css         # Core CSS variables, light/dark themes, components
│   │   └── *.css             
│   └── js/
│       └── main.js           # Shared dynamic behavior (theme toggle, mobile nav, toasts)
└── tests/                    # Robust test suite with 270+ test cases
```

---

## 💾 Database Schema

The database is built on SQLite with manually enforced foreign key constraints (`PRAGMA foreign_keys = ON`).

### 1. `users`
* `id` (INTEGER, Primary Key, Autoincrement)
* `name` (TEXT, Not Null)
* `email` (TEXT, Unique, Not Null)
* `password_hash` (TEXT, Not Null)
* `created_at` (TEXT, Default `CURRENT_TIMESTAMP`)

### 2. `expenses`
* `id` (INTEGER, Primary Key, Autoincrement)
* `user_id` (INTEGER, Foreign Key → `users(id)`, Not Null)
* `amount` (REAL, Not Null, positive rounded to 2 decimal places)
* `category` (TEXT, Not Null, limited to fixed list of 7 categories)
* `date` (TEXT, Not Null, YYYY-MM-DD)
* `description` (TEXT, Optional, max 250 characters)
* `receipt_path` (TEXT, Optional)
* `created_at` (TEXT, Default `CURRENT_TIMESTAMP`)

### 3. `budgets`
* `id` (INTEGER, Primary Key, Autoincrement)
* `user_id` (INTEGER, Foreign Key → `users(id)`, Not Null)
* `category` (TEXT, Not Null)
* `amount` (REAL, Not Null)
* `month` (TEXT, Not Null, YYYY-MM)
* `created_at` (TEXT, Default `CURRENT_TIMESTAMP`)

### 4. `recurring_rules`
* `id` (INTEGER, Primary Key, Autoincrement)
* `user_id` (INTEGER, Foreign Key → `users(id)`, Not Null)
* `amount` (REAL, Not Null)
* `category` (TEXT, Not Null)
* `frequency` (TEXT, Not Null: daily, weekly, monthly, yearly)
* `description` (TEXT, Optional)
* `last_generated_date` (TEXT, Not Null)
* `created_at` (TEXT, Default `CURRENT_TIMESTAMP`)

---

## 🚀 Installation & Quick Start

### 1. Clone & Navigate
```bash
git clone https://github.com/Anshhuman99/expense-tracker.git
cd expense-tracker
```

### 2. Create and Activate Virtual Environment
**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```
**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize and Seed Database
Spendly will automatically run migration files on launch. To pre-populate the database with a test user (`demo@spendly.com` / `demo123`) for local development:
```bash
python -c "from database.db import init_db, seed_db; init_db(); seed_db()"
```
> [!WARNING]
> Seeding is strictly intended for local development. Never run the seeding commands in a production environment as it inserts predefined credentials.

> [!IMPORTANT]
> Always configure secrets and API tokens via environment variables in production. Never commit credentials, `.env` files, or the generated database to version control.

### 5. Run the Application
```bash
python app.py
```
Open `http://localhost:5001` in your browser.

---

## 🧪 Running Tests

Spendly comes with an extensive unit and integration test suite powered by `pytest`.

Run all tests:
```bash
pytest
```
Run tests with verbosity:
```bash
pytest -v
```
Run a specific test module:
```bash
pytest tests/test_29-dark-mode.py -v
```
