# Spec: Custom Error Pages

## Overview
This feature replaces Flask's default basic error pages (404, 403, 500) with Spendly's premium branded error pages. 
A new directory `templates/errors/` will be created to house templates for `404.html` (Not Found), `403.html` (Forbidden), and `500.html` (Internal Server Error). 
Custom error handlers will be registered in `app.py` to handle these HTTP exceptions, render the respective templates with the appropriate HTTP status codes, and provide clean, helpful navigation back to the application's landing page or dashboard.
The pages will feature a premium, centered card-based design with status indicators (using colors from our palette), clear explanations of what went wrong, and call-to-action buttons.

---

## Depends on
- Step 1: Database Setup
- Step 2: Registration
- Step 3: Login / Logout
- Step 4: Profile Page Design
- Step 5: Backend Route Profile Page
- Step 6: Data Filter for Profile Page
- Step 7: Add Expense
- Step 8: Edit Expense
- Step 9: Delete Expense

---

## Routes
- `GET /trigger-500` (Testing route):
  - A developer/testing route that explicitly raises an unhandled exception or calls `abort(500)` to trigger the 500 error page.
  - Used for verification in automated tests.

---

## Database changes
No database changes.

---

## Templates
### Create
- `templates/errors/404.html`:
  - Extends `base.html`.
  - Displays a premium 404 illustration or icon, a "Page Not Found" title, a helpful message (e.g., "We can't seem to find the page you're looking for."), and a button to return to the Home page or Dashboard.
- `templates/errors/403.html`:
  - Extends `base.html`.
  - Displays an access denied indicator, a "Forbidden" title, a helpful message (e.g., "You do not have permission to access this page."), and a button to return to the Dashboard.
- `templates/errors/500.html`:
  - Extends `base.html`.
  - Displays a server error illustration or icon, an "Internal Server Error" title, a friendly message (e.g., "Something went wrong on our end. We're looking into it."), and a button to return home.

---

## Files to change
- `app.py`:
  - Register error handlers for 403, 404, and 500.
  - Add a `/trigger-500` route to trigger an internal server error for testing purposes.

---

## Files to create
- `templates/errors/404.html`: The HTML template for the 404 Page Not Found error.
- `templates/errors/403.html`: The HTML template for the 403 Forbidden error.
- `templates/errors/500.html`: The HTML template for the 500 Internal Server Error.
- `static/css/errors.css`: Design/styles for the error pages, featuring centered layout cards, styled typography, and action buttons using Spendly's CSS variables.
- `tests/test_10-custom-error-pages.py`: Test suite verifying:
  - Accessing a nonexistent URL returns 404 and displays the custom 404 template.
  - Accessing `/trigger-500` returns 500 and displays the custom 500 template.
  - A test verifying 403 Forbidden (e.g. attempting to edit/delete another user's expense or manually aborting 403) returns 403 and displays the custom 403 template.
  - Checking that all error pages extend `base.html` and contain the Spendly layout.

---

## New dependencies
No new dependencies.

---

## Rules for implementation
- No SQLAlchemy/ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- CSS variables only
- No hardcoded colours
- All templates extend base.html
- No inline CSS or JavaScript
- Use semantic HTML
- Always return the correct HTTP status code (403, 404, 500) from the custom error handlers.

---

## Definition of done
- [ ] Accessing a nonexistent URL (e.g., `/nonexistent-route`) renders the custom 404 page and returns a 404 status code.
- [ ] Attempting to access an unauthorized resource (e.g. editing another user's expense) renders the custom 403 page and returns a 403 status code.
- [ ] Accessing `/trigger-500` renders the custom 500 page and returns a 500 status code.
- [ ] The custom error templates are placed under `templates/errors/` and correctly extend `base.html`.
- [ ] All styling is written in `static/css/errors.css` (imported in the head of each error template) and strictly uses CSS variables.
- [ ] The layout of the error pages is responsive and visually consistent with Spendly's premium theme.
- [ ] Each error page provides an interactive, visible button to navigate back to the home page or dashboard.
- [ ] Automated tests in `tests/test_10-custom-error-pages.py` cover all three custom error scenarios and pass successfully.
