# Spec: Profile Settings

## Overview

Allow users to manage their personal account information from a dedicated settings page.
Users can update their display name and email address, and change their password with
current-password confirmation. All changes require server-side validation before saving.

## Depends on

- Step 03 (Login / Logout) — session management and password hashing
- Step 04/05 (Profile Page) — authenticated route pattern, `get_user_by_id`

## Routes

| Method | Path                 | Description                                          |
|--------|----------------------|------------------------------------------------------|
| GET    | `/settings`          | Render the profile settings page (auth required)     |
| POST   | `/settings/profile`  | Update name and/or email (auth required)             |
| POST   | `/settings/password` | Change password — requires current password (auth)   |

## Database changes

No new tables. The following existing columns on `users` are updated via parameterised queries:

- `name` — updated by the profile sub-form
- `email` — updated by the profile sub-form (must remain unique)
- `password_hash` — updated by the password sub-form

## Templates

### Create
- `templates/settings.html` — Settings page with two distinct card sections:
  1. **Update Profile** — name and email fields, pre-populated from current user data
  2. **Change Password** — current password, new password, confirm new password fields

### Modify
- `templates/base.html` — Add "Settings" nav link for authenticated users (between Insights and Sign out)

## Files to change

- `app.py` — Add three routes: `GET /settings`, `POST /settings/profile`, `POST /settings/password`
- `database/queries.py` — Add `update_user_profile(user_id, name, email)` and `update_user_password(user_id, password_hash)`
- `templates/base.html` — Add Settings nav link

## Files to create

- `templates/settings.html`
- `static/css/settings.css`

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy / ORMs
- Parameterised queries only (`?` placeholders)
- Passwords hashed with `werkzeug.security.generate_password_hash`
- Current password verified with `werkzeug.security.check_password_hash` before any password change
- CSS variables only — no hardcoded colours
- No inline CSS or inline JavaScript
- All templates extend `base.html`
- All routes must check `session.get('user_id')` and redirect to `/login` if not authenticated
- After a successful name change, update `session['user_name']` to reflect the new name immediately
- After a successful email change, verify the new email is not already used by another account (return flash error on `sqlite3.IntegrityError`)
- Validation:
  - Name: required, non-empty after strip
  - Email: required, must match `EMAIL_REGEX`, must be unique
  - Current password: required on password change form; must match stored hash
  - New password: minimum 8 characters
  - Confirm new password: must match new password
- Flash a clear success message after each successful update
- Flash a clear error message for every validation failure
- SQL for updates goes into `database/queries.py`, not inside route handlers

## Definition of done

- [ ] `GET /settings` returns 200 for authenticated users and redirects to `/login` for unauthenticated users
- [ ] The settings page renders two separate form sections: **Update Profile** and **Change Password**
- [ ] Both forms are pre-populated / partially pre-populated from the database
- [ ] `POST /settings/profile` with valid name + email updates the `users` row and flashes a success message
- [ ] `POST /settings/profile` with a duplicate email returns an error flash and does not update the database
- [ ] `POST /settings/profile` with an empty name returns an error flash and does not update the database
- [ ] `POST /settings/password` with a correct current password, valid new password (8+ chars), and matching confirmation updates `password_hash` and flashes success
- [ ] `POST /settings/password` with an incorrect current password returns an error flash and does not change the hash
- [ ] `POST /settings/password` with a new password shorter than 8 characters returns an error flash
- [ ] `POST /settings/password` where new and confirm passwords do not match returns an error flash
- [ ] After a successful name update, `session['user_name']` reflects the new name immediately (no re-login required)
- [ ] The Settings nav link appears in the navbar for authenticated users
- [ ] The page is responsive (desktop, tablet, mobile)
- [ ] All styling uses CSS variables (no hardcoded colours)
- [ ] All SQL is parameterised (no string-formatted queries)
