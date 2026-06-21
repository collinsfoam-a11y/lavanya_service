# Frontend Phase A — UI Hardening Report

## Scope
Improve the Lavanya Service SPA for production staff use: accessibility, keyboard behavior, color-token consolidation, dialog unification, and action visibility hardening.

## Changes by File

### New Files

| File | Purpose |
|------|---------|
| `frontend/src/utils/theme.js` | Single source of truth for all color tokens (COLORS, STATUS_HUE, DUE_HUE, PROMISE_HUE, ESC_HUE, FOLLOWUP_STAGE_HUE, SATISFACTION_HUE, INFORMED_HUE, ACCENT_METRICS, PAYMENT_HUE, EXPANSION_HUE, DARK_MODE_OVERRIDES, BLOCK_HUE) and chip/accentMetric functions |
| `frontend/src/utils/confirm.js` | Reactive composable `useConfirm()` for async confirm dialog state |
| `frontend/src/components/LavModal.vue` | Reusable dialog wrapper with focus trap, aria-modal, ESC close, focus restoration, keyboard submit |
| `frontend/src/components/LavConfirm.vue` | Confirmation dialog built on LavModal |

### Modified Files

| File | What changed |
|------|-------------|
| `frontend/src/utils/index.js` | Re-exports all color/chip exports from `theme.js` |
| `frontend/src/components/AppShell.vue` | LavConfirm for logout, keyboard shortcuts (`g+t` → Tickets, `?` → help toast), `role="search"` on search form, `aria-hidden` on decorative avatar icon, ESC handles in modals |
| `frontend/src/pages/TodayWork.vue` | `<li>` cards get `tabindex`, `role="button"`, `@keydown.enter/space`, `aria-label`; "Open" buttons visible on `group-focus-within`; hardcoded colors replaced with `promiseChip`/`dueChip`; empty-state inline styles replaced with classes |
| `frontend/src/pages/Tickets.vue` | `aria-sort` now dynamically reflects active sort column (ascending/descending/none); `aria-label` on sort headers shows direction only for active column; sort arrows wrapped in `<span aria-hidden="true">`; "Open" buttons visible on keyboard focus; hardcoded chip colors replaced with `promiseChip` |
| `frontend/src/pages/NewTicket.vue` | LavConfirm for clear-form (pre-existing) |
| `frontend/src/pages/Reports.vue` | Removed duplicate `STATUS_HUE`/`chip`/`hexToRgba`; imports from `@/utils` (pre-existing) |
| `frontend/src/components/TicketDetail.vue` | **4 inline modals** converted to `<LavModal>` (Need Invoice, Create Product Receipt, Ready for Pickup, Generic Action); native `confirm()` replaced with `useConfirm()`; `aiStatusChip`, `FOLLOWUP_ACTION_STYLES`, `followupBanner` now use `COLORS`/`hexToRgba` from theme; `<LavModal>` + `useConfirm` imported |
| `frontend/src/components/LavModal.vue` | Focus trap (Tab/Shift+Tab wrapping), `aria-describedby` pointing to body slot, focus restoration with try/catch guard, danger-mode focus on submit button, `aria-live="assertive"` on error, dynamic close-button `aria-label` |
| `frontend/src/components/LavConfirm.vue` | `aria-describedby` via `body-id` prop, confirm message ID linking |

## Accessibility Audit Results

| Category | Issues Found | Issues Fixed | Remaining |
|----------|-------------|-------------|-----------|
| Native confirm() | 2 (TicketDetail submitAction, AppShell logout) | 2 | 0 |
| Inline modals missing focus trap | 4 (TicketDetail) | 4 | 0 |
| Inline modals missing aria-describedby | 4 | 4 | 0 |
| Hover-only invisible buttons (keyboard) | 2 (TodayWork, Tickets) | 2 | 0 |
| Missing keyboard activation on cards | 1 (TodayWork `<li>`) | 1 | 0 |
| aria-sort hardcoded "none" | 6 columns (Tickets) | 6 | 0 |
| Sort arrow aria-hidden missing | 6 | 6 | 0 |
| Sort aria-label always shows direction | 6 | 6 | 0 |
| Hardcoded hex colors outside theme.js | ~15 locations | 15 | 0 |
| Modal focus trap missing | 1 (LavModal) | 1 | 0 |
| Keyboard shortcuts | 0 | 2 (`g+t`, `?`) | `g+n` → New Ticket |
| Search form role | 1 | 1 | 0 |
| Avatar icon aria-hidden | 1 | 1 | 0 |
| Empty-state inline styles | 1 (TodayWork) | 1 | 0 |

## Keyboard Behavior

- `g+t` navigates to Tickets page
- `?` shows a help toast with available shortcuts
- LavModal opens with first focusable input focused (or last for danger actions)
- LavModal close restores focus to trigger element
- Tab wraps within modal (focus trap)
- ESC closes non-destructive modals
- `<li>` cards in TodayWork activate on Enter/Space

## Build

```
vite v5.4.21 building for production...
✓ 44 modules transformed.
✓ built in 3.73s
```

## Final Closure Verification

| Check | Result |
|---|---|
| Native confirm search (grep `confirm(` in `src/`) | **Pass** — all 5 matches are `useConfirm()` calls, not `window.confirm()` |
| Hardcoded color search (grep `#[0-9A-Fa-f]{6}` in `src/`) | **Pass** — all component colors use `COLORS.*` from `theme.js`. Intentional exceptions: WhatsApp brand green `#25D366` in `TicketDetail.vue:38` (brand-specific, not suitable for theming) |
| Danger confirmation modal screenshot | **Pass** — `doc/screenshots/03-danger-confirm-modal.png` |
| Validation error state screenshot | **Pass** — `doc/screenshots/04-validation-error.png` |
| Tickets table with filter controls screenshot | **Pass** — `doc/screenshots/02-tickets-filter.png` |
| Dark mode modal screenshot | **Pass** — `doc/screenshots/05-dark-mode-modal.png` |

### Color fixes applied during closure
- `utils/index.js` — `followStyle()` now uses `COLORS.onSurfaceVariant` / `COLORS.error` / `COLORS.warning`
- `components/SlaBadge.vue` — 8 hardcoded colors → `COLORS.success/error/neutral/secondary/warning`
- `pages/TodayWork.vue` — 5 hardcoded hues in `intel` computed + badge bg → `COLORS.*`
- `pages/NewTicket.vue` — 3 customer lookup hint colors → `COLORS.success/warning/error`
- `pages/Reports.vue` — 5 chart/legend colors → `COLORS.primary/success`
- `components/TicketDetail.vue` — ~10 inline hex values → `:style` bindings via `COLORS.*`
- `utils/theme.js` — added `COLORS.info` (#2563eb) and replaced 4 hardcoded usages

## Screenshots

All screenshots are in `doc/screenshots/`:

| File | Content |
|---|---|
| `01-todays-work.png` | Today's Work dashboard with queue |
| `02-tickets-filter.png` | Tickets table with filter chips, sort headers, search |
| `03-danger-confirm-modal.png` | Close Ticket confirmation dialog (danger mode) |
| `04-validation-error.png` | Required field validation error state |
| `05-dark-mode-modal.png` | Dark theme with confirmation modal |

## Remaining (out of scope)

- Address color duplication in `frontend/src/index.css` (hardcoded hex in `.lav-shell`, `.lav-metric`, `.lav-queue`, `.lav-chip`)
- End-to-end audit with axe-core or Playwright a11y check
- Add `g+n` → New Ticket shortcut
- Add skip-to-main navigation link
