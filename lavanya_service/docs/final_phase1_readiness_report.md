# Lavanya eMart Helpdesk — Final Phase 1 Readiness Report

Date: 2026-06-11
Dev site: `lavanya-dev.localhost` | Reinstall test site: `lavanya-reinstall-test.localhost`
Stack: frappe 15.110.0 (version-15), helpdesk 1.25.1, lavanya_service 0.0.1
App HEAD at time of report: `fc5fc12`

---

## Technical Checklist

| Item                                              | Status |
| ------------------------------------------------- | ------ |
| Custom app `lavanya_service`, all changes in git   | DONE   |
| 7 ticket types, 10 statuses, 4 priorities          | DONE   |
| 38 HD Ticket custom fields                         | DONE   |
| Service Product Receipt + Custody Log Entry        | DONE   |
| Lavanya Default SLA (priority-driven, Mon-Sat 09:30-20:30) | DONE |
| Server-side validation guards (see acceptance)     | DONE   |
| 12 saved staff queues (HD View fixtures)           | DONE   |
| Reminder scanner + HD Notification + daily scheduler | DONE |
| 5 Lavanya roles + 56-row Custom DocPerm fixture    | DONE   |
| HD Ticket / All permission restricted (read+print) | DONE, self-healing via after_install/after_migrate |
| Token slip Print Format + fixture                  | DONE   |
| `required_apps = ["helpdesk"]`                     | DONE   |
| Operational docs pack (7 files in docs/)           | DONE   |
| Rerunnable acceptance suite (`tests/acceptance_phase1.py`) | DONE |

## Acceptance Test Result

`bench --site <site> execute lavanya_service.tests.acceptance_phase1.run`

- Dev site: **18/18 PASS** (transaction rolled back, no records persisted)
- Fresh reinstall site: **18/18 PASS**

Covered: insert-status reset (TC-000), Brand Registered guard (TC-001),
open-ticket follow-up guard (TC-011), closure-evidence guard (TC-010), serial
guard (TC-007), phone normalization + 10-digit validation (TC-PH1..3),
receipt LV-SR naming + custody log + status/log consistency (TC-004b..e).

Explicitly N/A by design in v1.1:
- TC-005 repeat-complaint auto-detection: fields exist
  (`is_repeated_complaint`, `previous_ticket_link`) but automation is
  deferred; staff set the flag manually.
- TC-003 field-level permissions: verified by the Phase 1L-7 smoke test
  procedure, to be re-run after real role assignments.

## Fresh-Site Reinstall Result

**PASS after two real defects were found and fixed by this gate:**

1. SLA fixture failure: importing stock `Default` (default_sla=0) before
   `Lavanya Default` exists raised "You must set one SLA as Default".
   Fix: fixture now exports only `Lavanya Default`;
   `setup/sla_fixes.ensure_helpdesk_sla_defaults` (after_install +
   after_migrate) idempotently disables the stock Default. (`1c2abfe`)
2. Duplicate broad `All` permission: helpdesk's install creates a broad
   Custom DocPerm All row; the fixture added the restricted one → fresh
   installs had BOTH (write/create open to all). Fix:
   `restrict_hd_ticket_all_permission` now keeps one row, forces the
   restricted target, deletes duplicates. (`fc5fc12`)

Final fresh-site state verified: all DocTypes, 38 custom fields, statuses,
types, priorities, 10 brands, SLA default/enabled correct, exactly one
restricted All row, 55 Lavanya DocPerm rows, print format present.

## Known Blockers / Open Items

| # | Item | Severity |
| - | ---- | -------- |
| 1 | Native role mapping decision needs business sign-off (see docs/role_mapping_decision.md; recommendation: Agent + one Lavanya role per staff user) | Blocker for user onboarding |
| 2 | Real staff UAT not performed (portal flows, restricted fields in agent UI, reminder visibility) | Blocker for go-live |
| 3 | Production infrastructure absent: prod bench, domain, SSL, backups + restore test, scheduler enabled, admin hardening | Blocker for go-live |
| 4 | Reports/dashboard phase not built (mitigated by 12 saved views + daily reminders + helpdesk native dashboard) | Non-blocking for pilot |
| 5 | Repeat-complaint auto-detection deferred (manual flag) | Non-blocking, Phase 2 |
| 6 | Email account / outbound notifications not configured | Non-blocking for pilot |

## Pilot Recommendation

**Conditional GO for a limited internal pilot** on the development bench,
restricted to ticket type `Customer Complaint - Site`, after:

1. Business signs off the role mapping (open item 1), AND
2. Test users are created per the mapping and the Phase 1L-7 permission
   smoke test is re-run with real assignments, AND
3. One week of staff UAT using docs/staff_quick_guide.md.

**NO-GO for production go-live** until open items 2 and 3 are closed.
Full rollout of all 7 ticket types on day one is NOT recommended under any
circumstance; expand type-by-type after the pilot stabilises.
