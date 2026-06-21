# P2.4 ERPNext Scaffold Safety Report

## Date
2026-06-20

## Safety Design Principles

1. **Zero Dependency**: No `erpnext` module is imported anywhere. All ERPNext interaction goes through Frappe's standard `frappe.get_all()` which is identical whether ERPNext is installed or not.

2. **Defensive Defaults**: All settings default to disabled (0). Three layers of gates:
   - ERPNext must be installed (`is_erpnext_installed()`)
   - `erpnext_enabled` must be 1
   - Per-feature flags must be 1 (customer_lookup_enabled, etc.)

3. **No Write Path**: No code path creates, submits, or modifies any ERPNext document. The adapter only uses `frappe.get_all()` — read-only.

4. **Safe Absence**: Every function handles ERPNext absence gracefully. No crash, no partial state.

## Safety Gates

### Gate 1: Installation Detection
```python
def is_erpnext_installed():
    return "erpnext" in frappe.get_installed_apps()
```

### Gate 2: Master Enable
Settings `erpnext_enabled` must be 1. Default: 0.

### Gate 3: Mode Lock
Settings `mode` controls what is allowed:
- `Disabled` — nothing
- `Read Only` — lookups only
- `Draft Only` — draft creation allowed (not implemented yet)
- `Posting Locked` — posting blocked even if other flags on

### Gate 4: Per-Feature Flags
Individual flags control specific lookups/exports:
- `customer_lookup_enabled`
- `supplier_lookup_enabled`
- `item_lookup_enabled`
- `invoice_lookup_enabled`
- `serial_lookup_enabled`
- `allow_draft_creation`
- `allow_accounting_posting`

### Gate 5: Role Authorization
All preview/status API endpoints require System Manager, Lavanya Manager, or Lavanya Service Coordinator role.

## What Is NOT Possible (by Design)

- ❌ Creating Sales Invoice
- ❌ Creating Purchase Invoice
- ❌ Creating Payment Entry
- ❌ Creating Journal Entry
- ❌ Creating Stock Entry
- ❌ Creating GL Entry
- ❌ Submitting any document
- ❌ Modifying Supplier/Customer ledgers
- ❌ Importing `erpnext` modules

## What IS Possible (Safe Operations)

- ✅ Detecting whether ERPNext is installed
- ✅ Reading ERPNext settings
- ✅ Looking up customers/suppliers/items (when ERPNext is installed AND enabled)
- ✅ Previewing what ERPNext documents *would* be created
- ✅ Safe structured response for all operations

## Static Code Analysis

No references found in Lavanya Service codebase for:
- `Purchase Invoice`, `Sales Invoice`, `Payment Entry`
- `Journal Entry`, `Stock Entry`, `GL Entry`
- `erpnext` module imports
- `make_gl_entries`, `make_purchase_invoice`, `make_sales_invoice`

## Test Coverage

| Test | Verifies |
|---|---|
| `test_erpnext_absent_does_not_crash` | No crash when ERPNext missing |
| `test_default_settings_disable_erp` | Settings default to disabled |
| `test_accounting_posting_locked_by_default` | Posting flag is 0 |
| `test_adapter_returns_unavailable` | Adapter safe when absent |
| `test_ticket_mapping_preview_*` | Preview safe when absent |
| `test_supplier_penalty_mapping_preview_*` | Penalty preview read-only |
| `test_stock_complaint_mapping_preview_*` | Stock preview read-only |
| `test_no_erp_write_doctypes_*` | No ERP Doctypes created (6 checks) |
| `test_no_gl_or_payment_or_invoice_creation` | All lookups return unavailable |
