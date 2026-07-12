# Spec: Receipt Upload

## Overview

Allow users to attach receipt images or PDF files to their expenses. When creating or editing an expense, the user can upload a file. The uploaded file is validated (allowed file types: png, jpg, jpeg, pdf; maximum size: 5MB), stored securely on disk in the `uploads/` directory (outside the public `static/` directory) with a sanitized, randomized unique filename, and associated with the expense. The upload file must only be served through an authenticated, ownership-checked route to ensure only the owner of the expense can view or download the receipt.

## Depends on

- Step 07 (Add Expense) — Forms need file input.
- Step 08 (Edit Expense) — Forms need file input and preview/deletion support.
- Step 09 (Delete Expense) — Deleting an expense must delete its associated physical file if it exists.
- Step 24 (Delete Account) — Deleting an account must delete all physical files for all the user's expenses.

## Routes

| Method | Path | Description |
|--------|------|-------------|
| GET    | `/expenses/<int:expense_id>/receipt` | Authenticated, ownership-checked route to serve/download the uploaded receipt file |
| POST   | `/expenses/<int:expense_id>/receipt/delete` | Authenticated, ownership-checked route to delete only the receipt from an expense |

## Database changes

Create a database migration file `database/migrations/002_add_receipt_path_to_expenses.sql` to add a new column to the `expenses` table:
- `receipt_path` — TEXT, nullable. Stores the relative filename of the uploaded file inside the `uploads/` directory.

## Templates

### Modify
- `templates/add_expense.html` — Add a file input field with appropriate accept attributes (`image/png, image/jpeg, application/pdf`) and instructions. Enable `enctype="multipart/form-data"` on the form.
- `templates/edit_expense.html` — Add a file input field, show a preview of the existing receipt if it exists (using the secure serving route), and add a button/form to delete the current receipt. Enable `enctype="multipart/form-data"` on the form.
- `templates/profile.html` — (Optional/Recommended) If an expense has a receipt, show a paperclip or image icon in the transactions list, linking to the receipt view.

## Files to change

- `app.py` — Add configuration for upload path and file limits. Implement the upload handling in `add_expense` and `edit_expense` route handlers. Add secure file serving route. Update delete expense and delete account logic to clean up physical receipt files.
- `database/queries.py` — Update query functions to insert, update, retrieve, and delete the `receipt_path` column in the `expenses` table.
- `templates/add_expense.html` — Add file input.
- `templates/edit_expense.html` — Add file input, current receipt view/delete button.
- `templates/profile.html` — Link or icon to show/preview the receipt.

## Files to create

- `database/migrations/002_add_receipt_path_to_expenses.sql`
- `static/css/receipt.css` — Styling for receipt previews and input fields.

## New dependencies

No new dependencies. Standard Python standard library functions (`werkzeug.utils.secure_filename`, `uuid`, `os`) will be used.

## Rules for implementation

- No SQLAlchemy / ORMs
- Parameterised queries only
- Store files in `uploads/`, outside `static/`, never executed or served from a public path directly
- Allowed extensions: `png`, `jpg`, `jpeg`, `pdf`
- Max file size: 5MB
- Sanitize filenames using `werkzeug.utils.secure_filename` and prefix with a UUID to prevent path traversal or name collisions
- Serve receipts only through an authenticated, ownership-checked route
- When an expense is deleted, or an account is deleted, delete the physical receipt files from disk to prevent orphaned files.
- CSS variables only — no hardcoded colours
- All templates extend `base.html`

## Definition of done

- [ ] Run migration successfully to add `receipt_path` column to the `expenses` table
- [ ] Uploading files during `add_expense` works, sanitizes the filename, saves to `uploads/`, and stores the path in the database
- [ ] Large files (> 5MB) or disallowed types are rejected with a helpful validation message
- [ ] GET `/expenses/<expense_id>/receipt` is authenticated and ownership-checked:
  - If user is not logged in, redirects to `/login`
  - If user is logged in but does not own the expense, returns 403 or 404
  - If user is the owner, serves the file securely from the `uploads/` directory
- [ ] Edit expense template allows replacing the receipt or deleting it. Deleting a receipt removes the physical file from disk and clears the `receipt_path` column in the database
- [ ] Deleting an expense deletes the associated physical file on disk (if any)
- [ ] Deleting an account deletes all associated physical files on disk for that user's expenses
- [ ] The app is responsive and displays the receipt previews cleanly
- [ ] All tests pass
