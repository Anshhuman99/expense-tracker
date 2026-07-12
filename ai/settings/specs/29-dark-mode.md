# Spec: Dark Mode

## Overview

Add an optional dark appearance for the entire Spendly application. Users can toggle between light and dark themes from the navbar. The selected preference is persisted in `localStorage` so it survives page reloads and browser sessions. The implementation relies entirely on CSS custom properties (variables) — no hardcoded colours anywhere.

## Dependencies

No new Python packages required. This is a purely frontend feature (CSS + JavaScript).

## Acceptance Criteria

- [ ] A theme toggle button is visible in the navbar (both logged-in and logged-out states)
- [ ] Clicking the toggle switches between light and dark themes instantly with no page reload
- [ ] The selected theme persists across page reloads via `localStorage`
- [ ] On first visit (no stored preference), the app defaults to light mode
- [ ] All pages render correctly in both light and dark modes with readable text, proper contrast, and consistent styling
- [ ] The toggle button displays a sun icon (☀️) in dark mode and a moon icon (🌙) in light mode
- [ ] Flash messages, toasts, modals, and all interactive elements are properly themed
- [ ] Charts and analytics visuals remain legible in dark mode
- [ ] No FOUC (Flash of Unstyled Content) — theme is applied before first paint via a blocking script in `<head>`

## Database Changes

None. Theme preference is stored client-side in `localStorage`.

## Routes

No new routes needed. This is a frontend-only feature.

## Templates

### Modified

- `templates/base.html` — Add theme toggle button to navbar, add inline blocking script in `<head>` to prevent FOUC

## Files to Modify

- `templates/base.html` — Theme toggle button in navbar + FOUC prevention script in `<head>`
- `static/css/style.css` — Add `[data-theme="dark"]` CSS variable overrides for all colour variables
- `static/js/main.js` — Add theme toggle logic and localStorage persistence

## Files to Create

None. All changes go into existing files.

## Validation

- Theme toggle must be keyboard-accessible (focusable, activatable with Enter/Space)
- Dark mode colours must have sufficient contrast (WCAG AA minimum)
- No hardcoded colours allowed — everything must use CSS variables

## Edge Cases

- First-time visitor with no localStorage: defaults to light mode
- User clears localStorage: reverts to light mode on next visit
- Rapid toggling: must not cause visual glitches
- Pages with charts (analytics.html, trends.html): chart colours must adapt
- Print: should print in light mode regardless of selected theme
- Mobile nav menu: must be properly themed in both modes

## Definition of Done

- [ ] Theme toggle button present and functional in navbar
- [ ] Dark mode CSS variables defined and applied to all pages
- [ ] Theme persists across page reloads via localStorage
- [ ] No FOUC on page load
- [ ] All existing pages render correctly in both themes
- [ ] Toggle is keyboard-accessible
- [ ] Tests pass
- [ ] No hardcoded colours introduced

### Implementation Constraints
- No SQLAlchemy/ORMs (use raw SQLite via database/db.py)
- Parameterised SQL queries only
- Passwords hashed with werkzeug.security
- CSS variables only (no hardcoded colours in HTML/CSS)
- All templates must extend base.html

Implementation must follow CLAUDE.md.
