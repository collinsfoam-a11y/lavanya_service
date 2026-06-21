# H2 — UI/UX Wiring, Settings, Modernisation + Theme System

> Phase task spec for the Lavanya Service SPA and backend.
> This document combines the original H2 UI/UX Wiring + Settings scope with the
> Modern UI/UX + Multiple Themes add-on. It is **one phase**, not a separate
> feature branch.

---

## Phase Goal

Modernise the Lavanya Service frontend while keeping all workflows safe, fast,
and staff-friendly, and wire a configurable settings layer that drives theme
choice, UI feature toggles, follow-up defaults, notification/penalty/ERP safety
locks, and default follow-up configuration.

Do not change backend workflow behaviour unless required for UI wiring.

---

## 1. Settings Module (backend + SPA)

Create / extend **Lavanya Service Settings** with these configuration groups.

### 1.1 General Service Defaults
- default next follow-up days per stage (brand, part pending, satisfaction check,
  no-update escalation)
- auto assignment toggles
- default service path and priority

### 1.2 Follow-Up Rules
- enable auto follow-up date calculation
- follow-up due hour
- skip Sundays / holidays
- max no-update counts
- customer notification rules

### 1.3 Notification Settings
- global notification toggle
- dry-run mode toggle
- WhatsApp/SMS enable (default off)
- default channel
- provider names / numbers
- manager approval required

### 1.4 Penalty Settings
- penalty computation toggle
- dry-run mode toggle
- manager approval required
- automatic daily computation
- **ERP posting remains blocked** until fully implemented

### 1.5 ERPNext Settings
- detect ERPNext presence
- mode: Disabled / Read-Only / Draft Only / Posting Locked
- read-only lookup, draft creation, posting only through explicit manager approval

### 1.6 UI Feature Flags
- next-action bar
- workflow timeline
- customer journey summary
- follow-up quality badge
- mobile field mode
- penalty tab / notification tab
- ERP status panel

### 1.7 Theme Preferences
- `default_theme`: Lavanya Light / Lavanya Dark / Lavanya Blue / Lavanya Green /
  High Contrast / Compact Counter Mode
- `allow_user_theme_override` (default 1)
- `compact_mode_enabled` (default 0)
- `large_text_mode_enabled` (default 0)
- `high_contrast_mode_enabled` (default 0)

### 1.8 Safety Locks
Display current safety lock states:
- live notifications off
- ERP posting disabled
- penalty apply disabled
- dry-run modes on

---

## 2. Theme System

Extend `frontend/src/utils/theme.js` into a proper theme engine.

### 2.1 Supported themes
- Lavanya Light
- Lavanya Dark
- Lavanya Blue
- Lavanya Green
- High Contrast
- Compact Counter Mode

### 2.2 Theme token contract
Each theme must define:
- background
- surface
- surfaceElevated
- textPrimary
- textSecondary
- border
- primary
- success
- warning
- danger
- info
- muted
- chip colors
- button colors
- timeline colors
- quality badge colors
- critical / important / normal bucket colors

No hardcoded colors inside components except approved brand-specific values
(e.g. WhatsApp green `#25D366`).

### 2.3 Runtime behaviour
- theme switch applies without page reload
- theme persists in `localStorage` or user preference
- system fallback works if saved theme is invalid
- dark mode remains readable
- high contrast mode is accessible
- compact counter mode reduces spacing for service counter use

---

## 3. Modern UI Refresh

Upgrade the visual design across:
- Ticket Detail
- Today’s Work
- Reports
- Penalty tab
- Notifications tab
- Settings page
- Mobile Field Mode

Focus on:
- clean spacing
- clear cards
- better section hierarchy
- modern buttons
- better chips / badges
- improved empty states
- better loading states
- clear error states
- consistent icons
- mobile-first layout

Do not make the UI decorative at the cost of speed. Staff must still complete
actions quickly.

---

## 4. New / Improved Shared Components

Create or improve shared components where duplication is clear:
- `LavCard`
- `LavSectionHeader`
- `LavBadge`
- `LavChip`
- `LavStatCard`
- `LavActionBar`
- `LavEmptyState`
- `LavLoadingState`
- `LavThemeToggle`
- `LavSafetyLockPanel`

Do not over-engineer. Add shared components only where duplication is clear.

---

## 5. Theme Selector UI

Add a theme selector in `/frontend/settings` or the top-right user/menu area.

Required behaviour:
- preview and switch themes
- theme switch applies without page reload
- persists in localStorage or user preference
- system fallback if saved theme invalid
- dark mode readable
- high contrast accessible
- compact counter mode reduces spacing

---

## 6. Compact Counter Mode

Create a compact theme/mode for showroom/service-counter use.

Purpose:
- show more tickets/actions on small screens
- reduce vertical spacing
- keep action buttons visible
- reduce scrolling

Apply especially to:
- Today’s Work
- Ticket list
- Ticket Detail
- Action modals
- Reports tables

---

## 7. Accessibility

Modern UI must still pass:
- keyboard navigation
- visible focus states
- modal focus trap
- ESC close where safe
- readable contrast
- large-text mode
- no icon-only actions without label/title

Do not remove existing `LavModal` / `LavConfirm` accessibility behaviour.

---

## 8. Tests / Static Checks

Add or extend tests:
- `test_theme_settings_defaults`
- `test_invalid_theme_falls_back_safely`
- `test_user_theme_override_allowed`
- `test_high_contrast_setting_available`
- `test_compact_mode_setting_available`

Static checks:

```bash
grep -R "#[0-9A-Fa-f]\{6\}" frontend/src || true
grep -R "window.confirm" frontend/src || true
grep -R "confirm(" frontend/src || true
```

Expected:
- no new hardcoded component colors
- no native confirm
- theme tokens used consistently

---

## 9. Screenshots Required

Add screenshots under `doc/screenshots/h2_ui_wiring/themes/`:

```text
01-lavanya-light-dashboard.png
02-lavanya-dark-dashboard.png
03-lavanya-blue-theme.png
04-lavanya-green-theme.png
05-high-contrast-theme.png
06-compact-counter-mode.png
07-theme-selector-settings.png
08-mobile-theme-view.png
09-ticket-detail-modernized.png
10-reports-modernized.png
```

---

## 10. Documentation

Create / update:
- `doc/h2_uiux_wiring_report.md`
- `doc/h2_theme_system_report.md`
- `doc/h2_theme_reference.md`
- `doc/lavanya-spa-status.md`
- `doc/lavanya-changelog.md`

`h2_theme_reference.md` must document:
- available themes
- theme purpose
- where theme preference is stored
- how compact mode works
- accessibility rules
- how to add a new theme later

---

## 11. Acceptance Criteria

H2 passes only if:

1. UI is visually modernised without slowing staff workflow.
2. Multiple themes are available.
3. Theme selector works.
4. Theme choice persists.
5. Compact Counter Mode works.
6. High Contrast Mode works.
7. Dark mode remains readable.
8. Mobile layout remains usable.
9. No new hardcoded colors are introduced.
10. Settings defaults are safe and documented.
11. Safety locks are visible and accurate.
12. Tests and static checks pass.
13. Documentation and screenshots are complete.

---

## 12. Safety Boundaries

- No live WhatsApp/SMS sending.
- No ERPNext accounting posting.
- No financial transactions.
- Penalty computation remains advisory/dry-run.
- All new backend logic gated by explicit settings defaults = off.
