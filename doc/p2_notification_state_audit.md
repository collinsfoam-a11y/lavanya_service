# P2.2 Notification Templates + Dry-run Queue — State Audit

> Audit date: 2026-06-20
> Auditor: AI agent after P2.1 commit
> Scope: Inspect existing P2.2 files; do not add new notification code until gaps are recorded.

---

## 1. Implemented Files

### Backend

| File | Status | Notes |
|---|---|---|
| `lavanya_service/setup/notifications.py` | ✅ present | Creates `Lavanya Notification Template`, `Lavanya Notification Queue`, seeds 15 default templates |
| `lavanya_service/api/notifications.py` | ✅ present | Whitelisted APIs: `get_notification_templates`, `get_notification_queue`, `preview_notification`, `queue_notification`, `approve_notification`, `cancel_notification`, `mark_notification_skipped` |
| `lavanya_service/notifications/provider.py` | ✅ present | `DryRunProvider`; `live_notifications_enabled()` guard |
| `lavanya_service/utils/phone.py` | ✅ present | `normalize_phone()` used by queueing |
| `lavanya_service/hooks.py` | ✅ wired | `after_install` / `after_migrate` call `setup.notifications.create_notification_doctypes` |
| `lavanya_service/tests/p2_notification_tests.py` | ✅ present | 10-check focused runner |

### Frontend

| File | Status | Notes |
|---|---|---|
| `frontend/src/components/TicketDetail.vue` | ✅ present | Communication Preview section with template select, rendered preview, past queue table |
| `frontend/src/pages/Reports.vue` | ✅ present | Notifications tab with status count cards and approve/cancel action table |
| `frontend/src/components/LavModal.vue` | ✅ present | Shared modal component (used by TicketDetail template selection) |
| `frontend/src/components/LavConfirm.vue` | ✅ present | Shared confirm dialog (used by Reports notification actions) |
| `frontend/src/utils/confirm.js` | ✅ present | `useConfirm()` composable |
| `frontend/src/utils/theme.js` | ✅ present | Color tokens used by notification chips |

### Documentation

| File | Status |
|---|---|
| `doc/p2_notification_templates_report.md` | ✅ present |
| `doc/p2_notification_template_catalog.md` | ✅ present |
| `doc/p2_notification_defects_found.md` | ✅ present |
| `doc/p2_notification_closure_audit.md` | ✅ present |
| `doc/p2_notification_uat_report.md` | ✅ present |
| `doc/p2_notification_state_audit.md` | ✅ this file |

### Screenshots

| File | Status |
|---|---|
| `doc/screenshots/p2_notifications/ticket_detail_communication_preview.png` | ✅ captured |
| `doc/screenshots/p2_notifications/template_selection_modal.png` | ✅ captured |
| `doc/screenshots/p2_notifications/rendered_whatsapp_preview.png` | ✅ captured |
| `doc/screenshots/p2_notifications/rendered_sms_preview.png` | ✅ captured |
| `doc/screenshots/p2_notifications/queue_list.png` | ✅ captured |
| `doc/screenshots/p2_notifications/approval_modal.png` | ✅ captured |
| `doc/screenshots/p2_notifications/notifications_report.png` | ✅ captured |
| `doc/screenshots/p2_notifications/dark_mode_notification_screen.png` | ✅ captured |

---

## 2. Missing Files

- `doc/screenshots/p2_notifications/01-ticket-detail-communication-preview.png` — naming mismatch (exists as `ticket_detail_communication_preview.png`)
- `doc/screenshots/p2_notifications/02-template-selection-modal.png` — naming mismatch (exists as `template_selection_modal.png`)
- `doc/screenshots/p2_notifications/03-whatsapp-preview.png` — naming mismatch (exists as `rendered_whatsapp_preview.png`)
- `doc/screenshots/p2_notifications/04-sms-preview.png` — naming mismatch (exists as `rendered_sms_preview.png`)
- `doc/screenshots/p2_notifications/05-notification-queue-list.png` — naming mismatch (exists as `queue_list.png`)
- `doc/screenshots/p2_notifications/06-approval-modal.png` — naming mismatch (exists as `approval_modal.png`)
- `doc/screenshots/p2_notifications/07-reports-notifications-tab.png` — naming mismatch (exists as `notifications_report.png`)
- `doc/screenshots/p2_notifications/08-dark-mode-notifications.png` — naming mismatch (exists as `dark_mode_notification_screen.png`)

No implementation files are missing.

---

## 3. Existing DocTypes

- `Lavanya Notification Template`
- `Lavanya Notification Queue`

Verified after `bench migrate`.

---

## 4. Existing APIs

All required APIs are implemented:

- `get_notification_templates`
- `get_notification_queue`
- `preview_notification`
- `queue_notification`
- `approve_notification`
- `cancel_notification`
- `mark_notification_skipped`

---

## 5. Existing Frontend UI

- Ticket Detail: Communication Preview section ✅
- Reports: Notifications tab with counts + action table ✅
- Template selection modal using `LavModal` ✅
- Approval/cancel using `LavConfirm`/`useConfirm` ✅
- Dark mode styling applied ✅

---

## 6. Existing Tests

- `lavanya_service/tests/p2_notification_tests.py` — 10 checks
- Result after clean DB state: **10 pass, 0 fail**

---

## 7. Safety Verification

| Check | Result |
|---|---|
| `LIVE_NOTIFICATIONS_ENABLED` guard | ✅ `provider.py` returns `False` by default; `DryRunProvider.send()` raises |
| No live WhatsApp/SMS send in queue path | ✅ `queue_notification` only inserts dry-run queue docs |
| No provider credentials in source | ✅ Grep for `TWILIO\|WHATSAPP_TOKEN\|SMS_KEY\|API_SECRET\|ACCESS_TOKEN\|provider_secret` returned no matches |
| No ERP/accounting references | ✅ Grep for `Journal Entry\|Payment Entry\|Sales Invoice\|Purchase Invoice\|GL Entry\|ERPNext\|General Ledger` returned no matches |
| No native `window.confirm()` | ✅ Grep returned no matches in `Reports.vue` / `TicketDetail.vue` |
| All queued records `dry_run = 1` | ✅ Verified in test output |
| Missing phone creates `Skipped` record | ✅ Verified |
| Missing variable fails preview safely | ✅ Verified |

---

## 8. Gaps / Issues Found and Fixed

### GAP-1: Screenshot naming does not match required scheme — FIXED
- Renamed all 8 screenshots to `01-ticket-detail-communication-preview.png` … `08-dark-mode-notifications.png`.

### GAP-2: Focused test runner is fragile to stale DB state — FIXED
- Added `_purge_stale()` to `p2_notification_tests.py` which runs at the start of `run()`.
- It deletes leftover `P2 Test Template%` templates, `P2.2 Notification Test` tickets, matching queue rows, and the stale agent user.
- Result: `bench execute lavanya_service.tests.p2_notification_tests.run` now returns **10 pass, 0 fail** reliably.

### GAP-3: Stale test templates in DB — ADDRESSED BY GAP-2
- `_purge_stale()` removes leftover test templates; after running the fixed test suite the active template count returns to 15 seeded templates.

### GAP-4: Dead code in `api/notifications.py` — FIXED
- Removed unused `assert_no_live_send(queue_doc)` function.

### GAP-5: No Malayalam/Mixed seeded templates — ACCEPTED DEFERRED SCOPE
- DocType supports `Malayalam` and `Mixed`; only English templates are seeded.
- No customer requirement or acceptance criterion mandates Malayalam/Mixed seed data for P2.2 closure.

---

## 9. Final Test Results

```text
bench --site lavanya-dev.localhost migrate                                               -> PASS
bench --site lavanya-dev.localhost execute lavanya_service.tests.p2_notification_tests.run -> 10 pass, 0 fail
bench --site lavanya-dev.localhost execute lavanya_service.tests.p2_tests.run             -> 18 pass, 0 fail
cd frontend && npm install && node node_modules/vite/bin/vite.js build                   -> PASS
```

---

## 10. Recommendation

P2.2 is complete. Proceed to update closure docs, SPA status, changelog, and commit notification-related files separately from P2.1.
