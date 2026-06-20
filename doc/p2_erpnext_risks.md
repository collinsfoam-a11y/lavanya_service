# P2.3 ERPNext Integration Risks

## Date
2026-06-20

## Risk Classification

| Severity | Definition |
|---|---|
| Critical | Data corruption, financial loss, regulatory non-compliance |
| High | Incorrect ledger entries, reconciliation failure |
| Medium | Data inconsistency, manual workaround needed |
| Low | Minor inconvenience, cosmetic issue |

---

## Risk 1: Premature Posting Without Configuration Validation

**Severity**: Critical
**Scenario**: Integration code posts GL entries before Company, Chart of Accounts, Fiscal Year, or Warehouses are configured.
**Impact**: Corrupted ledger, unresolvable entries, audit failure.
**Mitigation**:
- Pre-flight check: validate ERPNext configuration before any posting endpoint is enabled.
- Feature flag: `ERP_INTEGRATION_ENABLED = False` until all prerequisites are met.
- Dry-run mode mandatory for initial testing.
- All post-attempts are gated behind `bench --site site validate-erp-config`.
**Status**: Not started. No posting code exists.

---

## Risk 2: Idempotency Failure — Duplicate Debit/Credit Notes

**Severity**: Critical
**Scenario**: Same penalty computation or credit note triggers duplicate ERPNext document creation.
**Impact**: Double-counted revenue/expense, overstated supplier liability.
**Mitigation**:
- Uniqueness constraint: `reference_doctype + reference_name` per ERPNext document.
- Before creating, check `frappe.db.exists("Purchase Invoice", {"lavanya_reference_doctype": dt, "lavanya_reference_name": nm})`.
- Custom field `lavanya_reference_doctype` and `lavanya_reference_name` on ERPNext documents.
**Status**: Not implemented. Field adds needed as prerequisites.

---

## Risk 3: Partial Posting — Some Entries Fail Mid-Batch

**Severity**: High
**Scenario**: Batch posting process creates some documents but fails on others, leaving inconsistent state.
**Impact**: GL imbalance, manual reconciliation required.
**Mitigation**:
- Use `frappe.db.transaction()` atomic block for multi-document operations.
- Never auto-post; always require manager review step.
- Post one document at a time with success/failure logging.
**Status**: Architectural requirement. No code yet.

---

## Risk 4: Data Model Drift — Lavanya vs ERPNext Mismatch

**Severity**: High
**Scenario**: Lavanya Service brand names, product codes, or customer identifiers do not match ERPNext equivalents after sync.
**Impact**: Lookup failures, incorrect posting, manual reconciliation.
**Mitigation**:
- Maintain `lavanya_mapping` custom table linking Lavanya DocType names to ERPNext names.
- Sync failures are logged and surfaced in dashboard, not silently dropped.
- Manual override UI for correcting mismatches before posting.
**Status**: Mapping table design required before implementation.

---

## Risk 5: Authorization Escalation — Unauthorized Posting

**Severity**: High
**Scenario**: User without accounting permissions submits ERPNext documents through Lavanya Service UI.
**Impact**: Unauthorized financial transactions.
**Mitigation**:
- Posting endpoints check `frappe.has_permission("Purchase Invoice", "create")` and `"submit"`.
- Separate permission role: `Lavanya ERP Integration` (granted only to finance/manager roles).
- All posting events are audited with user, timestamp, document reference.
**Status**: Permissions not configured.

---

## Risk 6: Reconciliation Gap — Posted but Not Tracked

**Severity**: Medium
**Scenario**: ERPNext document is posted, but Lavanya Service record is not updated to reflect the new status.
**Impact**: Duplicate postings, status inconsistency.
**Mitigation**:
- After successful submit, update Lavanya record status atomically in same transaction.
- Example: Penalty Computation status → `Applied` after Debit Note submit.
- Idempotency check prevents re-post of already-applied records.
**Status**: Field `Applied` exists in computation status options.

---

## Risk 7: ERPNext Version Compatibility

**Severity**: Medium
**Scenario**: ERPNext v14, v15, or future v16 APIs change, breaking integration.
**Impact**: Integration stops working after ERPNext upgrade.
**Mitigation**:
- Pin ERPNext version requirement: `>=15.0.0, <16.0.0`.
- Abstract ERPNext API calls behind adapter interface (`LavanyaERPAdapter`).
- Integration tests in CI with target ERPNext version.
**Status**: Adapter pattern not yet implemented.

---

## Risk 8: Supplier Payment Block Double-Hold

**Severity**: Medium
**Scenario**: Both ERPNext `Payment Request` hold and Lavanya `Supplier Payment Block` exist simultaneously.
**Impact**: Confusion about which system governs payment release.
**Mitigation**:
- Designate ERPNext as the authoritative payment control system once integration is active.
- Lavanya Payment Block becomes a read-only mirror of ERPNext payment status.
- Transition plan: migrate existing blocks to ERPNext before cutting over.
**Status**: Single-source-of-truth decision pending.

---

## Risk 9: Performance — Bulk Lookup Timeout

**Severity**: Low
**Scenario**: SPA requests ERPNext lookups for every ticket in a list view, causing timeouts.
**Impact**: Slow page loads.
**Mitigation**:
- Cache ERPNext lookups (customer names, item details) in Lavanya Service custom fields.
- Refresh cache on-demand or via daily scheduler, not per-request.
- Batch API: `get_erp_customer_details([list of names])` returns all in one call.
**Status**: Architectural guideline. No implementation.

---

## Risk Summary Matrix

| # | Risk | Severity | Status |
|---|---|---|---|
| R1 | Premature posting without config | Critical | Not started |
| R2 | Idempotency failure — duplicates | Critical | Not started |
| R3 | Partial posting — inconsistent state | High | Not started |
| R4 | Data model drift — mismatch | High | Not started |
| R5 | Authorization escalation | High | Not started |
| R6 | Reconciliation gap | Medium | Not started |
| R7 | ERPNext version compatibility | Medium | Not started |
| R8 | Supplier payment block double-hold | Medium | Not started |
| R9 | Performance — bulk lookup | Low | Not started |

---

## Acceptance Gate

No ERPNext integration code should be merged until:
1. ERPNext is installed and configured.
2. All Critical and High risks have documented mitigations implemented.
3. Sandbox site passes dry-run posting tests.
4. Audit log is operational.
5. Rollback path exists (delete draft documents).
6. Manager approval workflow is gating all submissions.
