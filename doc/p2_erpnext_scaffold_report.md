# P2.4 ERPNext Readiness + Safe Integration Scaffold Report

## Date
2026-06-20

## Scope
Created a safe ERPNext integration scaffold for Lavanya Service without installing ERPNext, without importing ERPNext doctypes directly, and without posting any accounting or stock documents.

## Implementation

### 1. ERP Integration Settings DocType
Created `Lavanya ERP Integration Settings` with the following fields:

| Field | Type | Default | Purpose |
|---|---|---|---|
| `erpnext_enabled` | Check | 0 | Master enable/disable |
| `erpnext_installed_detected` | Check | 0 (read-only) | Auto-detected status |
| `mode` | Select | Disabled | Disabled / Read Only / Draft Only / Posting Locked |
| `default_company` | Data | None | ERPNext Company for posting |
| `customer_lookup_enabled` | Check | 0 | Enable customer lookups |
| `supplier_lookup_enabled` | Check | 0 | Enable supplier lookups |
| `item_lookup_enabled` | Check | 0 | Enable item lookups |
| `invoice_lookup_enabled` | Check | 0 | Enable invoice lookups |
| `serial_lookup_enabled` | Check | 0 | Enable serial number lookups |
| `allow_draft_creation` | Check | 0 | Allow draft document creation |
| `allow_accounting_posting` | Check | 0 | Allow GL / posting operations |
| `last_health_check_at` | Datetime | Auto | Last detection timestamp |
| `last_health_check_status` | Data | Auto | Detection result text |

Seeded with defaults: all disabled, mode=Disabled.

### 2. ERPNext Detector
Module: `lavanya_service/integrations/erpnext/detector.py`

Functions:
- `is_erpnext_installed()` — checks Frappe app registry, returns boolean
- `get_erpnext_status()` — returns structured status with mode, available, enabled, details
- `assert_erpnext_available()` — raises if absent or disabled

Key safety: no ERPNext module imports. Uses only `frappe.get_installed_apps()`.

### 3. Adapter Interface
Module: `lavanya_service/integrations/erpnext/adapter.py`

`ERPNextAdapter` class with static methods:
- `is_available()` — availability check
- `lookup_customer(mobile, name)` — read-only customer lookup
- `lookup_supplier(supplier_name, gstin)` — read-only supplier lookup
- `lookup_item(item_code, barcode, serial_no)` — read-only item lookup
- `lookup_sales_invoice(invoice_no, customer)` — read-only invoice lookup
- `lookup_serial_no(serial_no)` — read-only serial lookup

All methods:
- Return structured `{ok, available, message, data}` response
- Fail safely when ERPNext absent or disabled
- Check per-lookup enablement flags before querying

### 4. Mapping Preview API
Module: `lavanya_service/api/erp_preview.py`

Endpoints:
- `get_erp_status()` — returns status, mode, and detail flags
- `preview_ticket_erp_mapping(ticket)` — preview what ERPNext documents would be relevant
- `preview_supplier_penalty_erp_mapping(penalty_name)` — preview Debit Note mapping
- `preview_stock_complaint_erp_mapping(complaint_name)` — preview Purchase Return mapping

All endpoints: role-gated to Manager/Coordinator roles. Return safe preview only — no creation.

### 5. Hook Wiring
Added `lavanya_service.setup.erpnext_settings.create_erp_settings` to both `after_install` and `after_migrate` hooks.

### 6. Tests
Module: `lavanya_service/tests/p2_erp_scaffold_tests.py`
- 14 tests covering detection, defaults, adapter, preview, and no-post verification
- All 14 pass with ERPNext absent

## Verification

| Check | Result |
|---|---|
| ERPNext installed | NOT installed (expected) |
| Settings DocType created | Yes |
| Default settings disable all | Yes (all 0) |
| Detector returns safe status | Yes |
| Adapter returns unavailable | Yes |
| Mapping preview read-only | Yes |
| No ERP doctype creation | Yes (6/6 confirmed absent) |
| Frontend build | Passed |
| P2.4 tests | 14 pass, 0 fail |

## File Inventory

```
lavanya_service/setup/erpnext_settings.py
lavanya_service/integrations/__init__.py
lavanya_service/integrations/erpnext/__init__.py
lavanya_service/integrations/erpnext/detector.py
lavanya_service/integrations/erpnext/adapter.py
lavanya_service/api/erp_preview.py
lavanya_service/tests/p2_erp_scaffold_tests.py
lavanya_service/hooks.py (updated)
```
