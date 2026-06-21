# Lavanya Service — Change Log

> **Mandatory reading for any AI agent before making changes.**
> Per `../AGENTS.md` Rule 1: every change must be documented here with the
> format below. This file serves as the audit trail and synchronization point
> for all agents working on this app.

---

## 2026-06-21 19:00 — State-Logging: Follow-up Log child table + re-entry detection

### What changed
- `lavanya_service/setup/followup_fields.py` — Created `Follow-up Log Entry` child table doctype (6 fields: stage, completed_at, user, is_re_entry, action_label, notes). Added `followup_log` Table field and `lavanya_followup_log_section` Section Break to HD Ticket.
- `lavanya_service/hooks.py` — Added `Follow-up Log Entry` to DocType fixture exports. Added `followup_log` and `lavanya_followup_log_section` to Custom Field fixture exports.
- `lavanya_service/workflow/quick_actions.py` — Added `_append_followup_log()` helper that detects re-entry and requires notes on revisited stages. Added log calls to all 25 stage transition sites. Added `notes` parameter to `record_sc_followup`, `inform_customer`, `customer_confirmed`.
- `lavanya_service/api/workflow_actions.py` — Updated `record_sc_followup`, `inform_customer`, `customer_confirmed` wrappers to pass `notes` through.
- `lavanya_service/api/stitch_console.py` — Added `followup_log` array to ticket detail API response.
- `frontend/src/components/lavanya/tickets/LavWorkflowTimeline.vue` — Rewrote to derive completed/active/pending state from `followup_log` instead of `followup_stage`. Shows re-entry count badges.
- `lavanya_service/tests/e2e_followup_scenario.py` — Updated test calls to pass `notes` on re-entries. Added `2j2 followup_log has entry` assertion. Total: 147/147 PASS.

### Previous state
- `followup_stage` was overwritten on every transition — only the current stage was known
- No structured history of stage transitions
- No re-entry detection
- UI derived state from current `followup_stage` only

### Current state
- Every stage transition appends a `Follow-up Log` entry with timestamp, user, re-entry flag
- Re-entry is detected when a stage already exists in the log — requires mandatory notes
- UI derives completed/active/pending from log history
- Full journey audit trail preserved in structured child table

### Why changed
- Shift from "State-Overwrite" to "State-Logging" architecture
- Enable UI to show which stages were completed, how many times, and when
- Support re-entry loop with audit trail

### What was obtained
- Structured follow-up history on every ticket
- Re-entry detection with mandatory reason
- UI timeline driven by log, not by current stage only
- 147/147 E2E tests passing
- Safety scan: 10/10 PASS

### Compatibility notes
- `followup_stage` field still exists and is still written — backward compatible
- Old tickets without log entries will show empty timeline (future steps only)
- No breaking changes to existing API response shapes

---

## 2026-06-21 13:00 — S1-TEST-FIX-R1: Missing part_fitted_confirmed field + legacy test patch

### What changed
- `lavanya_service/setup/followup_fields.py` — Added `part_fitted_confirmed` Check field to the Part Tracking section. This field was referenced by `_assert_closure_gates` in `quick_actions.py` but never defined as a custom field, causing an unconditional block on any ticket with `part_required=1`.
- `lavanya_service/hooks.py` — Added `part_fitted_confirmed` to the fixture export list so it persists across migrations.
- `lavanya_service/tests/e2e_followup_scenario.py` — Rewrote `test_14_closure_rule` to match the v2.1 shared gate contract:
  - 14a: close_ticket blocks without satisfaction (negative) — PASS
  - 14b: close_ticket blocks with part_required=1, part_fitted_confirmed=0 (negative) — PASS
  - 14c: close_ticket succeeds after part gate satisfied (positive) — PASS
  - 14d: customer_confirmed blocks with part_required=1, part_fitted_confirmed=0 (negative) — PASS
  - 14e: customer_confirmed succeeds after part gate satisfied (positive) — PASS

### Previous state
- `part_fitted_confirmed` was referenced in `_assert_closure_gates` (quick_actions.py:301) but never defined as a custom field
- Any ticket with `part_required=1` could never be closed (unconditional block)
- Legacy test_14 assumed customer_confirmed could bypass the part gate (invalid under v2.1)
- `bench migrate` did not create the column because it was not in the field definitions

### Current state
- `part_fitted_confirmed` is a proper Check field on HD Ticket (default 0)
- Closure gate correctly blocks when part_required=1 AND part_fitted_confirmed=0
- Closure gate correctly allows when part_fitted_confirmed=1
- Both close_ticket AND customer_confirmed go through the same shared gate
- All 143 e2e tests pass: TOTAL: 143 | PASS: 143 | FAIL: 0

### Why changed
- P0 operational defect: closure gate referenced a non-existent field
- Legacy test validated old behavior that bypassed physical gates
- v2.1 doctrine: closure is only permitted when all sub-gates are satisfied

### What was obtained
- `part_fitted_confirmed` field created and migrated to database
- test_14 rewritten with 5 assertions (2 negative, 3 positive)
- 143/143 e2e tests pass
- No production closure logic weakened

### Compatibility notes
- `bench --site lavanya-dev.localhost migrate` ran successfully
- Existing close_ticket and customer_confirmed functions unchanged
- `_assert_closure_gates` unchanged — was already correct, just missing the field definition
- No migration steps needed beyond bench migrate (already done)

---

## 2026-06-21 13:30 — S1-GATE-HARDEN-R1: customer_confirmed bypass fix + confirmation gate + verification gate refinement

### What changed
- `lavanya_service/workflow/quick_actions.py`:
  - Added `_CUSTOMER_CONFIRM_RESOLVABLE_STAGES` constant: `{None, "", "customer_confirmation_pending", "customer_satisfied"}` — stages where customer_confirmed is the correct resolution path.
  - `customer_confirmed()`: Added `previous_stage` check before overwriting `followup_stage`. Now blocks if stage is in `_CLOSURE_VERIFICATION_STATES` but not in `_CUSTOMER_CONFIRM_RESOLVABLE_STAGES`. Prevents bypassing unresolved technician/appointment/service states.
  - `_assert_closure_gates()`: Added `customer_confirmation_received` check — ticket cannot close without customer confirmation. Also refined verification gate to allow `customer_confirmation_pending` when `customer_confirmation_received="Yes"`.
  - `close_ticket()`: Moved `doc.customer_confirmation_received = customer_confirmation_received` before `_assert_closure_gates()` call so the gate sees the correct value.
- `lavanya_service/tests/e2e_followup_scenario.py` — Rewrote `test_14_closure_rule` with 10 assertions:
  - 14a: close_ticket blocks without satisfaction (negative)
  - 14b: close_ticket blocks with part pending (negative)
  - 14c: close_ticket succeeds with all gates satisfied (positive)
  - 14d: Status = Closed after close_ticket
  - 14e: customer_confirmed blocks unresolved technician_call_pending (negative)
  - 14f: customer_confirmed blocks unresolved appointment_missed (negative)
  - 14g: customer_confirmed blocks unresolved no_technician_update (negative)
  - 14h: customer_confirmed blocks with part pending (negative)
  - 14i: customer_confirmed succeeds when only customer confirmation is pending (positive)
  - 14j: Status = Closed after customer_confirmed

### Previous state
- `customer_confirmed()` overwrote `followup_stage` to `"customer_satisfied"` BEFORE the gate check, erasing unresolved verification states
- No `customer_confirmation_received` check in the shared gate
- Verification gate blocked `customer_confirmation_pending` even when customer had confirmed
- `close_ticket()` set `customer_confirmation_received` on the doc AFTER the gate check

### Current state
- `customer_confirmed()` checks previous stage before overwriting — blocks if in unresolved service loop
- `_assert_closure_gates()` requires `customer_confirmation_received="Yes"` for all closure paths
- Verification gate allows `customer_confirmation_pending` only when `customer_confirmation_received="Yes"`
- Both paths set doc fields BEFORE the gate check

### Why changed
- v2.1 control invariant: customer_confirmed must not bypass unresolved service/technician states
- Shared gate must be complete: physical + verification + satisfaction + confirmation gates
- No side-door around verification loops

### What was obtained
- 146/146 e2e tests pass: TOTAL: 146 | PASS: 146 | FAIL: 0
- No bypass exists for unresolved technician/appointment/no-update states
- Both close_ticket and customer_confirmed enforce the same 4 gates
- Production code hardened, not weakened

### Compatibility notes
- `_CLOSURE_VERIFICATION_STATES` unchanged
- `_CUSTOMER_CONFIRM_RESOLVABLE_STAGES` is new constant — only affects customer_confirmed
- close_ticket behavior unchanged (already required customer_confirmation_received="Yes")
- No migration steps needed

## 2026-06-21 12:00 — UI-ENGINE-R1: Outcome-Capture Console with config-driven OUTCOME_MAP

### What changed
- `frontend/src/config/outcome-map.js` — NEW: Config-driven OUTCOME_MAP with `STAGE_ACTIONS` (12 followup_stage values mapped to primary/secondary/danger actions), `STATUS_ACTIONS` (5 ticket statuses), `ACTION_REGISTRY` (25+ action definitions with labels, icons, colors, endpoints, required fields), `resolveActions()`, `getPrimaryAction()`, `canCloseTicket()`.
- `frontend/src/components/ActionScreen.vue` — NEW: Engine-driven outcome capture screen with ticket summary, primary action display, outcome-specific buttons (success/partial/failed/parked), successor actions display, loading/success states, slide-up animation.
- `frontend/src/components/TicketDetail.vue` — Updated imports to include OUTCOME_MAP config. Updated `nextActions` computed to use `resolveEngineActions()` from config instead of hardcoded logic. Updated `closureGuard` to use `engineCanClose()` from config.
- `frontend/src/pages/TodayWork.vue` — Added ActionScreen import. Added `selectedActionTicket` state. Added `enrichedGroups` computed that enriches each ticket with `engineActions`, `primaryAction`, `primaryActionLabel`, `primaryActionIcon`, `primaryActionColor`. Updated template to show action buttons next to each ticket. Added scoped CSS for action buttons and ticket row layout.

### Previous state
- TicketDetail.vue had hardcoded `nextActions` logic that didn't follow the config-driven pattern
- TodayWork.vue showed tickets without showing what action the engine recommends for each ticket
- No ActionScreen component existed — outcome capture required navigating to TicketDetail and finding the right button
- No config-driven OUTCOME_MAP existed — action definitions were scattered across multiple files

### Current state
- Config-driven OUTCOME_MAP provides single source of truth for all action definitions
- Each ticket in TodayWork queue shows its engine-determined primary action with a prominent button
- ActionScreen provides action-specific outcome capture with verb-specific buttons
- Successor actions are displayed after submission
- All action definitions are centralized in one config file
- Build passes with 68 modules transformed

### Why changed
- UI-ENGINE-R1 spec requires "The engine decides. The UI confesses" pattern
- Need config-driven approach to maintain consistency across 25+ action types
- Outcome buttons replace manual form filling for better UX
- Centralized action definitions make it easier to add new actions without modifying multiple files

### What was obtained
- Config-driven OUTCOME_MAP with 25+ action definitions
- ActionScreen component with outcome-specific buttons
- TodayWork shows engine-determined actions for each ticket
- TicketDetail uses config for next actions and closure guard
- Build passes: `node node_modules/vite/bin/vite.js build` — PASS, 68 modules, 6.37s
- No breaking changes to existing functionality

### Compatibility notes
- No backend changes — all frontend only
- Existing TicketDetail functionality preserved
- Existing TodayWork metric grid and filters preserved
- No schema changes required
- No migration steps needed

---

## Changelog entry format

```markdown
## YYYY-MM-DD HH:MM — Short title of change

### What changed
- `path/to/file.py` — specific description of what was modified/added/removed

### Previous state
What the code looked like / what existed before / what was missing

### Current state
What the code looks like now / what was added / what changed

### Why changed
Why this change was necessary (bug fix, feature request, refactor, etc.)

### What was obtained
The measurable outcome: fixed bug, new capability, performance gain, etc.

### Compatibility notes
- What existing code was checked for breakage
- What tests were run
- Any migration steps needed
```

---

## 2026-06-21 08:35 — H5 operational masters and service data foundation

### What changed
- `lavanya_service/setup/operational_masters.py` — added idempotent H5 setup for `Lavanya Customer Product`, `Lavanya Warranty History Entry`, `Lavanya Proof Category`, proof-category seeds, and extension fields on Brand Service Master, Service Center Master, Local Technician Master, Lavanya Service Appointment, and Service Product Receipt.
- `lavanya_service/api/operational_masters.py` — added customer product sync/history APIs, service-center and technician filtered lookups, proof-category validation, master suggestions, and appointment create/status APIs.
- `lavanya_service/setup/install.py` — wired H5 setup into the existing install/migrate path.
- `lavanya_service/api/stitch_console.py` — delegated appointment creation to the H5 API while preserving existing free-text technician compatibility.
- `lavanya_service/tests/h5_operational_masters.py` — added 13 rollback-safe checks for H5 DocTypes, product/warranty history, duplicate serial handling, lookups, proof validation, appointment transitions, and no communication/email/notification side effects.
- `doc/h5_operational_masters_report.md` — added the H5 implementation and safety-boundary report.
- `doc/lavanya-app-reference.md` and `doc/lavanya-spa-status.md` — documented H5 DocTypes, APIs, setup step, test module, and verification status.

### Previous state
Customer profile, product item/category, service receipt, appointment, brand/service-center/technician masters, and repeat-detection foundations existed, but there was no customer-owned product record or warranty history timeline. Existing appointment records stored technician as free text only, and proof categories were not controlled by a master.

### Current state
H5 provides a dedicated customer product/warranty-history data foundation, controlled proof categories, richer operational master fields, filtered master lookup APIs, and appointment status transitions without creating a separate architecture or changing ERP/accounting behavior.

### Why changed
H5 requires operational masters and service data foundations before deeper showroom receiving, warranty history, and product-history UI can be safely built.

### What was obtained
- Python compile check on changed modules: PASS.
- `lavanya_service.tests.h5_operational_masters.run`: 13 pass, 0 fail.
- `lavanya_service.tests.theme_settings.run`: 29 pass, 0 fail.
- `lavanya_service.tests.stitch_console_spa.run`: PASS.
- `lavanya_service.tests.p2_tests.run`: 18 pass, 0 fail.
- `lavanya_service.tests.today_work.run`: 23 pass, 1 fail; TW-015 remains the documented pre-existing group-order mismatch.
- `node node_modules/vite/bin/vite.js build`: PASS, with existing Browserslist warning only.
- H5 APIs create no `Communication`, `Email Queue`, or `Notification Log` rows.

### Compatibility notes
- No live WhatsApp/SMS, ERP posting, ERP draft posting, accounting entry, stock posting, penalty application, automatic closure, or automatic repeat-linking was introduced.
- The existing `stitch_console.schedule_appointment` endpoint keeps accepting free-text technician names; it fills `technician_link` only when a matching `Local Technician Master` exists.
- Request-time H5 APIs do not call setup functions to avoid transaction commits during tests or user workflows; setup remains in install/migrate and explicit setup execution.

---

## 2026-06-20 23:30 — H2 foundation: theme engine, settings DocType, shared components, tests

### What changed
- `frontend/src/utils/theme-engine.js` — new runtime theme engine defining 6 themes (Lavanya Light, Lavanya Dark, Lavanya Blue, Lavanya Green, High Contrast, Compact Counter Mode), CSS-variable application, localStorage persistence, invalid-theme fallback.
- `frontend/src/utils/theme.js` — re-exports theme engine utilities while keeping legacy `COLORS` and chip helpers for backward compatibility.
- `frontend/src/index.css` — migrated `lav-*` semantic classes and base styles to CSS custom properties so they respond to theme changes.
- `frontend/tailwind.config.mjs` — color tokens now reference CSS variables.
- `frontend/src/composables/useTheme.js` — new reactive Vue composable.
- `frontend/src/components/LavThemeToggle.vue` — new accessible theme selector.
- `frontend/src/components/AppShell.vue` — added `LavThemeToggle` to header; added Settings nav item.
- `frontend/src/App.vue` — initializes theme on mount; added `g+s` keyboard shortcut for Settings.
- `frontend/src/pages/Settings.vue` — new settings page showing theme selector, safety locks, and UI feature flags.
- `frontend/src/router.js` — registered `/settings` route.
- `frontend/src/components/LavCard.vue`, `LavSectionHeader.vue`, `LavBadge.vue`, `LavChip.vue`, `LavStatCard.vue`, `LavActionBar.vue`, `LavEmptyState.vue`, `LavLoadingState.vue`, `LavSafetyLockPanel.vue` — new shared components.
- `lavanya_service/setup/ui_settings.py` — new `Lavanya Service Settings` Single DocType with theme preferences, UI feature flags, and safety-lock mirrors.
- `lavanya_service/api/ui_settings.py` — new whitelisted `get_lavanya_service_settings` endpoint.
- `lavanya_service/hooks.py` — wired `ui_settings.create_lavanya_settings` to `after_install` and `after_migrate`.
- `lavanya_service/tests/theme_settings.py` — new 15-check test module for defaults, theme options, UI flags, safety locks, and API safe-fallback.
- `doc/h2_uiux_wiring_settings_modernisation_theme_system.md` — consolidated H2 task spec.
- `doc/h2_theme_system_report.md` — implementation report.
- `doc/h2_theme_reference.md` — theme reference for future developers.
- `doc/h2_uiux_wiring_report.md` — UI/UX wiring report.
- `doc/lavanya-spa-status.md` — added H2 foundation entry and remaining H2 work items.
- `doc/lavanya-app-reference.md` — documented `Lavanya Service Settings` DocType, `api/ui_settings.py`, `theme_settings` test module, and updated frontend file map.

### Previous state
- SPA had a static light theme with hardcoded Tailwind colors and a few dark-token helpers in `theme.js`.
- No `Lavanya Service Settings` DocType existed.
- No Settings SPA page existed.
- Shared components were limited to `AppShell`, `TicketDetail`, `LavModal`, `LavConfirm`, `SlaBadge`.

### Current state
- SPA supports 6 runtime-switchable themes with instant application and localStorage persistence.
- `Lavanya Service Settings` provides backend defaults for theme, UI flags, and safety locks.
- Settings page is live at `/frontend/settings`.
- 10 new shared components are available for page modernization.
- 15 theme/settings tests pass.

### Why changed
- H2 requires a modern, configurable UI with multiple themes, accessibility modes, and a settings backbone.

### What was obtained
- `node node_modules/vite/bin/vite.js build`: PASS.
- `lavanya_service.tests.theme_settings.run`: 15 pass, 0 fail.
- `lavanya_service.tests.stitch_console_spa.run`: PASS.
- `lavanya_service.tests.p2_tests.run`: 18 pass, 0 fail.
- `lavanya_service.tests.today_work.run`: 23/24 pass (TW-015 group-order mismatch pre-existing, unrelated to theme work).
- Static checks: no new hardcoded component colors; no native `confirm()` usage.

### Compatibility notes
- No backend workflow behavior changed.
- Existing `COLORS`, chip helpers, and dark-token exports in `theme.js` remain available for components that have not yet migrated to CSS variables.
- `today_work` TW-015 mismatch was present before H2 changes.

---

## 2026-06-21 04:30 — H4: final UI/UX polish and interaction regression layer

### What changed
- `frontend/src/components/LavTicketCard.vue` — new shared ticket card showing customer, phone, product, status, next action, due state, quality badge, escalation, and customer-informed state.
- `frontend/src/index.css` — added token-driven `LavTicketCard` and Field Mode action styles; all new styles use `var(--lav-*)` theme tokens.
- `frontend/src/components/AppShell.vue` — improved active nav state, compact mobile labels, mobile nav prioritization, page subtitle, and user action separation.
- `frontend/src/components/LavActionBar.vue` — visually separated primary, secondary, and danger action groups.
- `frontend/src/components/TicketDetail.vue` — reordered top stack to action-first layout, changed WhatsApp wording to draft-only, and added explicit closure guard language.
- `frontend/src/pages/TodayWork.vue` — replaced dense bucket rows with `LavTicketCard` while keeping Critical / Important / Normal tiers.
- `frontend/src/pages/Tickets.vue` — added saved filters, mobile card view, desktop Next Action and Quality columns, and clearer filtered-empty state.
- `frontend/src/pages/Reports.vue` — added prominent Penalty and Notification safety-state cards.
- `frontend/src/pages/Settings.vue` — added manager/read-only state, dirty-state indicator, sticky save/reset bar, and feature-flag descriptions.
- `frontend/src/pages/FieldMode.vue` — reused `LavTicketCard`, added recent work, and added sticky safe quick actions.
- `lavanya_service/tests/theme_settings.py` — extended static UI checks for native dialog calls, `/field` route, `LavTicketCard`, Settings dirty state, and compact-mode CSS.
- `doc/h4_uiux_upgrade_audit.md` — new page-by-page audit with problems, fixes, remaining issues, and screenshot requirements.
- `doc/h4_uiux_upgrade_report.md` — new implementation report.

### Previous state
- H3B pages were functionally modernized but ticket cards were duplicated, mobile filtering was table-dependent, Ticket Detail did not lead with the action bar, and Settings lacked a clear dirty-state/save layer.

### Current state
- The operational workflow is more action-first and scan-friendly across Dashboard/Today’s Work, Tickets, Ticket Detail, Reports, Settings, and Field Mode.
- Safety states for notification/penalty areas are more visible.
- Static regression coverage now checks H4 UI wiring and forbidden native dialogs.

### Why changed
- H4 requires the app to feel production-ready for showroom/service-counter staff while preserving existing workflow and safety gates.

### What was obtained
- `node node_modules/vite/bin/vite.js build`: PASS.
- `lavanya_service.tests.theme_settings.run`: 29/29 pass.
- `lavanya_service.tests.stitch_console_spa.run`: PASS on sequential rerun; first parallel run hit transient `tabSeries` contention.
- `lavanya_service.tests.p2_tests.run`: 18/18 pass.
- `lavanya_service.tests.today_work.run`: 23/24 pass; TW-015 group-order mismatch remains pre-existing.

### Compatibility notes
- No backend workflow behavior changed.
- No live WhatsApp/SMS, ERP posting, penalty application, accounting entry, stock posting, or automatic closure was introduced.
- Existing closure guard remains server-side; UI now explains the guard state more clearly.
- Screenshot capture was not available in this session; manual instructions are documented in `doc/h4_uiux_upgrade_audit.md`.

---

## 2026-06-21 03:00 — H3B: Tickets/Reports modernization, Mobile Field Mode, shared-component fixes

### What changed
- `frontend/src/components/LavSectionHeader.vue` — added `badge` and `accent` props; displays ticket count badge with accent color.
- `frontend/src/components/LavStatCard.vue` — added `caption` prop (alias for `sub`); shows sub-detail line when provided.
- `frontend/src/components/LavEmptyState.vue` — added `message` (alias for `description`) and `tone` props; `tone="error"` renders error styling.
- `frontend/src/components/LavLoadingState.vue` — added `layout` prop; `layout="card-list"` renders metric-grid + row skeletons matching Today's Work / Tickets.
- `frontend/src/pages/Tickets.vue` — modernized with `LavSectionHeader` (header + New Ticket action), `LavChip` (status filter), `LavLoadingState`, `LavEmptyState` (with action slot), `LavCard` (table wrapper).
- `frontend/src/pages/Reports.vue` — modernized all 8 tabs (Overview, Brand Delay, Supplier, Follow-up Quality, Penalty, Notifications, Aging, Reports) using `LavSectionHeader`, `LavStatCard` (summary cards), `LavCard` (table/containers), `LavLoadingState`, `LavEmptyState`; preserved dry-run/safety behavior in Penalty/Notifications.
- `frontend/src/pages/FieldMode.vue` — new Mobile Field Mode page at `/field` for counter/showroom staff: large action tiles (New Ticket, Find Customer), phone/ticket search with `stitch_console.get_ticket_list`, critical-work snapshot via `today_work.get_today_work`, quick-open TicketDetail drawer.
- `frontend/src/router.js` — registered `/field` route.
- `frontend/src/components/AppShell.vue` — added Field Mode nav item (icon: `phone_iphone`).
- `doc/lavanya-spa-status.md` — updated H2/H3 progress and remaining work.
- `doc/lavanya-app-reference.md` — documented FieldMode page, `/field` route, and new shared-component props.

### Previous state
- Tickets.vue used custom header, status chips, skeleton/empty states, and bare table.
- Reports.vue used inline headers, custom summary cards, raw tables, and custom loading/empty states across 8 tabs.
- No Field Mode page existed for counter/showroom staff.
- LavSectionHeader/LavStatCard/LavEmptyState/LavLoadingState lacked `badge`/`accent`/`caption`/`message`/`tone`/`layout` props — pages passing them rendered no content.
- Mobile navigation lacked Field Mode entry.

### Current state
- Tickets.vue and Reports.vue fully use shared `Lav*` components; consistent styling, accessible skeletons/empty states, and compact-mode aware.
- Field Mode page provides touch-first experience: large tap targets, phone search, critical counts, and quick drawer access.
- All shared components now support the props used by pages; sub-detail lines, badge counts, error tones, and card-list skeletons render correctly.
- SPA build passes; all backend tests pass (theme_settings 23/23, p2_tests 18/18, stitch_console_spa PASS, today_work 23/24 with documented pre-existing TW-015).

### Why changed
- H3B requires modernizing remaining pages with shared component library, adding Mobile Field Mode for showroom staff, and fixing shared-component prop gaps from H2.

### What was obtained
- `node node_modules/vite/bin/vite.js build`: PASS.
- `lavanya_service.tests.theme_settings.run`: 23/23 pass.
- `lavanya_service.tests.p2_tests.run`: 18/18 pass.
- `lavanya_service.tests.stitch_console_spa.run`: PASS.
- `lavanya_service.tests.today_work.run`: 23/24 pass (TW-015 pre-existing).
- No live WhatsApp/SMS, ERP posting, or penalty application enabled.
- No native `confirm()`/`alert()` introduced; uses `LavConfirm`.

### Compatibility notes
- No backend workflow behavior changed.
- Penalty/Notifications tabs retain all dry-run logic, manager-approval gates, and safety-lock checks.
- `LavConfirm` used throughout; no native dialogs.
- TW-015 mismatch was present before H3B changes.

---

## 2026-06-21 00:30 — H3 progress: Ticket Detail Modernisation + Follow-up Intelligence + editable settings

### What changed
- `frontend/src/utils/followup-quality.js` — new utility that computes follow-up quality (Good / Needs Attention / Poor) from ticket stage, last follow-up, next follow-up, and customer-informed status.
- `frontend/src/components/lavanya/tickets/LavWorkflowTimeline.vue` — new reusable workflow timeline showing intake → registration → service → resolution → closure stages with current-stage highlight and stage metadata.
- `frontend/src/components/lavanya/tickets/LavCustomerJourneyCard.vue` — new reusable customer-journey summary card replacing the inline grid in Ticket Detail.
- `frontend/src/components/lavanya/tickets/LavFollowupQualityBadge.vue` — new computed quality badge component (chip style) driven by `followup-quality.js`.
- `frontend/src/components/TicketDetail.vue` — integrated `LavWorkflowTimeline`, `LavCustomerJourneyCard`, `LavFollowupQualityBadge`, and wrapped the next-action buttons in `LavActionBar`; removed now-unused `qualityChip` and `followupUrgency` helpers.
- `frontend/src/pages/TodayWork.vue` — applied `LavSectionHeader`, `LavStatCard`, `LavLoadingState`, and `LavEmptyState`; retained existing bucket logic and urgency-first ordering.
- `frontend/src/pages/Settings.vue` — made theme flags and UI feature flags editable for managers; added save and reset-to-safe-defaults actions; wired `LavConfirm` instead of native `confirm`.
- `lavanya_service/api/ui_settings.py` — added `can_manage_lavanya_settings`, `save_lavanya_service_settings`, and `reset_lavanya_service_settings`; manager-only (Lavanya Manager / System Manager / Administrator) with validation for editable fields and theme options; safety locks remain read-only mirrors.
- `lavanya_service/tests/theme_settings.py` — extended from 15 to 23 checks covering save permission gating, editable-field updates, safety-lock ignoring, invalid-theme rejection, reset-to-defaults, and manager detection.
- `doc/lavanya-spa-status.md` — updated H2/H3 remaining work and verification table.

### Previous state
- Ticket Detail had inline next-action bar, customer-journey grid, and a computed follow-up chip, but no reusable workflow-timeline or journey-card components.
- Today’s Work rendered metrics and states with custom markup rather than the shared `Lav*` components introduced in H2.
- Settings page was read-only; managers could not persist theme or UI flag changes from the SPA.
- `api/ui_settings.py` only exposed a read endpoint.

### Current state
- Ticket Detail uses reusable H3 ticket components for timeline, journey summary, and quality badge, with actions grouped via `LavActionBar`.
- Today’s Work uses shared `Lav*` components for metric cards, section headers, and loading/empty states while preserving Critical/Important/Normal tiering.
- Settings page is editable for managers and resets safely to defaults.
- Backend enforces manager-only writes, validates themes, and ignores safety-lock attempts from the editable save path.
- Theme/settings test module now has 23 passing checks.

### Why changed
- H3 requires modern, reusable ticket-detail components and follow-up intelligence indicators; H2 remaining work requires applying shared components across pages and making settings editable.

### What was obtained
- `node node_modules/vite/bin/vite.js build`: PASS.
- `lavanya_service.tests.theme_settings.run`: 23 pass, 0 fail.
- `lavanya_service.tests.stitch_console_spa.run`: PASS.
- `lavanya_service.tests.p2_tests.run`: 18 pass, 0 fail.
- `lavanya_service.tests.today_work.run`: 23/24 pass (TW-015 group-order mismatch pre-existing, unrelated to H3 work).
- Static checks: no native `confirm()` in changed code; safety locks remain disabled-by-default.

### Compatibility notes
- No backend workflow behavior changed.
- Existing `qualityBadge`/`qualityChip` helpers in `utils/index.js` remain available; Ticket Detail now imports only `qualityBadge`.
- `Lavanya Service Settings` safety-lock fields remain read-only mirrors of backend gates.
- TW-015 mismatch was present before H3 changes.

---

## 2026-06-20 22:00 — H2 task spec created: UI/UX Wiring, Settings, Modernisation + Theme System

### What changed
- `doc/h2_uiux_wiring_settings_modernisation_theme_system.md` — created the consolidated H2 phase task specification combining UI/UX wiring, settings, modernisation, and the multiple-theme add-on.

### Previous state
- H2 UI/UX Wiring + Settings was referenced in other docs but had no dedicated task document.
- The Modern UI/UX + Multiple Themes add-on existed only in conversation, not in the repo.

### Current state
- A single canonical H2 task document exists covering: settings groups (general defaults, follow-up rules, notifications, penalty, ERPNext, UI feature flags, theme preferences, safety locks), theme system requirements, modern UI refresh targets, shared component list, theme selector behaviour, compact counter mode, accessibility rules, tests, screenshots, documentation, acceptance criteria, and safety boundaries.

### Why changed
- Required to keep the expanded H2 scope in one controlled phase and give all agents a single source of truth before implementation starts.

### What was obtained
- Clear, reviewable H2 scope with acceptance criteria and safety boundaries.

### Compatibility notes
- No code changed; no tests required.
- Implementation of the spec is the next step.

---

## 2026-06-20 21:30 — P2.2 Notification Templates + Dry-run Queue closed

### What changed
- `doc/p2_notification_state_audit.md` — created a current-state audit documenting implemented files, missing files, existing DocTypes/APIs/frontend UI, tests, safety checks, gaps, and verification results.
- `doc/screenshots/p2_notifications/` — renamed the 8 captured screenshots to the required `01-` … `08-` naming scheme.
- `lavanya_service/tests/p2_notification_tests.py` — hardened test runner with `_purge_stale()` to clean leftover templates/tickets/queue rows/agent user from prior interrupted runs; set `send_welcome_email: 0` on the test agent user to avoid SMTP failures on the dev site.
- `lavanya_service/api/notifications.py` — removed unused `assert_no_live_send()` dead code.
- `doc/p2_notification_templates_report.md`, `doc/p2_notification_defects_found.md`, `doc/p2_notification_closure_audit.md`, `doc/p2_notification_uat_report.md` — updated verification counts, screenshot names, and fixed-defect notes.
- `doc/lavanya-spa-status.md` — added P2.2 closure entry to the done table.

### Previous state
P2.2 notification implementation existed from parallel work and was documented as ready for closure, but the state had not been independently audited. Screenshot names did not match the required scheme, the focused test runner was fragile to stale DB state, and a dead helper function remained in `api/notifications.py`.

### Current state
P2.2 is closed. The dry-run notification template and queue infrastructure is verified: 15 templates active, preview/queue/approve/cancel/skip workflows working, live sending blocked, no provider credentials, no ERP/accounting side effects. P2.2 tests pass 10/10 and P2.1 regression remains 18/18.

### Why changed
P2.2 needed an independent state audit and hardening before it could be safely committed as a closed milestone separate from P2.1.

### What was obtained
- `lavanya_service.tests.p2_notification_tests.run`: 10 pass, 0 fail via `bench execute`.
- `lavanya_service.tests.p2_tests.run`: 18 pass, 0 fail.
- `bench --site lavanya-dev.localhost migrate`: PASS.
- Frontend production build: PASS.
- 8 P2.2 screenshots in required `doc/screenshots/p2_notifications/`.

### Compatibility notes
- No P2.1 penalty code was changed.
- No live WhatsApp/SMS provider, ERPNext integration, customer portal, CSAT, or accounting posting was started.
- Frontend `Reports.vue` and `TicketDetail.vue` notification UI was preserved unchanged.

---

## 2026-06-20 22:00 — P2.4 ERPNext safe integration scaffold reviewed and documented

### What changed
- `doc/lavanya-changelog.md` — added this closure entry for the already-committed P2.4 ERPNext scaffold.
- `doc/lavanya-spa-status.md` — added P2.4 closure row and updated P2.1/P2.2 rows from "uncommitted" to committed status.
- `doc/p2_erpnext_scaffold_defects_found.md` — added a post-commit review section confirming independent verification, no write-side ERP behavior, and the changelog gap fix.

### Previous state
P2.4 ERPNext scaffold was committed by a parallel agent (`35c387c`) with implementation and safety docs, but the required changelog entry was missing and the SPA status table did not reflect the closure.

### Current state
P2.4 scaffold is reviewed and documented. The scaffold remains disabled-by-default, read-only, and safe when ERPNext is absent. No ERP document creation paths exist.

### Why changed
AGENTS.md Rule 1 requires every change to be documented in the changelog. The parallel P2.4 commit omitted this, so the gap is being closed before moving on.

### What was obtained
- `lavanya_service.tests.p2_erp_scaffold_tests.run`: 14 pass, 0 fail.
- Frontend production build: PASS.
- Static verification: no ERPNext imports, no write-side ERP document creation, all defaults disabled.

### Compatibility notes
- No ERPNext module or doctype is required for the scaffold to load safely.
- No accounting, stock, sales, purchase, or payment posting code was introduced.
- The scaffold is intentionally disabled (`erpnext_enabled=0`, `mode=Disabled`) until an admin explicitly enables it.

---

## 2026-06-20 20:00 — P2.1 Supplier Penalty Computation closed

### What changed
- `frontend/src/pages/Reports.vue` — added penalty detail modal and approve/waive/reject narration/reason modals using `LavModal` and `useConfirm()`.
- `doc/p2_penalty_computation_report.md` — updated verification status to CLOSED; listed captured screenshots and final closure verdict.
- `doc/p2_penalty_defects_found.md` — closed `P2-OPEN-001` (frontend modals/screenshots) and documented the remaining non-P2.1 email-configuration regression blocker.
- `doc/lavanya-spa-status.md` — updated the P2.1 entry to reflect closed state and completed modal/screenshot work.

### Previous state
P2.1 backend/API verification was complete (18/18), but the frontend detail/narration modals and required screenshots were still listed as the active closure gate. The defect log still had an open item for the missing modals.

### Current state
P2.1 is closed. The Reports Center Penalty tab displays a detail modal and approve/waive/reject modals that require narration/reason. Final screenshots are captured in `doc/screenshots/p2_penalty/`. Build, migration, and tests all pass.

### Why changed
P2.1 cannot be closed without the frontend UI that exposes the audited manager actions (approve/waive/reject) and the required screenshot evidence.

### What was obtained
- P2.1 backend/API runner: 18 pass, 0 fail.
- Frontend production build: PASS.
- Migration: PASS.
- Screenshots captured: 7 files in `doc/screenshots/p2_penalty/`.
- Static check: no native `window.confirm` in `Reports.vue`; only `useConfirm()` composable calls.

### Compatibility notes
- `LavModal`, `LavConfirm`, `useConfirm()`, and `theme.js` are shared components/utils already introduced by the concurrent frontend Phase A pass; the penalty modals reuse them without adding new dependencies.
- No ERPNext/accounting, WhatsApp, SMS, customer portal, or P2.2/P2.3 scope was started.
- Test command: `docker exec -i devcontainer-example-frappe-1 bash -lc 'cd /workspace/development/frappe-bench && bench --site lavanya-dev.localhost execute lavanya_service.tests.p2_tests.run > /tmp/p2-final.txt 2>&1; grep -v Enqueuing /tmp/p2-final.txt'`.
- Build command: `cd frontend && node node_modules/vite/bin/vite.js build`.

---

## 2026-06-20 18:10 — P2.1 penalty backend verification docs and tests

### What changed
- `lavanya_service/tests/p2_tests.py` — extended the P2.1 runner from 10 to 18 checks by adding summary/list/detail API smoke, blank approval narration, blank waiver reason, waiver zeroing, missing rejection reason, and rejected-status coverage.
- `doc/p2_penalty_rules.md` — added the explicit operational boundary: advisory/operational only, no ERP posting, no accounting entry, no WhatsApp/SMS, manager narration required, and accounting application deferred to a future phase.
- `doc/p2_penalty_computation_report.md` — corrected verification status to migration passed, 18/18 backend/API checks passed, current SPA build sanity passed, and final frontend screenshots/build still pending until the detail/narration modals land.
- `doc/p2_penalty_defects_found.md` — added backend test-coverage defect notes and the current open frontend modal/screenshot gate.
- `doc/lavanya-app-reference.md` — documented P2.1 DocTypes, penalty APIs, scheduler job, test module, setup hook, and import-map references.

### Previous state
P2.1 backend computation and APIs existed, and the original P2.1 runner passed 10 checks. Documentation existed from a concurrent batch but still had stale verification counts, incomplete advisory-boundary wording, and did not list the new P2.1 modules in the app reference.

### Current state
The P2.1 backend/API runner now reports 18 pass, 0 fail. The docs clearly state P2.1 is advisory/operational only and does not post ERPNext/accounting entries or send WhatsApp/SMS. The app reference includes the penalty doctypes, APIs, daily scheduler, and test module.

### Why changed
P2.1 cannot be closed without durable audit controls and documentation that future agents can trust. Backend tests needed to cover the required narration/reason checks directly instead of relying on manual inspection.

### What was obtained
- Verified migration completed cleanly.
- Verified `lavanya_service.tests.p2_tests.run` returns `{"pass": 18, "fail": 0}` after purging leaked test artifacts caused by an earlier truncated-output run.
- Established clear remaining closure gates: frontend detail/narration modals, final build after those modals, required screenshots, and regression checks.
- Verified current SPA build sanity after `npm install` restored Rollup optional dependency `@rollup/rollup-win32-x64-msvc`.

### Compatibility notes
- Existing frontend calls pass non-empty action text, so server-side narration enforcement remains backward-compatible.
- No ERPNext/accounting, WhatsApp, SMS, customer portal, or P2.2/P2.3 scope was started.
- Test command run: `docker exec -i devcontainer-example-frappe-1 bash -lc 'cd /workspace/development/frappe-bench && bench --site lavanya-dev.localhost execute lavanya_service.tests.p2_tests.run > /tmp/p2run.txt 2>&1; grep -v Enqueuing /tmp/p2run.txt'`.
- Build command run: `node node_modules/vite/bin/vite.js build` from `frontend` after `npm install` repaired optional dependencies. Build retry passed; npm reported cleanup permission warnings and 2 audit findings.

---

## 2026-06-20 12:00 — Initial comprehensive documentation system (commit 9c0756b)

### What changed
- `AGENTS.md` — rewritten with stricter rules (must-read-all-docs, changelog
  updates, backward-compat checks, test runs)
- `doc/lavanya-changelog.md` — created this file with entry format
- `doc/lavanya-app-reference.md` — created complete auto-generated app reference

### Previous state
Only `AGENTS.md` existed with 5 basic rules. No centralized app reference,
no changelog, no mandatory backward-compatibility checks.

### Current state
Three files form a documentation system:
1. `AGENTS.md` — 7 strict rules for any AI agent
2. `doc/lavanya-changelog.md` — change audit trail
3. `doc/lavanya-app-reference.md` — complete app reference for agents

### Why changed
Multiple agents working on the app need a single source of truth to avoid
duplicate work, broken dependencies, and incompatible changes.

### What was obtained
- Any agent can now understand the full app in one file
- Any change is traceable with before/after/why
- Backward-compatibility checks are mandatory
- Tests must be run after every change

### Compatibility notes
- All existing docs remain untouched
- No code was modified
- No migration needed
- Also included: multi-agent delta batch (SPA UI/UX polish, Reminder Engine
  Steps 3-5, AI advisory, follow-up tracking, stage layer, dashboards)
- Repo: https://github.com/collinsfoam-a11y/lavanya_service

---

## 2026-06-20 14:30 — Comprehensive frontend deep analysis audit

### What changed
- `doc/lavanya-frontend-audit.md` — created with 13-section audit (architecture,
  component tree, state, routing, API, design system, responsiveness, a11y,
  performance, code quality, browser compat, upgrade suggestions, modern standards)
- `doc/lavanya-frontend-deep-analysis.md` — created with 12-section deep analysis
  (modern design patterns, anti-pattern catalog, responsive matrix, feature gap
  analysis, phased improvement roadmap, documentation gaps, what to avoid,
  detailed browser compat matrix, feature completeness check, ADRs, code org
  recommendations, tech radar)

### Previous state
Frontend had no dedicated audit/analysis document. Only `doc/lavanya-spa-status.md`
existed with build status.

### Current state
Two comprehensive frontend documents exist:
1. `doc/lavanya-frontend-audit.md` — standard audit (13 sections)
2. `doc/lavanya-frontend-deep-analysis.md` — deep analysis (12 sections)

### Why changed
User requested comprehensive audit covering: modern design comparison, anti-patterns,
all browser sizes, feature gaps, upgrade suggestions, what to avoid, what's missing.

### What was obtained
- Complete responsive matrix for 320px-1920px with critical breakpoint analysis
- 11 anti-patterns cataloged with fixes
- 10 backend features identified as missing from frontend
- 24 improvement items in 4-phase roadmap with effort/impact estimates
- Technology radar with 8 technologies assessed
- Detailed browser compatibility table across 7 browsers
- Architectural decision records documented
- Feature completeness check (27 items checked)

### Compatibility notes
- No code was modified — documentation only

---

## 2026-06-21 12:00 — H5D: Restore deferred service record modules safely

### What changed
- `lavanya_service/setup/comm_log.py` — Customer Communication Log DocType
- `lavanya_service/setup/demo_record.py` — Demo Installation Record DocType
- `lavanya_service/setup/replacement_record.py` — Replacement Record DocType
- `lavanya_service/setup/return_record.py` — Return Service Record DocType
- `lavanya_service/setup/stock_record.py` — Stock Complaint Record DocType
- `lavanya_service/setup/store_record.py` — Store Service Record DocType
- `lavanya_service/setup/area_perf_log.py` — Area Performance Log DocType
- `lavanya_service/setup/supplier_sla.py` — Supplier SLA Definition DocType
- `lavanya_service/setup/supplier_payment_block.py` — Supplier Payment Block DocType
- `lavanya_service/setup/supplier_perf_log.py` — Supplier Performance Log DocType
- `lavanya_service/tasks/payment_block.py` — Advisory payment block scheduler (Pending Review only)
- `lavanya_service/tasks/performance_log.py` — Read-only supplier/area performance log scheduler
- `lavanya_service/setup/install.py` — Added `_ensure_h5d_service_records()` step
- Deleted `lavanya_service/utils/ensure_whitelist.py` (incomplete, whitelisting via hooks.py)

### Previous state
13 deferred files in `.worktree-temp/` blocked by missing `setup/masters.py` dependency.

### Current state
All 12 restorable files committed. Dependencies on `setup/masters.py` (ensure_doctype/field/permission) verified compatible. All DocType creation is idempotent. Scheduler tasks are advisory (payment_block: Pending Review status) or read-only (performance_log). Wired into install/migrate pipeline.

### Why changed
Service record DocTypes, supplier governance, communication logs, and performance tracking were documented but not installed. Restoring them completes the operational data foundation.

### Compatibility notes
- All `ensure_doctype` calls are idempotent
- No ERP posting, accounting entries, or live WhatsApp/SMS
- Supplier payment block creates records in "Pending Review" status — requires manager action

---

## 2026-06-21 12:30 — H5E: Linked service record UI + verification

### What changed
- `lavanya_service/api/stitch_console.py` — Added `_linked_service_records()` helper, wired into `get_ticket_detail()`
- `frontend/src/components/TicketDetail.vue` — Added Service Records section with read-only cards for Replacement, Return, Stock Complaint, Store Service, Demo/Installation, and Communication Log
- Added `hasLinkedRecords` computed property
- Added "Records" entry to sticky section nav

### Previous state
Service record DocTypes existed but had no visibility in Ticket Detail. Staff could not see linked replacement/return/stock/store records from the ticket view.

### Current state
`get_ticket_detail()` now fetches linked records across 6 DocTypes. Ticket Detail shows read-only cards with key fields and color-coded borders. Section only renders when records exist.

### Compatibility notes
- `_linked_service_records()` silently skips missing DocTypes
- All records are read-only display; no edit/create forms added
- No new API endpoints required

---

## 2026-06-21 13:00 — H5F: Pilot readiness regression gate

### What changed
- `doc/h5f_pilot_readiness_report.md` — Created complete pilot readiness report
- `doc/lavanya-changelog.md` — This entry
- Static safety scan confirmed: 0 native confirm/alert/prompt, 0 live WhatsApp/SMS, 0 ERP posting, 0 penalty application, 0 COLORS.* in Vue

### Previous state
H5A-H5E feature work complete but no formal pilot readiness documentation or merge preparation.

### Current state
Full static safety verification passed. Pilot readiness report documents:
- 8 commits on safety branch
- Feature inventory (28 items)
- Known gaps (6 items, all low/medium severity)
- Verification command inventory
- Merge instructions from safety branch to feature branch

### Compatibility notes
- Merge to `feature/phase-2-frappe-ui-scaffold` with `--no-ff`
- SPA build verification pending (requires Windows host `node_modules`)
- TW-015 known pre-existing group-order mismatch in today_work tests

---

## 2026-06-21 14:00 — H6A: Read-only WhatsApp inbox and draft foundation

### What changed
- `lavanya_service/setup/whatsapp_inbox.py` — WhatsApp Inbound Message + WhatsApp Draft Outbound DocTypes
- `lavanya_service/api/whatsapp_inbox.py` — 6 API endpoints (list_inbound, list_draft, create_draft, review_draft, review_inbound, link_to_ticket, get_ticket_drafts)
- `lavanya_service/hooks.py` — doc_event validate hook on WhatsApp Draft Outbound for `_block_live_send` guard
- `frontend/src/pages/WhatsAppInbox.vue` — Inbound + Draft tabs with review/link actions
- `frontend/src/router.js` — `/whatsapp` route
- `frontend/src/components/AppShell.vue` — WhatsApp nav item

### Previous state
No WhatsApp inbox; customer messages not captured. Draft outbound existed only as dry-run template preview on Ticket Detail.

### Current state
WhatsApp Inbound Message DocType captures customer messages read-only. Draft Outbound creates drafts only — `live_send_blocked=1` locked. Server-side guard blocks "Sent (External)" status, `external_message_id`, and `sent_at`. Manager review workflow: Draft → Manager Reviewed → Approved (Ready). No live send path exists.

### Compatibility notes
- `_block_live_send()` enforced via hooks.py `validate` — cannot be bypassed from Desk/API
- All API endpoints read-only or draft-only
- No Twilio/360dialog/WhatsApp Business API calls

---

## 2026-06-21 14:30 — H6B: Read-only CRM relationship card

### What changed
- `lavanya_service/setup/crm_settings.py` — 8 CRM safety fields on Lavanya Service Settings (all default 0/Disabled)
- `lavanya_service/integrations/crm/detector.py` — CRM detection (is_crm_installed, can_read_crm)
- `lavanya_service/integrations/crm/adapter.py` — Read-only CRM relationship adapter (0 writes)
- `lavanya_service/api/stitch_console.py` — `_crm_relationship_payload()` enriches get_ticket_detail
- `frontend/src/components/TicketDetail.vue` — CRM Relationship card with service risk/sales opportunity badges
- `frontend/src/pages/Settings.vue` — CRM safety state card + "CRM automation: DISABLED" lock

### Previous state
CRM relationship visibility was missing. No customer CRM context in service tickets.

### Current state
CRM detector checks if Frappe CRM is installed. Adapter fetches contact/organization/open-deal counts (read-only). Service risk computed from escalation/overdue/satisfaction. Sales opportunity computed from warranty status/repeat/replacement. 0 CRM record creation paths. Settings confirm CRM automation disabled.

### Compatibility notes
- Adapter has 0 insert/save/create on CRM DocTypes
- `can_read_crm()` gates all lookups
- Settings defaults: `crm_enabled=0`, `crm_mode=Disabled`

---

## 2026-06-21 15:00 — H6C: Read-only Customer 360 view

### What changed
- `lavanya_service/api/customer_360.py` — `get_customer_360(mobile)` endpoint (5 sections: identity, products, tickets, CRM, WhatsApp)
- `frontend/src/pages/Customer360.vue` — Full Customer 360 page with search, identity card, ticket stats, products, CRM summary, WhatsApp summary
- `frontend/src/router.js` — `/customer-360?mobile=` route
- `frontend/src/components/AppShell.vue` — Customer 360 nav item
- `frontend/src/components/TicketDetail.vue` — "View Customer 360" link from customer section

### Previous state
No single-page customer intelligence view. Staff had to navigate between Tickets, Ticket Detail, and Reports to see customer context.

### Current state
Customer 360 aggregates identity (profile + ticket fallback), products (warranty history), tickets (active/closed with stats), CRM (from H6B adapter), and WhatsApp (from H6A inbox). All read-only. Links from Ticket Detail pass mobile via query param.

### Compatibility notes
- All data sources are read-only endpoints
- 0 CRM writes, 0 WhatsApp sends, 0 ERP posting
- Falls back gracefully if CRM or WhatsApp DocTypes are missing

---

## 2026-06-21 15:30 — H6D: Pilot regression gate

### What changed
- `doc/h6d_pilot_regression_report.md` — Complete regression report (20 commits, 9 pages, 18 components, 19 TicketDetail sections)
- `doc/lavanya-changelog.md` — This entry
- Static safety scan: 0 COLORS Vue, 0 native dialogs, 0 live WhatsApp API, 0 CRM writes

### Previous state
H3B-H6C feature stack complete but no final regression documentation.

### Current state
Full safety scan passed. Regression report documents entire stack. Merge instructions prepared for `feature/phase-2-frappe-ui-scaffold → main`.

### Compatibility notes
- Merge to main with `--no-ff`
- TW-015 known pre-existing
- SPA build requires Windows host `node_modules`
- No migration needed
