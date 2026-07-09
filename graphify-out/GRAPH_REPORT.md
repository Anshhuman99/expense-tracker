# Graph Report - .  (2026-07-09)

## Corpus Check
- Corpus is ~25,636 words - fits in a single context window. You may not need a graph.

## Summary
- 222 nodes · 328 edges · 32 communities (26 shown, 6 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.95)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Expense Filtering & Retrieval
- Core Application & Layout templates
- Expense Modification & Deletion
- SQLite Connection & Database Seeding
- User Dashboard & Stats Queries
- AI Review & Test Agent Infrastructure
- Expense Creation Tests
- Analytics Dashboard Concept
- Authentication Concept
- Database Schema Concept
- Expense Management Concept
- Profile View Concept
- Registration Concept

## God Nodes (most connected - your core abstractions)
1. `get_db()` - 35 edges
2. `get_filtered_expenses()` - 16 edges
3. `init_db()` - 15 edges
4. `seed_db()` - 11 edges
5. `get_expense_by_id()` - 10 edges
6. `profile()` - 9 edges
7. `get_user_by_id()` - 9 edges
8. `get_summary_stats()` - 9 edges
9. `get_recent_transactions()` - 9 edges
10. `get_categories()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `load_logged_in_user()` --calls--> `get_db()`  [EXTRACTED]
  app.py → database/db.py
- `profile()` --calls--> `get_db()`  [EXTRACTED]
  app.py → database/db.py
- `profile()` --calls--> `get_categories()`  [EXTRACTED]
  app.py → database/queries.py
- `profile()` --calls--> `get_filtered_expenses()`  [EXTRACTED]
  app.py → database/queries.py
- `edit_expense()` --calls--> `get_expense_by_id()`  [EXTRACTED]
  app.py → database/queries.py

## Import Cycles
- None detected.

## Communities (32 total, 6 thin omitted)

### Community 0 - "Expense Filtering & Retrieval"
Cohesion: 0.06
Nodes (37): get_categories(), get_filtered_expenses(), Retrieve all unique categories logged by a specific user, sorted alphabetically., Retrieve expenses for a specific user filtered by category, date range, and sear, Test that if start_date > end_date, 0 results are returned and     the page disp, Test that malformed date inputs do not cause the application to crash,     handl, Test that empty strings for filter fields are ignored and treated as unfiltered., Test that KPI stats cards and Category Breakdown sidebar remain overall summarie (+29 more)

### Community 1 - "Core Application & Layout templates"
Cohesion: 0.09
Nodes (15): add_expense(), analytics(), delete_expense(), edit_expense(), landing(), load_logged_in_user(), login(), privacy() (+7 more)

### Community 2 - "Expense Modification & Deletion"
Cohesion: 0.07
Nodes (28): get_expense_by_id(), Retrieve a single expense by its ID.     Returns a dict with keys: id, user_id,, client(), 3. Nonexistent expense check:        Verify that attempting to edit a non-existe, 4. Normal page load:        Verify that GET /expenses/<id>/edit when logged in l, 5. Validation errors:        Verify that submitting invalid inputs flashes valid, 6. Success path:        Verify that submitting valid changes updates the databas, 1. Guest redirect:        Verify that accessing the edit expense page (via GET o (+20 more)

### Community 3 - "SQLite Connection & Database Seeding"
Cohesion: 0.21
Nodes (21): delete_expense(), get_db(), get_user_category_breakdown(), get_user_expense_stats(), get_user_recent_expenses(), init_db(), Delete an existing expense record by ID., seed_db() (+13 more)

### Community 4 - "User Dashboard & Stats Queries"
Cohesion: 0.19
Nodes (14): profile(), get_category_breakdown(), get_recent_transactions(), get_summary_stats(), get_user_by_id(), Retrieves the category breakdown of expenses for a given user.     Returns a lis, Retrieves summary stats for a given user.     Returns a dict with:       - total, Retrieve user information by user ID.     Returns a dict with keys: name, email, (+6 more)

### Community 5 - "AI Review & Test Agent Infrastructure"
Cohesion: 0.20
Nodes (4): Quality Review, Security Review, Test Execution, Test Generation

### Community 6 - "Expense Creation Tests"
Cohesion: 0.18
Nodes (10): client(), 4. Success path:        Verify that posting valid data adds the expense to the d, 1. Guest redirect:        Verify that accessing the add expense page (via GET or, 2. Normal page load:        Verify that GET /expenses/add when logged in renders, Fixture to set up a clean, isolated database for each test run.     Monkeypatche, 3. Validation errors:        Verify that POSTing with invalid inputs (amount, ca, test_guest_redirect(), test_normal_page_load() (+2 more)

## Knowledge Gaps
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_db()` connect `SQLite Connection & Database Seeding` to `Expense Filtering & Retrieval`, `Core Application & Layout templates`, `Expense Modification & Deletion`, `User Dashboard & Stats Queries`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `get_filtered_expenses()` connect `Expense Filtering & Retrieval` to `Core Application & Layout templates`, `SQLite Connection & Database Seeding`, `User Dashboard & Stats Queries`?**
  _High betweenness centrality (0.059) - this node is a cross-community bridge._
- **Why does `get_expense_by_id()` connect `Expense Modification & Deletion` to `Core Application & Layout templates`, `SQLite Connection & Database Seeding`, `User Dashboard & Stats Queries`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **What connects `Update an existing expense record.`, `Delete an existing expense record by ID.`, `Retrieve user information by user ID.     Returns a dict with keys: name, email,` to the rest of the system?**
  _41 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Expense Filtering & Retrieval` be split into smaller, more focused modules?**
  _Cohesion score 0.05708245243128964 - nodes in this community are weakly interconnected._
- **Should `Core Application & Layout templates` be split into smaller, more focused modules?**
  _Cohesion score 0.09247311827956989 - nodes in this community are weakly interconnected._
- **Should `Expense Modification & Deletion` be split into smaller, more focused modules?**
  _Cohesion score 0.07126436781609195 - nodes in this community are weakly interconnected._