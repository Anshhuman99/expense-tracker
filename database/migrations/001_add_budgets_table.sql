-- Migration 001: Add budgets table
-- Creates a per-category monthly budget table.
-- This migration is idempotent (CREATE TABLE IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS budgets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    category   TEXT    NOT NULL,
    amount     REAL    NOT NULL,
    month      TEXT    NOT NULL,
    created_at TEXT    DEFAULT (datetime('now')),
    UNIQUE(user_id, category, month)
);
