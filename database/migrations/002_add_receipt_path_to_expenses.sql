-- Migration to add receipt_path to expenses table
ALTER TABLE expenses ADD COLUMN receipt_path TEXT;
