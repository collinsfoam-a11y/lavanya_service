# H2 Theme Reference

> Quick reference for the Lavanya Service theme system.

---

## Available themes

| Id | Label | When to use |
|----|-------|-------------|
| `lavanya-light` | Lavanya Light | Default service desk and office use. |
| `lavanya-dark` | Lavanya Dark | Low-light environments, evening shifts. |
| `lavanya-blue` | Lavanya Blue | Brand-aligned blue tint. |
| `lavanya-green` | Lavanya Green | Calmer, high-readability green tint. |
| `high-contrast` | High Contrast | Accessibility / vision impairment. |
| `compact-counter` | Compact Counter Mode | Showroom / service counter with small screens. |

---

## Where theme preference is stored

- **User device**: `localStorage.getItem('lavanya-theme')`.
- **Organisation default**: `Lavanya Service Settings.default_theme` (Frappe Single DocType).
- **Override permission**: `Lavanya Service Settings.allow_user_theme_override`.

At runtime the SPA trusts the localStorage value if the user is allowed to
override; otherwise it falls back to the organisation default. Invalid values
resolve to `lavanya-light`.

---

## How compact mode works

Compact Counter Mode (`compact-counter`):

- Sets `data-compact="true"` on `<html>`.
- Reduces `--lav-spacing-scale` to `0.75`.
- Shrinks gutters, container padding, card padding, and metric heights.
- Disables metric hover lift to keep the UI dense and fast.

Target screens: Today’s Work, ticket lists, ticket detail, action modals,
reports tables.

---

## Accessibility rules

- All themes must maintain WCAG 2.1 AA contrast for normal text.
- `high-contrast` theme uses black/white plus high-contrast accent colors.
- Focus states are visible (`outline: 2px solid var(--lav-primary)`).
- `prefers-reduced-motion` disables animations.
- Icon-only controls must have `aria-label` or visible text.

---

## How to add a new theme later

1. Open `frontend/src/utils/theme-engine.js`.
2. Add a new entry to `THEMES` with a unique id, label, description, tokens,
   spacing, and typography.
3. Ensure the token map covers every `--lav-*` variable used in
   `frontend/src/index.css` and `frontend/tailwind.config.mjs`.
4. Add the theme name to `THEME_OPTIONS` in
   `lavanya_service/setup/ui_settings.py` so it appears in the backend default.
5. Optionally add a swatch gradient to `LavThemeToggle.vue`.
6. Add a test in `lavanya_service/tests/theme_settings.py`.
7. Rebuild the SPA.

---

## Token contract

Every theme must define:

- `background`, `surface`, `surfaceElevated`
- `textPrimary`, `textSecondary`, `textMuted`
- `border`, `borderLight`
- `primary`, `primaryContainer`, `onPrimary`, `onPrimaryContainer`
- `secondary`, `secondaryContainer`, `onSecondary`
- `tertiary`, `tertiaryContainer`, `onTertiary`
- `success`, `successContainer`, `onSuccess`
- `warning`, `warningContainer`, `onWarning`
- `danger`, `dangerContainer`, `onDanger`
- `info`, `infoContainer`, `onInfo`
- `muted`, `chipDefault`, `chipDefaultText`
- `timelineCompleted`, `timelineCurrent`, `timelineWaiting`, `timelineBlocked`, `timelinePending`
- `qualityGood`, `qualityNeedsUpdate`, `qualityAtRisk`, `qualityCritical`
- `bucketCritical`, `bucketImportant`, `bucketNormal`

---

## Related docs

- `doc/h2_uiux_wiring_settings_modernisation_theme_system.md` — full H2 task spec.
- `doc/h2_theme_system_report.md` — implementation report.
- `doc/h2_uiux_wiring_report.md` — broader UI/UX wiring report.
