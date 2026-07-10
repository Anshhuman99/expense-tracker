# Spec: Responsive Design

## Overview
This feature optimizes the entire Spendly application layout for mobile, tablet, and desktop viewports, ensuring zero horizontal scrolling, excellent legibility, and premium aesthetics. A major element of this is introducing a modern, mobile-friendly hamburger menu for navigation links on smaller screens (< 768px). Additionally, we will enhance the dashboard stats grids, the filter form, form container cards (login, register, add/edit/delete expense), the custom toast container, and the transaction list (transforming the tables to readable card blocks or highly scrollable blocks on mobile), while maintaining accessibility compliance (color contrast, tap targets of at least 44x44px, and logical keyboard navigation).

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
- Step 12: Better Flash Messages

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
  - Introduce a responsive mobile menu toggle button (hamburger icon) inside `.nav-inner`, visible only on screens `< 768px`.
  - Wrap the main navigation links in a container that supports both desktop row layout and mobile drawer/dropdown overlay layout.
  - Set appropriate `aria-expanded` and `aria-controls` properties for the hamburger button to comply with accessibility practices.

---

## Files to change
- `templates/base.html`: Add mobile navigation button structure and mobile-drawer layout class structure.
- `static/js/main.js`: Add Vanilla JavaScript to handle the toggle interaction of the hamburger menu (toggling classes, updating `aria-expanded` attributes, and closing menu when clicking outside).
- `static/css/style.css`:
  - Enhance base layouts (navbar, hero, features, footer, auth forms) with updated media queries.
  - Define mobile-drawer/hamburger classes with sliding or fading transitions using CSS variables only.
  - Adjust margins, padding, and font sizes using clamp/rem values where appropriate to scale down gracefully.
- `static/css/profile.css`:
  - Update stats grid to scale dynamically (e.g. 3 columns on desktop, 2 columns on tablet, 1 column on mobile).
  - Modify `.filters-form` to wrap cleanly, aligning elements and inputs vertically on small viewports without overlapping.
  - Apply responsive styling to `.expense-table`: transform the table on mobile (e.g. at `< 600px`) into a stacked list layout where each row functions as a visually distinct card block, or ensure complete, clean horizontal scroll boundaries within `.table-responsive`.
  - Update edit/delete action button hit areas to meet the minimum size requirement.
- `static/css/add_expense.css` / `static/css/edit_expense.css` / `static/css/delete_expense.css`:
  - Ensure form action buttons (Save/Cancel) wrap and stretch appropriately on small screens rather than breaking out of container boundaries.
- `static/css/analytics.css`:
  - Verify layout responsiveness of coming soon teasers, scaling images and blocks beautifully.
- `static/css/errors.css`:
  - Ensure custom error pages render without content truncation or clipping.

---

## Files to create
No new files.

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
- Ensure all interactive elements (close buttons, hamburger menu, action links, inputs) have a minimum hit target size of 44px x 44px.
- Use logical tab order and visible focus rings (`:focus-visible`) for keyboard navigation.

---


