# Lavanya Service — Expansion Plan

## Part A: Corrected Design Baseline

### A.1 ERD Corrections

The current app already has these values; the design doc must match reality:

| Entity | Design Doc Says | Actual Code | Correction |
|--------|---------------|-------------|------------|
| HD Ticket `escalation_level` | "None, Level-1, Level-2, Level-3" (4 values) | `None, L1 - Agent Follow-up, L2 - Coordinator Escalation, L3 - Manager Escalation, L4 - Owner / Brand Manager Escalation` (5 values) | Use actual 5-level ladder |
| HD Ticket `ticket_type` | "Service, Exchange, Demo, Return, Stock, Store Service, General" (7 types) | `Customer Complaint - Site, Customer Product at Store, Stock Complaint, Installation / Demo, Replacement / DOA, Out of Warranty Local Service, Free Service` (7 types, different) | Keep existing 7; proposed flows use `service_flow_type` not `ticket_type` |
| HD Ticket `closure_type` | "Resolved, Closed-No-Response, Parts Not Available, Customer Withdrew" | `Resolved by Brand Service, Resolved by Local Technician, Replacement Completed, Customer Collected Product, Customer Cancelled, Duplicate Ticket, Not Purchased From Lavanya - Guided Only, Brand Denied Warranty, Customer Not Responding, Closed After Manager Approval, Other` (11 options) | Use actual options |
| HD Ticket `product_type` | "LED TV" in ERD example | Select: `AC, Refrigerator, Washing Machine, Mixer, Induction Cooker, Chimney, Hob, Gas Stove, TV, Water Purifier, Other` | Correct example to `TV` |
| HD Ticket `status` | "10 statuses: New→In Progress→Resolved→Closed" | Correct (these are Helpdesk native) | No change |
| HD Ticket `service_flow_type` | "11 flows" | `Customer Complaint - Site, Customer Product at Store, Installation / Demo, Periodic / Free Service, Stock Complaint, Out of Warranty Local Service, Extended Warranty Claim, Replacement / Exchange, Refund Case, Finance Sale Service Issue, Reopened / Repeat Complaint` (11 flows) | No correction needed, but design doc proposes 6 new values |
| HD Ticket `current_service_stage` | "33 stages" | 46 stages (grouped: Intake, Brand, Extended Warranty, Technician, Waiting, Product at Store, Installation, Periodic, Stock, Closure) | Correction: 46 stages, not 33 |

### A.2 Follow-up Stage Values (12, all defined)

| Value | Set By | Purpose |
|-------|--------|---------|
| `registration_done` | `register_brand_complaint` | Brand complaint registered |
| `technician_call_pending` | *(orphan — no action sets it)* | Technician call needed |
| `technician_called` | `verify_technician_called` | Technician contacted |
| `technician_visit_pending` | *(orphan — no action sets it)* | Technician visit pending |
| `technician_visited` | `verify_technician_visit` | Technician visited |
| `no_technician_update` | `mark_no_update` | No update → escalate |
| `sc_followup_done` | `record_sc_followup` | SC follow-up recorded |
| `customer_informed` | `inform_customer` | Customer informed |
| `part_pending` | `waiting_for_part` | Part/spare pending |
| `customer_confirmation_pending` | `record_satisfaction` (not Satisfied) | Awaiting customer |
| `customer_satisfied` | `record_satisfaction` (Satisfied) | Satisfied |
| `customer_not_satisfied` | `record_satisfaction` (Not Satisfied) | Not satisfied |

### A.3 Service Path Values (7, all defined)

`brand_warranty`, `brand_denied_local`, `out_of_warranty_local`, `customer_paid_local`, `lavanya_paid_goodwill`, `demo_installation`, `stock_supplier`

### A.4 Existing Service Flows (11 flows, 46 stages)

See `stage_rules.py:CURRENT_SERVICE_STAGES` for full list.

### A.5 Existing DocTypes (9)

Brand Service Master, Service Center Master, Local Technician Master, Free Service Rule, Service Product Receipt, Custody Log Entry (child), Lavanya Customer Profile, Lavanya Product Category, Lavanya Product Item

---

## Part B: Implementation Plan

Organized in 3 phases matching the design doc's P0/P1/P2 priorities, but restructured so each phase produces working, verifiable increments.

---

### Phase 1 — Foundation: Stage Rules + DocTypes (P0)

**Goal:** Add the 6 new service flows, 38 new stages, new next actions, and 3 core DocTypes so the system can route tickets through the new flows.

#### Step 1.1 — Extend stage_rules.py

**Files:** `lavanya_service/stage_rules.py`

**Changes:**
1. Add 6 new `SERVICE_FLOW_TYPES`:
   - `store_service`, `stock_supplier`, `demo_installation`, `replacement_approved_new`, `replacement_goodwill`, `return_service`
2. Add 38 new `CURRENT_SERVICE_STAGES` grouped by flow:
   - **store_service (8):** `product_received_at_store`, `brand_sc_notified`, `brand_sc_picked_up`, `brand_sc_diagnosis_pending`, `diagnosis_received`, `product_returned_to_store`, `customer_notified_for_collection`, `product_handed_over`
   - **replacement (8):** `replacement_approved_by_brand`, `old_unit_collected`, `new_unit_dispatched`, `new_unit_delivered`, `old_unit_returned_to_brand`, `brand_reimbursement_pending`, `reimbursement_received`, `replacement_record_completed`
   - **return_service (7):** `return_requested`, `product_received`, `return_reason_verified`, `brand_notified_for_return`, `brand_return_decision`, `customer_refund_processed`, `product_disposition`
   - **demo_installation (6):** `demo_installation_requested`, `technician_assigned`, `scheduled`, `demo_installation_in_progress`, `product_demonstrated`, `installation_completed`, `demo_customer_feedback_pending`
   - **stock_supplier (7):** `stock_issue_identified`, `supplier_notified`, `supplier_acknowledged`, `awaiting_supplier_response`, `replacement_received`, `defective_returned_to_supplier`, `credit_note_received`, `stock_updated`
3. Add new `NEXT_ACTIONS` (24 new): `Notify Brand SC for Pickup`, `Await Brand SC Diagnosis`, `Record Diagnosis Received`, `Notify Customer for Collection`, `Hand Over Product`, `Arrange Old Unit Collection`, `Dispatch New Unit`, `Confirm New Unit Delivery`, `Return Old Unit to Brand`, `Follow Up Brand Reimbursement`, `Record Reimbursement Received`, `Verify Return Reason`, `Notify Brand for Return`, `Await Brand Return Decision`, `Process Customer Refund`, `Update Product Disposition`, `Assign Technician for Demo`, `Confirm Scheduling`, `Monitor Demo Progress`, `Record Demo Feedback`, `Notify Supplier of Stock Issue`, `Await Supplier Response`, `Confirm Defective Returned`, `Update Stock Records`
4. Add new `STAGE_DEFAULT_ACTION` entries for all 38 new stages
5. Add new `STAGE_SLA_MINUTES` entries
6. Update `TICKET_TYPE_TO_FLOW` for new ticket types (or keep existing mapping, since proposed flows use `service_flow_type` not `ticket_type`)
7. Add `service_path` → `service_flow_type` derivation helper

**Verification:**
```bash
bench --site lavanya-dev.localhost console <<< "
import frappe
from lavanya_service.stage_rules import SERVICE_FLOW_TYPES, CURRENT_SERVICE_STAGES, NEXT_ACTIONS
assert 'store_service' in SERVICE_FLOW_TYPES, 'store_service flow missing'
assert 'replacement_approved_by_brand' in CURRENT_SERVICE_STAGES, 'replacement stage missing'
assert len(NEXT_ACTIONS) >= 75, f'expected 75+ next actions, got {len(NEXT_ACTIONS)}'
print('PASS: stage_rules.py extended')
"
```

#### Step 1.2 — Extend followup_fields.py (service_path)

**Files:** `lavanya_service/setup/followup_fields.py`

**Changes:**
1. Add 2 new `SERVICE_PATH_OPTIONS`: `store_service`, `replacement_brand`, `return_service`
2. Run migration: `bench --site lavanya-dev.localhost execute lavanya_service.setup.followup_fields.create_followup_fields`

**Verification:**
```bash
bench --site lavanya-dev.localhost console <<< "
import frappe
from lavanya_service.setup.followup_fields import SERVICE_PATH_OPTIONS
assert 'store_service' in SERVICE_PATH_OPTIONS, 'store_service path missing'
assert 'return_service' in SERVICE_PATH_OPTIONS, 'return_service path missing'
print('PASS: service_path extended')
"
```

#### Step 1.3 — Create Supplier SLA Definition DocType

**Files:** New `lavanya_service/setup/supplier_sla.py`

**Changes:**
1. Create DocType `Supplier SLA Definition` via `frappe.get_doc({"doctype":"DocType", ...})` pattern (same as `setup/masters.py`)
2. Fields: `brand` (Link to Brand Service Master), `service_center` (optional Link to Service Center Master), `response_sla_hours` (Int), `resolution_sla_hours` (Int), `payment_block_delay_days` (Int), `payment_terms` (Select: Net 30, Net 45, Net 60, Advance), `penalty_percent` (Float), `applicable_product_types` (Small Text), `enabled` (Check)
3. Register in `hooks.py` fixture list
4. Seed default records for 10 brands from design doc

**Verification:**
```bash
bench --site lavanya-dev.localhost execute lavanya_service.setup.supplier_sla.create_supplier_sla_doctype
bench --site lavanya-dev.localhost console <<< "
import frappe
assert frappe.db.exists('DocType', 'Supplier SLA Definition')
count = frappe.db.count('Supplier SLA Definition', {'enabled': 1})
assert count >= 10, f'expected 10+ enabled records, got {count}'
print(f'PASS: Supplier SLA Definition created with {count} records')
"
```

#### Step 1.4 — Create Supplier Payment Block DocType

**Files:** New `lavanya_service/setup/supplier_payment_block.py`

**Changes:**
1. Create DocType `Supplier Payment Block`
2. Fields: `brand` (Link to Brand Service Master), `service_center` (optional Link to Service Center Master), `block_status` (Select: Active, Released, Pending Review), `blocked_at` (Datetime), `released_at` (Datetime), `blocked_by` (Link to User), `block_reason` (Small Text), `release_reason` (Small Text), `overdue_ticket_count` (Int, computed), `max_delay_days` (Float, computed)
3. Register in `hooks.py` fixture list

**Verification:**
```bash
bench --site lavanya-dev.localhost execute lavanya_service.setup.supplier_payment_block.create_supplier_payment_block_doctype
bench --site lavanya-dev.localhost console <<< "
import frappe
assert frappe.db.exists('DocType', 'Supplier Payment Block')
print('PASS: Supplier Payment Block created')
"
```

#### Step 1.5 — Add service_flow_type → stages mapping + Stage Machine

**Files:** `lavanya_service/stage_rules.py`

**Changes:**
1. Add `FLOW_STAGES` dict mapping each flow to its ordered stage list
2. Add `advance_stage(ticket)` helper that moves to the next stage in the flow
3. Add `service_path_to_flow(path)` helper mapping paths to flows

**Verification:**
```bash
bench --site lavanya-dev.localhost execute lavanya_service.tests.test_corrected_design.run 2>&1
```

---

### Phase 2 — Workflow: Quick Actions + API + UI (P0)

**Goal:** Add the quick actions and API endpoints needed to drive the 6 new flows, and wire them into the stage machine.

#### Step 2.1 — New Quick Actions

**Files:** `lavanya_service/workflow/quick_actions.py`

**Changes (10 new actions):**
1. `notify_brand_sc_for_pickup(ticket_name, brand_sc=None, ...)` — sets stage `brand_sc_notified`
2. `record_diagnosis_received(ticket_name, diagnosis=None, ...)` — sets stage `diagnosis_received`
3. `notify_customer_for_collection(ticket_name, ...)` — sets stage `customer_notified_for_collection`
4. `hand_over_product(ticket_name, ...)` — sets stage `product_handed_over`
5. `collect_old_unit(ticket_name, serial_no=None, ...)` — sets stage `old_unit_collected`
6. `dispatch_new_unit(ticket_name, new_serial_no=None, ...)` — sets stage `new_unit_dispatched`
7. `return_old_unit_to_brand(ticket_name, ...)` — sets stage `old_unit_returned_to_brand`
8. `record_brand_reimbursement(ticket_name, amount=None, ...)` — sets stage `reimbursement_received`
9. `verify_return_reason(ticket_name, reason=None, ...)` — sets stage `return_reason_verified`
10. `notify_brand_for_return(ticket_name, ...)` — sets stage `brand_notified_for_return`

All actions follow existing pattern: `_require_roles`, `_load_ticket`, `_block_if_final`, set stage, `_set_last_followup`, `_save_ticket`, `_result`.

**Verification:**
```bash
bench --site lavanya-dev.localhost console <<< "
import frappe
from lavanya_service.workflow import quick_actions
for name in ['notify_brand_sc_for_pickup', 'record_diagnosis_received', 
             'notify_customer_for_collection', 'hand_over_product',
             'collect_old_unit', 'dispatch_new_unit', 'return_old_unit_to_brand',
             'record_brand_reimbursement', 'verify_return_reason', 'notify_brand_for_return']:
    assert hasattr(quick_actions, name), f'{name} missing'
print('PASS: 10 new quick actions defined')
"
```

#### Step 2.2 — API Wrappers

**Files:** `lavanya_service/api/workflow_actions.py`

**Changes:**
1. Add `@frappe.whitelist(methods=["POST"])` wrappers for each new quick action
2. Add to the existing form script API set

**Verification:**
```bash
bench --site lavanya-dev.localhost console <<< "
import frappe
from lavanya_service.api import workflow_actions
for name in ['notify_brand_sc_for_pickup', 'record_diagnosis_received',
             'notify_customer_for_collection', 'hand_over_product',
             'collect_old_unit', 'dispatch_new_unit', 'return_old_unit_to_brand',
             'record_brand_reimbursement', 'verify_return_reason', 'notify_brand_for_return']:
    assert hasattr(workflow_actions, name), f'API wrapper {name} missing'
print('PASS: API wrappers registered')
"
```

#### Step 2.3 — Scheduler: check_payment_block_triggers

**Files:** New `lavanya_service/tasks/payment_block.py`, `hooks.py`

**Changes:**
1. Implement `check_payment_block_triggers()` — scans active tickets by brand, compares delay to SLA definition's `payment_block_delay_days`, creates `Supplier Payment Block` in `Pending Review` if threshold exceeded
2. Register in `hooks.py:scheduler_events` daily at 06:00

**Verification:**
```bash
bench --site lavanya-dev.localhost execute lavanya_service.tasks.payment_block.check_payment_block_triggers 2>&1
bench --site lavanya-dev.localhost console <<< "
import frappe
# Should have created Pending Review blocks for brands with overdue tickets
blocks = frappe.get_all('Supplier Payment Block', filters={'block_status': 'Pending Review'})
print(f'PASS: {len(blocks)} payment blocks in Pending Review')
"
```

---

### Phase 3 — Records: New DocTypes + Link Fields (P0/P1)

**Goal:** Add the 5 business-record DocTypes (Replacement, Return, Store, Demo, Stock) and link them to HD Ticket.

#### Step 3.1 — New DocTypes (5)

**Files:** New files under `lavanya_service/setup/`:
- `setup/replacement_record.py` → `Replacement Record`
- `setup/return_record.py` → `Return Service Record`
- `setup/store_record.py` → `Store Service Record`
- `setup/demo_record.py` → `Demo Installation Record`
- `setup/stock_record.py` → `Stock Complaint Record`

Each follows the existing `setup/masters.py` pattern: `frappe.get_doc({"doctype":"DocType", ...})` with `module`, `custom=1`, fields as defined in §§2.4-2.8 of design doc.

**Verification:**
```bash
for dt in "Replacement Record" "Return Service Record" "Store Service Record" "Demo Installation Record" "Stock Complaint Record"; do
  bench --site lavanya-dev.localhost console <<< "import frappe; assert frappe.db.exists('DocType', '$dt'), '$dt missing'; print('$dt: OK')"
done
```

#### Step 3.2 — HD Ticket Link Fields

**Files:** New `lavanya_service/setup/new_ticket_fields.py`

**Changes:**
Add 6 new custom fields to HD Ticket:
- `store_service_reference` (Link to Store Service Record, permlevel 1)
- `replacement_reference` (Link to Replacement Record, permlevel 1)
- `return_reference` (Link to Return Service Record, permlevel 1)
- `demo_installation_reference` (Link to Demo Installation Record, permlevel 1)
- `stock_complaint_reference` (Link to Stock Complaint Record, permlevel 1)
- `store_service_location` (Link to Store/Branch master — new DocType, or Data if master not built)
- `product_received_via` (Select: Customer Walk-in, Store Pickup from Home)
- `area` (Data)
- `payment_block_eligible` (Check, permlevel 1)

**Verification:**
```bash
bench --site lavanya-dev.localhost execute lavanya_service.setup.new_ticket_fields.create_fields
bench --site lavanya-dev.localhost console <<< "
import frappe
m = frappe.get_meta('HD Ticket')
for fn in ['store_service_reference', 'replacement_reference', 'return_reference',
           'demo_installation_reference', 'stock_complaint_reference', 'area']:
    assert m.has_field(fn), f'{fn} missing on HD Ticket'
print('PASS: all link fields added')
"
```

#### Step 3.3 — Advance Stage Hooks

**Files:** `lavanya_service/hooks.py` (doc_events)

**Changes:**
1. Wire `doc_events` so that creating a `Replacement Record` auto-advances the HD Ticket stage to `new_unit_dispatched` (or appropriate stage)
2. Wire similar auto-advance for Store/Return/Demo/Stock records

**Verification:**
Run the full E2E test scenario including a replacement flow.

---

### Phase 4 — Performance Tracking (P1)

#### Step 4.1 — Supplier + Area Performance Log DocTypes

**Files:** New `setup/supplier_performance_log.py`, `setup/area_performance_log.py`

**Changes:**
1. Create `Supplier Performance Log` with fields from design doc §2.1
2. Create `Area Performance Log` with fields from design doc §2.2
3. Register in `hooks.py`

#### Step 4.2 — Scheduler Jobs

**Files:** New `lavanya_service/tasks/performance.py`

**Changes:**
1. `compute_supplier_performance()` — daily 00:30: aggregates HD Ticket data by brand for previous day
2. `compute_area_performance()` — daily 00:45: aggregates by pincode/area

#### Step 4.3 — Brand Service Master Computed Fields

**Files:** `lavanya_service/setup/masters.py`

**Changes:**
1. Add `avg_resolution_days` (Float), `escalation_rate` (Float), `payment_blocked` (Check, computed), `payment_block_days` (Int) to Brand Service Master
2. Add a `before_save` hook or scheduler update to refresh computed values

**Verification:**
```bash
bench --site lavanya-dev.localhost execute lavanya_service.tasks.performance.compute_supplier_performance 2>&1
bench --site lavanya-dev.localhost console <<< "
import frappe
logs = frappe.get_all('Supplier Performance Log', limit=5)
assert len(logs) > 0, 'No performance logs generated'
print(f'PASS: {len(logs)} performance logs created')
"
```

---

### Phase 5 — API + Reports (P1/P2)

#### Step 5.1 — Manager Report Endpoints

**Files:** `lavanya_service/api/manager_reports.py`

**Changes:**
Add 4 new endpoints:
- `supplier_performance(brand=None, from_date=None, to_date=None)` — rolling 90d metrics
- `area_performance(area=None, from_date=None, to_date=None)` — area metrics
- `payment_block_status()` — all active/pending blocks
- `brand_delay_summary(brand=None)` — delay statistics per brand

#### Step 5.2 — Payment Block Manual Actions

**Files:** `lavanya_service/api/workflow_actions.py`

**Changes:**
Add 2 endpoints:
- `block_supplier_payment(block_name, ...)` — activate a Pending Review block
- `release_supplier_block(block_name, ...)` — release an Active block

**Verification:**
```bash
bench --site lavanya-dev.localhost console <<< "
from lavanya_service.api.manager_reports import supplier_performance, area_performance, payment_block_status, brand_delay_summary
for fn in [supplier_performance, area_performance, payment_block_status, brand_delay_summary]:
    result = fn()
    assert isinstance(result, dict), f'{fn.__name__} should return dict'
print('PASS: all report endpoints respond')
"
```

---

### Phase 6 — Customer Communication Log (P2)

#### Step 6.1 — DocType

**Files:** New `lavanya_service/setup/comm_log.py`

**Changes:**
1. Create `Customer Communication Log` with fields from design doc §2.10
2. Auto-log from `inform_customer` action (hook into existing quick action)

#### Step 6.2 — WhatsApp/SMS Integration

**Files:** New `lavanya_service/integrations/whatsapp.py`, `lavanya_service/integrations/sms.py`

**Changes:**
1. Implement send/receive abstractions for WhatsApp and SMS
2. Wire into `inform_customer` to log sent status
3. Implement delivery status callback endpoints

**Verification:**
```bash
bench --site lavanya-dev.localhost console <<< "
import frappe
assert frappe.db.exists('DocType', 'Customer Communication Log')
# Verify a communication log was auto-created after inform_customer
log = frappe.get_all('Customer Communication Log', limit=1)
assert len(log) > 0, 'No communication logs created'
print('PASS: Customer Communication Log working')
"
```

---

### Phase 7 — Hardening (P2)

#### Step 7.1 — Payment Block Auto-Release

**Files:** `lavanya_service/tasks/payment_block.py`

**Changes:**
1. Add auto-release: if no overdue tickets remain for a brand, auto-release the block
2. Add notification when block is released

#### Step 7.2 — Penalty Computation

**Files:** `lavanya_service/api/manager_reports.py`

**Changes:**
1. Compute penalty amounts based on `Supplier SLA Definition.penalty_percent` × delay days × ticket value
2. Return in `supplier_performance` endpoint

#### Step 7.3 — ERPNext Integration

**Files:** New `lavanya_service/integrations/erpnext.py`

**Changes:**
1. Link Sales Invoice / Stock Entry to Replacement Record fields
2. Create credit note from Return Service Record

---

## Part C: End-to-End Verification

### C.1 Unit Tests

Run after each phase:
```bash
bench --site lavanya-dev.localhost run-tests --module lavanya_service.tests.test_corrected_design
```

### C.2 E2E Scenario Tests

Run after Phase 2:
```bash
bench --site lavanya-dev.localhost execute lavanya_service.tests.e2e_followup_scenario.run
```
Expected: 140+ tests, 0 failures.

Run after Phase 3:
```bash
bench --site lavanya-dev.localhost execute lavanya_service.tests.e2e_replacement_scenario.run
bench --site lavanya-dev.localhost execute lavanya_service.tests.e2e_return_scenario.run
bench --site lavanya-dev.localhost execute lavanya_service.tests.e2e_store_service_scenario.run
```

### C.3 Manual Verification Checklist

1. **Create a store_service ticket:** Set `ticket_type = "Customer Product at Store"`, verify stages flow through `product_received_at_store` → `brand_sc_notified` → `diagnosis_received` → `customer_notified_for_collection` → `product_handed_over`
2. **Create a replacement ticket:** Set `service_flow_type = "Replacement / Exchange"`, execute `collect_old_unit` → `dispatch_new_unit` → `record_brand_reimbursement`, verify `Replacement Record` created
3. **Payment block trigger:** Set a ticket's `stage_due_at` to 10 days past due, run scheduler, verify `Supplier Payment Block` created
4. **Manager override:** Verify manager can activate/release payment blocks
5. **Performance logs:** Verify `Supplier Performance Log` and `Area Performance Log` contain data after scheduler runs

---

## Part D: File Change Summary

| Phase | File | Action |
|-------|------|--------|
| 1.1 | `stage_rules.py` | Edit: add flows, stages, actions, SLAs, mappings |
| 1.2 | `setup/followup_fields.py` | Edit: add service_path values |
| 1.3 | `setup/supplier_sla.py` | **New** |
| 1.4 | `setup/supplier_payment_block.py` | **New** |
| 2.1 | `workflow/quick_actions.py` | Edit: add 10 new actions |
| 2.2 | `api/workflow_actions.py` | Edit: add 10 API wrappers |
| 2.3 | `tasks/payment_block.py` | **New** |
| 2.3 | `hooks.py` | Edit: register scheduler |
| 3.1 | `setup/replacement_record.py` | **New** |
| 3.1 | `setup/return_record.py` | **New** |
| 3.1 | `setup/store_record.py` | **New** |
| 3.1 | `setup/demo_record.py` | **New** |
| 3.1 | `setup/stock_record.py` | **New** |
| 3.2 | `setup/new_ticket_fields.py` | **New** |
| 3.3 | `hooks.py` | Edit: doc_events wiring |
| 4.1 | `setup/supplier_performance_log.py` | **New** |
| 4.1 | `setup/area_performance_log.py` | **New** |
| 4.2 | `tasks/performance.py` | **New** |
| 4.3 | `setup/masters.py` | Edit: Brand fields |
| 5.1 | `api/manager_reports.py` | Edit: 4 new endpoints |
| 5.2 | `api/workflow_actions.py` | Edit: 2 new endpoints |
| 6.1 | `setup/comm_log.py` | **New** |
| 6.2 | `integrations/whatsapp.py` | **New** |
| 6.2 | `integrations/sms.py` | **New** |
| 7.1 | `tasks/payment_block.py` | Edit: auto-release |
| 7.3 | `integrations/erpnext.py` | **New** |
| — | `doc/lavanya-expanded-design.md` | Edit: correct ERD comments, field values |
