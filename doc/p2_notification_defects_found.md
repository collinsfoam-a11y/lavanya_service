# P2.2 Notification Defects Found

## Fixed During Implementation
- `P2N-DEFECT-001`: Notification API and provider modules were missing.
  - Fix: added `lavanya_service.api.notifications` and `lavanya_service.notifications.provider`.

- `P2N-DEFECT-002`: Notification DocTypes did not exist.
  - Fix: added setup module and install/migrate hooks for template and queue DocTypes.

- `P2N-DEFECT-003`: Missing-variable rendering needed safe failure semantics.
  - Fix: preview returns `ok: false`, `missing_variables`, and an error string instead of rendering unsafe text.

- `P2N-DEFECT-004`: Missing customer phone needed auditability.
  - Fix: queueing creates `Skipped` records with `Missing or invalid customer phone.` instead of dropping silently.

- `P2N-DEFECT-005`: Frontend confirmation needed to avoid native `confirm()`.
  - Fix: Ticket Detail and Reports notification actions use `LavConfirm`/`useConfirm`.

- `P2N-DEFECT-006`: Ticket Detail modal placement was inside the drawer transition and did not mount reliably.
  - Fix: moved modal components outside the transition wrapper.

## Closure Audit Findings (2026-06-20)

- `P2N-DEFECT-007`: Focused P2.2 test runner showed intermittent DB-integrity failures after audit script altered DB state.
  - Impact: 5-6 out of 10 P2.2 tests fail when the shared test DB has stale templates from prior runs.
  - Root cause: test `_new_template()` uses random hash suffix but `autoname="field:template_name"` depends on the template_name field being unique; combined with sequential test cleanup not always cleaning partial inserts, collisions occur.
  - The independent audit script (`audit_p2_notifications.py`) exercising the identical APIs passed with 0 failures, confirming no production defect.
  - Recommendation: convert test runner to Frappe-standard `unittest.TestCase` classes with proper `setUp/tearDown` per-test isolation.

- `P2N-DEFECT-008`: P2.1 penalty test runner also affected by shared DB state from audit runs.
  - Impact: `test_no_penalty_before_grace` and `test_fixed_after_grace` sometimes fail with DB integrity errors.
  - Root cause: same shared-DB sequential test issue as P2N-DEFECT-007.
  - Confirmed: standard Frappe test suite (`bench run-tests --app lavanya_service`) passes clean with `Ran 11 tests ... OK`.

## Fixed During Audit / Closure (2026-06-20)
- `P2N-DEFECT-009`: Screenshot file names did not match the required `01-` … `08-` scheme.
  - Fix: renamed the 8 files in `doc/screenshots/p2_notifications/` to the required names.

- `P2N-DEFECT-010`: P2.2 focused runner failed when stale test templates/tickets/agent user remained from prior interrupted runs.
  - Fix: added `_purge_stale()` in `lavanya_service.tests.p2_notification_tests` to clean leftovers before the test suite runs.

- `P2N-DEFECT-011`: Test agent user creation triggered a welcome email, which failed on the dev site because SMTP is not configured.
  - Fix: set `send_welcome_email: 0` when creating `p2-agent@example.test`.

- `P2N-DEFECT-012`: Dead helper `assert_no_live_send()` in `api/notifications.py` was defined but unused.
  - Fix: removed the dead function.

## Remaining Risks
- Live provider integration is intentionally absent; a later phase must add provider-specific credentials, retries, delivery receipts, opt-out controls, and rate limits.
- Default Malayalam/Mixed content is not authored yet; language options exist for later template creation.
- Existing direct WhatsApp link behavior in Ticket Detail predates P2.2 and remains manual staff-initiated behavior; P2.2 queue infrastructure itself performs no live sends.
- Focused test runners are not standard Frappe unittest classes; they should be converted before relying on them as CI gates.
