# Lavanya eMart Real-World Ticket System Implementation Plan

Date: 2026-06-16
Repository: `collinsfoam-a11y/lavanya_service`

## 1. Objective

Upgrade the current Lavanya Helpdesk customization into a real showroom service control room for a multi-brand electronics and home appliances outlet.

Target workflow:

`Customer -> Product -> Complaint -> Brand Registration -> Follow-up -> Resolution -> Customer Confirmation -> Feedback -> Performance Report`

The main business goal is to prevent missed follow-ups, lost brand complaint numbers, weak warranty verification, and unclear staff ownership.

## 2. Current baseline

The repository already has a strong foundation:

- Helpdesk app dependency.
- `HD Ticket` override through `LavanyaHDTicket`.
- Server-side ticket validation.
- Indian mobile normalization.
- Customer profile lookup and sync.
- QR complaint intake.
- Brand/product controlled intake.
- Service Product Receipt and custody tracking.
- Role-based field filtering.
- SLA and permission setup helpers.

The missing layer is operational execution: Today’s Work, scheduled escalation, communication logs, WhatsApp updates, warranty proof workflow, branch/counter accountability, and owner dashboards.

## 3. Implementation principles

1. Backend validation is mandatory.
2. Setup must be idempotent.
3. Staff should not remember next actions manually.
4. Every follow-up must have a system trace.
5. Public QR intake must remain narrow and validated.
6. Customer-visible references must be unique.
7. Static lists should gradually move to master data.
8. Reports must show owner-level risk clearly.

## 4. Phase 1 — Setup hardening and core fields

### 4.1 Unify setup orchestration

Problem: `setup/install.py` runs only part of the available setup functions. Some setup logic appears outside the main install/migrate chain.

Tasks:

- Expand `_steps()` in `lavanya_service/setup/install.py`.
- Include all required idempotent setup functions.
- Ensure HD Ticket custom fields, customer intake scripts, product master scripts, masters, permissions, and SLA setup are applied from one orchestration path.
- Add setup verification output.

Acceptance criteria:

- Fresh install works without manual correction.
- `bench migrate` can run repeatedly without duplicate records.
- Required DocTypes, custom fields, form scripts, and views exist after migration.

### 4.2 Add missing HD Ticket fields

Add these fields:

| Field | Type | Purpose |
|---|---|---|
| public_reference | Data | Customer-safe ticket reference |
| branch | Link | Multi-showroom readiness |
| counter | Select / Link | Counter accountability |
| product_location | Select | Home / showroom / service center |
| invoice_no | Data | Brand registration support |
| invoice_attachment_status | Select | Invoice proof workflow |
| warranty_end_date | Date | Warranty calculation |
| warranty_verified | Check | Verified warranty state |
| warranty_verified_by | Link User | Audit |
| next_action | Select | Work queue action |
| next_action_owner | Link User | Ownership |
| escalation_level | Select | Escalation control |
| last_customer_update_at | Datetime | Customer communication SLA |
| brand_last_contacted_at | Datetime | Brand follow-up SLA |
| service_center_last_contacted_at | Datetime | Service-center SLA |

### 4.3 Unique public reference

Problem: QR intake currently returns a non-unique reference format based on mobile last digits.

Tasks:

- Generate a unique public reference such as `LV-TKT-.YYYY.-.#####`.
- Return it from QR submission.
- Add search support by public reference.

Acceptance criteria:

- Every ticket has a unique public reference.
- QR users receive a usable reference.
- Staff can find the ticket by that reference.

## 5. Phase 2 — Today’s Work and follow-up engine

This is the highest-priority phase.

### 5.1 Scheduler tasks

Enable scheduler events in `hooks.py`.

Create tasks:

- `mark_overdue_followups`
- `update_escalation_levels`
- `create_daily_manager_digest`

Acceptance criteria:

- Scheduler runs without errors.
- Tasks are idempotent.
- No duplicate daily digest records.

### 5.2 Today’s Work API

Create API:

`lavanya_service.api.work_queue.get_todays_work`

Return tickets where:

- `next_follow_up_date <= today`
- status is not Closed or Cancelled
- pending reason exists

Group by:

- overdue
- due today
- registration pending
- brand ticket pending
- spare pending
- ready for pickup
- customer not reachable

Acceptance criteria:

- Staff see only relevant assigned work.
- Manager sees all pending work.
- Owner dashboard can consume the same API.

### 5.3 HD Views to seed

Create views:

1. Today’s Follow-up
2. Overdue Follow-up
3. Registration Pending
4. Brand Ticket Number Pending
5. Spare Pending
6. Product at Store
7. Ready for Pickup
8. Repeat Complaints
9. Closed Without Confirmation
10. Manager Escalation

### 5.4 Escalation rules

| Condition | Escalation |
|---|---|
| Follow-up overdue 1 day | Coordinator |
| Overdue 2 days | Manager |
| Overdue 4 days | Owner |
| Spare pending 3 days | Manager |
| Product at store over 7 days | Manager |
| Repeat complaint within 7 days | Manager |

## 6. Phase 3 — Structured activity log

Create child table:

`Lavanya Ticket Activity Log`

Fields:

| Field | Type |
|---|---|
| action_datetime | Datetime |
| action_type | Select |
| channel | Select |
| actor | Link User |
| contacted_party | Select |
| contact_person | Data |
| outcome | Select |
| customer_visible_note | Small Text |
| internal_note | Small Text |
| next_follow_up_date | Date |
| next_action | Select |

Action types:

- Customer Called
- Customer Not Reachable
- WhatsApp Sent
- Brand Registered
- Brand Line Busy
- Service Center Contacted
- Technician Assigned
- Technician Visited
- Part Pending
- Estimate Shared
- Customer Approved Estimate
- Ready for Pickup
- Customer Collected
- Closure Confirmed
- Negative Feedback

Acceptance criteria:

- Every quick action appends a log row.
- Log rows update last customer/brand/service-center contact timestamps.
- Normal staff cannot rewrite old logs.

## 7. Phase 4 — Quick actions

Add backend APIs and Helpdesk form actions:

- Mark Brand Registered
- Brand Line Busy
- Customer Called
- Customer Not Reachable
- Service Center Contacted
- Part Pending
- Ready for Pickup
- Customer Collected
- Close With Confirmation

Each quick action must:

- check role permission
- update status
- update pending reason
- update next follow-up date
- append activity log
- update relevant timestamp

## 8. Phase 5 — Warranty and invoice verification

### 8.1 Warranty calculation

Tasks:

- Add `warranty_end_date`.
- Use product item default warranty months.
- Calculate warranty status suggestion from purchase date.
- Allow manager override with reason.

### 8.2 Invoice proof workflow

Tasks:

- Add invoice number.
- Add invoice proof status.
- Add invoice attachment requirement for in-warranty brand-backed cases.
- Add optional invoice upload to QR form.

Acceptance criteria:

- Brand registration cannot be marked complete without proof or override.
- Warranty decisions are auditable.

## 9. Phase 6 — WhatsApp/customer communication

Create DocType:

`Lavanya WhatsApp Message Log`

Fields:

| Field | Type |
|---|---|
| ticket | Link HD Ticket |
| customer_mobile | Data |
| template_name | Data |
| message_type | Select |
| status | Select |
| provider_message_id | Data |
| sent_at | Datetime |
| failure_reason | Small Text |

Message events:

1. Ticket acknowledgement
2. Brand registration pending
3. Brand ticket registered
4. Technician visit pending
5. Spare pending
6. Ready for pickup
7. Closure confirmation
8. Feedback request

Acceptance criteria:

- Every outbound message is logged.
- Failed messages appear in a report.
- Manager/coordinator can manually resend.

## 10. Phase 7 — Product-at-store strengthening

Tasks:

- Add receipt print format.
- Add customer signature/photo proof field.
- Add accessories checklist.
- Add physical condition checklist.
- Enforce expected return date.
- Add customer pickup confirmation.
- Block ticket closure unless custody status is delivered/collected/cancelled.

Acceptance criteria:

- Every product received at store has custody tracking.
- Product handover history is clear.
- Ready-for-pickup and delivered states are reportable.

## 11. Phase 8 — Repeat complaint intelligence

Rules:

- Same mobile + product + brand within 30 days.
- Same serial number within 180 days.
- Complaint after service within 7 days.

Tasks:

- Add `detect_repeated_complaint(doc)`.
- Auto-set repeated complaint flag.
- Auto-link previous ticket.
- Escalate repeat cases to manager.

Acceptance criteria:

- Repeat cases are flagged automatically.
- Manager view shows repeat cases.
- Closure requires stronger narration for repeat complaints.

## 12. Phase 9 — Reports and dashboard

Create reports:

1. Pending Tickets by Age
2. Pending by Brand
3. Pending by Service Center
4. Pending by Product Type
5. Spare Pending
6. Registration Pending
7. Product at Store Custody
8. Ready for Pickup
9. Repeat Complaints
10. SLA Breach
11. Closed Without Confirmation
12. Brand Performance
13. Staff Follow-up Performance
14. Customer Feedback

Owner dashboard cards:

| Metric | Purpose |
|---|---|
| Open tickets | Workload |
| Overdue tickets | Risk |
| Registration pending | Brand action gap |
| Spare pending | Delay risk |
| Product at store | Custody risk |
| Repeat complaints | Quality issue |
| Closed today | Productivity |
| Negative feedback | Reputation risk |

## 13. Phase 10 — Master data expansion

### Product categories to add

- Fan
- Iron Box
- Geyser
- Oven / OTG
- Microwave Oven
- Grinder
- Wet Grinder
- Juicer
- Kettle
- Cooker
- Flask
- Cookware
- Speaker / Audio
- Stabilizer
- Inverter / UPS
- Small Appliance
- Kitchenware

### Brand master fields to maintain

- toll-free number
- WhatsApp number
- portal URL
- dealer code
- escalation contact
- service center
- default SLA
- free service support
- notes

## 14. Phase 11 — Tests and README

Tests required:

- QR valid submission
- QR invalid mobile
- QR invalid brand/product
- QR rate limit
- public reference uniqueness
- phone normalization
- customer profile sync
- duplicate mobile conflict handling
- brand registered required fields
- follow-up required fields
- closure required fields
- protected field guard
- quick action permissions
- scheduler idempotency
- setup idempotency

README additions:

- supported Frappe/Helpdesk version
- install command
- migration command
- role matrix
- QR URL
- scheduler setup
- test command
- setup verification checklist

## 15. Sprint execution order

### Sprint 1

- Setup orchestrator hardening
- Public reference
- Branch/counter/product location
- Today’s Work API
- Scheduler events
- Overdue escalation
- HD Views

### Sprint 2

- Activity log
- Quick action APIs
- Quick action form script
- Repeat complaint baseline

### Sprint 3

- Invoice fields
- Warranty calculation
- QR invoice/photo upload
- Brand registration proof enforcement
- Master data expansion

### Sprint 4

- WhatsApp message log
- Message template events
- Manual resend
- Failure report

### Sprint 5

- Owner dashboard
- Script reports
- Staff performance reports
- README
- Tests
- Fresh-site hardening verification

## 16. Non-goals for first release

Do not prioritize these before the follow-up engine is stable:

- full AI chatbot
- complex customer portal
- ERP/POS billing integration
- advanced technician mobile app
- automated brand portal submission

## 17. Definition of done

The system is pilot-ready when:

1. Every ticket has customer, product, complaint, source, and next action.
2. Every pending ticket has pending reason and next follow-up date.
3. Overdue tickets appear automatically.
4. Manager can see service risk in one view.
5. Brand registration is controlled.
6. Closure requires customer confirmation.
7. Product-at-store cases have custody history.
8. QR gives a unique public reference.
9. Repeat complaints are flagged.
10. Fresh install and migrate are idempotent.
