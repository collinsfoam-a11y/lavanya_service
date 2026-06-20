# Lavanya Service — Complete App Reference

> **Read this FIRST before making any changes.**
> Auto-generated from codebase audit on 2026-06-20.

---

## 1. App Metadata

| Property | Value |
|----------|-------|
| App name | `lavanya_service` |
| Version | `0.0.1` |
| Publisher | Lavanya eMart |
| Required app | `helpdesk` (v1.25.1) |
| Frappe version | v15.110.0 |
| License | MIT |

---

## 2. File Map (complete source tree)

```
lavanya_service/
  __init__.py                    # v0.0.1
  hooks.py                       # App registration, fixtures, scheduler, doc_events, overrides

  api/
    __init__.py
    coordinator_dashboard.py     # Coordinator dashboard (parallel agent)
    customer_intake.py           # lookup_customer_by_mobile, sync_customer_profile_from_ticket
    intake_masters.py            # Brand/Category/Item CRUD for form scripts
    manager_reports.py           # Report catalog + drill-down
    product_receipt_actions.py   # Product receipt custody moves
    qr_intake.py                 # QR complaint intake (guest-facing)
    repeat_complaints.py         # Repeat complaint detection
    stitch_console.py            # 7 SPA endpoints: list, detail, activity, new-ticket, etc.
    today_work.py                # DEPRECATED wrapper (no longer used as endpoint)
    workflow_actions.py          # 16 POST quick-action endpoints + get_current_user_roles

  overrides/
    client.py                    # get(), get_ticket(), get_ticket_customizations overrides
    hd_ticket.py                 # LavanyaHDTicket(HDTicket): before_validate/validate/on_update

  reminders/
    notification_output.py       # Dry-run reminder notifications (daily + escalation)
    ticket_reminders.py          # Follow-up due/overdue queries for scheduler

  reports/
    manager_dashboard.py         # SQL report queries (9 reports)

  setup/
    install.py                   # after_install / after_migrate entry point
    masters.py                   # Brand/SC/Technician/FreeService DocType creation + seed
    service_receipt.py           # Service Product Receipt + Custody Log Entry DocTypes
    customer_profile.py          # Lavanya Customer Profile DocType + form scripts
    helpdesk_config.py           # Statuses, priorities, types configuration
    hd_ticket_fields.py          # 60+ HD Ticket custom fields
    service_stages.py            # Stage layer fields (programmatic)
    followup_fields.py           # Follow-up tracking fields (programmatic)
    intake_masters.py            # Product Category/Item DocTypes + HD Ticket link fields
    ai_fields.py                 # AI advisory fields
    reminder_rule.py             # Lavanya Reminder Rule DocType
    appointment.py               # Lavanya Service Appointment DocType
    field_permissions.py         # Permlevel 1/2 field protection
    sla_config.py                # Default SLA "Lavanya Default"
    sla_fixes.py                 # SLA idempotent fixup
    permission_fixes.py          # HD Ticket "All" role restriction
    ticket_template.py           # Default ticket template fields
    runtime_defaults.py          # HD Settings defaults

  tasks/
    reminder_refresh.py          # Hourly batch reminder state persistence

  tests/
    acceptance_phase1.py         # Phase 1 acceptance tests
    ai_advisory.py               # AI advisory engine tests
    customer_intake.py           # Customer lookup/sync tests
    e2e_followup_scenario.py     # End-to-end follow-up scenario
    frappe_ui_console.py         # Frappe UI console tests
    fresh_install_integrity.py   # Fresh install integrity checks
    intake_masters.py            # Intake master CRUD tests
    phone_normalization.py       # Phone normalization tests
    pilot_readiness.py           # Pilot readiness checks
    product_receipt_ux.py        # Product receipt UX tests
    production_readiness.py      # Production readiness checks
    qr_intake.py                 # QR intake tests
    reminder_engine.py           # Reminder engine resolution tests (21)
    reminder_refresh.py          # Reminder refresh persistence tests (14)
    repeat_detection.py          # Repeat complaint detection tests
    reports_dashboard.py         # Report dashboard tests
    role_browser_uat_permissions.py  # Role/permission UAT tests
    scheduler_and_sla.py         # Scheduler + SLA tests
    stage_layer.py               # Stage layer tests
    stitch_console_actions.py    # SPA action endpoint tests
    stitch_console_spa.py        # SPA endpoint tests
    system_pushed_notifications.py  # Notification tests
    ticket_template_integrity.py # Template integrity tests
    today_work_page.py           # Today's Work page tests
    today_work.py                # Today's Work logic tests (24)
    warranty_recommendation.py   # Warranty recommendation tests
    workflow_quick_actions.py    # Quick action function tests

  utils/
    phone.py                     # normalize_phone() — Indian mobile normalization
    add_client_script.py         # Client script utility (parallel agent)

  validations/
    hd_ticket.py                 # Server-side validations on save (420 lines)
    service_receipt.py           # Service Product Receipt validation

  workflow/
    quick_actions.py             # 16 quick action functions (680 lines)
    today_work.py                # Today's Work grouping engine (543 lines)

  www/
    frontend.html                # SPA serve page (auto-synced from build)
    frontend.py                  # No-cache controller for SPA
    qr_complaint.html            # QR complaint form
    qr_complaint.py              # QR complaint controller

  doc/
    lavanya-requirements.md      # Source-grounded requirements
    lavanya-overview.md          # High-level overview
    lavanya-spa-status.md        # SPA build log & pending work
    lavanya-expanded-design.md   # Proposed expansions
    lavanya-app-reference.md     # THIS FILE
    lavanya-changelog.md         # Change audit trail

  fixtures/                      # JSON record fixtures
    role.json, custom_field.json, client_script.json,
    hd_ticket_status.json, hd_ticket_priority.json,
    hd_ticket_type.json, hd_ticket_template.json,
    hd_settings.json, hd_view.json, hd_form_script.json,
    custom_docperm.json, print_format.json,
    hd_service_level_agreement.json

  frontend/                      # Vue 3 SPA
    src/
      pages/                     # TodayWork.vue, Tickets.vue, Reports.vue, NewTicket.vue
      components/                # AppShell.vue, TicketDetail.vue, NotFound.vue
      utils/                     # index.js, toast.js
      api.js                     # call() / post() helpers
      router.js                  # Vue Router config
    tailwind.config.mjs          # frappe-ui preset
```

---

## 3. Custom DocTypes

### 3.1 Brand Service Master
| Field | Type | Details |
|-------|------|---------|
| brand_name | Data | Required, unique, autoname |
| toll_free_number | Data | |
| registration_channel | Select | Toll Free / WhatsApp / Web Portal / Dealer Portal / Email |
| portal_url | Data | |
| dealer_code | Data | |
| default_registration_sla_hours | Int | Default 4 |
| free_service_supported | Check | |
| notes | Small Text | |

**Source:** `setup/masters.py:create_brand_service_master()`
**Seeds:** LG, Samsung, Whirlpool, Voltas, Preethi, Bajaj, Prestige, Crompton, Kent, Faber

### 3.2 Service Center Master
| Field | Type | Details |
|-------|------|---------|
| service_center_name | Data | Required, unique, autoname |
| brand | Link → Brand Service Master | Required |
| phone | Data | |
| contact_person | Data | |
| coverage_pincodes | Small Text | |
| status | Select | Active / Delayed-Prone / Out of Area / Blacklisted, default Active |

**Source:** `setup/masters.py:create_service_center_master()`

### 3.3 Local Technician Master
| Field | Type | Details |
|-------|------|---------|
| technician_name | Data | Required, unique, autoname |
| phone | Data | |
| skills | Small Text | |
| default_commission_type | Select | Fixed Amount / Percentage / No Commission / Included in Service Cost |
| default_commission_value | Currency | |
| active | Check | Default 1 |

**Source:** `setup/masters.py:create_local_technician_master()`

### 3.4 Free Service Rule
| Field | Type | Details |
|-------|------|---------|
| brand | Link → Brand Service Master | |
| product_type | Select | AC / Refrigerator / ... / Other |
| service_type | Select | AC Free Service / Chimney Service / Water Purifier Service / Demo Follow-up |
| brand_backed | Check | Default 0 |
| due_after_days | Int | Required |
| reminder_before_days | Int | Default 7 |
| active | Check | Default 1 |

**Autoname:** `FSR-.#####`

**Source:** `setup/masters.py:create_free_service_rule()`

### 3.5 Service Product Receipt
| Field | Type | Details |
|-------|------|---------|
| ticket | Link → HD Ticket | |
| receipt_date | Datetime | |
| received_by | Link → User | |
| customer_name | Data | |
| phone | Data | |
| address | Small Text | |
| product_type | Data | |
| brand | Data | |
| model_no | Data | |
| serial_no | Data | |
| accessories_received | Small Text | |
| physical_condition | Small Text | |
| current_custody_status | Select | Received at Store / Handed to Service Center / With Local Technician / Returned to Store / Ready for Customer Pickup |
| custody_log | Table → Custody Log Entry | |

**Naming series:** `LV-SR-.YYYY.-.####`

**Source:** `setup/service_receipt.py`

### 3.6 Custody Log Entry (child of Service Product Receipt)
| Field | Type | Details |
|-------|------|---------|
| custody_action | Data | |
| custody_status | Data | |
| action_datetime | Datetime | |
| from_party | Data | |
| to_party | Data | |
| handled_by | Data | |

### 3.7 Lavanya Customer Profile
| Field | Type | Details |
|-------|------|---------|
| customer_name | Data | Required |
| primary_mobile | Data | Required, unique, indexed |
| primary_mobile_raw | Data | Hidden, read-only |
| alternate_mobile | Data | |
| alternate_mobile_raw | Data | Hidden, read-only |
| address | Small Text | |
| pincode | Data | |
| last_ticket | Link → HD Ticket | |
| ticket_count | Int | Default 0 |
| last_product_type | Data | |
| last_brand | Link → Brand Service Master | |
| disabled | Check | Default 0 |

**Autoname:** `LV-CUST-.#####`
**Auto-created:** On first ticket save by phone number.

**Source:** `setup/customer_profile.py`

### 3.8 Lavanya Product Category
| Field | Type | Details |
|-------|------|---------|
| category_name | Data | Required, unique, autoname |
| parent_category | Link → self | |
| disabled | Check | |

**Source:** `setup/intake_masters.py:ensure_product_category_doctype()`

### 3.9 Lavanya Product Item
| Field | Type | Details |
|-------|------|---------|
| item_name | Data | Required, unique, autoname |
| item_type | Link → Lavanya Product Category | |
| brand | Link → Brand Service Master | |
| model_no | Data | |
| default_warranty_months | Int | Default 0 |
| disabled | Check | |

**Source:** `setup/intake_masters.py:ensure_product_item_doctype()`

### 3.10 Lavanya Reminder Rule
(22 fields — created programmatically by `setup/reminder_rule.py`)
Resolution-priority rule engine configuration. Defines per-brand/per-stage/per-product rules with specificity scoring.

### 3.11 Lavanya Service Appointment
| Field | Type | Details |
|-------|------|---------|
| ticket | Link → HD Ticket | |
| appointment_datetime | Datetime | |
| technician | Data | |
| notes | Small Text | |
| status | Select | Scheduled / Completed / Cancelled |

---

## 4. HD Ticket Custom Fields (~85 fields)

### 4.1 Customer Section
`customer_name`, `phone_1`, `phone_2`, `phone_1_raw`, `phone_1_normalized`,
`phone_2_raw`, `phone_2_normalized`, `address`, `pincode`

### 4.2 Product Section
`product_type` (11 options), `product_category` (Link → Product Category),
`product_item` (Link → Product Item), `product_subtype`,
`brand` (Link → Brand Service Master), `model_no`, `serial_no`

### 4.3 Purchase Section
`purchased_from_lavanya` (Select: Yes/No), `invoice_source`, `old_erp_reference`,
`purchase_date`, `warranty_status` (In Warranty / Out of Warranty / Unknown / Extended Warranty / Brand Denied)

### 4.4 Brand Service Section
`manufacturer_registration_required`, `manufacturer_registered`,
`brand_ticket_number`, `registration_date`, `registration_pending_reason`,
`brand_registration_recommended`, `brand_registration_override_reason`,
`brand_registration_recommended_at`, `service_center`, `local_technician`

### 4.5 Follow-up Section
`is_repeated_complaint`, `previous_ticket_link`, `pending_reason` (24 options),
`next_follow_up_date`, `closure_type` (11 options),
`service_product_receipt`, `work_narration`,
`customer_confirmation_received`, `closed_by`, `closure_date`

### 4.6 Stage Layer (programmatic — `setup/service_stages.py`)
`service_flow_type` (11 flows), `current_service_stage` (46 stages),
`next_action` (27 actions), `next_action_owner`, `next_action_role`,
`stage_due_at`, `pre_overdue_alert_at`, `overdue_status`, `escalation_level`,
`customer_informed`, `customer_informed_channel`, `customer_informed_at`,
`customer_informed_by`, `customer_promised_update_at`, `customer_promise_status`,
`promise_breach_reason`

### 4.7 Follow-up Tracking (programmatic — `setup/followup_fields.py`)
`service_path`, `followup_stage`, `service_charge_type`,
`customer_satisfaction_status`, `customer_informed_status`,
`last_service_center_followup`, `last_followup_summary`, `last_followup_at`,
`no_update_count`, `part_required`, `part_name`, `part_expected_date`,
`part_delay_reason`, `customer_informed_about_part_delay`,
`estimated_amount`, `customer_approved_amount`, `technician_payable`,
`commission_amount`, `payment_status`

### 4.8 AI Advisory (programmatic — `setup/ai_fields.py`)
`ai_review_status`, `ai_suggested_next_action`, `ai_risk_reason`,
`ai_manager_summary`, `ai_suggested_customer_message`, `ai_advisory_source`,
`ai_last_reviewed_at`, `ai_reviewed_by`

---

## 5. API Endpoints (whitelisted)

All endpoints are `@frappe.whitelist()`. POST endpoints are marked with `[POST]`.

### 5.1 Stitch Console (`api/stitch_console.py`) — 7 endpoints

| Endpoint | Method | Purpose | Key params |
|----------|--------|---------|------------|
| `get_ticket_list` | GET | Paginated ticket list | search, status, start (default 0), page_length (default 30, max 100) |
| `get_ticket_detail` | GET | Full ticket detail for drawer | ticket_id |
| `get_ticket_activity` | GET | Merged timeline (notes + system changes) | ticket_id, limit (default 50, max 100) |
| `add_ticket_note` | POST | Add internal note | ticket_id, note |
| `get_new_ticket_options` | GET | Brand/product/ticket type options | — |
| `create_ticket` | POST | Staff-side ticket creation | customer_name, mobile, complaint_details, product_type, brand, +optional |
| `set_customer_promise` | POST | Record/cancel customer promise | ticket_name, promised_at, status (Kept/Clear/datetime) |
| `schedule_appointment` | POST | Schedule site visit | ticket_name, appointment_datetime, technician, notes |

### 5.2 Workflow Actions (`api/workflow_actions.py`) — 17 endpoints

| Endpoint | Method | Purpose | Key params |
|----------|--------|---------|------------|
| `register_brand_complaint` | POST | Register with brand | ticket_name, brand_ticket_number, registration_date, next_follow_up_date, service_center |
| `need_invoice_from_customer` | POST | Request invoice | ticket_name, next_follow_up_date, note |
| `follow_up_service_center` | POST | Log SC follow-up | ticket_name, follow_up_result, next_follow_up_date |
| `waiting_for_part` | POST | Mark part pending | ticket_name, pending_reason, next_follow_up_date |
| `mark_product_ready` | POST | Mark ready for pickup | ticket_name, next_follow_up_date |
| `customer_confirmed` | POST | Close with customer OK | ticket_name, work_narration, closure_type |
| `close_ticket` | POST | Close ticket | ticket_name, work_narration, closure_type, customer_confirmation_received |
| `create_product_receipt` | POST | Create receipt | ticket_name, accessories_received, physical_condition, product_type, brand, model_no, serial_no |
| `verify_technician_called` | POST | Verify tech called | ticket_name, technician_name, notes |
| `verify_technician_visit` | POST | Verify tech visited | ticket_name, technician_name, visit_result, notes |
| `record_sc_followup` | POST | Record SC follow-up | ticket_name, follow_up_result, next_follow_up_date, customer_informed_status |
| `inform_customer` | POST | Log customer contact | ticket_name, message, channel |
| `mark_no_update` | POST | Escalate on no update | ticket_name, notes |
| `escalate_case` | POST | Escalate manually | ticket_name, reason |
| `record_satisfaction` | POST | Log satisfaction | ticket_name, satisfaction_status, notes |
| `record_customer_approval` | POST | Log cust approval | ticket_name, approved_amount, payment_status, notes |
| `get_current_user_roles` | GET | Role info | — |

### 5.3 Customer Intake (`api/customer_intake.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `lookup_customer_by_mobile` | GET | Find customer by phone (profile→ticket→not found) |

### 5.4 Qr Intake (`api/qr_intake.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `get_qr_intake_options` | GET | Field options for QR form |
| `submit_qr_complaint` | POST | Guest complaint intake |

### 5.5 Overrides (`overrides/client.py`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `lavanya_service.overrides.client.get` | — | Overrides frappe.client.get for HD Ticket |
| `lavanya_service.overrides.client.get_ticket` | — | Overrides helpdesk get_one |
| `lavanya_service.overrides.client.get_ticket_customizations` | — | Overrides helpdesk get_ticket_customizations |

---

## 6. Quick Actions (16 backend functions)

All in `workflow/quick_actions.py`. Each independently enforces role, status, required fields.

| Function | Allowed Roles | Statuses | Key result |
|----------|--------------|----------|------------|
| `register_brand_complaint` | Manager, Coordinator | non-final | status=Brand Registered |
| `need_invoice_from_customer` | Manager, Coordinator, Agent | non-final | status=Waiting on Customer |
| `follow_up_service_center` | Manager, Coordinator, Agent | non-final | status based on result |
| `waiting_for_part` | Manager, Coordinator, Agent | non-final | status=Waiting on Part / Approval |
| `mark_product_ready` | Manager, Coordinator, Front Desk | non-final | status=Ready for Pickup |
| `customer_confirmed` | Manager, Coordinator | non-final | status=Closed |
| `close_ticket` | Manager, Coordinator | non-final | status=Closed (requires satisfaction) |
| `create_product_receipt` | Manager, Coordinator, Front Desk | non-final, "Customer Product at Store" type, no existing receipt | Receipt created |
| `verify_technician_called` | Manager, Coordinator | non-final | followup_stage=technician_called |
| `verify_technician_visit` | Manager, Coordinator | non-final | followup_stage=technician_visited |
| `record_sc_followup` | Manager, Coordinator | non-final | followup_stage=sc_followup_done |
| `inform_customer` | Manager, Coordinator, Agent | non-final | customer_informed=Yes |
| `mark_no_update` | Manager, Coordinator | non-final | escalation_level incremented |
| `escalate_case` | Manager, Coordinator | non-final | escalation_level incremented |
| `record_satisfaction` | Manager, Coordinator | non-final | satisfaction recorded |
| `record_customer_approval` | Manager, Coordinator | non-final | amount recorded |

**Bypass roles:** System Manager (can run any action)
**Final statuses (blocked):** Closed, Cancelled

---

## 7. Stage Rules (`stage_rules.py`)

### 7.1 Service Flow Types (11)
Customer Complaint - Site, Customer Product at Store, Installation / Demo,
Periodic / Free Service, Stock Complaint, Out of Warranty Local Service,
Extended Warranty Claim, Replacement / Exchange, Refund Case,
Finance Sale Service Issue, Reopened / Repeat Complaint

### 7.2 Service Stages (46)
From Complaint Received → Details Pending → Warranty Check Pending → Brand Registration Pending →
Brand Registered → Service Center Follow-up → Extended Warranty Check Pending →
Claim Registration Pending → Provider Follow-up → Provider Denied →
Technician Visit Pending → Technician Visited - Issue Pending →
Spare Pending → Estimate Approval Pending → Customer Not Reachable → Waiting on Customer →
Product Received at Store → Handed to Service Center → Returned to Store → Ready for Pickup →
Delivered to Customer → Installation Registration Pending → Installation Technician Visit Pending →
Installation Completed → Periodic Service Due → Customer Contact Pending → Service Scheduled →
Feedback Pending → Stock Proof Pending → Supplier Follow-up Pending → Credit Note Pending →
Replacement Pending → Stock Decision Pending → Customer Verification Pending →
Closure Confirmation Pending → Closed → Cancelled

### 7.3 Next Actions (27)
Check Warranty, Request Missing Details, Register with Brand, Follow up Service Center,
Schedule Technician Visit, Await Technician Visit, Order Spare / Part, Await Approval,
Inform Customer, Call Customer, Await Customer Response, Verify with Customer,
Confirm Closure, Collect Payment, Register Extended Warranty Claim, Follow up Provider,
Request Documents, Capture Proof, Follow up Supplier, Hand to Service Center,
Mark Returned to Store, Mark Ready for Pickup, Deliver to Customer, Schedule Service,
Record Feedback, Reschedule Follow-up, Manager Override

### 7.4 Terminal Stages
`Closed`, `Cancelled`

### 7.5 Ticket Type → Flow Mapping
```
Customer Complaint - Site → Customer Complaint - Site
Customer Product at Store → Customer Product at Store
Stock Complaint → Stock Complaint
Installation / Demo → Installation / Demo
Replacement / DOA → Replacement / Exchange
Out of Warranty Local Service → Out of Warranty Local Service
Free Service → Periodic / Free Service
```

### 7.6 Stage SLA (minutes)
Stage-specific SLA used by reminder engine for Due-Soon/Overdue calculation.
SLA ranges: 30 min (Complaint Received) → 24h (Brand Registered, Service Center Follow-up, etc.)
Default SLA: 24h
Pre-overdue lead times: graduated by SLA bucket (10 min for 30-min SLA, up to 4h for 24h+ SLA).

---

## 8. Scheduler Jobs

### Hourly
- `tasks/reminder_refresh.refresh_active_ticket_reminders` — persist computed
  reminder state (stage_due, pre-overdue, escalation, promise breach) for active
  tickets. Idempotent, batched (50/txn), max 500 tickets.

### Daily
- `reminders/notification_output.run_daily_reminder_notifications_dry_safe`
- `reminders/notification_output.run_escalation_notifications_dry_safe`

---

## 9. Tests (29 modules)

All tests are plain `run()` functions (not `test_*`), executed via bench console.

| Module | Focus | Count |
|--------|-------|-------|
| `acceptance_phase1` | Phase 1 acceptance criteria | — |
| `ai_advisory` | AI advisory engine | — |
| `customer_intake` | Customer lookup + profile sync | — |
| `e2e_followup_scenario` | Full follow-up scenario | — |
| `frappe_ui_console` | Frappe UI console | — |
| `fresh_install_integrity` | Fresh install checks | — |
| `intake_masters` | Brand/Category/Item CRUD | — |
| `phone_normalization` | Phone number normalization | — |
| `pilot_readiness` | Pilot readiness | — |
| `product_receipt_ux` | Product receipt UX | — |
| `production_readiness` | Production readiness | — |
| `qr_intake` | QR complaint intake | — |
| `reminder_engine` | Rule resolution engine | 21 |
| `reminder_refresh` | Scheduler persistence | 14 |
| `repeat_detection` | Repeat complaint detection | — |
| `reports_dashboard` | Report queries | — |
| `role_browser_uat_permissions` | Role/permission UAT | — |
| `scheduler_and_sla` | Scheduler + SLA | — |
| `stage_layer` | Stage layer defaults | — |
| `stitch_console_actions` | SPA action endpoints | — |
| `stitch_console_spa` | SPA data endpoints | — |
| `system_pushed_notifications` | Notifications | — |
| `ticket_template_integrity` | Template integrity | — |
| `today_work_page` | Today's Work page | — |
| `today_work` | Today's Work logic | 24 |
| `warranty_recommendation` | Warranty recommendation | — |
| `workflow_quick_actions` | Quick action functions | — |

---

## 10. Roles (5 custom roles)

| Role | Abbreviation | Quick actions | Today's Work groups |
|------|-------------|---------------|---------------------|
| Lavanya Manager | Manager | All 16 | All 17 |
| Lavanya Service Coordinator | Coordinator | All 16 | All 17 |
| Lavanya Helpdesk Agent | Agent | Need Invoice, Follow Up SC, Waiting for Part, Inform Customer | overdue/due-today/registration-pending/waiting-customer/waiting-part/technician-call/technician-visit/no-update/customer-not-informed/escalated/satisfaction-pending |
| Lavanya Front Desk | Front Desk | Create Product Receipt, Product Ready | ready-for-pickup/receipt-missing/new-complaints |
| Lavanya Viewer | Viewer | None | All 17 (read-only) |

**Defined in:** `fixtures/role.json`

---

## 11. Permissions Architecture

### 11.1 Permlevel System
- **Permlevel 0:** Default — most fields
- **Permlevel 1:** Service coordination fields — Manager, Agent, Coordinator can write;
  Front Desk, Viewer read-only
- **Permlevel 2:** Closure control fields — Manager, Coordinator can write; Agent read-only;
  Front Desk none; Viewer read-only

### 11.2 Permlevel 1 Fields (17)
`manufacturer_registration_required`, `manufacturer_registered`, `brand_ticket_number`,
`registration_date`, `registration_pending_reason`, `brand_registration_recommended`,
`brand_registration_override_reason`, `brand_registration_recommended_at`, `service_center`,
`local_technician`, `is_repeated_complaint`, `previous_ticket_link`, `pending_reason`,
`next_follow_up_date`, `service_product_receipt`, `work_narration`

### 11.3 Permlevel 2 Fields (4)
`closure_type`, `customer_confirmation_received`, `closed_by`, `closure_date`

### 11.4 Quick Action Permission Bypass
Quick actions set `doc.flags.ignore_lavanya_field_guard = True` before saving,
bypassing permlevel checks. This is safe because each action independently enforces
role checks. **Never honored for Guest** (public QR endpoint cannot exploit it).

### 11.5 "All" Role Restriction
HD Ticket read=1, write=0, create=0, delete=0, print=1 — everyone can read,
but cannot write/create/delete without explicit role.

---

## 12. Validation Rules

### 12.1 HD Ticket Validations (on save)
- **Phone normalization** — automatically normalizes Indian mobile numbers (10 digits)
- **Protected field permissions** — blocks unauthorized writes to service coordination
  and closure control fields (unless bypass flag set)
- **Brand registration recommendation** — auto-flags in-warranty tickets needing brand registration
- **Brand registration validation** — Brand Registered status requires ticket number + date
- **Brand registration override** — if skipping recommended registration, reason required
- **Follow-up validation** — certain statuses require pending_reason + next_follow_up_date
- **Serial number validation** — Customer Product at Store and Replacement/DOA require serial_no
- **Closure validation** — Closed status requires closure_type + work_narration + confirmation

### 12.2 Service Product Receipt Validations
- Validates receipt fields
- Enforces custody log completeness

### 12.3 Customer Profile Validations
- Primary mobile must be valid Indian mobile (10 digits, starts with 6/7/8/9)
- Normalized on save automatically

**Source files:**
- `validations/hd_ticket.py` (420 lines)
- `validations/service_receipt.py`
- `api/customer_intake.py:normalize_customer_profile_phone_numbers`

---

## 13. Override Class

`LavanyaHDTicket(HDTicket)` in `overrides/hd_ticket.py`:

- `before_validate()` — normalize phone numbers
- `validate()` — validate_ticket() + assign_defaults() (stage layer)
- `on_update()` — sync_customer_profile_from_ticket()
- `validate_higher_perm_levels()` — protected field permissions
- `db_insert()` / `db_update()` — protected field permissions

---

## 14. Setup Steps (idempotent install/migrate)

Executed in order by `setup/install.py:ensure_lavanya_service_setup()`:

1. Create custom DocTypes + seed brand masters
2. Create Service Product Receipt + Custody Log Entry DocTypes
3. Create Lavanya Customer Profile DocType
4. Configure HD statuses, priorities, types
5. Create Product Category + Item DocTypes + HD Ticket link fields
6. Configure default ticket template fields
7. Create Default SLA
8. Configure runtime defaults
9. Fix HD Ticket "All" permission (read-only)
10. Ensure SLA defaults

Additional post-install hooks:
- `setup/appointment.py` — Lavanya Service Appointment DocType
- `setup/service_stages.py` — Stage layer fields
- `setup/reminder_rule.py` — Reminder Rule DocType
- `setup/ai_fields.py` — AI advisory fields
- `setup/followup_fields.py` — Follow-up tracking fields

---

## 15. Today's Work Groups (17 buckets)

| Key | Label | Priority | Visible to |
|-----|-------|----------|------------|
| overdue_follow_up | Overdue Follow-up | 1 | All |
| no_technician_update | No Technician Update | 2 | Agent+Manager+Coord |
| escalated_cases | Escalated Cases | 3 | Agent+Manager+Coord |
| customer_not_informed | Customer Not Informed | 4 | Agent+Manager+Coord |
| technician_call_due | Technician Call Verification Due | 5 | Agent+Manager+Coord |
| technician_visit_due | Technician Visit Verification Due | 6 | Agent+Manager+Coord |
| due_today | Due Today | 7 | All |
| registration_recommended | Registration Recommended | 8 | All |
| registration_pending | Registration Pending | 9 | All |
| waiting_on_customer | Waiting on Customer | 10 | All |
| waiting_on_part | Waiting on Part / Approval | 11 | All |
| ready_for_pickup | Ready for Pickup | 12 | All |
| customer_satisfaction_pending | Customer Satisfaction Pending | 13 | Agent+Manager+Coord |
| product_receipt_missing | Product Receipt Missing | 14 | All (Front Desk focus) |
| closure_pending | Closure Pending | 15 | All |
| new_complaints | New Complaints | 16 | All |
| upcoming_work | Upcoming Work | 17 | All |

---

## 16. Important Considerations

### 16.1 Phone Normalization
- Normalizes Indian mobile numbers: strips +91, 0 prefix, non-digit chars
- Validates: 10 digits, starts with 6/7/8/9, not all same digit
- Raw + normalized stored in separate fields on HD Ticket + Customer Profile
- Normalized phone is the de facto customer identifier

### 16.2 Stage Layer vs. Status
- The stage layer (`service_flow_type` / `current_service_stage` / `next_action`) is a
  **layer above** Helpdesk status. It does NOT replace status.
- Today's Work classification is driven by **status** (not stage).
- Stage fields are used for Due-Soon/Overdue calculation and the drawer display.

### 16.3 Reminder Engine
- Rule-first approach (not AI-first)
- Specificity scoring: brand 20, stage 20, product 15, ticket-type 15, flow 10,
  warranty-route 10, pending-reason 10, priority 10
- **Dry-run only** as of June 2026 — computed state persisted hourly but no
  notifications sent (notification_output.py is dry-run safe)

### 16.4 Two Surfaces Coexist
- Standard Helpdesk Desk (full operations)
- Vue SPA at `/frontend` (Stitch console — additive, not replacement)

### 16.5 Cross-platform Build
- `node_modules` is installed for Windows host (not container)
- SPA build: `cd frontend && node node_modules/vite/bin/vite.js build`
- Built assets: `lavanya_service/public/frontend/assets/` (untracked)
- Serve page: `lavanya_service/www/frontend.html` (auto-synced, committed)

### 16.6 Production SLA Config
- Working days: Monday–Saturday, 09:30–20:30
- Default priority: Medium
- Priority targets: Urgent (2h response/24h resolution), High (4h/48h),
  Medium (8h/72h), Low (24h/120h)

---

## 17. Fixtures (exported via hooks.py)

| Fixture | Records |
|---------|---------|
| DocType | 9 custom doctypes |
| Custom Field | 85 HD Ticket fields |
| Client Script | HD Ticket form scripts |
| HD Ticket Status | 10 statuses |
| HD Ticket Priority | 4 priorities |
| HD Ticket Type | 7 types |
| HD Service Level Agreement | Lavanya Default |
| HD Ticket Template | Default |
| HD Settings | HD Settings |
| HD View | 12 Lavanya views |
| HD Form Script | 7 form scripts |
| Role | 5 roles |
| Custom DocPerm | Permissions for all roles + doctypes |
| Print Format | Lavanya Service Product Receipt Token |

**JSON files in** `fixtures/` directory.

---

## 18. Import Map (what imports what from where)

```
validations/hd_ticket.py ← overrides/hd_ticket.py (validate_ticket, normalize_ticket_phone_numbers)
validations/hd_ticket.py ← workflow/quick_actions.py (validate_ticket)
stage_rules.py ← overrides/hd_ticket.py (assign_defaults)
stage_rules.py ← workflow/today_work.py (compute_overdue_status, compute_promise_status)
stage_rules.py ← api/stitch_console.py (compute_overdue_status, compute_promise_status, flow_for_ticket_type)
reminder_engine.py ← workflow/today_work.py (derive_escalation_level, refresh_ticket_reminder_state, get_active_rules)
reminder_engine.py ← api/stitch_console.py (refresh_ticket_reminder_state, derive_escalation_level, get_active_rules)
utils/phone.py ← api/customer_intake.py (normalize_phone, normalized_mobile)
utils/phone.py ← validations/hd_ticket.py (normalize_phone)
api/customer_intake.py ← overrides/hd_ticket.py (sync_customer_profile_from_ticket)
workflow/quick_actions.py ← api/workflow_actions.py (all 16 functions)
```

**Critical dependency chain:**
`stage_rules.py` → `today_work.py` → `reminder_engine.py` → `stitch_console.py`
(Changes to `stage_rules.py` must be verified across ALL downstream consumers.)

---

## 19. URL Routes

| Route | Controller | Purpose |
|-------|-----------|---------|
| `/frontend` | `www/frontend.py` + `www/frontend.html` | SPA entry (no-cache) |
| `/frontend/<path:app_path>` | route rule → `/frontend` | SPA sub-routes |
| `/qr-complaint` | route rule → `qr_complaint` | QR intake form |

**Source:** `hooks.py:website_route_rules`
