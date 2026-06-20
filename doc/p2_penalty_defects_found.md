# P2.1 Penalty Defects Found

## Fixed
- `P2-DEFECT-001`: Frappe autoname used literal old dot-series text under `format:`.
  - Impact: duplicate primary-key errors such as `PEN-COMP-.YYYY.-.#####`.
  - Fix: changed rule naming to `format:PEN-RULE-{#####}` and computation naming to `format:PEN-COMP-{YYYY}-{#####}`; updated live DocType metadata.

- `P2-DEFECT-002`: Within-grace computation created zero-amount records.
  - Impact: reports showed advisory rows before penalty eligibility.
  - Fix: `compute_penalty_for_ticket` now returns `None` when `chargeable_days <= 0`.

- `P2-DEFECT-003`: No-rule manager-review path missed `max_penalty_amount`.
  - Impact: no-rule computation raised a missing-key exception.
  - Fix: added `max_penalty_amount: 0` and stores no-rule rows as `Manager Review`.

- `P2-DEFECT-004`: Reports penalty actions used native `confirm()`.
  - Impact: violated UI confirmation standard.
  - Fix: replaced with `useConfirm()`/`LavConfirm` and added Reject action.

- `P2-DEFECT-005`: Approval, waiver, and rejection APIs accepted blank narration/reason.
  - Impact: weak audit trail.
  - Fix: backend now requires approval narration, waiver reason, and rejection reason.

- `P2-DEFECT-006`: P2.1 backend tests did not cover summary/list/detail API smoke, blank narration/reason, or rejection success.
  - Impact: API audit requirements could regress while the original 10-test suite still passed.
  - Fix: extended `lavanya_service.tests.p2_tests.run` to 18 checks, covering summary/list/detail APIs, approval narration, waiver reason and zeroing, rejection reason, and rejected status.

- `P2-DEFECT-007`: Piped/truncated bench output can abort the custom runner before cleanup.
  - Impact: leaked temporary `Supplier Penalty Rule` / `Supplier Penalty Computation` rows can make `mgr_review_no_rule` fail.
  - Fix: purge leaked rows during verification and run the suite to a full output file instead of piping directly to `tail`/`grep`.

## Open / Pending Verification
- (none — P2.1 closed)

## Remaining Risks
- Penalty rules are data-driven; incorrect generic active rules can affect many tickets.
- P2.1 is advisory only; downstream accounting application must be designed separately if required later.
- Existing custom test runner is not a standard Frappe unittest class; keep it until converted in a later test-hardening pass.
- Wider Frappe regression modules remain blocked by dev-site email configuration (`Automatic Linking can be activated only if Incoming is enabled`, `Invalid Outgoing Mail Server or Port`). These are environment/email-configuration issues and are not P2.1 computation failures; P2.1 is closed with this known non-P2.1 limitation documented.
