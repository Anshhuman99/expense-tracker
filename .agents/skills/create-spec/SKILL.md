---
name: create-spec
description: Create a Spendly feature specification and feature branch.
argument-hint: <step-number> <feature-name>
allowed-tools: run_command, view_file, write_to_file
---

You are the Spendly specification agent.

User input: $ARGUMENTS

## Workflow

### 1. Verify project
Run:
- git rev-parse --is-inside-work-tree

Ensure these files exist:
- CLAUDE.md
- app.py
- database/db.py

Stop if any are missing.

---

### 2. Ensure clean working tree
Run:
- git status --porcelain

If not empty, stop and ask the user to commit or stash changes.

---

### 3. Parse input
Extract:
- step_number (02 format)
- feature_title
- feature_slug (kebab-case)
- branch = feature/<feature_slug>

---

### 4. Create branch
Run:
- git checkout main
- git pull origin main
- git checkout -b feature/<feature_slug>

If the branch already exists, append a suffix (e.g. -01, -02) to create a unique branch, or stop if not possible.

---

### 5. Read project conventions
Read:
- CLAUDE.md
- database/db.py (to understand existing table structure)

---

### 6. Create specification
Create:
- ai/settings/specs/<step_number>-<feature_slug>.md

Use this template:

# Spec: <Feature Title>

## Overview

## Dependencies

## Acceptance Criteria

## Database Changes

## Routes

## Templates

## Files to Modify

## Files to Create

## Validation

## Edge Cases

## Definition of Done

### Implementation Constraints
- No SQLAlchemy/ORMs (use raw SQLite via database/db.py)
- Parameterised SQL queries only
- Passwords hashed with werkzeug.security
- CSS variables only (no hardcoded colours in HTML/CSS)
- All templates must extend base.html

Implementation must follow CLAUDE.md.

---

### 7. Finish
Print only:
Branch: <branch_name>
Spec: ai/settings/specs/<step_number>-<feature_slug>.md
Next: Enter Plan Mode.
