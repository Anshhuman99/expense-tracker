```md
---
description: Create a spec file and feature branch for the next Spendly step.
argument-hint: Step number and feature name, e.g. 2 registration
allowed-tools: Read, Write, Glob, Grep, Bash(git:*)
---

You are creating the next Spendly feature. Follow CLAUDE.md exactly.

User input: $ARGUMENTS

1. Verify project
- Ensure this is a Git repo (`git rev-parse --is-inside-work-tree`).
- Verify CLAUDE.md, app.py and database/db.py exist.
- If not, stop.

2. Ensure clean working tree
- Run `git status --porcelain`.
- If output exists, stop and ask the user to commit or stash changes.

3. Parse $ARGUMENTS
Extract:
- step_number (2→02)
- feature_title (Title Case)
- feature_slug (lowercase kebab-case, max 40 chars)
- branch_name = feature/<feature_slug>
If unclear, ask for clarification.

4. Validate
- Read CLAUDE.md.
- Stop if the step is already complete.

5. Create branch
- Find a unique branch name (append -01, -02... if needed).
- Run:
  - `git checkout main`
  - `git pull origin main`
  - `git checkout -b <branch_name>`

6. Research
Read:
- CLAUDE.md
- app.py
- database/db.py
- .claude/specs/*
Reuse existing conventions. Don't duplicate specs or invent project details.

7. Write spec
Save `.claude/specs/<step_number>-<feature_slug>.md` with:

# Spec: <feature_title>

- Overview
- Depends on
- Routes (or "No new routes")
- Database changes (or "No database changes")
- Templates (Create / Modify)
- Files to change
- Files to create
- New dependencies (or "No new dependencies")
- Rules for implementation
- Definition of done

Always include these rules:
- No SQLAlchemy/ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- CSS variables only
- No hardcoded colours
- All templates extend base.html

Definition of done must be objective and testable.

8. Finish
Print only:

Branch: <branch_name>
Spec file: .claude/specs/<step_number>-<feature_slug>.md
Title: <feature_title>

Then print:

Review the spec at .claude/specs/<step_number>-<feature_slug>.md then enter Plan Mode with Shift+Tab twice to begin implementation.

Never implement code or print the spec unless requested.
```
