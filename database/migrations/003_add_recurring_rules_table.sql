-- Migration to add recurring rules table and add reference column in expenses
CREATE TABLE IF NOT EXISTS recurring_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    frequency TEXT NOT NULL, -- 'daily', 'weekly', 'monthly', 'yearly'
    start_date TEXT NOT NULL, -- 'YYYY-MM-DD'
    last_generated TEXT, -- 'YYYY-MM-DD'
    created_at TEXT DEFAULT (datetime('now'))
);

ALTER TABLE expenses ADD COLUMN recurring_rule_id INTEGER REFERENCES recurring_rules(id) ON DELETE SET NULL;
