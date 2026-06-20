# P2.4 ERPNext Scaffold Defects Found

## Date
2026-06-20

## Fixed During Implementation

- `P2E-DEFECT-001`: `_get_settings()` used `frappe.db.get_single_value()` on a non-Single DocType.
  - Impact: crashed when trying to read settings after initial seed.
  - Fix: changed to `frappe.db.get_value(SETTINGS_DOCTYPE, {}, "name", order_by="creation desc")`.
  - Verification: `debug_erp_settings.py` confirmed correct retrieval.

- `P2E-DEFECT-002`: `seed_default_erp_settings()` had circular import risk.
  - Impact: calling `is_erpnext_installed()` during seed could fail if imports were not yet resolved.
  - Fix: import is deferred inside the function body (module `from ... import` at the top of the seed function).
  - Verification: migrate ran successfully on a fresh configuration.

## Remaining Risks

- **R-E1**: If ERPNext is installed later, the default settings seed will create a `Default` record only once. Manual settings update is required to enable any feature.
  - Mitigation: Admin must set `erpnext_enabled=1` and choose a mode.
  - Status: Accepted — this is intentional behavior.

- **R-E2**: The adapter's `_check_availability()` currently returns None from settings validation because it requires ERPNext installed AND enabled. When ERPNext is installed but settings are not updated, features remain unavailable.
  - Mitigation: Health check API surfaces this state clearly.
  - Status: Accepted.

- **R-E3**: No UI is yet implemented for managing ERP integration settings. Settings must be changed via Frappe Desk UI or direct DB.
  - Mitigation: Settings DocType is registered and visible in Desk UI.
  - Status: Accepted for P2.4 scope.

- **R-E4**: P2.4 test runner is a custom runner, not a standard Frappe unittest.TestCase class. Conversion deferred.
  - Mitigation: Existing tests pass. Standard Frappe test suite also passes.
  - Status: Low risk.

## Post-Commit Review (2026-06-20)

- Commit `35c387c` was reviewed after it was created by a parallel agent.
- Independent verification run: `lavanya_service.tests.p2_erp_scaffold_tests.run` → **14 pass, 0 fail**.
- Static re-check confirmed:
  - No `import erpnext` or `from erpnext` statements.
  - No creation of Sales Invoice, Purchase Invoice, Payment Entry, Journal Entry, Stock Entry, or GL Entry.
  - `Lavanya ERP Integration Settings` defaults to `erpnext_enabled=0`, `mode=Disabled`, `allow_accounting_posting=0`, `allow_draft_creation=0`.
  - Preview APIs (`preview_ticket_erp_mapping`, `preview_supplier_penalty_erp_mapping`, `preview_stock_complaint_erp_mapping`) are read-only and return empty `would_create` lists when ERPNext is absent or disabled.
- No write-side ERP behavior found.
- Changelog gap identified and fixed separately.

## Static Verification

No ERPNext module imports found in Lavanya Service codebase. All code paths use only Frappe framework APIs (`frappe.get_all`, `frappe.db.exists`, `frappe.get_installed_apps`). No accounting/stock/sales/purchase document creation code exists.
