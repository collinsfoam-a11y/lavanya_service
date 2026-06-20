# Lavanya Service — Expansion Plan (Corrected)

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

### A.2 Stage Naming Convention

**CRITICAL:** All existing stages use **Title Case with spaces** (e.g., "Product Received at Store", "Brand Registered", "Technician Visit Pending"). The design doc uses snake_case (`product_received_at_store`). Every new stage must use **Title Case with spaces** to maintain consistency in the Select field. Verification commands must use Title Case.

### A.3 Existing Stages That Conflict With Proposed Ones

| Proposed Stage (design doc style) | Existing Stage (Title Case) | Action |
|-----------------------------------|----------------------------|--------|
| `product_received_at_store` | "Product Received at Store" | **Reuse existing** — do not create duplicate |
| `installation_completed` | "Installation Completed" | **Reuse existing** — do not create duplicate |
| `replacement_pending` | "Replacement Pending" | **Rename proposed** to avoid confusion; use "Replacement Initiated" |

### A.4 Follow-up Stage Values (12, all defined)

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

### A.5 Service Path Values (7, all defined)

`brand_warranty`, `brand_denied_local`, `out_of_warranty_local`, `customer_paid_local`, `lavanya_paid_goodwill`, `demo_installation`, `stock_supplier`

### A.6 Existing Service Flows (11 flows, 46 stages)

See `stage_rules.py:CURRENT_SERVICE_STAGES` for full list.

### A.7 Existing DocTypes (9)

Brand Service Master, Service Center Master, Local Technician Master, Free Service Rule, Service Product Receipt, Custody Log Entry (child), Lavanya Customer Profile, Lavanya Product Category, Lavanya Product Item

### A.8 Flow Overlap: Proposed `store_service` vs Existing "Customer Product at Store"

**CRITICAL DESIGN DECISION:** The existing flow "Customer Product at Store" already has 5 stages:
- Product Received at Store → Handed to Service Center → Returned to Store → Ready for Pickup → Delivered to Customer

The proposed `store_service` flow has:
- product_received_at_store → brand_sc_notified → brand_sc_pickup → diagnosis_pending → diagnosis_received → product_returned_to_store → customer_notified → product_handed_over

**Decision: `store_service` REPLACES "Customer Product at Store"** — the existing flow is too simple; replace it with the detailed 8-stage store service flow. This means:
- `store_service` is NOT a new `SERVICE_FLOW_TYPE` value; it replaces the existing "Customer Product at Store" in-place
- The existing 5 stages (Product Received at Store, Handed to Service Center, Returned to Store, Ready for Pickup, Delivered to Customer) are REPLACED by 8 new stages
- Existing tickets with "Customer Product at Store" flow will still work (their stage values remain valid in the DB, just no longer in the option list)
- The new `current_service_stage` values for this flow become: "Product Received at Store" (reused), "Brand SC Notified", "Brand SC Picked Up", "Brand SC Diagnosis Pending", "Diagnosis Received", "Product Returned to Store", "Customer Notified for Collection", "Product Handed Over"

---

## Part B: Implementation Plan

Organized in 3 phases matching the design doc's P0/P1/P2 priorities, but restructured so each phase produces working, verifiable increments.

---

### Phase 1 — Foundation: Stage Rules + DocTypes (P0)

**Goal:** Add the 6 new service flows, new stages, new next actions, and 3 core DocTypes so the system can route tickets through the new flows.

#### Step 1.1 — Extend stage_rules.py

**Files:** `lavanya_service/stage_rules.py`

**Changes:**
1. The new flows use the **existing** `service_flow_type` values where possible. No new `SERVICE_FLOW_TYPES` values needed because:
   - `store_service` → replaces "Customer Product at Store" in-place (existing flow, new stages)
   - `replacement_brand` → already handled by "Replacement / Exchange" flow
   - `return_service` → already handled by "Customer Complaint - Site" flow (expanded with return stages)
   - `demo_installation` → already handled by "Installation / Demo" flow
   - `stock_supplier` → already handled by "Stock Complaint" flow

   **Decision:** No new `SERVICE_FLOW_TYPES` values. The 6 design-doc flows map to 4 existing flows. The `service_path` field is used to distinguish sub-flows within a flow.

2. Add new `CURRENT_SERVICE_STAGES` in Title Case (13 new stages total):
   - **store_service (7 new + 1 reused):** "Product Received at Store" (reused from existing), "Brand SC Notified", "Brand SC Picked Up", "Brand SC Diagnosis Pending", "Diagnosis Received", "Product Returned to Store", "Customer Notified for Collection", "Product Handed Over"
   - **replacement (4 new):** "Old Unit Collected", "New Unit Dispatched", "Brand Reimbursement Pending", "Reimbursement Received"
   - **return_service (4 new):** "Return Requested", "Return Reason Verified", "Brand Notified for Return", "Customer Refund Processed"
   - **demo_installation (1 new, 1 existing reused):** "Demo Scheduled" (new), "Installation Completed" (reused)
   - **stock_supplier (2 new):** "Supplier Notified", "Credit Note Received"

   Total new stages: 13 (from 46 → 59). Verification: `assert len(CURRENT_SERVICE_STAGES) == 59`

3. Add new `NEXT_ACTIONS` (12 new): `Notify Brand SC for Pickup`, `Await Brand SC Diagnosis`, `Record Diagnosis Received`, `Notify Customer for Collection`, `Hand Over Product`, `Arrange Old Unit Collection`, `Dispatch New Unit`, `Follow Up Brand Reimbursement`, `Record Reimbursement Received`, `Verify Return Reason`, `Notify Brand for Return`, `Process Customer Refund`

4. Add new `STAGE_DEFAULT_ACTION` entries for all 13 new stages. **Every new stage MUST have an entry** or `assign_defaults` will KeyError:

   ```
   "Product Received at Store": "Hand to Service Center",   # existing
   "Brand SC Notified": "Await Brand SC Diagnosis",
   "Brand SC Picked Up": "Follow up Service Center",
   "Brand SC Diagnosis Pending": "Follow up Service Center",
   "Diagnosis Received": "Inform Customer",
   "Product Returned to Store": "Notify Customer for Collection",
   "Customer Notified for Collection": "Hand Over Product",
   "Product Handed Over": "Confirm Closure",
   "Old Unit Collected": "Dispatch New Unit",
   "New Unit Dispatched": "Follow Up Brand Reimbursement",
   "Brand Reimbursement Pending": "Follow Up Brand Reimbursement",
   "Reimbursement Received": "Confirm Closure",
   "Return Requested": "Verify Return Reason",
   "Return Reason Verified": "Notify Brand for Return",
   "Brand Notified for Return": "Process Customer Refund",
   "Customer Refund Processed": "Confirm Closure",
   "Demo Scheduled": "Await Technician Visit",
   "Supplier Notified": "Follow up Supplier",
   "Credit Note Received": "Confirm Closure",
   ```

5. Add new `STAGE_SLA_MINUTES` entries (can use `DEFAULT_SLA_MINUTES = 24*60` for most):

   ```python
   "Brand SC Diagnosis Pending": 48 * _H,
   "Brand Reimbursement Pending": 72 * _H,
   "Return Reason Verified": 24 * _H,
   "Brand Notified for Return": 72 * _H,
   ```

6. Remove existing stages that are replaced: "Handed to Service Center", "Returned to Store", "Ready for Pickup", "Delivered to Customer" (the old store-service stages) — only if `store_service` flow replaces "Customer Product at Store" entirely.

7. Update `flow_for_ticket_type` — no changes needed (existing mapping covers all flows).

**Verification:**
```bash
bench --site lavanya-dev.localhost console <<< "
import frappe
from lavanya_service.stage_rules import SERVICE_FLOW_TYPES, CURRENT_SERVICE_STAGES, NEXT_ACTIONS, STAGE_DEFAULT_ACTION
assert 'Store Service' in SERVICE_FLOW_TYPES or 'Customer Product at Store' in SERVICE_FLOW_TYPES, 'store flow missing'
assert 'Brand SC Notified' in CURRENT_SERVICE_STAGES, 'Brand SC Notified stage missing'
assert 'Diagnosis Received' in CURRENT_SERVICE_STAGES, 'Diagnosis Received stage missing'
assert 'Old Unit Collected' in CURRENT_SERVICE_STAGES, 'Old Unit Collected stage missing'
assert len(CURRENT_SERVICE_STAGES) >= 55, f'expected 55+ stages, got {len(CURRENT_SERVICE_STAGES)}'
assert len(NEXT_ACTIONS) >= 65, f'expected 65+ next actions, got {len(NEXT_ACTIONS)}'
# Verify every new stage has a default action
for stage in ['Brand SC Notified', 'Brand SC Picked Up', 'Brand SC Diagnosis Pending',
              'Diagnosis Received', 'Product Returned to Store', 'Customer Notified for Collection',
              'Product Handed Over', 'Old Unit Collected', 'New Unit Dispatched',
              'Brand Reimbursement Pending', 'Reimbursement Received',
              'Return Requested', 'Return Reason Verified', 'Brand Notified for Return',
              'Customer Refund Processed', 'Demo Scheduled']:
    assert stage in STAGE_DEFAULT_ACTION, f'{stage} missing STAGE_DEFAULT_ACTION'
print(f'PASS: stage_rules.py extended with {len(CURRENT_SERVICE_STAGES)} stages, {len(NEXT_ACTIONS)} actions')
"
```

#### Step 1.2 — Extend followup_fields.py (service_path)

**Files:** `lavanya_service/setup/followup_fields.py`

**Changes:**
1. Add 3 new `SERVICE_PATH_OPTIONS` values: `store_service`, `replacement_brand`, `return_service`
   - NOTE: The header comment says "2 new" but we add 3. `store_service` handles store-related service work, `replacement_brand` for brand-approved replacements, `return_service` for customer return/refund cases.

2. Run migration:
```bash
bench --site lavanya-dev.localhost execute lavanya_service.setup.followup_fields.create_followup_fields
```

**Verification:**
```bash
bench --site lavanya-dev.localhost console <<< "
import frappe
from lavanya_service.setup.followup_fields import SERVICE_PATH_OPTIONS
options = SERVICE_PATH_OPTIONS.split('\n')
assert 'store_service' in options, 'store_service path missing'
assert 'replacement_brand' in options, 'replacement_brand path missing'
assert 'return_service' in options, 'return_service path missing'
print(f'PASS: service_path has {len(options)} options')
"
```

#### Step 1.3 — Create Supplier SLA Definition DocType

**Files:** New `lavanya_service/setup/supplier_sla.py`

**Changes:**
1. Create DocType `Supplier SLA Definition` via `frappe.get_doc({"doctype":"DocType", ...})` pattern (same as `setup/masters.py`)
2. **Do NOT add to hooks.py fixture list** — custom DocTypes are created programmatically. Instead, add to `after_install`/`after_migrate` in `hooks.py`.
3. Fields: `brand` (Link to Brand Service Master), `service_center` (optional Link to Service Center Master), `response_sla_hours` (Int), `resolution_sla_hours` (Int), `payment_block_delay_days` (Int), `payment_terms` (Select: Net 30, Net 45, Net 60, Advance), `penalty_percent` (Float), `applicable_product_types` (Small Text), `enabled` (Check)
4. Seed default records for 10 brands

**hooks.py additions:**
- Add `lavanya_service.setup.supplier_sla.create_supplier_sla_doctype` to `after_install` and `after_migrate` lists
- Add `Supplier SLA Definition` to the fixture `Custom DocPerm` filter's `parent` list (for permission records)

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
1. Create DocType `Supplier Payment Block` via programmatic pattern
2. Fields: `brand` (Link to Brand Service Master), `service_center` (optional Link to Service Center Master), `block_status` (Select: Active, Released, Pending Review), `blocked_at` (Datetime), `released_at` (Datetime), `blocked_by` (Link to User), `block_reason` (Small Text), `release_reason` (Small Text), `overdue_ticket_count` (Int, computed), `max_delay_days` (Float, computed)
3. Add to `after_install`/`after_migrate` and fixture Custom DocPerm list

**Verification:**
```bash
bench --site lavanya-dev.localhost execute lavanya_service.setup.supplier_payment_block.create_supplier_payment_block_doctype
bench --site lavanya-dev.localhost console <<< "
import frappe
assert frappe.db.exists('DocType', 'Supplier Payment Block')
print('PASS: Supplier Payment Block created')
"
```

#### Step 1.5 — Stage Rules: service_path → flow derivation

**Files:** `lavanya_service/stage_rules.py`

**Changes:**
1. Add `SERVICE_PATH_TO_FLOW` dict mapping new service_path values to existing service_flow_type values:

   ```python
   SERVICE_PATH_TO_FLOW = {
       "store_service": "Customer Product at Store",
       "replacement_brand": "Replacement / Exchange",
       "return_service": "Customer Complaint - Site",
   }
   ```

   (Existing paths `brand_warranty`, `brand_denied_local`, etc. already map correctly via `flow_for_ticket_type`.)

2. Add `derive_flow_from_path(path)` helper that returns the service_flow_type for a given service_path.

3. Add `get_next_stage(stage, flow)` helper that returns the next stage in the flow's ordered stage list. Uses a `FLOW_STAGES_ORDERED` dict.

**Verification:**
```bash
bench --site lavanya-dev.localhost execute lavanya_service.tests.test_corrected_design.run 2>&1
```

---

### Phase 2 — Workflow: Quick Actions + API + UI (P0)

**Goal:** Add the quick actions and API endpoints needed to drive the 4 expanded flows, and wire them into the stage machine.

#### Step 2.1 — New Quick Actions

**Files:** `lavanya_service/workflow/quick_actions.py`

**Changes (10 new actions):**
All actions follow existing pattern: `_require_roles`, `_load_ticket`, `_block_if_final`, set stage, `_set_last_followup`, `_save_ticket`, `_result`.

1. `notify_brand_sc_for_pickup(ticket_name, brand_sc=None, ...)` — sets stage "Brand SC Picked Up"
2. `record_diagnosis_received(ticket_name, diagnosis=None, ...)` — sets stage "Diagnosis Received"
3. `notify_customer_for_collection(ticket_name, ...)` — sets stage "Customer Notified for Collection"
4. `hand_over_product(ticket_name, ...)` — sets stage "Product Handed Over"
5. `collect_old_unit(ticket_name, serial_no=None, ...)` — sets stage "Old Unit Collected"
6. `dispatch_new_unit(ticket_name, new_serial_no=None, ...)` — sets stage "New Unit Dispatched"
7. `return_old_unit_to_brand(ticket_name, ...)` — sets stage "Brand Reimbursement Pending"
8. `record_brand_reimbursement(ticket_name, amount=None, ...)` — sets stage "Reimbursement Received"
9. `verify_return_reason(ticket_name, reason=None, ...)` — sets stage "Return Reason Verified"
10. `notify_brand_for_return(ticket_name, ...)` — sets stage "Brand Notified for Return"

**IMPORTANT:** All new actions must set `current_service_stage` directly (e.g., `doc.current_service_stage = "Brand SC Notified"`), following the existing pattern in `quick_actions.py`. They set `followup_stage` to existing values (`sc_followup_done` or `customer_informed` or leave as-is) — `followup_stage` is NOT extended with new values for these flows.

**Imports note:** New actions may need additional setup imports (e.g., `from frappe.utils import now_datetime` is already imported).

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
2. Each wrapper follows the existing pattern: imports `quick_actions`, delegates to the matching function, passes through all keyword arguments

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

#### Step 2.3 — Form Script UI Buttons

**Files:** `lavanya_service/setup/quick_actions_form_script.py`

**Changes:**
1. Add 10 new button definitions to the `actions` array in the form script body
2. Each button follows the existing pattern: `action("Label", function () { lavanyaModal({...}) })`
3. Run after editing:
```bash
bench --site lavanya-dev.localhost execute lavanya_service.setup.quick_actions_form_script.ensure_quick_action_form_scripts
```

**Note:** This step was missing from the original plan. The form script is how users trigger quick actions from the HD Ticket form UI.

#### Step 2.4 — Scheduler: check_payment_block_triggers

**Files:** New `lavanya_service/tasks/payment_block.py`, `hooks.py`

**Changes:**
1. Implement `check_payment_block_triggers()` — scans active tickets by brand, compares delay to SLA definition's `payment_block_delay_days`, creates `Supplier Payment Block` in `Pending Review` if threshold exceeded
2. Register in `hooks.py:scheduler_events` daily at 06:00:
   ```python
   scheduler_events = {
       "hourly": [
           "lavanya_service.tasks.reminder_refresh.refresh_active_ticket_reminders",
       ],
       "daily": [
           "lavanya_service.reminders.notification_output.run_daily_reminder_notifications_dry_safe",
           "lavanya_service.reminders.notification_output.run_escalation_notifications_dry_safe",
           "lavanya_service.tasks.payment_block.check_payment_block_triggers",
       ],
   }
   ```

**Verification:**
```bash
bench --site lavanya-dev.localhost execute lavanya_service.tasks.payment_block.check_payment_block_triggers 2>&1
bench --site lavanya-dev.localhost console <<< "
import frappe
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

**Register in hooks.py:**
- Add each `create_*_doctype` function to both `after_install` and `after_migrate` lists
- Add each new DocType name to the fixture `Custom DocPerm` filter's `parent` list

**Verification:**
```bash
for dt in "Replacement Record" "Return Service Record" "Store Service Record" "Demo Installation Record" "Stock Complaint Record"; do
  printf "import frappe; assert frappe.db.exists('DocType', '$dt'), '$dt missing'; print('$dt: OK')" | bench --site lavanya-dev.localhost console
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
- `store_service_location` (Data — not Link, since there's no Store/Branch master yet)
- `area` (Data)
- `payment_block_eligible` (Check, permlevel 1)
- `product_received_via` (Select: Customer Walk-in, Store Pickup from Home)

**Register in field_permissions.py:** Add link fields to `PERMLEVEL_1_FIELDS`:
```python
PERMLEVEL_1_FIELDS = [
    # ...existing fields...
    "store_service_reference",
    "replacement_reference",
    "return_reference",
    "demo_installation_reference",
    "stock_complaint_reference",
    "payment_block_eligible",
]
```

**Register in hooks.py fixture list:** Add new fieldnames to the `Custom Field` fixture filter.

**Register in hooks.py after_install/after_migrate:**
```python
after_migrate = [
    # ...existing entries...
    "lavanya_service.setup.new_ticket_fields.create_fields",
]
```

**Verification:**
```bash
bench --site lavanya-dev.localhost execute lavanya_service.setup.new_ticket_fields.create_fields
bench --site lavanya-dev.localhost console <<< "
import frappe
m = frappe.get_meta('HD Ticket')
for fn in ['store_service_reference', 'replacement_reference', 'return_reference',
           'demo_installation_reference', 'stock_complaint_reference', 'area',
           'store_service_location', 'product_received_via', 'payment_block_eligible']:
    assert m.has_field(fn), f'{fn} missing on HD Ticket'
print('PASS: all link fields added')
"
```

#### Step 3.3 — Advance Stage Hooks (doc_events)

**Files:** `lavanya_service/hooks.py`, `lavanya_service/overrides/hd_ticket.py`

**Changes:**
1. Wire `doc_events` so that creating a `Replacement Record` auto-advances the linked HD Ticket stage to "New Unit Dispatched" (or appropriate stage)
2. Wire similar auto-advance for Store/Return/Demo/Stock records
3. Use `override_doctype_class` for LavanyaHDTicket (already set), or add doc_events entries:

```python
doc_events = {
    "Lavanya Customer Profile": {
        "before_validate": "lavanya_service.api.customer_intake.normalize_customer_profile_phone_numbers",
    },
    "Service Product Receipt": {
        "validate": "lavanya_service.validations.service_receipt.validate_service_product_receipt",
    },
    "Replacement Record": {
        "after_insert": "lavanya_service.workflow.stage_advancers.advance_on_record_created",
    },
    "Return Service Record": {
        "after_insert": "lavanya_service.workflow.stage_advancers.advance_on_record_created",
    },
}
```

4. Create new `lavanya_service/workflow/stage_advancers.py` with generic handler.

**Verification:**
Run the full E2E test scenario including a replacement flow.

---

### Phase 4 — AI Advisory Updates (P1)

**Files:** `lavanya_service/ai_advisory.py`

**Changes:**
1. Add new flow-specific detection in `is_ai_review_candidate`:
   ```python
   _STORE_SERVICE_FLOW = "Customer Product at Store"  # already in ai_advisory.py as _PRODUCT_AT_STORE_FLOW
   _REPLACEMENT_FLOW = "Replacement / Exchange"
   _RETURN_FLOW = "Customer Complaint - Site"  # when service_path == "return_service"
   ```

2. Add new candidate reasons:
   - `store_service_ageing` — product at store service stage and overdue
   - `reimbursement_pending` — in "Brand Reimbursement Pending" stage and overdue
   - `return_pending` — in return stage and overdue

3. Add new templates in `_TEMPLATES` dict for each new reason

4. Update `_followup_flow_steps` to handle new `service_path` values — if `service_path == "store_service"`, show different step ordering

**Verification:**
```bash
bench --site lavanya-dev.localhost execute lavanya_service.tests.test_ai_advisory.run 2>&1
```

---

### Phase 5 — Today's Work Classification Updates (P1)

**Files:** `lavanya_service/workflow/today_work.py`

**Changes:**
1. Add new `service_path` values to `classify_ticket` function so tickets with `service_path == "store_service"` etc. appear in correct buckets
2. Add new stage-based groupings if needed (if new stages don't match existing bucket rules)

**Verification:**
```bash
bench --site lavanya-dev.localhost execute lavanya_service.tests.test_today_work.run 2>&1
```

---

### Phase 6 — Performance Tracking (P2)

#### Step 6.1 — Supplier + Area Performance Log DocTypes

**Files:** New `setup/supplier_performance_log.py`, `setup/area_performance_log.py`

**Changes:**
1. Create `Supplier Performance Log` with fields from design doc §2.1
2. Create `Area Performance Log` with fields from design doc §2.2
3. Register via `after_install`/`after_migrate` (not fixture JSON)

#### Step 6.2 — Scheduler Jobs

**Files:** New `lavanya_service/tasks/performance.py`

**Changes:**
1. `compute_supplier_performance()` — daily 00:30: aggregates HD Ticket data by brand for previous day
2. `compute_area_performance()` — daily 00:45: aggregates by pincode/area
3. Register in `hooks.py:scheduler_events` daily

#### Step 6.3 — Brand Service Master Computed Fields

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

### Phase 7 — API + Reports (P2)

#### Step 7.1 — Manager Report Endpoints

**Files:** `lavanya_service/api/manager_reports.py`

**Changes:**
Add 4 new endpoints:
- `supplier_performance(brand=None, from_date=None, to_date=None)` — rolling 90d metrics
- `area_performance(area=None, from_date=None, to_date=None)` — area metrics
- `payment_block_status()` — all active/pending blocks
- `brand_delay_summary(brand=None)` — delay statistics per brand

#### Step 7.2 — Payment Block Manual Actions

**Files:** `lavanya_service/api/workflow_actions.py`

**Changes:**
Add 2 endpoints:
- `block_supplier_payment(block_name, ...)` — activate a Pending Review block
- `release_supplier_block(block_name, ...)` — release an Active block

#### Step 7.3 — Customer Communication Log

**Files:** New `lavanya_service/setup/comm_log.py`

**Changes:**
1. Create `Customer Communication Log` with fields from design doc §2.10
2. Auto-log from `inform_customer` action (hook into existing quick action)

---

### Phase 8 — Hardening (P2)

#### Step 8.1 — Payment Block Auto-Release

**Files:** `lavanya_service/tasks/payment_block.py`

**Changes:**
1. Add auto-release: if no overdue tickets remain for a brand, auto-release the block
2. Add notification when block is released

#### Step 8.2 — Penalty Computation

**Files:** `lavanya_service/api/manager_reports.py`

**Changes:**
1. Compute penalty amounts based on `Supplier SLA Definition.penalty_percent` × delay days × ticket value
2. Return in `supplier_performance` endpoint

#### Step 8.3 — Fix `part_required` Check Field Comparison

**Files:** `lavanya_service/ai_advisory.py` (line 369)

**Changes:**
```python
# Current (buggy):
part_required = doc.get("part_required") == 1 or doc.get("part_required") == "Yes"

# Fixed:
part_required = bool(doc.get("part_required"))
```
`part_required` is a Check field (stores 0 or 1 as int). The existing `== "Yes"` check (copied from an older text-field pattern) never matches. Fix to `bool(doc.get(...))`.

#### Step 8.4 — WhatsApp/SMS Integration (Optional)

**Files:** New `lavanya_service/integrations/whatsapp.py`, `lavanya_service/integrations/sms.py`

**Changes:**
1. Implement send/receive abstractions for WhatsApp and SMS
2. Wire into `inform_customer` to log sent status
3. Implement delivery status callback endpoints

#### Step 8.5 — ERPNext Integration (Optional)

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

1. **Create a store_service ticket:** Set `ticket_type = "Customer Product at Store"`, verify stages flow through "Product Received at Store" → "Brand SC Notified" → "Diagnosis Received" → "Customer Notified for Collection" → "Product Handed Over"
2. **Create a replacement ticket:** Set `service_flow_type = "Replacement / Exchange"`, execute `collect_old_unit` → `dispatch_new_unit` → `record_brand_reimbursement`, verify stage progression
3. **Payment block trigger:** Set a ticket's `stage_due_at` to 10 days past due, run scheduler, verify `Supplier Payment Block` created
4. **Manager override:** Verify manager can activate/release payment blocks
5. **Performance logs:** Verify `Supplier Performance Log` and `Area Performance Log` contain data after scheduler runs

---

## Part D: File Change Summary

| Phase | File | Action |
|-------|------|--------|
| 1.1 | `stage_rules.py` | Edit: add stages, actions, SLAs, mappings (Title Case) |
| 1.2 | `setup/followup_fields.py` | Edit: add 3 new service_path values |
| 1.3 | `setup/supplier_sla.py` | **New** — register in after_install/migrate + fixture perm list |
| 1.4 | `setup/supplier_payment_block.py` | **New** — register in after_install/migrate + fixture perm list |
| 1.5 | `stage_rules.py` | Edit: add FLOW_STAGES_ORDERED + helpers |
| 2.1 | `workflow/quick_actions.py` | Edit: add 10 new actions |
| 2.2 | `api/workflow_actions.py` | Edit: add 10 API wrappers |
| 2.3 | `setup/quick_actions_form_script.py` | Edit: add 10 UI button definitions |
| 2.4 | `tasks/payment_block.py` | **New** |
| 2.4 | `hooks.py` | Edit: register scheduler |
| 3.1 | `setup/replacement_record.py` | **New** — register in after_install/migrate + fixture perm list |
| 3.1 | `setup/return_record.py` | **New** |
| 3.1 | `setup/store_record.py` | **New** |
| 3.1 | `setup/demo_record.py` | **New** |
| 3.1 | `setup/stock_record.py` | **New** |
| 3.2 | `setup/new_ticket_fields.py` | **New** — register in after_install/migrate |
| 3.2 | `setup/field_permissions.py` | Edit: add link fields to PERMLEVEL_1_FIELDS |
| 3.2 | `hooks.py` | Edit: add new fieldnames to Custom Field fixture filter |
| 3.3 | `workflow/stage_advancers.py` | **New** |
| 3.3 | `hooks.py` | Edit: doc_events for auto-advance |
| 4 | `ai_advisory.py` | Edit: add new flow detections + templates |
| 5 | `workflow/today_work.py` | Edit: add new service_path classifications |
| 6.1 | `setup/supplier_performance_log.py` | **New** |
| 6.1 | `setup/area_performance_log.py` | **New** |
| 6.2 | `tasks/performance.py` | **New** |
| 6.3 | `setup/masters.py` | Edit: Brand computed fields |
| 7.1 | `api/manager_reports.py` | **New** (or Edit if file exists) |
| 7.2 | `api/workflow_actions.py` | Edit: 2 new payment block endpoints |
| 7.3 | `setup/comm_log.py` | **New** |
| 8.1 | `tasks/payment_block.py` | Edit: auto-release |
| 8.3 | `ai_advisory.py` | Edit: fix `part_required == "Yes"` bug |
| 8.4 | `integrations/whatsapp.py` | **New** (optional) |
| 8.4 | `integrations/sms.py` | **New** (optional) |
| 8.5 | `integrations/erpnext.py` | **New** (optional) |
| — | `hooks.py` | Edit: after_install/migrate lists, scheduler_events, fixture lists |
| — | `doc/lavanya-expanded-design.md` | Edit: correct ERD comments, field values, stage naming convention |

---

## Part E: Pre-Implementation Checklist

Before starting any implementation, these design decisions must be confirmed:

1. **Store Service flow:** Does `store_service` REPLACE "Customer Product at Store" in-place, or coexist beside it? **Recommend: Replace in-place.** The existing 5-stage flow is insufficient for the detailed store workflow.

2. **Replacement flows:** Keep "Replacement / Exchange" as one flow (as now), or split into `replacement_approved_new` and `replacement_goodwill`? **Recommend: Keep one flow.** The `service_path` field (`replacement_brand`) distinguishes the sub-type.

3. **`store_service_location` field type:** Data (string) vs Link to a new Store/Branch master? **Recommend: Data (string)** for now. A master DocType can be built later. This avoids scope creep in the initial implementation.

4. **Existing stage removal:** When replacing the "Customer Product at Store" stages ("Handed to Service Center", "Returned to Store", "Ready for Pickup", "Delivered to Customer"), remove them from `CURRENT_SERVICE_STAGES` or keep them for backward compatibility? **Recommend: Remove from option list but keep in DB.** Existing tickets with these stages will still display them correctly (stored values don't depend on option list). New tickets will only see the new stages.

5. **`followup_stage` for new flows:** The new quick actions should set `followup_stage` to existing values (`sc_followup_done`, `customer_informed`, or leave as-is). Do NOT extend `FOLLOWUP_STAGE_OPTIONS` with new values — the follow-up tracking layer is separate from the stage machine.
