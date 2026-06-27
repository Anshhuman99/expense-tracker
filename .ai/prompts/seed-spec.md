```md
---
description: Create a specification file and Git feature branch for the next Spendly feature.
argument-hint: Step number and feature name, e.g. 2 registration
allowed-tools: Read, Write, Glob, Grep, Bash(git:*)
---

You are creating the next feature specification for Spendly.

Follow CLAUDE.md exactly.
Do not invent project details that cannot be inferred from the existing codebase.

User input:

$ARGUMENTS

---

## 1. Verify project

Ensure:

- This is a Git repository (`git rev-parse --is-inside-work-tree`)
- `CLAUDE.md` exists
- `app.py` exists
- `database/db.py` exists

If any check fails, stop and explain why.

---

## 2. Ensure a clean working tree

Run:

git status --porcelain

If the working tree is not clean, stop and ask the user to commit or stash their changes before creating a new feature.

---

## 3. Parse arguments

Extract:

- step_number (pad to two digits, e.g. 2 → 02)
- feature_title (Title Case)
- feature_slug (lowercase kebab-case, maximum 40 characters)
- branch_name = feature/<feature_slug>

If the request is ambiguous, ask for clarification before continuing.

---

## 4. Validate

Read:

- CLAUDE.md

Stop if:

- the requested step already exists
- the feature has already been implemented

---

## 5. Create feature branch

Generate a unique branch name.

If

feature/<slug>

already exists, append

-01
-02
-03

until unique.

Run:

git checkout main

git pull origin main

git checkout -b <branch_name>

---

## 6. Research the existing project

Read:

- CLAUDE.md
- app.py
- database/db.py
- .ai/settings/specs/*

Reuse existing:

- architecture
- naming conventions
- route patterns
- helper functions
- template structure
- styling conventions

Do not duplicate existing functionality.

When extending existing features, prefer modifying existing helpers rather than introducing unnecessary new ones.

Prefer incremental development.

Each specification should implement one cohesive feature suitable for a single pull request unless the user explicitly requests otherwise.

---

## 7. Write the specification

Save:

.ai/settings/specs/<step_number>-<feature_slug>.md

The specification must be implementation-ready.

Assume another developer or AI agent will implement the feature without asking follow-up questions.

Every section should remove ambiguity rather than simply describe the feature.

Use the following structure.

# Spec: <Feature Title>

## Overview

Explain:

- what feature is being added
- how users interact with it
- which existing functionality it extends
- which parts of the application are affected
- implementation scope
- what is intentionally not changing

---

## Depends on

List all prerequisite implementation steps.

Reference existing:

- routes
- helper functions
- templates
- database schema
- previous specifications

required before this feature can be implemented.

---

## Routes

If no routes change, explicitly state:

No new routes.

Otherwise specify for every modified route:

- HTTP method
- URL
- new query parameters
- form fields
- parameter formats
- optional vs required
- default behaviour
- validation rules
- fallback behaviour
- user-visible errors

---

## Database changes

If none, explicitly state:

No database changes.

Otherwise describe:

- schema changes
- migrations
- indexes
- helper function changes
- new helper parameters
- SQL behaviour

Do not write implementation code.

---

## Templates

For every template specify whether it is:

- Created
- Modified

Describe:

- placement
- UI components
- labels
- active states
- conditional rendering
- retained values
- empty-state behaviour

Avoid vague instructions such as "add a form."

---

## Files to change

List every modified file.

Explain the responsibility of each modification.

Avoid generic descriptions such as:

"update profile"

---

## Files to create

List every new file.

Explain why each file is needed.

If none, explicitly state:

No new files.

---

## New dependencies

If none, explicitly state:

No new dependencies.

Otherwise explain why each dependency is required.

---

## Rules for implementation

Always include:

- No SQLAlchemy or ORMs
- Raw sqlite3 only via get_db()
- Parameterised SQL queries only
- Never concatenate user input into SQL
- Passwords hashed with werkzeug
- CSS variables only
- No hardcoded colours
- No inline styles
- All templates extend base.html
- Business logic belongs in Python, not Jinja templates

Also include any feature-specific implementation constraints.

---

## Validation and Edge Cases

For every user input define:

- valid input
- invalid input
- missing input
- malformed input
- conflicting values
- fallback behaviour
- user-visible messages

The application should never crash because of invalid input.

---

## Behaviour

Describe exactly how the feature behaves.

Avoid vague statements such as:

- add filtering
- support searching
- update dashboard

Instead define:

- default behaviour
- filtered behaviour
- ordering
- limits
- search semantics
- AND / OR behaviour
- sorting
- persistence of state
- empty results

When database queries are involved, describe the expected SQL behaviour without writing SQL code.

---

## Testing

List automated tests that should be added or updated.

Include:

- default behaviour
- successful behaviour
- validation failures
- edge cases
- empty states
- security-related behaviour where appropriate

---

## Definition of Done

Every checklist item must be objectively verifiable.

Include:

- successful behaviour
- default behaviour
- validation behaviour
- edge cases
- UI behaviour
- empty-state behaviour

Avoid vague statements such as:

- Filtering works correctly.

Instead write measurable acceptance criteria.

---

Before saving the specification, verify:

- Scope is clearly defined.
- The feature is appropriately sized for a single pull request.
- Every user-visible behaviour is specified.
- Validation rules exist for every user input.
- Edge cases are covered.
- Empty states are defined.
- Modified files are listed.
- New files are justified.
- No implementation ambiguity remains.

---

## 8. Finish

Print only:

Branch: <branch_name>

Spec file:

.ai/settings/specs/<step_number>-<feature_slug>.md

Title:

<feature_title>

Then print:

Review the specification at

.ai/settings/specs/<step_number>-<feature_slug>.md

Then enter Plan Mode.

Never implement code.

Never print the specification unless explicitly requested.
```
