# Spec: Delete Account

## Overview

Allow users to permanently remove their account from Spendly. This requires password confirmation for security. When an account is deleted, all associated expense records and budget records must be safely deleted inside a transaction (enforced by foreign key cascades or manual deletion in a single database transaction). After deletion, the user's session is cleared and they are redirected to the landing page with a confirmation flash message.

## Depends on

- Step 23 (Profile Settings) — The Delete Account button on the settings page redirects to the confirmation page.

## Routes

| Method | Path               | Description                                           |
|--------|--------------------|-------------------------------------------------------|
| GET    | `/account/delete`  | Render the delete account confirmation page           |
| POST   | `/account/delete`  | Permanently delete the account (password confirmation) |

## Database changes

No new tables. The delete action deletes the row from the `users` table corresponding to the logged-in user.
Because `PRAGMA foreign_keys = ON` is enabled, all rows in `expenses` and `budgets` referencing the user's ID must be cascadingly deleted, or manually deleted in a transaction to prevent orphan records.

## Templates

### Create
- `templates/delete_account.html` — A page containing a warning block and a form requesting the current password to confirm deletion.

### Modify
- `templates/settings.html` — Update the "Delete My Account" button to link to the route `url_for('delete_account')` instead of the static `/account/delete`.

## Files to change

- `app.py` — Add `/account/delete` GET and POST routes.
- `database/queries.py` — Add `delete_user_account(user_id)` query helper.
- `templates/settings.html` — Link the delete button using `url_for`.

## Files to create

- `templates/delete_account.html`
- `static/css/delete_account.css`

## New dependencies

No new dependencies.

## Rules for implementation

- No SQLAlchemy / ORMs
- Parameterised queries only
- Validate current password using `werkzeug.security.check_password_hash` before executing the deletion
- Clear session (`session.clear()`) after successful deletion
- Do the deletion inside a transaction. Both user deletion and any cascade deletions must succeed together.
- CSS variables only — no hardcoded colours
- All templates extend `base.html`
- All routes must check authentication

## Definition of done

- [ ] Unauthenticated users attempting to access GET or POST `/account/delete` are redirected to `/login`
- [ ] GET `/account/delete` renders the confirmation page with a form asking for password
- [ ] POST `/account/delete` with an incorrect password flashes an error message and does not delete the account
- [ ] POST `/account/delete` with the correct password deletes the user from the `users` table, deletes all their expenses and budgets, clears their session, and redirects to the landing page with a success message
- [ ] The entire delete operation runs inside a database transaction to ensure safety
- [ ] The "Delete My Account" button on the Settings page successfully routes to the confirmation page
- [ ] The page is responsive (desktop, tablet, mobile) and follows the app style guide
