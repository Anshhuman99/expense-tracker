# Spec: Empty States

## Overview
This feature introduces premium, user-friendly empty states on the dashboard (`/profile`). When a user has logged no expenses yet or when filters yield no matches, we will replace the default empty tables/lists with rich, centered, card-based empty states. These will feature meaningful icons/illustrations, descriptive copy, and contextual call-to-action buttons (such as "Add Your First Expense" or "Clear Filters") to guide the user's next steps.

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

---

## Routes
No new routes.

---

## Database changes
No database changes.

---

## Templates
### Modify
- `templates/profile.html`:
  - Check if the user has no expenses at all (`stats.total_count == 0` and not `is_filtered`). In this scenario, display a large, prominent dashboard empty state card inside the main area instead of the expense table. This card will contain:
    - An illustration or icon (e.g. using a SVG or a styled Material Symbols icon like `receipt_long` or `folder_open`).
    - Title: "No Expenses Logged Yet"
    - Subtitle: "Start tracking your personal expenses to see summary statistics, breakdowns, and your transactions list here!"
    - Primary CTA button: "Add Your First Expense" linking to `/expenses/add`.
  - In the Category Breakdown sidebar, check if the breakdown is empty. If so, display a clean inline placeholder empty state:
    - An icon (like `pie_chart` or `analytics`).
    - Helper text: "No category data available yet."
  - Check if filters are active but return zero transactions (`is_filtered` is True and `len(recent_expenses) == 0`). In this case:
    - Render a filtered-empty-state card inside the main card container (below the filter form).
    - It will contain an icon/illustration (e.g. `search_off` or `filter_list_off`).
    - Title: "No Matches Found"
    - Subtitle: "We couldn't find any expenses matching your active filters. Try clearing your filters or adjusting your date range."
    - Button: "Clear Active Filters" linking back to the base `/profile` dashboard.

---

## Files to change
- `templates/profile.html`: Update the conditionals to handle and display rich empty states for empty database records, filtered empty records, and empty category breakdown.

---

## Files to create
- `static/css/empty_states.css`: Premium empty state styles, containing styling for empty-state containers, icons/illustrations, header titles, helper text, and CTA buttons. (Make sure this stylesheet is linked in the dashboard/profile template).
- `tests/test_11-empty-states.py`: Test suite verifying:
  - When a new user logs in (with 0 expenses) and accesses `/profile`, the main empty state (No Expenses Logged Yet) with the "Add Your First Expense" button is displayed.
  - When a user has expenses but applies a filter that returns nothing, the filter-empty-state is displayed, along with a "Clear Active Filters" button/link.
  - Checking that all templates render and contain correct styling classes.

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
- [ ] A user with 0 expenses sees a premium dashboard empty state in the main content area of `/profile`.
- [ ] The dashboard empty state includes a clean layout, a styled icon/illustration, descriptive text, and a working primary button to "Add Your First Expense".
- [ ] A user who filters their expenses such that 0 results are returned sees a filtered empty state card.
- [ ] The filtered empty state includes an icon, descriptive text, and a working button or link to "Clear Active Filters".
- [ ] The Category Breakdown sidebar shows a simple, clean placeholder when there are 0 expenses.
- [ ] All empty state styles are defined in `static/css/empty_states.css` and use CSS variables for colors, typography, borders, and margins.
- [ ] Automated tests in `tests/test_11-empty-states.py` cover both primary empty states (database empty and filter empty) and pass successfully.
