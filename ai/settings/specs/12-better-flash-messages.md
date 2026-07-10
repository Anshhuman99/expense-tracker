# Spec: Better Flash Messages

## Overview
This feature standardizes all application success, warning, and error notifications with a premium, toast-based alert system. We will replace the static, plain flash banner in `templates/base.html` with a modern Toast notification system that slides in, features meaningful icons (such as success, warning, and error states), supports a manual close button, and automatically fades out/dismisses after 5 seconds using custom CSS animations and a small JavaScript hook. The login and registration error styling will also be updated to share this visual design language.

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
- Step 10: Custom Error Pages
- Step 11: Empty States

---

## Routes
No new routes.

---

## Database changes
No database changes.

---

## Templates
### Modify
- `templates/base.html`:
  - Update the flash rendering block inside the main content area (making sure it applies globally but is formatted as a floating/fixed toast container).
  - Structure each message to contain:
    - An icon container holding a Material Symbols Outlined icon depending on the category (`check_circle` for success, `error` for error, `warning` for warning).
    - The alert message text.
    - A close button class with a span icon (e.g. `close`) that allows the user to manually dismiss it.
  - Link the new stylesheet `static/css/flash_messages.css`.
- `templates/login.html` and `templates/register.html`:
  - Update the inline flash/error notification containers (`.auth-error` and `.auth-success`) to use the standardized styling rules and class naming conventions.

---

## Files to change
- `templates/base.html`: Standardize global flash markup structure to support Toast styles and icons.
- `templates/login.html`: Update login-specific error and flash wrappers.
- `templates/register.html`: Update registration-specific error and flash wrappers.
- `static/js/main.js`: Implement auto-dismiss after 5 seconds and manual dismiss event listeners with exit animations.

---

## Files to create
- `static/css/flash_messages.css`: Styling for toast notifications, container placement (fixed top-right or top-center), distinct themed color schemes using CSS variables (backgrounds, borders, icon colors), close button styling, and entrance/exit keyframe animations.

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

---

## Definition of done
- [ ] Flash messages are rendered in a fixed/floating toast container (e.g., top-right or top-center) and do not push page content layout when they appear.
- [ ] Each flash category (success, error, warning) is styled with distinct, readable color palettes using CSS variables (no hardcoded colors).
- [ ] Each notification includes an appropriate Material Symbols Outlined icon representing its category.
- [ ] Each notification has a working manual close button (`×` or icon) that immediately triggers a dismiss animation and removes the notification.
- [ ] Notifications automatically fade and slide out to dismiss after 5 seconds if not closed manually.
- [ ] The custom styling and dismissal animations are defined in `static/css/flash_messages.css`.
- [ ] Login and registration pages render their error boxes with the same standardized notification aesthetics.
- [ ] Automated tests verify that the templates render notifications correctly and that `flash_messages.css` is served.
