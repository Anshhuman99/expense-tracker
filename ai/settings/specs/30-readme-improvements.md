# Spec: README Improvements

## Overview

Create a comprehensive and polished `README.md` at the project root. The document should serve as the primary documentation of Spendly, highlighting its architecture, features (including the newly added Dark Mode), setup guidelines, tech constraints, and database design. It will act as a professional landing page for recruiters and portfolio presentation.

## Dependencies

No new dependencies.

## Acceptance Criteria

- [ ] Clear, professional title and description of Spendly as a lightweight personal expense tracker
- [ ] List of all core features (Landing page, registration, login/logout, profile dashboard, filters, add/edit/delete expense, analytics dashboard, monthly budgets, spending insights, search/sorting/pagination, CSV/Excel/PDF export, receipt uploads, recurring expenses, dark mode)
- [ ] Detailed setup and installation instructions (virtualenv creation, dependency installation, seeding db, running dev server, running tests)
- [ ] Architecture overview showing files and directory structures
- [ ] Database schema details (users, expenses, budgets, recurring rules, uploads, etc.)
- [ ] Tech stack summary highlighting constraints (Flask, SQLite, vanilla CSS, vanilla JS, raw SQLite queries only, no SQLAlchemy)
- [ ] Clean, professional Markdown styling, table formatting, and code blocks

## Database Changes

None.

## Routes

None.

## Templates

None.

## Files to Modify

None (since README.md doesn't exist yet, we will create it).

## Files to Create

- `README.md` — The main documentation page

## Validation

- Ensure all markup renders correctly
- No broken links or markdown syntax warnings
- Professional styling matching the quality of the project

## Edge Cases

- Setup instructions must work seamlessly on macOS, Linux, and Windows (mention both Unix and Windows activation steps)
- Seeding database step must be clearly described

## Definition of Done

- [ ] README.md created at root directory
- [ ] Contains all major sections: Features, Tech Stack, Setup/Installation, Architecture, DB Schema
- [ ] Mentions and documents Dark Mode
- [ ] Setup commands verified
- [ ] Markdown renders properly
- [ ] Tests pass

### Implementation Constraints
- No SQLAlchemy/ORMs (use raw SQLite via database/db.py)
- Parameterised SQL queries only
- Passwords hashed with werkzeug.security
- CSS variables only (no hardcoded colours in HTML/CSS)
- All templates must extend base.html

Implementation must follow CLAUDE.md.
