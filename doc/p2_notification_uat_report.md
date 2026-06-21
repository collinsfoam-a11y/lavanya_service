# P2.2 Notification UAT Report

## UAT Date

2026-06-20

## UAT Scope

User Acceptance Testing for P2.2 dry-run notification template and queue infrastructure. All tests performed under dry-run mode only.

## UAT Environment

- Site: `lavanya-dev.localhost`
- Frappe v15.110.0
- Container: `devcontainer-example-frappe-1`
- User: `Administrator` (System Manager role)
- Agent user: `p2-agent@example.test` (Lavanya Helpdesk Agent role)

## Test Cases

### UAT-N-01: Template Coverage

**Verify all 15 event templates exist.**

- Outcome: **PASS**
- Evidence: DB query returned 15 active templates covering all 15 required event types across WhatsApp, SMS, and Internal channels.
- Notes: All WhatsApp/SMS templates require approval by default. Internal templates do not.

### UAT-N-02: Normal Message Preview

**Preview a WhatsApp template for a ticket with all fields populated.**

- Outcome: **PASS**
- Evidence: `preview_notification` returned `ok=True` with correctly rendered message including customer_name, ticket_id, and product_type. No missing variables.
- Sample output: "Hello Audit Customer, your service ticket 0425 for Refrigerator has been created."

### UAT-N-03: Missing Variable Safety

**Preview a template that references a variable not available on the ticket.**

- Outcome: **PASS**
- Evidence: `preview_notification` returned `ok=False` with `missing_variables: ["definitely_missing_var"]`. No crash, no partial render with raw template syntax.
- Sample output: Missing variable `definitely_missing_var` is reported explicitly.

### UAT-N-04: Queue with Valid Phone

**Queue a WhatsApp notification for a ticket with a valid Indian mobile number.**

- Outcome: **PASS**
- Evidence: Queue record created with `dry_run=1`, `status="Approval Pending"`, `phone="9876543210"` (normalized), `rendered_message` populated. Audit fields recorded.
- Phone normalization verified: raw `+91 98765 43210` normalized to `9876543210`.

### UAT-N-05: Queue with Missing Phone

**Queue a WhatsApp notification for a ticket with no phone number.**

- Outcome: **PASS**
- Evidence: Queue record created with `status="Skipped"`, `error_message="Missing or invalid customer phone."`, `phone=""`. The template is still previewable but the queue entry correctly reports the block reason.

### UAT-N-06: Live Send Block

**Verify the provider abstraction blocks live sending when `LIVE_NOTIFICATIONS_ENABLED` is not set.**

- Outcome: **PASS**
- Evidence: `DryRunProvider.send()` raised `frappe.ValidationError("Live notifications are disabled; dry-run queue only.")`.
- Confirmed `frappe.conf.get("LIVE_NOTIFICATIONS_ENABLED")` returns `None` (falsy).

### UAT-N-07: Manager Approval

**Approve a queued notification as Administrator.**

- Outcome: **PASS**
- Evidence: Queue status updated to `Approved`, `approved_by="Administrator"`, `approved_at` timestamp recorded. The record remains dry-run with no live send triggered.

### UAT-N-08: Agent Cannot Approve

**Attempt to approve a queued notification as Lavanya Helpdesk Agent.**

- Outcome: **PASS**
- Evidence: `PermissionError` raised. Agent role (`Lavanya Helpdesk Agent`) does not have `APPROVAL_ROLES` membership.
- Agent CAN preview templates (via `PREVIEW_ROLES`).

### UAT-N-09: Cancel Notification

**Cancel a queued notification with a reason.**

- Outcome: **PASS**
- Evidence: Queue status updated to `Cancelled`, reason recorded in `error_message` field.

### UAT-N-10: Mark Skipped

**Mark a queued notification as skipped with a reason.**

- Outcome: **PASS**
- Evidence: Queue status updated to `Skipped`, reason recorded in `error_message` field.

### UAT-N-11: Frontend Communication Preview

**Open Ticket Detail for a ticket, select a notification template, and preview the rendered message.**

- Outcome: **PASS** (verified via screenshot capture)
- Evidence: `ticket_detail_communication_preview.png` shows the Communication Preview section with template selector, rendered preview pane, and past queue table.

### UAT-N-12: Frontend Template Modal

**Open the template selection modal to browse available templates.**

- Outcome: **PASS** (verified via screenshot capture)
- Evidence: `template_selection_modal.png` shows the modal with all templates listed.

### UAT-N-13: Frontend Reports Notifications Tab

**Navigate to Reports and view the Notifications tab.**

- Outcome: **PASS** (verified via screenshot capture)
- Evidence: `notifications_report.png` shows the queue list with status cards and action buttons.

### UAT-N-14: Dark Mode Readability

**View the Notifications tab with dark-mode styles.**

- Outcome: **PASS** (verified via screenshot capture)
- Evidence: `dark_mode_notification_screen.png` shows the table with dark theme colors applied.

### UAT-N-15: No Native Confirm

**Verify that notification UI actions use LavConfirm, not native window.confirm().**

- Outcome: **PASS**
- Evidence: Grep for `window.confirm` and `native.confirm` in `TicketDetail.vue` and `Reports.vue` returned no matches. All confirmation flows use `useConfirm()/LavConfirm`.

### UAT-N-16: No Provider Credentials Committed

**Verify no WhatsApp/SMS provider credentials are stored in source code.**

- Outcome: **PASS**
- Evidence: Grep for `TWILIO`, `WHATSAPP_TOKEN`, `SMS_KEY`, `API_SECRET`, `ACCESS_TOKEN`, `provider_secret` in notification source files returned no matches.

### UAT-N-17: Frontend Build

**Run production build and verify zero errors.**

- Outcome: **PASS**
- Evidence: `npx vite build` completed with `built in 34.02s`, 0 errors.

### UAT-N-18: Existing Flows Unchanged

**Verify that penalty tab, ticket workflows, and manager dashboard still work.**

- Outcome: **PASS**
- Evidence: `bench --site lavanya-dev.localhost run-tests --app lavanya_service` returned `Ran 11 tests ... OK`. Reports route returns HTTP 200.

## UAT Summary

| # | Test Case | Result |
|---|---|---|
| UAT-N-01 | Template Coverage | PASS |
| UAT-N-02 | Normal Message Preview | PASS |
| UAT-N-03 | Missing Variable Safety | PASS |
| UAT-N-04 | Queue with Valid Phone | PASS |
| UAT-N-05 | Queue with Missing Phone | PASS |
| UAT-N-06 | Live Send Block | PASS |
| UAT-N-07 | Manager Approval | PASS |
| UAT-N-08 | Agent Cannot Approve | PASS |
| UAT-N-09 | Cancel Notification | PASS |
| UAT-N-10 | Mark Skipped | PASS |
| UAT-N-11 | Frontend Communication Preview | PASS |
| UAT-N-12 | Frontend Template Modal | PASS |
| UAT-N-13 | Frontend Reports Notifications Tab | PASS |
| UAT-N-14 | Dark Mode Readability | PASS |
| UAT-N-15 | No Native Confirm | PASS |
| UAT-N-16 | No Provider Credentials | PASS |
| UAT-N-17 | Frontend Build | PASS |
| UAT-N-18 | Existing Flows Unchanged | PASS |

**Final Result: 18/18 PASS**

## Automated Regression Verification

```text
bench --site lavanya-dev.localhost migrate                                               -> PASS
bench --site lavanya-dev.localhost execute lavanya_service.tests.p2_notification_tests.run -> 10 pass, 0 fail
bench --site lavanya-dev.localhost execute lavanya_service.tests.p2_tests.run             -> 18 pass, 0 fail
cd frontend && npm install && node node_modules/vite/bin/vite.js build                   -> PASS
```

## Notes

- All queue operations are dry-run only. No live WhatsApp/SMS was sent during UAT.
- Template catalog defaults to English; Malayalam and Mixed language options are available as DocType select options but no templates are seeded in those languages yet.
- The existing Ticket Detail "Message on WhatsApp" link is a pre-P2.2 manual staff-initiated feature and is unrelated to the P2.2 notification queue infrastructure.
- Earlier intermittent DB-integrity failures in the focused test runner were resolved by adding `_purge_stale()` cleanup and disabling the welcome email for the test agent user.
