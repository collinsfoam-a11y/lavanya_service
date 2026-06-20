# Lavanya Service Production Readiness Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `lavanya_service` secure, reproducible, observable, role-correct, migration-safe, and verifiably ready for a controlled production launch without replacing the existing Vue service console.

**Architecture:** Keep the current hybrid architecture. The Vue 3 SPA is the primary operator interface, Frappe Desk is the administration and fallback interface, and server-side Frappe APIs remain authoritative for permissions, state transitions, SLA/reminder calculations, and audit history. Adopt patterns selectively from Frappe Helpdesk, CRM, Insights, Drive, and the official Frappe UI starter; do not clone or overwrite the existing frontend.

**Tech Stack:** Current baseline: Frappe Framework 15.110.0 and Frappe Helpdesk 1.25.1. Staging adoption target: Frappe Framework 15.110.0 with Frappe Helpdesk 1.26.1. Application stack: Python, MariaDB, Redis/RQ, Vue 3, Frappe UI, Vue Router, Pinia, Vite 5, Tailwind CSS, FrappeTestCase, Vitest, Playwright, Docker/Bench.

---

## 1. Scope and release policy

This plan hardens the system already implemented. It does not add new service flows, payment systems, stock workflows, external messaging automation, or AI execution features.

The Phase 2 platform strategy is:

1. Stabilize the existing Frappe v15 application before any major-version migration.
2. Validate Helpdesk 1.26.1 on a scratch/staging site and adopt its native bulk reply, dark mode, customer synchronization, and related portal improvements instead of rebuilding them in `lavanya_service`.
3. Keep ERPNext customer synchronization conditional because ERPNext is not installed in the current bench.
4. Treat Frappe/ERPNext v16 as a separate post-stabilization migration project with its own compatibility assessment and rollback plan.
5. Extend native Helpdesk behavior only where a documented Lavanya requirement remains unmet.

The release policy is:

1. Security and data correctness before UI polish.
2. A clean checkout must reproduce the live schema and frontend.
3. Every API must enforce permissions independently of page visibility.
4. Vue may hide unavailable actions, but server-side checks remain mandatory.
5. Tests must run through standard Frappe and frontend commands.
6. No production deployment until fresh install, repeated migrate, backup restore, and role-based browser UAT pass.

### Upstream pattern references

- Frappe Helpdesk 1.26.1: ticket queues, ticket details, SLA presentation, agent workflow, bulk reply, dark mode, and conditional ERPNext customer synchronization.
- Frappe CRM: application bootstrap, Pinia, FrappeUI registration, dialogs, resources, realtime setup.
- Frappe Insights: dashboard filters, metrics, charts, report loading/error states.
- Frappe Drive: upload UX and responsive application patterns.
- Official `frappe/frappe-ui-starter`: minimal `frappeRequest` and `resourcesPlugin` setup.

Do not copy upstream code blindly. Confirm API compatibility with the installed Frappe/UI versions and preserve license notices where direct code is reused.

## 2. Production definition of done

Production readiness requires all of the following:

- `git status --short` is clean at the release commit.
- `git diff --check` returns exit code 0.
- All intended schema, fixtures, pages, API modules, and frontend assets are tracked.
- `bench --site <test-site> run-tests --app lavanya_service` discovers and passes tests.
- The legacy custom runner gate reports 26/26 until all coverage is migrated.
- Frontend unit/component tests pass.
- Playwright role matrix passes for Manager, Coordinator, Front Desk, Agent, Viewer, and Guest.
- Clean Linux `npm ci && npm run build` succeeds.
- `npm audit --omit=dev` has no unaccepted high or critical findings.
- Fresh-site install succeeds.
- Existing-site migration succeeds twice without additional changes.
- Backup and restore drill succeeds.
- No unauthorized dashboard, report, ticket, profile, or phone lookup data is returned.
- Scheduler has no invalid-site authentication errors and no unbounded queue growth.
- Production runbook, rollback procedure, monitoring, and owner sign-off are complete.

## 3. Delivery phases and hard gates

| Phase | Focus | Exit gate |
|---|---|---|
| 0 | Baseline and change control | Reproducible inventory and protected working branch |
| 1 | Test foundation | Standard tests discovered; current failures represented |
| 2 | P0 correctness and security | Receipt and permission regressions pass |
| 3 | Data/report/reminder correctness | Counts, dates, SLA, batching and dedupe are correct |
| 4 | Helpdesk 1.26.1 adoption | Scratch upgrade passes and native capabilities are accepted or gap-documented |
| 5 | Vue production foundation | Auth, roles, Frappe UI resources and errors are centralized |
| 6 | UI workflow and accessibility | Role/status actions and keyboard/mobile behavior pass |
| 7 | Migration and build reproducibility | Clean install/build/migrate succeeds |
| 8 | Operations and resilience | Monitoring, backup, restore and scheduler health proven |
| 9 | UAT, load and release | Signed release candidate and rollback rehearsal |

Do not start a later phase while an earlier hard gate is red, except for independent test scaffolding that does not alter behavior.

---

### Task 1: Freeze the baseline and create a production-hardening branch

**Files:**
- Create: `docs/release/production-readiness-baseline.md`
- Modify: `.gitignore`
- Review: all modified and untracked files reported by `git status --short`

**Step 1: Create an isolated worktree**

Run from the app repository:

```powershell
git worktree add ..\lavanya_service-production-ready -b hardening/production-ready
```

Expected: a clean isolated worktree based on the current intended branch.

**Step 2: Inventory the dirty source tree**

Record every current modified and untracked path, its purpose, and whether it belongs in the product.

Expected decisions:

- Track intended AI advisory, dashboard, page, fixture, and setup files.
- Remove temporary/import-only scripts if they are not runtime dependencies.
- Preserve unrelated user changes; do not reset them.

**Step 3: Capture the runtime baseline**

Document:

```bash
bench version
bench --site lavanya-dev.localhost list-apps
bench --site lavanya-dev.localhost show-config
git rev-parse HEAD
node --version
npm --version
```

Also record:

- HD Ticket count.
- Custom field count.
- Installed custom DocTypes.
- Scheduler status.
- Current test result: 24/26 custom runners.
- Current routes and HTTP status.

**Step 4: Establish the initial quality gate**

Run:

```powershell
git diff --check
git status --short
```

Expected initially: known failures are recorded, not ignored.

**Step 5: Commit only the baseline document**

```bash
git add docs/release/production-readiness-baseline.md .gitignore
git commit -m "docs: capture production hardening baseline"
```

---

### Task 2: Convert custom runners into discoverable Frappe tests

**Files:**
- Create: `lavanya_service/tests/test_receipt_api.py`
- Create: `lavanya_service/tests/test_api_permissions.py`
- Create: `lavanya_service/tests/test_today_work.py`
- Create: `lavanya_service/tests/test_reminder_engine.py`
- Create: `lavanya_service/tests/test_installation.py`
- Create: `lavanya_service/tests/test_workflow_actions.py`
- Modify: existing `lavanya_service/tests/*.py` runners as temporary compatibility wrappers

**Step 1: Prove current discovery failure**

Run:

```bash
bench --site lavanya-dev.localhost run-tests --app lavanya_service
```

Expected: `Ran 0 tests`.

**Step 2: Create `FrappeTestCase` smoke coverage**

Add one minimal discoverable test:

```python
from frappe.tests.utils import FrappeTestCase


class TestLavanyaServiceSmoke(FrappeTestCase):
    def test_app_is_installed(self):
        self.assertIn("lavanya_service", frappe.get_installed_apps())
```

**Step 3: Verify discovery becomes non-zero**

Run:

```bash
bench --site lavanya-dev.localhost run-tests --app lavanya_service
```

Expected: at least one test runs.

**Step 4: Migrate behavior coverage**

Move assertions from each `run()` module into independent test methods. Tests must:

- Use unique test identifiers.
- Set user context explicitly.
- Roll back or clean up in `tearDown`.
- Avoid deleting linked tickets when rollback is sufficient.
- Avoid depending on execution order.

**Step 5: Keep the legacy aggregate gate temporarily**

Create a non-mutating script that executes all remaining `run()` entrypoints and fails if any fail.

Expected transitional gates:

- Standard tests: non-zero and green.
- Legacy runners: 26/26.

**Step 6: Commit**

```bash
git add lavanya_service/tests
git commit -m "test: add discoverable frappe test foundation"
```

---

### Task 3: Fix Service Product Receipt visibility and uniqueness

**Files:**
- Modify: `lavanya_service/api/stitch_console.py`
- Modify: `lavanya_service/workflow/quick_actions.py`
- Modify: `lavanya_service/setup/service_receipt.py`
- Test: `lavanya_service/tests/test_receipt_api.py`
- Test: `lavanya_service/tests/test_workflow_actions.py`

**Step 1: Write the failing receipt visibility test**

Create a non-submittable `Service Product Receipt`, link it to an HD Ticket, call `get_ticket_detail`, and assert:

```python
self.assertEqual(result["receipt"]["number"], receipt.name)
self.assertEqual(result["receipt"]["custody_status"], "Received at Store")
```

**Step 2: Verify it fails**

Run:

```bash
bench --site lavanya-dev.localhost run-tests \
  --module lavanya_service.tests.test_receipt_api
```

Expected: receipt number is `None`.

**Step 3: Fix the read path**

Resolution order:

1. Read `HD Ticket.service_product_receipt`.
2. Validate that the linked receipt belongs to the requested ticket.
3. If the link is absent, query by `ticket` without filtering `docstatus=1`.
4. Return a permission-safe receipt payload.

**Step 4: Add database-level duplicate protection**

Make the receipt `ticket` relationship unique, or implement a safe unique index patch if Frappe custom DocType metadata cannot express it reliably.

Use a database lock when creating a receipt:

```python
frappe.db.get_value("HD Ticket", ticket_name, "name", for_update=True)
```

Then repeat the duplicate check inside the transaction.

**Step 5: Prevent receipt/ticket product mismatch**

Choose one rule and test it:

- Recommended: receipt product identity comes from the ticket and cannot be overridden through the action API.
- Allow staff input only for custody-specific details such as accessories and physical condition.

**Step 6: Verify**

Run:

```bash
bench --site lavanya-dev.localhost run-tests \
  --module lavanya_service.tests.test_receipt_api
bench --site lavanya-dev.localhost run-tests \
  --module lavanya_service.tests.test_workflow_actions
```

**Step 7: Commit**

```bash
git add lavanya_service/api/stitch_console.py \
  lavanya_service/workflow/quick_actions.py \
  lavanya_service/setup/service_receipt.py \
  lavanya_service/tests/test_receipt_api.py \
  lavanya_service/tests/test_workflow_actions.py
git commit -m "fix: make product receipt workflow consistent"
```

---

### Task 4: Introduce a single API authorization policy

**Files:**
- Create: `lavanya_service/api/permissions.py`
- Modify: `lavanya_service/api/coordinator_dashboard.py`
- Modify: `lavanya_service/api/manager_dashboard.py`
- Modify: `lavanya_service/api/manager_reports.py`
- Modify: `lavanya_service/api/customer_intake.py`
- Modify: `lavanya_service/api/stitch_console.py`
- Test: `lavanya_service/tests/test_api_permissions.py`

**Step 1: Define the role matrix**

Create constants:

```python
MANAGER_ROLES = {"System Manager", "Lavanya Manager"}
COORDINATOR_ROLES = MANAGER_ROLES | {"Lavanya Service Coordinator"}
INTAKE_ROLES = COORDINATOR_ROLES | {"Lavanya Front Desk", "Lavanya Helpdesk Agent"}
VIEWER_ROLES = INTAKE_ROLES | {"Lavanya Viewer"}
```

Document exactly which endpoint class each role may use.

**Step 2: Write failing role-matrix tests**

For Manager, Coordinator, Agent, Front Desk, Viewer, and Guest, test:

- Coordinator dashboard.
- Manager dashboard.
- Manager-only report.
- Operational report.
- Customer lookup.
- Ticket detail outside permitted scope.

Expected failures before implementation:

- Viewer, Front Desk, and Agent can currently read manager/coordinator dashboards.
- Broad customer lookup is currently accessible to all authenticated test roles.

**Step 3: Add reusable authorization helpers**

Helpers must:

- Reject Guest.
- Check explicit role sets.
- Check global DocType read permission.
- Check document-level permission where a ticket/document is supplied.
- Return no data before authorization succeeds.

**Step 4: Replace page-only security assumptions**

Page JSON roles control navigation only. Every whitelisted method must independently call the authorization helper.

**Step 5: Make mutations POST-only**

Audit all `@frappe.whitelist()` actions that mutate state and add:

```python
@frappe.whitelist(methods=["POST"])
```

Read APIs may remain GET-compatible.

**Step 6: Verify the complete matrix**

Run:

```bash
bench --site lavanya-dev.localhost run-tests \
  --module lavanya_service.tests.test_api_permissions
```

Expected:

- Guest: denied all internal APIs.
- Viewer: approved read-only ticket views only.
- Front Desk/Agent: only intended operational datasets.
- Coordinator: coordinator and approved manager operational views.
- Manager: complete approved access.

**Step 7: Commit**

```bash
git add lavanya_service/api lavanya_service/tests/test_api_permissions.py
git commit -m "fix: enforce api authorization policy"
```

---

### Task 5: Make all report and dashboard queries permission-aware

**Files:**
- Modify: `lavanya_service/reports/manager_dashboard.py`
- Modify: `lavanya_service/api/manager_reports.py`
- Modify: `lavanya_service/api/coordinator_dashboard.py`
- Modify: `lavanya_service/api/manager_dashboard.py`
- Create: `lavanya_service/reports/query_scope.py`
- Test: `lavanya_service/tests/test_api_permissions.py`
- Test: `lavanya_service/tests/test_reports.py`

**Step 1: Write a row-level permission test**

Create two tickets visible to different test users. Assert that each user receives only permitted rows from:

- Daily follow-up.
- Ticket list.
- Dashboard groups.
- CSV/report drill-down.

**Step 2: Centralize query scope**

Preferred order:

1. Use `frappe.get_list`, which applies permission query conditions.
2. Use Frappe Query Builder for joins.
3. If raw SQL is necessary, explicitly apply Frappe permission conditions before executing it.

Never rely only on `frappe.has_permission("HD Ticket", "read")`.

**Step 3: Correct report date semantics**

Use `closure_date` for closure reports instead of `modified`.

Define cancellation date behavior explicitly. If no cancellation timestamp exists, add one through a migration-safe field and set it during the cancellation action.

**Step 4: Correct dashboard count semantics**

- `include_counts=False` must actually avoid expensive count queries.
- List and count filters must be identical.
- Handle `NULL`, empty string, and `[]` assignment consistently.
- Avoid loading entire reports only to call `len`.

**Step 5: Add pagination and limits**

Every drill-down endpoint must accept bounded pagination:

```text
start >= 0
page_length in 1..100
```

Return:

```json
{"rows": [], "count": 0, "has_more": false}
```

**Step 6: Verify**

Run report permission, date, count, and pagination tests.

**Step 7: Commit**

```bash
git add lavanya_service/reports lavanya_service/api lavanya_service/tests/test_reports.py
git commit -m "fix: scope dashboards and reports to authorized data"
```

---

### Task 6: Correct Today's Work counts and fail-closed role handling

**Files:**
- Modify: `lavanya_service/workflow/today_work.py`
- Modify: `lavanya_service/api/today_work.py`
- Modify: `frontend/src/pages/TodayWork.vue`
- Test: `lavanya_service/tests/test_today_work.py`
- Test: `frontend/src/pages/__tests__/TodayWork.spec.js`

**Step 1: Write failing tests**

Cover:

- A ticket in multiple groups counts once in `summary.total_unique`.
- Bucket counts remain independent.
- Unrecognised roles receive no groups or a permission error.
- Counts reflect all matching database rows, not only the displayed page.

**Step 2: Define the response contract**

Recommended shape:

```json
{
  "summary": {
    "total_unique": 16,
    "overdue": 5,
    "due_today": 3
  },
  "groups": [
    {"key": "overdue_follow_up", "count": 5, "tickets": []}
  ]
}
```

**Step 3: Separate count queries from row queries**

Do not infer totals from truncated lists. Use permission-scoped count queries and a bounded ticket page.

**Step 4: Fail closed**

Replace `allowed or all_keys` with an empty set or explicit `PermissionError`.

**Step 5: Resolve the “Total Pending” contract**

The product decision is:

- Display “Total Pending” using unique tickets; or
- Remove that assertion and document the six-metric design.

Recommended: display a unique “Total Pending” summary because it provides a stable operational headline.

**Step 6: Verify backend and component behavior**

Run the Frappe test module and Vitest component test.

**Step 7: Commit**

```bash
git add lavanya_service/workflow/today_work.py \
  lavanya_service/api/today_work.py \
  frontend/src/pages/TodayWork.vue \
  lavanya_service/tests/test_today_work.py \
  frontend/src/pages/__tests__/TodayWork.spec.js
git commit -m "fix: make todays work counts accurate"
```

---

### Task 7: Make reminder timing authoritative and scalable

**Files:**
- Modify: `lavanya_service/setup/service_stages.py`
- Modify: `lavanya_service/reminder_engine.py`
- Modify: `lavanya_service/tasks/reminder_refresh.py`
- Modify: `lavanya_service/reminders/notification_output.py`
- Create: `lavanya_service/patches/v1_0/add_stage_entered_at.py`
- Modify: `lavanya_service/patches.txt`
- Test: `lavanya_service/tests/test_reminder_engine.py`
- Create: `lavanya_service/tests/test_reminder_notifications.py`

**Step 1: Add `stage_entered_at`**

Write a migration patch and lifecycle hook so this field changes only when `current_service_stage` changes.

Backfill existing tickets conservatively:

- Use existing stage audit evidence where available.
- Otherwise use current `modified` once and mark it as a backfilled approximation.

**Step 2: Write timing tests**

Verify unrelated ticket edits do not move stage due dates.

**Step 3: Implement or remove inactive rule fields**

For each configured field, choose one:

- Implement and test it.
- Remove it from the DocType and UI.
- Mark it explicitly reserved and prevent users from configuring it.

Fields requiring a decision:

- `repeat_every_minutes`
- `manager_escalate_after_minutes`
- `owner_escalate_after_minutes`
- `pause_when_sla_paused`
- `business_hours_only`

Recommended: implement escalation thresholds and SLA pause handling now; defer business-calendar calculation unless production requirements demand it.

**Step 4: Prevent scheduler starvation**

Replace the fixed oldest-500 selection with deterministic cursor-based batching or process all active tickets in bounded batches.

Persist a cursor/heartbeat that includes:

- Last processed ticket.
- Candidate count.
- Processed count.
- Error count.
- Duration.

**Step 5: Correct notification deduplication**

Dedupe on:

```text
recipient + ticket + category + day
```

Ensure a normal reminder cannot suppress a later escalation. Add a severity-upgrade test.

**Step 6: Define transaction behavior**

Commit per bounded batch only. Log ticket-specific failures and expose aggregate job health.

**Step 7: Verify**

Test:

- Stage anchor stability.
- Rule thresholds.
- More than 500 active tickets.
- Repeated scheduler runs.
- Reminder plus escalation on the same day.
- No duplicate same-category notification.

**Step 8: Commit**

```bash
git add lavanya_service/reminder_engine.py \
  lavanya_service/tasks/reminder_refresh.py \
  lavanya_service/reminders/notification_output.py \
  lavanya_service/setup/service_stages.py \
  lavanya_service/patches.txt \
  lavanya_service/patches/v1_0 \
  lavanya_service/tests
git commit -m "fix: make reminder scheduling reliable"
```

---

### Task 8: Validate Helpdesk 1.26.1 and adopt native Phase 2 capabilities

**Files:**
- Create: `docs/release/helpdesk-1.26.1-adoption.md`
- Create: `scripts/verify_helpdesk_upgrade.ps1`
- Modify only if a documented gap remains: `lavanya_service/hooks.py`
- Test: `lavanya_service/tests/test_helpdesk_126_adoption.py`

**Step 1: Freeze the current platform baseline**

Record the exact Frappe, Helpdesk, Telephony and `lavanya_service` revisions, installed apps, enabled scheduler state, queues and current migration status.

Do not upgrade the live development site first.

**Step 2: Create a scratch site and restore representative data**

Use a new site or a sanitized restore. Install the same apps and pin Helpdesk 1.26.1 while retaining Frappe 15.110.0.

**Step 3: Run the upgrade**

Execute backup, dependency install, asset build, migrate, cache clear and process restart using the documented bench deployment path. Capture every command and result.

**Step 4: Verify native capabilities before writing custom code**

Verify:

- Bulk reply, attachments, drafts and signatures.
- Dark mode across native Helpdesk pages.
- Agent home/dashboard behavior.
- Portal settings and ticket exports.
- Custom ticket naming support.
- Multiple outgoing mail account selection.
- Message-ID/References threading fallback.
- Knowledge-base likes, dislikes and views.
- Empty states and loading states.

For each item classify:

```text
native-pass | native-gap | not-applicable | blocked-by-business-decision
```

**Step 5: Gate ERPNext customer synchronization**

The current bench does not include ERPNext. Confirm Helpdesk remains healthy without it. Do not add `erpnext` to `required_apps`, install ERPNext, or create duplicate synchronization hooks until the user approves ERPNext installation and duplicate-resolution rules.

**Step 6: Record extension decisions**

If native behavior satisfies the requirement, use it directly. If a gap exists, document the exact requirement, upstream behavior, proposed extension point, permission model and regression test before modifying `lavanya_service`.

Do not copy native bulk reply, dark mode, threading, signature or knowledge-base implementations into the custom app.

**Step 7: Verify rollback**

Restore the pre-upgrade backup to a separate scratch site and prove the documented rollback path.

**Step 8: Commit**

```bash
git add docs/release/helpdesk-1.26.1-adoption.md \
  scripts/verify_helpdesk_upgrade.ps1 \
  lavanya_service/tests/test_helpdesk_126_adoption.py
git commit -m "test: validate helpdesk 1.26.1 adoption"
```

---

### Task 9: Establish the Vue application bootstrap

**Files:**
- Modify: `frontend/src/main.js`
- Modify: `frontend/src/router.js`
- Create: `frontend/src/stores/session.js`
- Create: `frontend/src/stores/roles.js`
- Create: `frontend/src/resources/session.js`
- Modify: `frontend/src/api.js`
- Modify: `frontend/package.json`
- Test: `frontend/src/stores/__tests__/session.spec.js`

**Step 1: Add Pinia and Frappe UI plugins**

Follow the CRM/official starter pattern:

```javascript
setConfig('resourceFetcher', frappeRequest)
app.use(FrappeUI)
app.use(resourcesPlugin)
app.use(createPinia())
app.use(router)
```

Do not change routes or visible design in this step.

**Step 2: Create session bootstrap**

Load:

- Current user.
- User display name.
- Roles.
- CSRF token/context needed by the SPA.

Represent states explicitly:

```text
loading | authenticated | guest | error
```

**Step 3: Add a router guard**

Before protected routes:

- Await session bootstrap.
- Redirect Guest to `/login?redirect-to=/frontend...`.
- Preserve the intended destination.
- Avoid rendering the application shell before auth is known.

**Step 4: Centralize HTTP error parsing**

Parse `_server_messages` safely for GET and POST.

Behavior:

- 400: show actual validation message.
- 401/403 due to session: refresh session and redirect to login.
- 403 due to role: show “You do not have access”.
- 409/duplicate-style errors: show conflict message.
- 500: show stable user message and log correlation information.

**Step 5: Verify**

Unit tests:

- Guest redirect.
- Authenticated bootstrap.
- Session expiration after initial load.
- Validation error preservation.
- Permission error presentation.

**Step 6: Commit**

```bash
git add frontend/src/main.js frontend/src/router.js frontend/src/api.js \
  frontend/src/stores frontend/src/resources frontend/package.json
git commit -m "feat: add production session bootstrap"
```

---

### Task 10: Make navigation and ticket actions role/status-aware

**Files:**
- Modify: `frontend/src/components/AppShell.vue`
- Modify: `frontend/src/components/TicketDetail.vue`
- Create: `frontend/src/workflow/actionPolicy.js`
- Create: `frontend/src/workflow/rolePolicy.js`
- Test: `frontend/src/workflow/__tests__/actionPolicy.spec.js`
- Test: `frontend/src/components/__tests__/TicketDetail.spec.js`
- Test: `lavanya_service/tests/test_api_permissions.py`

**Step 1: Create a declarative action policy**

Each action declares:

```javascript
{
  key,
  roles,
  statuses,
  receiptStates,
  requiresReceipt,
  endpoint
}
```

**Step 2: Match server rules**

At minimum fix:

- Reopen appears only for `Closed`.
- Receipt creation appears only when no receipt exists and ticket type permits it.
- Ready-for-pickup requires a receipt in the correct custody state.
- Custody transitions appear only from valid prior states.
- Closure actions appear only to authorized roles.

**Step 3: Filter navigation**

- Reports visible only to approved report roles.
- New Ticket visible only to intake roles.
- Administration links go to Frappe Desk.
- Display actual user identity in the user menu.

**Step 4: Preserve server authority**

The client policy is UX only. Keep all server authorization/state validation and test direct API calls.

**Step 5: Verify**

Component tests render each role/status combination and assert visible actions.

**Step 6: Commit**

```bash
git add frontend/src/components frontend/src/workflow frontend/src/components/__tests__
git commit -m "fix: align vue actions with workflow permissions"
```

---

### Task 11: Migrate high-risk UI primitives to Frappe UI

**Files:**
- Modify: `frontend/src/components/TicketDetail.vue`
- Modify: `frontend/src/pages/NewTicket.vue`
- Modify: `frontend/src/pages/Tickets.vue`
- Modify: `frontend/src/pages/Reports.vue`
- Modify: `frontend/src/pages/TodayWork.vue`
- Create: `frontend/src/components/common/AsyncState.vue`
- Create: `frontend/src/components/common/EmptyState.vue`
- Create: `frontend/src/components/common/ConfirmActionDialog.vue`

**Step 1: Migrate dialogs first**

Replace custom modal containers with Frappe UI `Dialog`.

Acceptance:

- Focus trapped.
- Escape closes when safe.
- Focus returns to trigger.
- Dialog title and description are announced.
- Submit button exposes loading state.

**Step 2: Migrate form controls**

Use `FormControl`, `TextInput`, `Select`, `Textarea`, `Checkbox`, and `ErrorMessage`.

Keep backend validation authoritative.

**Step 3: Standardize asynchronous states**

Every resource view gets:

- Skeleton/loading.
- Empty state.
- Permission state.
- Retryable error state.
- Success state.

**Step 4: Use side-panel workflow**

Retain TicketDetail as the Helpdesk/CRM-style side panel instead of navigating operators away from their queue.

**Step 5: Keep visual change bounded**

Do not redesign colors or information hierarchy during component migration. Make behavior equivalent first.

**Step 6: Verify**

Run component tests and Playwright keyboard checks.

**Step 7: Commit**

```bash
git add frontend/src
git commit -m "refactor: adopt frappe ui workflow components"
```

---

### Task 12: Correct dates, CSV export, WhatsApp links and client safety

**Files:**
- Create: `frontend/src/utils/date.js`
- Create: `frontend/src/utils/csv.js`
- Modify: `frontend/src/pages/TodayWork.vue`
- Modify: `frontend/src/pages/Tickets.vue`
- Modify: `frontend/src/pages/Reports.vue`
- Modify: `frontend/src/components/TicketDetail.vue`
- Test: `frontend/src/utils/__tests__/date.spec.js`
- Test: `frontend/src/utils/__tests__/csv.spec.js`

**Step 1: Replace UTC date slicing**

Remove operational use of:

```javascript
new Date().toISOString().slice(0, 10)
```

Use site-provided date/time or an explicit Asia/Kolkata-aware utility.

**Step 2: Neutralize spreadsheet formulas**

Before CSV escaping, prefix cells beginning with `=`, `+`, `-`, or `@` with a single quote.

Add tests for:

```text
=CMD()
-1+1
SUM(A1:A2)
@malicious
```

**Step 3: Harden external links**

Use:

```javascript
window.open(url, '_blank', 'noopener,noreferrer')
```

Validate and normalize phone numbers before constructing WhatsApp URLs.

**Step 4: Verify**

Run unit tests with DST-independent fixed clocks and India-local midnight cases.

**Step 5: Commit**

```bash
git add frontend/src/utils frontend/src/pages frontend/src/components/TicketDetail.vue
git commit -m "fix: harden frontend dates and exports"
```

---

### Task 13: Make DocType and setup migrations idempotent and atomic

**Files:**
- Modify: `lavanya_service/setup/install.py`
- Modify: `lavanya_service/setup/appointment.py`
- Modify: `lavanya_service/setup/reminder_rule.py`
- Modify: `lavanya_service/setup/service_receipt.py`
- Modify: setup modules containing internal `frappe.db.commit()`
- Modify or remove: `lavanya_service/utils/add_client_script.py`
- Create: `lavanya_service/patches/v1_0/reconcile_custom_doctypes.py`
- Modify: `lavanya_service/patches.txt`
- Test: `lavanya_service/tests/test_installation.py`

**Step 1: Write repeated-migrate tests**

Capture metadata before and after running setup twice. Assert:

- No duplicate fields.
- No duplicate permissions.
- No duplicate statuses, roles, scripts, or templates.
- Existing field types are not mutated illegally.
- Schema changes are reconciled.

**Step 2: Remove import-time mutation**

`add_client_script.py` must expose a callable setup function only. No database writes at module import.

**Step 3: Reconcile existing custom DocTypes**

Appointment and Reminder Rule setup must update fields and permissions when the DocType already exists rather than returning `"exists"`.

Prefer standard fixtures or patches for stable metadata.

**Step 4: Reduce commits**

Remove internal commits from nested setup functions where practical. Let install/migrate control the transaction boundary.

If a step must commit, document why and make the partial state recoverable.

**Step 5: Update stale setup documentation**

Make `_steps()` comments match the actual setup sequence.

**Step 6: Verify**

On a scratch site:

```bash
bench --site lavanya-migrate-test.localhost migrate
bench --site lavanya-migrate-test.localhost migrate
```

Expected: both succeed and the second run produces no duplicate metadata.

**Step 7: Commit**

```bash
git add lavanya_service/setup lavanya_service/utils \
  lavanya_service/patches.txt lavanya_service/patches \
  lavanya_service/tests/test_installation.py
git commit -m "fix: make install and migrate idempotent"
```

---

### Task 14: Make frontend dependencies and builds reproducible

**Files:**
- Modify: `frontend/package.json`
- Keep one: `frontend/package-lock.json` or `frontend/yarn.lock`
- Delete the unused lockfile
- Modify: `frontend/vite.config.mjs`
- Modify: `frontend/README.md`
- Modify: `.gitignore`
- Create: `scripts/verify_frontend.ps1`

**Step 1: Choose one package manager**

Recommended for the current environment: npm, because the clean audit used `npm ci`.

Delete `yarn.lock`, pin the package manager in `package.json`, and document:

```json
"packageManager": "npm@<approved-version>"
```

**Step 2: Pin Frappe UI**

Do not depend on an unpinned GitHub head. Use an approved release or exact commit compatible with Frappe 15 and the selected upstream patterns.

**Step 3: Upgrade vulnerable transitive dependencies**

Run:

```bash
npm audit --omit=dev
npm outdated
```

Update deliberately, then verify UI behavior. Do not use an unreviewed forced major upgrade.

**Step 4: Prevent cross-platform `node_modules` reuse**

Ensure `node_modules` is never tracked or copied between Windows and Linux containers.

Build only after:

```bash
rm -rf node_modules
npm ci
```

inside the target Linux environment.

**Step 5: Make Vite config testable**

Allow build configuration to receive the webserver port through environment/config fallback so an isolated clean build does not require a complete bench tree.

Ensure the production sync plugin fails with a clear message if the destination directory is absent.

**Step 6: Add deterministic build verification**

`verify_frontend.ps1` must:

- Copy source without `node_modules`.
- Install clean dependencies in the container.
- Run tests.
- Run build.
- Confirm generated index references existing hashed assets.
- Confirm CSRF placeholder/context is retained.

**Step 7: Commit**

```bash
git add frontend scripts/verify_frontend.ps1 .gitignore
git commit -m "build: make frontend dependencies reproducible"
```

---

### Task 15: Add frontend unit and Playwright role-based tests

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/vitest.config.js`
- Create: `frontend/src/test/setup.js`
- Create: `playwright.config.js`
- Create: `frontend/tests/e2e/auth.spec.js`
- Create: `frontend/tests/e2e/ticket-workflow.spec.js`
- Create: `frontend/tests/e2e/role-matrix.spec.js`
- Create: `frontend/tests/e2e/reports.spec.js`
- Create: `frontend/tests/e2e/fixtures/session.js`

**Step 1: Add Vitest**

Scripts:

```json
"test": "vitest run",
"test:watch": "vitest"
```

Cover pure policies, utilities, stores, and core components.

**Step 2: Add Playwright**

Use Playwright projects for authenticated role sessions. Reuse the repository's server-side `login_as` session harness; never store or type production passwords.

**Step 3: Seed dedicated UAT users**

Create users through test setup, not production fixtures:

- Manager.
- Coordinator.
- Front Desk.
- Helpdesk Agent.
- Viewer.

**Step 4: Implement role matrix**

For each role verify:

- Login/logout.
- Visible navigation.
- Today’s Work groups.
- Ticket list scope.
- Ticket detail visibility.
- Visible and hidden actions.
- Direct API denial for hidden actions.

**Step 5: Implement critical journeys**

At minimum:

1. Create ticket.
2. Register brand complaint.
3. Create product receipt.
4. Move custody states.
5. Mark ready for pickup.
6. Deliver product.
7. Close and reopen a closed ticket.
8. Add follow-up and customer promise.
9. Open permitted report and export safe CSV.

**Step 6: Add Guest/session tests**

- Guest visiting `/frontend` redirects to login.
- Expired session redirects without losing return path.
- Permission errors do not expose stack traces.

**Step 7: Commit**

```bash
git add frontend playwright.config.js
git commit -m "test: add frontend and role based ui coverage"
```

---

### Task 16: Add CI gates

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `scripts/run_custom_test_gate.py`
- Create: `scripts/check_fixtures.py`
- Create: `scripts/check_whitelisted_permissions.py`

**Step 1: Define CI jobs**

Jobs:

1. Python compile and formatting checks.
2. Frappe standard tests.
3. Legacy custom runner gate.
4. Frontend install, audit, unit tests and build.
5. Fixture/schema policy checks.
6. Playwright smoke against a prepared site.

**Step 2: Add security-oriented static checks**

Fail CI when:

- New whitelisted methods lack an authorization decision.
- A mutation is exposed through unrestricted GET.
- Forbidden runtime records appear in fixtures.
- Both npm and Yarn lockfiles exist.
- Import-time setup mutation is detected.

These checks supplement review; they do not replace runtime permission tests.

**Step 3: Add artifact retention**

Store:

- Test results.
- Playwright traces, screenshots and videos on failure.
- Built frontend manifest.
- App/version inventory.

**Step 4: Verify CI locally where possible**

Run the same scripts inside the devcontainer before pushing.

**Step 5: Commit**

```bash
git add .github scripts
git commit -m "ci: enforce production readiness gates"
```

---

### Task 17: Clean scheduler and operational runtime

**Files:**
- Modify: `lavanya_service/hooks.py`
- Create: `lavanya_service/monitoring.py`
- Create: `docs/runbooks/scheduler-and-worker.md`
- Create: `docs/runbooks/site-cleanup.md`
- Test: `lavanya_service/tests/test_scheduler_health.py`

**Step 1: Remove or disable broken scratch sites**

Inspect:

- `lavanya-customer-migration-test.localhost`
- `lavanya-reinstall-test.localhost`

For each, either repair credentials and document ownership, or archive/remove it through the approved site-cleanup process.

Expected: scheduler log no longer reports MariaDB authentication errors for abandoned sites.

**Step 2: Add scheduler health signals**

Expose or log:

- Last successful reminder refresh.
- Tickets scanned/changed/errors.
- Last daily notification run.
- Notification created/deduped/skipped counts.
- Worker queue depth.
- Oldest queued job age.

**Step 3: Define alert thresholds**

Examples:

- No hourly reminder success for 2 hours.
- Any repeated ticket processing error.
- Queue depth continuously above agreed threshold.
- Oldest job above agreed age.
- Database/Redis unavailable.

**Step 4: Size workers**

Run a controlled load test and decide whether one worker is sufficient. Separate short/default and long queues in production if long jobs delay operator actions.

**Step 5: Verify**

Run scheduler jobs manually on a scratch site, inspect logs, and confirm no duplicate side effects.

**Step 6: Commit**

```bash
git add lavanya_service/hooks.py lavanya_service/monitoring.py \
  lavanya_service/tests/test_scheduler_health.py docs/runbooks
git commit -m "ops: add scheduler health and runbooks"
```

---

### Task 18: Build a fresh-site and migration verification harness

**Files:**
- Create: `scripts/verify_fresh_site.ps1`
- Create: `scripts/verify_migrate_idempotency.ps1`
- Create: `docs/runbooks/fresh-site-verification.md`

**Step 1: Automate fresh-site creation**

The script must:

1. Create a temporary site.
2. Install Telephony if required.
3. Install Helpdesk.
4. Install `lavanya_service`.
5. Run migrate.
6. Build assets.
7. Run backend tests.
8. Probe `/`, `/helpdesk`, `/frontend`, and public QR route if retained.

**Step 2: Verify exact schema**

Check:

- Required custom fields.
- Required custom DocTypes.
- Required pages.
- Required roles and DocPerms.
- Form/Client scripts.
- Scheduler jobs.
- No production users or tickets installed as fixtures.

**Step 3: Run migrate twice**

Capture metadata counts before and after the second migration.

Expected: no duplicates and no unexpected mutations.

**Step 4: Destroy only the named temporary site**

The script must verify the resolved site path and require an explicit temporary-site prefix before deletion.

**Step 5: Commit**

```bash
git add scripts docs/runbooks/fresh-site-verification.md
git commit -m "test: automate fresh install and migrate verification"
```

---

### Task 19: Prove backup, restore and rollback

**Files:**
- Create: `docs/runbooks/backup-restore.md`
- Create: `docs/runbooks/release-rollback.md`
- Create: `scripts/verify_restore.ps1`

**Step 1: Create a full backup**

```bash
bench --site <source-site> backup --with-files
```

Record database, public files and private files artifacts.

**Step 2: Restore to a scratch site**

Restore all three artifacts to a new site and run migrate.

**Step 3: Validate restored behavior**

Check:

- Ticket count.
- Customer profile count.
- Receipt links and custody logs.
- Attachments.
- Roles and permissions.
- Frontend routes.
- Scheduler disabled until validation finishes.

**Step 4: Rehearse application rollback**

Procedure:

1. Backup before deployment.
2. Tag current production commit.
3. Deploy release candidate.
4. Run migrate and smoke tests.
5. Simulate rollback to previous tag.
6. Restore database if the migration is not backward-compatible.

**Step 5: Define rollback decision thresholds**

Rollback immediately on:

- Permission/data exposure.
- Migration failure.
- Ticket creation/action failure.
- Receipt/custody corruption.
- Sustained API or worker outage.

**Step 6: Commit**

```bash
git add docs/runbooks scripts/verify_restore.ps1
git commit -m "docs: add tested backup and rollback procedures"
```

---

### Task 20: Execute performance, concurrency and security validation

**Files:**
- Create: `tests/performance/ticket_lists.py`
- Create: `tests/performance/reminder_refresh.py`
- Create: `tests/security/api_matrix.py`
- Create: `docs/release/performance-results.md`
- Create: `docs/release/security-results.md`

**Step 1: Define representative volume**

Agree on expected production size:

- Active tickets.
- Closed tickets.
- Daily ticket creation.
- Staff users.
- Concurrent operators.
- Attachments.

Use at least 2x the expected first-year active volume for staging tests.

**Step 2: Test critical reads**

Measure p50/p95 for:

- Today’s Work.
- Ticket list/search.
- Ticket detail.
- Manager reports.
- Customer lookup.

Set explicit acceptance thresholds before testing.

**Step 3: Test write concurrency**

Simulate:

- Two users creating a receipt for the same ticket.
- Two users applying different ticket transitions.
- Scheduler refreshing while an operator changes stage.
- Concurrent follow-up updates.

Expected: one valid outcome, no duplicate receipts, no silent overwrites.

**Step 4: Test security**

Verify:

- Guest/internal endpoint boundaries.
- Role and row-level permission matrix.
- CSRF enforcement.
- CSV formula protection.
- No stack traces or secrets in responses.
- Rate limits for public QR endpoints.
- Attachment access permissions.

**Step 5: Record results**

Any accepted limitation requires owner, reason, expiry date, and compensating control.

**Step 6: Commit**

```bash
git add tests docs/release
git commit -m "test: record performance and security validation"
```

---

### Task 21: Run formal role-based UAT

**Files:**
- Create: `docs/uat/production-uat-script.md`
- Create: `docs/uat/production-uat-results.md`

**Step 1: Prepare realistic staging data**

Include:

- New complaint.
- Registration pending.
- Waiting on customer.
- Waiting on part.
- Product at store with and without receipt.
- Ready for pickup.
- Resolved.
- Closed.
- Repeat complaint.
- Promise breach.
- Overdue/escalated ticket.

**Step 2: Run UAT by role**

Each real role owner must validate:

- Information visible.
- Information intentionally hidden.
- Available actions.
- Required fields.
- Error messages.
- Search/filter/report behavior.
- Mobile/tablet usability if required.

**Step 3: Confirm Desk fallback**

Verify managers can administer master data, roles, and exceptional ticket corrections through Desk without editing upstream Helpdesk code.

**Step 4: Capture sign-off**

Record:

- User.
- Role.
- Date.
- Release commit.
- Passed/failed scenarios.
- Accepted limitations.

**Step 5: Commit**

```bash
git add docs/uat
git commit -m "docs: record production uat"
```

---

### Task 22: Prepare and deploy the release candidate

**Files:**
- Update: `lavanya_service/docs/production_hardening_checklist.md`
- Update: `lavanya_service/docs/final_phase1_readiness_report.md`
- Update: `docs/internal_pilot_readiness.md`
- Create: `CHANGELOG.md`
- Create: `docs/release/release-candidate.md`

**Step 1: Remove stale claims**

Update older readiness documents so they do not claim “GO” based on obsolete commits or superseded test results.

**Step 2: Run the complete release gate**

Required commands:

```bash
git diff --check
git status --short
python -m compileall -q lavanya_service
bench --site <test-site> run-tests --app lavanya_service
npm ci
npm run test
npm run build
npm audit --omit=dev
```

Also run:

- Legacy 26-runner gate.
- Playwright role matrix.
- Fresh-site verification.
- Double migrate.
- Restore verification.
- HTTP smoke.
- Scheduler health check.

**Step 3: Confirm a clean repository**

Expected:

```text
git status --short
```

returns no output.

**Step 4: Tag the release candidate**

```bash
git tag -a v1.0.0-rc.1 -m "Lavanya Service production release candidate 1"
```

**Step 5: Deploy to staging**

Use the same Docker images, app commits, environment settings, proxy configuration, and worker layout intended for production.

**Step 6: Observe staging**

Minimum soak:

- One complete hourly reminder cycle.
- One complete daily notification cycle.
- Realistic operator workflow.
- No permission, scheduler, queue, or migration errors.

**Step 7: Production go/no-go**

Go only when:

- All hard gates pass.
- Backup exists.
- Restore drill passed.
- Rollback owner is present.
- Manager, Coordinator, Front Desk and Agent sign-offs are recorded.
- Release commit and app versions are pinned.

**Step 8: Final release**

```bash
git tag -a v1.0.0 -m "Lavanya Service production release"
git push origin hardening/production-ready --tags
```

---

## 4. Recommended implementation sequence

Execute tasks in this order:

1. Task 1 — baseline.
2. Task 2 — standard test foundation.
3. Tasks 3–6 — P0/P1 security and correctness.
4. Task 7 — reminder reliability.
5. Task 8 — Helpdesk 1.26.1 scratch upgrade and native capability adoption.
6. Tasks 9–12 — Vue production foundation and UI correctness.
7. Tasks 13–16 — migrations, dependencies, frontend tests, CI.
8. Tasks 17–19 — operations, fresh install, backup and rollback.
9. Tasks 20–21 — security/performance validation and UAT.
10. Task 22 — release candidate and production decision.

Tasks 3 and 4 can be developed in parallel only after Task 2 provides independent regression coverage. Task 8 must use an isolated scratch site and must not be merged until its compatibility and rollback evidence is reviewed. Merge behavior changes one at a time and rerun the complete gate after every merge.

## 5. Effort estimate

For one experienced Frappe/Vue engineer with access to business role owners:

| Workstream | Estimated engineering days |
|---|---:|
| Test foundation and CI | 3–4 |
| Security and data correctness | 4–6 |
| Reminder/report correctness | 3–5 |
| Vue session, role UX and Frappe UI migration | 5–8 |
| Migration/build reproducibility | 3–4 |
| Operations, restore, performance and release | 4–6 |
| Total | 22–33 |

This estimate excludes major new service flows and external messaging integrations. Calendar duration will be longer if role-owner UAT and infrastructure provisioning are not available continuously.

## 6. Immediate first milestone

The first milestone is complete only when:

- Standard Frappe tests are discovered.
- The receipt bug has a failing regression test.
- Dashboard/report/customer lookup permission leaks have failing role-matrix tests.
- Those tests are fixed and pass.
- The intended untracked runtime files are classified.
- No new feature work has been added.

That milestone removes the highest production risk and establishes a trustworthy base for the remaining hardening work.
