# H2 UI/UX Wiring Report

> Part of H2 — UI/UX Wiring, Settings, Modernisation + Theme System.
> Extended by H3 — Ticket Detail Modernisation + Follow-up Intelligence.
> Extended by H3B — Tickets/Reports Modernisation + Mobile Field Mode.

---

## Scope covered in this pass

This pass delivers the foundational wiring for H2, extended by H3 and H3B:

1. **Theme system** — six themes, runtime switching, CSS-variable driven design.
2. **Settings backend** — `Lavanya Service Settings` Single DocType with theme
   preferences, UI feature flags, and safety-lock mirrors.
3. **Settings SPA page** — `/frontend/settings` with theme selector, safety
   locks, and UI flags; **H3**: manager-only editable with save/reset.
4. **Shared component library** — `LavCard`, `LavSectionHeader`, `LavBadge`,
   `LavChip`, `LavStatCard`, `LavActionBar`, `LavEmptyState`, `LavLoadingState`,
   `LavThemeToggle`, `LavSafetyLockPanel`, `LavWorkflowTimeline`,
   `LavCustomerJourneyCard`, `LavFollowupQualityBadge`.
5. **Static checks & tests** — no new hardcoded component colors, no native
   `confirm()`, 23 theme/settings tests passing.
6. **H3: Ticket Detail Modernisation** — `LavWorkflowTimeline`, `LavCustomerJourneyCard`,
   `LavFollowupQualityBadge` integrated into `TicketDetail.vue`; next actions grouped via `LavActionBar`.
6. **H3B: Tickets/Reports Modernisation + Mobile Field Mode** —
   - `Tickets.vue`: `LavSectionHeader`, `LavChip`, `LavLoadingState`, `LavEmptyState`, `LavCard`.
   - `Reports.vue` (8 tabs): `LavSectionHeader`, `LavStatCard`, `LavCard`, `LavLoadingState`, `LavEmptyState`.
   - `FieldMode.vue`: new `/field` page for counter/showroom staff — large action tiles, phone search, critical work snapshot, quick-open drawer.
   - `AppShell.vue`: Field Mode nav item added.

---

## Backend → UI wiring matrix

| Backend | API | Frontend consumer |
|---------|-----|-------------------|
| `Lavanya Service Settings` DocType | `lavanya_service.api.ui_settings.get_lavanya_service_settings` | `pages/Settings.vue` |
| Theme engine tokens | `frontend/src/utils/theme-engine.js` | Tailwind + `index.css` + components |
| Safety locks | `get_lavanya_service_settings` | `LavSafetyLockPanel` / `Settings.vue` |
| UI feature flags | `get_lavanya_service_settings` | `Settings.vue` (gates pages/sections) |
| Settings save/reset | `save_lavanya_service_settings` / `reset_lavanya_service_settings` | `Settings.vue` (manager-only) |
| Manager check | `can_manage_lavanya_settings` | `Settings.vue` (conditional edit UI) |

---

## What is intentionally deferred (remaining after H3B)

Full modernization of every screen is a larger body of work. The following
remain open and are documented in `doc/lavanya-spa-status.md` pending work:

- Manager / Coordinator dashboards as SPA pages (`api/manager_dashboard.py`, `coordinator_dashboard.py` exist).
- Role work-centers (Agent "My Work", Front Desk "Work Center").
- Front Desk: New Ticket / Create Receipt as SPA.
- Product Custody Detail / Ready-for-Pickup views.
- Role-aware Quick Action buttons (hide actions the user can't run).
- Today's Work: table vs. bucket toggle.
- Playwright smoke test for `/frontend` routes.
- CI: build the SPA + run the test modules on PR.
- Helpdesk 1.26.1 scratch upgrade and native capability acceptance matrix.
- Production P0 regression suite: receipt visibility and permission boundaries.
- Screenshots for each theme, layout, and new H3/H3B pages.

---

## Verification

| Check | Result |
|-------|--------|
| `node node_modules/vite/bin/vite.js build` | PASS |
| `lavanya_service.tests.theme_settings.run` | 23/23 pass |
| `lavanya_service.tests.stitch_console_spa.run` | PASS |
| `lavanya_service.tests.p2_tests.run` | 18/18 pass |
| `lavanya_service.tests.today_work.run` | 23/24 pass (TW-015 pre-existing) |
| No live WhatsApp/SMS, ERP posting, penalty apply | Verified |
| No native `confirm()` / `alert()` | Verified (uses `LavConfirm`) |

---

## Next steps

See `doc/lavanya-spa-status.md` §3 for the full pending work list.

## Verification

- Build: PASS.
- Theme/settings tests: 15/15 PASS.
- SPA endpoint regression: PASS.
- P2.1 penalty regression: 18/18 PASS.
- Static checks: no new hardcoded colors, no native confirm.

---

## Next steps

1. Apply `LavCard`, `LavSectionHeader`, `LavBadge`, `LavChip`, `LavStatCard`,
   `LavActionBar`, `LavEmptyState`, `LavLoadingState` to Today’s Work, Tickets,
   Reports, Ticket Detail, and Penalty/Notification tabs.
2. Add workflow timeline and customer journey summary components to Ticket Detail.
3. Implement Critical/Important/Normal bucket grouping in Today’s Work (visual
   layer only; backend grouping already exists).
4. Capture required screenshots under `doc/screenshots/h2_ui_wiring/themes/`.
