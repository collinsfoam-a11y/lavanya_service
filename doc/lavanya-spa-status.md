# Lavanya Service Console (SPA) — Status, Backlog & Verification

> **AI agents (any tool):** this is a living doc. Per [`../AGENTS.md`](../AGENTS.md)
> you must read it before starting, and after every step update it with **what /
> how / why / remaining** (move done items to §2 with their commit, prune §3). Keep
> it honest.

A living record of the Vue SPA at `/frontend` (the Stitch "Lavanya Service
Console" design realized on the frappe-ui theme). Covers **what's done**, **what's
pending**, **how to build each pending item**, and **how to verify** — including a
reproducible authenticated-screenshot harness.

Branch: `feature/phase-2-frappe-ui-scaffold`
Site (dev): `lavanya-dev.localhost` (container `devcontainer-example-frappe-1`, webserver port `8001`, published to host)

---

## 1. Architecture at a glance

| Concern | Location |
|---|---|
| SPA source | `frontend/src/` (Vue 3 + Vite) |
| Theme base | `frontend/tailwind.config.mjs` → frappe-ui preset (`frappe-ui/tailwind`) |
| Pages | `frontend/src/pages/` — `TodayWork.vue`, `Tickets.vue`, `Reports.vue` |
| Shared components | `frontend/src/components/` — `AppShell.vue`, `TicketDetail.vue` |
| Router | `frontend/src/router.js` (history base `/frontend`) |
| API helper | `frontend/src/api.js` — `call()` (GET) / `post()` (POST w/ CSRF) |
| Build output | `lavanya_service/public/frontend/` (hashed assets) |
| Serve page | `lavanya_service/www/frontend.html` (auto-synced from build) + `www/frontend.py` (no-cache) |
| Backend APIs | `lavanya_service/api/stitch_console.py`, `manager_reports.py`, `workflow_actions.py` |
| Workflow/guards | `lavanya_service/workflow/quick_actions.py`, `today_work.py` |
| Reports queries | `lavanya_service/reports/manager_dashboard.py` |

**Build/serve loop:** a Vite `closeBundle` plugin copies the built `index.html`
into `www/frontend.html` on every build, and `www/frontend.py` sets `no_cache`
so `/frontend` always serves the latest hashed assets without `bench clear-cache`.

**Cross-platform note:** `node_modules` is installed for the Windows host, so the
container cannot build. Always build on the **host**:
```
cd frontend && node node_modules/vite/bin/vite.js build
```

---

## 2. What we did (done)

All on the frappe-ui theme base. Newest first.

| Commit | What | Verified |
|---|---|---|
| _(latest)_ | **Reminder Engine Step 4 — Hourly Scheduler Refresh + Batching** (`tasks/reminder_refresh.py`): persists the Step-3 computed state so Today's Work / reports / dashboards don't recompute live. `refresh_active_ticket_reminders(batch_size=50, max_tickets=500, dry_run=False, now=None)` wired to `scheduler_events.hourly` (merged, not replacing the existing `daily`). Active filter excludes Closed/Resolved/Cancelled/Spam/Archived; `get_active_ticket_names(limit, offset)`; batched with commit-per-batch; per-ticket failures logged (`frappe.log_error`) without aborting. Persists `stage_due_at`/`pre_overdue_alert_at` (only when computed — never wipes), `overdue_status`, `escalation_level`, `customer_promise_status`. **Idempotent**: storage no-ops identical writes, manual `next_follow_up_date` never touched, and a `[Customer Promise Breach]` Comment + `promise_breach_reason` written **once** on the Pending→Breached transition (transition-guard + existing-comment guard). No AI / messages / closures. | `tests/reminder_refresh.py` 14/14 (active-only, closed-ignored, idempotent-refetch, manual-preserve, stage-fields-persist, Pending→Breached, breach-comment-once incl. stale-row, dry-run-no-write, max cap); full sweep green; **live: 2 real runs idempotent** (run1 changed 16, run2 changed 0, 0 breaches/errors); hourly hook registered |
| _(prev)_ | **Reminder Engine Step 3 — Rule Resolution Engine** (`reminder_engine.py`): rule-first, **compute-only, non-destructive** brain. `resolve_reminder_rule` (specificity-scored: brand 20 / stage 20 / product 15 / ticket-type 15 / flow 10 / warranty-route 10 / pending-reason 10 / priority 10; ranked priority→specificity→modified) + `calculate_next_followup` (manual `next_follow_up_date` preserved unless `force`) / `calculate_due_soon_at` / `calculate_stage_due_at` (None when no stage SLA → old tickets fall back to `next_follow_up_date`) / `derive_escalation_level` (overdue-age + repeat/promise-breach/product-at-store/spare bumps) / `derive_customer_update_due` / `refresh_ticket_reminder_state` (save=False default; never overwrites manual follow-up). Read-only `get_reminder_state` API. Today's Work payload gains additive `reminder_rule_applied`/`computed_*`/`customer_update_due` (in-memory, cached rules; classification unchanged). Safe hardcoded fallback when no rule. No AI, no messages, no closures, no writes by default. | `tests/reminder_engine.py` 21/21 (priority, specificity, fallback, disabled, manual-preserve, due-soon<stage-due, escalation-by-age, promise bump, update-due, old-ticket fallback); stage_layer/today_work(24)/stitch_console_spa green; live `get_reminder_state(0014)` + Today's Work payload verified |
| _(prev)_ | **Reminder Engine Step 2 — Customer-promise tracking**: `customer_promised_update_at` / `customer_promise_status` / `promise_breach_reason` fields (programmatic); `stage_rules.compute_promise_status` (Pending→Breached once the promised time passes unless Kept); `set_customer_promise` write-scoped API (logs a `[Customer Informed]` Comment — no new activity table); promise surfaced in the drawer Service Stage section + "Set Customer Promise" quick action; Today's Work gains a promise filter + per-row "Promise breach" chip; `get_customer_promise_breach_report` + `promise_breach` report-catalog entry. Live compute overrides stored status everywhere. | `compute_promise_status` 4 cases (past+Pending→Breached, past+Kept→Kept, future→Pending, blank→None) + breach report run; `stage_layer`/`today_work` (24)/`stitch_console_spa` sweep green; SPA rebuilt |
| `cf24432` | **Reminder Engine Step 1 — plan + skeleton**: approved `docs/reminder_engine_implementation_plan.md` (rule-first, AI-advisory-only) + `Lavanya Reminder Rule` config DocType created programmatically (22 fields, resolution-priority design). No engine wired yet — config foundation only. | DocType inserts; hooks wired; no behavior change |
| `c3d5d88` | **Delta Sprint 2**: surface stage fields in the drawer (read "Service Stage" section, blank-safe); Today's Work flow/stage/due/escalation filter bar + per-row Due-status chip; Due-Soon from `stage_due_at`/`pre_overdue_alert_at` with **fallback** to `next_follow_up_date` for old tickets; escalation mapped to `escalation_level` (filtering only — existing escalation report/notify untouched, no new activity table). | `tests/stage_layer.py` + sweep green; browser screenshots |
| _(prev)_ | **Delta Sprint 1** (per `docs/spa_alignment_delta_implementation_plan.md`): stage layer on top of the SPA — `service_flow_type` / `current_service_stage` / `next_action` (+ stage/SLA/escalation/customer-informed fields) created **programmatically** (not via the shared fixture), `stage_rules.py` source-of-truth, default-stage assignment on new tickets, "Stage Missing" cleanup report. Status / Today's Work / Comment-activity unchanged. | fields created; ticket_type→flow maps; defaults populate; test sweep green |
| `c516fcd` | **Complete ticket lifecycle**: custody moves (Send to SC / Returned from SC / Delivered), Reopen, repeat-complaint detect+link banner, and New Ticket customer auto-fill by mobile — all reusing existing backends. | full custody chain create→delivered runs as uat.coordinator; SPA tests pass |
| _(prev)_ | **In-console New Ticket screen** (`/new-ticket`) replacing the external link; `create_ticket` + `get_new_ticket_options` (staff actor, reuses QR intake validation). | create_ticket works as uat.frontdesk (0026); screen renders |
| `9161ede` | **Critical fix**: `/frontend` served the literal `{{ csrf_token }}` placeholder → every POST 400'd for non-Administrator users (Admin bypasses CSRF, masking it). Controller now injects `frappe.sessions.get_csrf_token()`. | verified as uat.coordinator: real token, action returns 200; source-guard test added |
| `0d3a649` | **Reporting depth** (gap-analysis change #7): Reports overview gains a 30-day created-vs-resolved trend (SVG), status + closure-type breakdown bars (manager-only), and per-report CSV export. New `get_report_trends`/`get_report_breakdowns`. | SPA + report tests; browser screenshot shows trend + breakdowns |
| `cc013fc` | **SLA visibility** (gap-analysis change #2): shared `SlaBadge` shows Helpdesk SLA state (breached/met/paused/due) on Tickets, Today's Work, and the ticket drawer. SLA fields added to the list/today-work/detail payloads. | 24 today_work + SPA tests; browser screenshots show breached/due badges |
| `4e6b972` | **Status-model unification** (gap-analysis change #1): Today's Work derives active/terminal from the unified `status_category` (Resolved=terminal) instead of hard-coded status strings — robust to any status incl. Helpdesk-native Open/Replied. | 24 today_work tests (incl. Replied TW-014c) + live check; payload doesn't leak status_category |
| `43c0ca0` | **Fix**: `cache: 'no-store'` on API reads so a refresh always shows live data (no-cache-header responses could be served stale by the browser heuristic cache). | browser diag: pages load live data |
| `f12bb3e` | **Bug fix**: Helpdesk-native `Open`/`Replied` tickets were invisible on Today's Work (classifier didn't map them). Active tickets matching no bucket now surface as new complaints. NOTE: normal tickets already get `New` (HD Settings `default_ticket_status=New` + Helpdesk `set_default_status`); the only `Open` ticket is the install seed `0001`. So no status-normalization code is needed — this fix is the safety net for seed/`Replied` edge cases. | live data (Open ticket 0001) + regression TW-014b; 23 today_work tests pass |
| `3398545` | Tests: SPA endpoint coverage (`tests/stitch_console_spa.py`) + fixed the stale quick-action assertion broken by Phase 2 wiring | both modules pass via bench console |
| `a8f6acf` | Removed 19 redundant plain-CSS color classes (now generated by Tailwind) | build grep + screenshots |
| `cc849fa` | **Bug fix**: empty Tickets list — `URLSearchParams` sent `search=undefined` literally; `call()` now drops null/undefined params | screenshots |
| `e3d5c99` | Wired the 5 remaining ticket Quick Actions via one config-driven modal | action ran live |
| `2574216` | Ticket Detail activity timeline + add-note | API smoke test |
| `0c943ab` | Global header search + Today's Work metric sub-detail lines | screenshots |
| `7d8ab85` | Rebuilt Reports as the Stitch drill-down report catalog | API + screenshots |
| `2ea4f83` | Adopted frappe-ui Tailwind preset (fixed utility/responsive generation root cause; Tailwind 3.0→3.4) | built CSS grep |
| `948f799` | Native Tickets list page (search + status filter) | API smoke test |

**Net result:** 3 live SPA pages (Today's Work, Tickets, Reports) + Ticket Detail
drawer, all wired to live APIs, all Quick Actions functional, theme on the same
base as Helpdesk/CRM.

### Backend endpoints added
- `stitch_console.get_ticket_list(search, status, start, page_length)` — permission-scoped HD Ticket list
- `stitch_console.get_ticket_activity(ticket_id)` / `add_ticket_note(ticket_id, note)` — timeline + notes
- `manager_reports.get_report_catalog()` / `get_report(report)` — drill-down catalog reusing `reports.manager_dashboard`

---

## 3. Pending work

Stitch designs exist for 19 screens; 3 + the Ticket drawer are built. Remaining
(by value):

| # | Item | Type | Backend needed? |
|---|---|---|---|
| P1 | Customer QR complaint form (mobile intake) | New page | Mostly exists: `api/qr_intake.py`, `customer_intake.py` |
| P2 | Manager / Coordinator dashboards as SPA pages | New pages | Exists: `api/manager_dashboard.py`, `coordinator_dashboard.py` (parallel agent built Desk versions) |
| P3 | Role work-centers (Agent "My Work", Front Desk "Work Center") | New pages | Reuse `today_work.get_today_work` (role-aware) |
| P4 | Front Desk: New Ticket / Create Receipt as SPA | New pages | `workflow_actions.create_product_receipt` exists |
| P5 | Product Custody Detail / Ready-for-Pickup views | New pages | `product_receipt_actions.py` |
| P6 | Role-aware Quick Action buttons (hide actions the user can't run) | Enhancement | `workflow_actions.get_current_user_roles` |
| P7 | Today's Work: table vs. bucket toggle (Stitch shows a sortable table w/ owner column) | Enhancement | add owner/`_assign` to `today_work` payload |
| P8 | Open a PR for the branch | Process | — |
| P9 | Playwright smoke test for `/frontend` routes (assert render + data load) — the API tests landed in `3398545`, this UI half is still open | Test | reuse §5d session harness |
| P10 | CI: build the SPA + run the test modules on PR | Process | — |

### Known open items / cleanup
- Dev-test data on `lavanya-dev`: ticket **0021** left "In Progress", a note on **0014** (from smoke tests) — delete via Desk if desired.
- Scratch screenshot tooling at `D:\lav_shots` (outside repo) — safe to delete.
- Built assets under `public/frontend/assets/` are **untracked**; only the serve-page HTML is committed (build regenerates assets on deploy). Decide whether to track them for zero-build deploys.
- `lav-*` semantic classes still hardcode token hex; intentional (kept), but could move to `@apply` if desired.

---

## 4. How to build each pending item

General recipe for a new SPA page (P1–P5):
1. **Backend**: confirm/[add] a whitelisted method in `lavanya_service/api/…`. Keep it permission-scoped (`frappe.has_permission`) and role-gated where org-wide.
2. **Smoke-test it** with `bench execute` (see §5) before touching the frontend.
3. **Page**: add `frontend/src/pages/<Name>.vue`, wrap content in `<AppShell>`, fetch via `call()`/`post()` from `@/api`. Reuse Stitch patterns (status chips, `lav-metric`, tables) and real Tailwind utilities.
4. **Route**: register in `frontend/src/router.js`; add a nav item in `AppShell.vue` `navItems` if top-level.
5. **Build on host** (see §1), which auto-syncs the serve page.
6. **Verify** (see §5).

Item-specific notes:
- **P1 Customer QR form** — public/guest intake; check `qr_intake.get_qr_intake_options` for the field options, post via `customer_intake`. Mind guest permissions and CSRF.
- **P2 dashboards** — `get_manager_dashboard` already returns a `summary` dict; render as metric cards (can reuse `Reports.vue` catalog pattern or `lav-metric`).
- **P3 work-centers** — `today_work.get_today_work` is already role-aware; a thin page filtered to the role's groups is enough.
- **P6 role-aware buttons** — fetch `get_current_user_roles` on drawer open, hide/disable actions whose allowed roles the user lacks (mirror the `_require_roles` sets in `quick_actions.py`).
- **P7 owner column** — add `_assign`/owner to `SAFE_TICKET_FIELDS` in `today_work.py`, then render a table variant.

---

## 5. How to verify

### 5a. Build verification
```
cd frontend && node node_modules/vite/bin/vite.js build
```
Expect `✓ built in …` and `[lavanya] synced www/frontend.html`. Grep the built
CSS to confirm utilities emit, e.g.:
```
grep -oF 'md\:hidden' ../lavanya_service/public/frontend/assets/index-*.css
```

### 5b. Backend API smoke test (no browser)
```
docker exec devcontainer-example-frappe-1 bash -lc \
 "cd /workspace/development/frappe-bench && \
  bench --site lavanya-dev.localhost execute \
  lavanya_service.api.stitch_console.get_ticket_list --kwargs '{\"page_length\": 3}'"
```
Run as a specific role by replacing `--kwargs` target; or test write actions
(e.g. `workflow_actions.follow_up_service_center`) — note these mutate data.

**Test modules** live in `lavanya_service/tests/` (plain `run()` functions, not
`test_*`). They mutate/clean up their own data, so run via console import (the
`bench execute dotted.path` form mis-evals these):
```
printf 'from lavanya_service.tests import stitch_console_spa as t\nt.run()\n' \
 | docker exec -i devcontainer-example-frappe-1 bash -lc \
   "cd /workspace/development/frappe-bench && bench --site lavanya-dev.localhost console"
```
SPA-relevant modules: `stitch_console_spa` (list/activity/reports endpoints),
`stitch_console_actions` (quick-action wiring + permissions).

### 5c. Serve check
```
docker exec devcontainer-example-frappe-1 bash -lc \
 "curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: lavanya-dev.localhost' \
  http://localhost:8001/frontend"
```
Expect `200`. Repeat for `…/assets/lavanya_service/frontend/assets/<hashed>.css`.

### 5d. Authenticated browser screenshots (the gold standard)

The console is auth-gated. To screenshot real pages **without typing a password**,
mint an Administrator session server-side via `bench` and drive headless Chrome
with it. (Requires Chrome on host + `puppeteer-core`; the harness lives at
`D:\lav_shots`.)

1. **Mint a session id** (passwordless, admin op):
```
printf '%s\n' \
 "import frappe" "from frappe import auth" \
 "frappe.utils.set_request(method='GET', path='/app')" \
 "frappe.local.cookie_manager = auth.CookieManager()" \
 "lm = auth.LoginManager()" "lm.login_as('Administrator')" "frappe.db.commit()" \
 "print('SIDOUT:' + str(frappe.session.sid))" \
 | docker exec -i devcontainer-example-frappe-1 bash -lc \
   "cd /workspace/development/frappe-bench && bench --site lavanya-dev.localhost console"
```
   Grab the `SIDOUT:<hash>` value.

2. **Verify the session** from the host:
```
curl -s -H "Cookie: sid=<hash>" \
  http://lavanya-dev.localhost:8001/api/method/frappe.auth.get_logged_user
```
   Expect `{"message":"Administrator"}`.

3. **Screenshot** with `puppeteer-core` driving the host Chrome: set the `sid`
   cookie, `goto` each `/frontend/<route>`, `page.screenshot({fullPage:true})`.
   (See `D:\lav_shots\shoot.js` for the working script — routes `/`, `/tickets`,
   `/reports`, a report drill-down click, and a Tickets-row click for the drawer.)

This method caught the empty-Tickets bug (`cc849fa`) that build/serve checks missed —
**prefer it for any UI change.**

> Security note: never type the real password into the login form or POST it to
> `/api/method/login` from automation. The `login_as` server-side mint above is an
> administrative DB operation, not credential entry, and is the compliant path.

---

## 6. Quick reference — verify a change end-to-end
1. Edit `frontend/src/…`
2. `node node_modules/vite/bin/vite.js build` (host) → expect synced serve page
3. `bench execute` any new API (5b) → expect real data
4. Serve check (5c) → `200`
5. Authenticated screenshot (5d) → eyeball the page
6. Commit **only own files** (never `git add -A`; a parallel agent also writes here —
   avoid `setup/`, `api/coordinator_dashboard.py`, `api/manager_dashboard.py`,
   `fixtures/client_script.json`, `page/*dashboard/`, `utils/add_client_script.py`).
