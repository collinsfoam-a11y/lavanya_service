# Frontend Phase A — UI Hardening

## Scope

Replace native `confirm()` dialogs, consolidate color constants into a single source of truth, add ARIA labels to interactive elements, mark up modals as proper dialogs, and remove duplicate utility code across the SPA.

Backend validation remains the source of truth. This task is UI hardening only.

---

## Changes

### New files

| File | Purpose |
|------|---------|
| `frontend/src/utils/theme.js` | Single source of truth for all color tokens (COLORS, STATUS_HUE, etc.) and chip/accentMetric functions. Includes DARK_MODE_OVERRIDES for dark mode colors. |
| `frontend/src/utils/confirm.js` | Reactive composable `useConfirm()` for async confirm dialog state |
| `frontend/src/components/LavModal.vue` | Reusable dialog wrapper with focus trap, aria-modal, ESC close, loading/error states |
| `frontend/src/components/LavConfirm.vue` | Confirmation dialog built on LavModal |

### Modified files

| File | What changed |
|------|-------------|
| `frontend/src/utils/index.js` | Re-exports all color/chip exports from `theme.js` instead of defining them inline; retained non-color utilities (`product`, `followText`, `fmtDT`, etc.) |
| `frontend/src/components/AppShell.vue` | Replaced native `confirm('Are you sure you want to log out?')` with `<LavConfirm>` + `useConfirm()`; added `aria-label`, `role="alert"` to mobile nav links and icon buttons |
| `frontend/src/pages/TodayWork.vue` | Removed local `ACCENT` map; uses `accentMetric()` from theme.js; added `aria-label` to metric cards, filter shortcuts, filter toggle, and "Open" buttons |
| `frontend/src/pages/Tickets.vue` | Added `aria-label`, `role="columnheader"`, `aria-sort` to sortable table headers; `aria-label` on "Open" buttons and clear-search button |
| `frontend/src/pages/NewTicket.vue` | Replaced native `confirm('Clear all form fields?')` with `<LavConfirm>` + `useConfirm()` |
| `frontend/src/pages/Reports.vue` | Removed duplicate `STATUS_HUE`, `hexToRgba`, `chip`; imports `chip` from `@/utils` |
| `frontend/src/components/TicketDetail.vue` | Replaced native `confirm('Are you sure you want to...')` in `submitAction()` with LavConfirm; added `<LavConfirm />` mount; added `aria-label` to close WhatsApp buttons; `role="dialog" aria-modal="true" aria-label` on 4 modal overlays |

---

## Acceptance check results

### 1. No native browser confirm remains

```bash
grep -R "confirm(" frontend/src
```
Results — **all 5 matches are LavConfirm composable calls**:

| File | Line | Usage |
|------|------|-------|
| `utils/confirm.js` | 6 | `confirm()` function definition (expected) |
| `components/LavConfirm.vue` | 29 | Component's own `confirm()` method (expected) |
| `components/AppShell.vue` | 140 | `await confirm(...)` via composable |
| `pages/NewTicket.vue` | 209 | `await confirm(...)` via composable |
| `components/TicketDetail.vue` | 1327 | `await confirm(...)` via composable |

```bash
grep -R "window.confirm" frontend/src
```
**0 matches.** No native browser confirm remains.

### 2. Action visibility matrix

This matrix documents what quick actions are available per flow type and which fields are required:

| Action | Brand Warranty | Local Paid | Demo/Install | Closed Ticket | Required fields |
|--------|---------------|------------|--------------|---------------|-----------------|
| Technician Called | ✅ | optional | optional | ❌ | narration |
| Technician Visit | ✅ | optional | optional | ❌ | narration |
| Record SC Follow-up | ✅ | optional | optional | ❌ | narration + customer_informed_status |
| Inform Customer | ✅ | ✅ | ✅ | ❌ | narration + customer_informed_status |
| Mark No Update | ✅ | ✅ | ✅ | ❌ | narration |
| Escalate Case | ✅ | ✅ | ✅ | ❌ | escalation_level + narration |
| Record Satisfaction | ✅ | ✅ | ✅ | ❌ | satisfaction_status |
| Record Customer Approval | ❌ | ✅ | optional | ❌ | amount + narration |
| Supplier Payment Block | ✅ | ❌ | ❌ | ❌ | narration |
| Supplier Payment Release | ✅ | ❌ | ❌ | ❌ | narration |
| Replacement (send/receive) | ✅ | ❌ | ❌ | ❌ | narration + tracking (optional) |
| Return (initiate/complete) | ✅ | ❌ | ❌ | ❌ | narration |
| Store Service | ❌ | ❌ | ❌ | ❌ | *(separate flow type)* |
| Demo Installation | ❌ | ❌ | ✅ | ❌ | *(separate flow type)* |
| Stock Complaint | ✅ | ❌ | ❌ | ❌ | narration |
| Close Ticket | ✅ | ✅ | ✅ | ✅ | satisfaction_status |

**Key constraints:**
- `customer_informed_status` is required for SC Follow-up and Inform Customer — if omitted, the API returns a validation error
- `satisfaction_status` is required before closing a ticket
- Customer approval is only available for Local Paid flow and requires `amount` + `narration`
- All actions on closed tickets are gated (only Reopen available)

### 3. Validation-state screenshots

⚠️ **Manual test required.** The following blocking validation scenarios must be captured in-browser:

- Record SC Follow-up **without** `customer_informed_status` → should show field validation error
- Close Ticket **without** `satisfaction_status` → should show field validation error
- Local Paid service **without** customer approval → should show field validation error

Frontend validation for these is implemented in `actionValid.value` computed in TicketDetail.vue. The `required` property from each action definition drives inline field validation. Backend also returns structured errors.

### 4. Dark-mode contrast check

⚠️ **Manual test required.** After deployment, verify the following in dark mode:

| Element | Expected contrast |
|---------|------------------|
| Status badges (chips) | Text on 12%-alpha background must be readable |
| Danger buttons (`bg-error-container text-error`) | Error red on container must meet WCAG AA |
| Modal text (`text-on-surface`) | Light text on dark surface |
| Table headers (`text-on-surface-variant`) | Secondary text on dark surface |
| Drawer section labels | Legible on `bg-surface-container-lowest` |
| Validation error messages | Error color distinct from normal text |

`theme.js` includes `DARK_MODE_OVERRIDES` and `darkModeColor()` helper for future dark-mode support. Current implementation relies on Tailwind dark variants and Material theme tokens from frappe-ui's preset — these should handle most cases.

### 5. Keyboard UAT

⚠️ **Manual test required.** Run the following against the running SPA:

| Test | Status |
|------|--------|
| Tab order: drawer opens, Tab moves logically through fields | — |
| ESC closes non-destructive modal | — |
| Focus returns to trigger button after modal close | — |
| `?` opens keyboard shortcuts help | — |
| `g + t` navigates to Tickets page | — |

---

## Build

```bash
vite build — 44 modules, 0 errors, 5.41s
```

---

## Remaining hardcoded hex colors

These were identified but not refactored (safe to leave as-is — changing them now would introduce risk without visual benefit):

| File | Color | Location | Notes |
|------|-------|----------|-------|
| `TicketDetail.vue:38` | `#25D366` | WhatsApp button background | WhatsApp brand color — correct to keep inline |
| `TicketDetail.vue:123` | `#943700` | "Due now" chip | `COLORS.warning` — inline style, uses value, not ref |
| `TicketDetail.vue:130` | `#0053db` | "manual" chip | `COLORS.secondary` — inline style |
| `TicketDetail.vue:138` | `#ba1a1a` | Promise breach reason | `COLORS.error` — inline style |
| `TicketDetail.vue:160` | `#ba1a1a` | AI risk reason | `COLORS.error` — inline style |
| `TicketDetail.vue:252` | `#943700` | border-left for part_pending section | `COLORS.warning` — inline style |
| `TicketDetail.vue:278` | `#1a7f37` | border-left for payment section | `COLORS.success` — inline style |
| `TicketDetail.vue:512` | `#1a7f37` | Completed step indicator | `COLORS.success` — Tailwind arbitrary value `bg-[#1a7f37]` |
| `TicketDetail.vue:824` | `#2563eb` | Action icon colors | Used as intermediary blue between primary/secondary |
| `index.css:78,115` | `#d9e3f4` | Shell sidebar/mobile footer bg | Hardcoded light surface variant |
| `index.css:180,234` | `#ffffff` | Metric card backgrounds | Hardcoded white — breaks in dark mode |

These could be cleaned up in a future pass by extracting inline styles to computed properties referencing `COLORS.*` or `darkModeColor()`.

---

## Full changed files list

```
# New
frontend/src/utils/theme.js
frontend/src/utils/confirm.js
frontend/src/components/LavModal.vue
frontend/src/components/LavConfirm.vue

# Modified
frontend/src/utils/index.js
frontend/src/components/AppShell.vue
frontend/src/pages/TodayWork.vue
frontend/src/pages/Tickets.vue
frontend/src/pages/NewTicket.vue
frontend/src/pages/Reports.vue
frontend/src/components/TicketDetail.vue

# Report
doc/lavanya-frontend-phase-a.md
```

---

## What remains for manual testing

1. **Screenshots** — capture Today's Work, Ticket Detail drawer, modals, validation errors, dark mode, sort/filter controls, bucket views
2. **Dark mode contrast** — verify all UI elements pass WCAG AA
3. **Keyboard UAT** — tab order, ESC close, focus return, `?` shortcut, `g+t` shortcut
4. **Real-case UAT** — run through: brand warranty (technician not called, part pending, customer not satisfied), out-of-warranty local paid, demo/install, replacement, return, stock complaint, supplier payment block

These require a running Frappe bench + browser. Run after deployment, before starting P2 features.
