# Lavanya eMart Real-World Ticket System Gap Audit

Date: 2026-06-16
Repository: `collinsfoam-a11y/lavanya_service`
Business context: Lavanya eMart is a multi-brand electronics and home appliances showroom. Service work includes phone complaints, WhatsApp complaints, direct visits, QR customer intake, installation/demo requests, stock complaints, in-store product handover, brand service registration, spare follow-up, customer closure confirmation, and escalation.

## 1. Executive verdict

The repository is no longer a generic helpdesk add-on. It already contains a strong showroom-service foundation: custom HD Ticket fields, customer identity capture, phone normalization, brand registration control, service product receipt/custody tracking, QR customer intake, role-based field filtering, and install/migrate seeders.

However, it is not yet a full real-world Lavanya eMart service control room. The missing layer is operational execution: task queues, follow-up scheduler, WhatsApp/customer communication log, SLA ageing escalation, brand/service-center performance reports, owner dashboards, repeated-complaint intelligence, invoice/warranty verification workflow, and automated closure confirmation.

## 2. Pros already present

### 2.1 Fresh install and migration hardening

- `hooks.py` requires the Helpdesk app and wires `after_install` and `after_migrate` to a unified setup routine.
- `setup/install.py` explicitly makes setup idempotent and avoids creating users, agents, tickets, customer profiles, product receipts, or outbound side effects during install.
- This is correct architecture for Frappe/Helpdesk because metadata fixtures alone can fail on fresh sites when custom DocTypes are not fully visible.

### 2.2 HD Ticket override is in the right place

- `override_doctype_class` replaces `HD Ticket` with `LavanyaHDTicket`.
- The override normalizes phone numbers before validation, applies ticket validation, syncs the customer profile after update, and enforces protected-field permissions at `validate_higher_perm_levels`, `db_insert`, and `db_update`.
- This is a strong backend guardrail. It prevents relying only on frontend hiding or read-only fields.

### 2.3 Customer identity logic is stronger than a normal helpdesk

- Phone numbers are normalized to Indian 10-digit mobile numbers.
- Raw values are preserved separately.
- Customer profile lookup supports primary and alternate mobile numbers.
- Ticket history can be used to autofill customer name, alternate mobile, address, pincode, last product type, and last brand.
- `Lavanya Customer Profile` uses `LV-CUST-.#####`, which matches the earlier customer identity requirement.

### 2.4 Brand service workflow is already partly modeled

- Ticket fields include brand, product type, model number, serial number, purchase source, purchase date, warranty status, manufacturer registration requirement, manufacturer registered status, brand ticket number, registration date, registration pending reason, service center, local technician, pending reason, next follow-up date, closure type, work narration, and customer confirmation.
- Validation requires a brand ticket number and registration date when status is `Brand Registered`.
- In-warranty cases can trigger brand registration recommendation.
- Closed tickets require closure type, work narration, and customer confirmation.

### 2.5 QR customer intake is production-conscious

- The QR endpoint validates required fields server-side.
- It checks brand and product type against controlled values.
- It rate-limits by normalized mobile and IP.
- It uses a honeypot field to suppress bots.
- It returns a safe acknowledgement instead of exposing internal ticket names.
- It avoids explicit manual commit and relies on the request lifecycle.

### 2.6 In-store product receipt is a major operational win

- `Service Product Receipt` models customer product custody.
- It has custody statuses such as received at store, handed to service center, with local technician, returned to store, ready for pickup, delivered to customer, and cancelled.
- It tracks accessories, physical condition, estimated/approved/final cost, approval requirement, approval received, and custody log.
- This directly supports showroom realities for mixers, induction cookers, TVs, small appliances, and products physically received at the counter.

### 2.7 Role-based UI filtering exists

- `overrides/client.py` filters which custom fields are returned to Helpdesk frontend users.
- Front Desk gets intake fields.
- Helpdesk Agent gets intake and service coordination fields.
- Manager and Service Coordinator get full service and closure fields.
- Viewer gets read-only intake fields.

## 3. Cons and risks found

### 3.1 Install flow does not appear to run all available configuration modules

`setup/install.py` currently runs supporting masters, service receipt DocTypes, customer profile DocType, product category/item DocTypes, permission fixes, and SLA fixes. It does not call the available configurators for:

- `create_hd_ticket_custom_fields()` from `setup/hd_ticket_fields.py`
- `configure_customer_intake()` from `setup/customer_profile.py`
- `configure_intake_masters()` from `setup/intake_masters.py`

This may be intentional if these are installed via fixtures, but it creates a hardening gap. The repository has multiple code-based setup functions, yet the unified installer only calls part of them. Fresh-site behavior should be deterministic.

Recommended change: create a single `setup/orchestrator.py` or expand `_steps()` to include every idempotent setup function after making all of them safe against duplicate rows and protected Helpdesk defaults.

### 3.2 Product taxonomy is still too narrow for Lavanya eMart

The product type list covers AC, refrigerator, washing machine, mixer, induction cooker, chimney, hob, gas stove, TV, water purifier, and other. Lavanya eMart also sells many kitchen appliances and utensils/household products. The system should not force real complaints into `Other`.

Recommended additions:

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
- Small Appliance
- Kitchenware
- Home Appliance
- Audio / Speaker
- Stabilizer
- Inverter / UPS
- Furniture / Stand / Mount
- Other Kitchen Item

Better change: move product type from static Select to master-driven category/subcategory hierarchy. Static Select will become a maintenance bottleneck.

### 3.3 Brand master seed list is too small

Seed brands are only LG, Samsung, Whirlpool, Voltas, Preethi, Bajaj, Prestige, Crompton, Kent, and Faber. Lavanya showroom needs brands such as Lloyd, Daikin, Hitachi, Carrier, Blue Star, Haier, Panasonic, V-Guard, Butterfly, Havells, Usha, Philips, Pigeon, Sunflame, Kaff, Elica, Bosch, IFB, Godrej, Onida, Sony, Vu, TCL, Lloyd, and others.

Recommended change: add a `brand_seed.csv` or JSON fixture with service metadata: toll-free number, WhatsApp number, portal URL, dealer code, local service center, escalation contact, default SLA, free-service support, service coverage notes.

### 3.4 QR intake captures too little for real service registration

The QR form collects customer name, mobile, product type, brand, complaint details, complaint type, model number, serial number, address, pincode, and preferred callback time.

Missing fields for real manufacturer registration:

- Invoice number
- Purchase date
- Purchased from Lavanya: yes/no/unknown
- Invoice upload or photo proof
- Product location: customer home / showroom / service center
- Alternate mobile
- Landmark
- WhatsApp consent
- Service urgency
- Warranty card availability
- Installation/demo preferred date
- Product image upload
- Complaint image/video upload

Recommended change: add optional file attachments and invoice proof support. Without invoice proof, brand registration will still depend on manual follow-up.

### 3.5 QR safe reference is not unique enough

`safe_ref = LV-QR-last4digits` is customer-friendly but not unique. Multiple complaints from the same mobile will produce the same visible reference.

Recommended change: create a public reference field such as `LV-QR-.YYYY.-.#####` or return a masked version of the ticket name. Keep internal ticket names hidden if required, but the reference must be unique for customer follow-up.

### 3.6 Public QR endpoint uses Administrator context

The QR endpoint switches the session to Administrator to insert the ticket because Helpdesk creates a Communication and a Guest cannot save the ticket. This is operationally understandable, but it is a high-risk pattern if future code expands before validation.

Recommended change: create a dedicated disabled-login service user such as `qr.intake@lavanya.local` with only the minimum roles needed. Use a narrow service method with explicit allowlist fields. Add an audit field `intake_created_by_system = QR Intake`.

### 3.7 Follow-up dates are validated but not executed

Tickets require `pending_reason` and `next_follow_up_date` for follow-up statuses. But no scheduler is enabled in `hooks.py`. There is no automated daily job to push overdue tickets, escalate stale tickets, or generate Today’s Work.

Recommended change: add scheduler events:

- Hourly: mark overdue follow-ups and escalation flags.
- Daily morning: create Today’s Work queue for staff.
- Daily evening: notify manager for untouched overdue tickets.
- Daily: spare-pending and service-center-delayed digest.

### 3.8 No explicit action log for customer communication

Work narration exists, but a real service desk needs a structured log:

- Customer called
- Customer not reachable
- WhatsApp sent
- Brand registered
- Brand line busy
- Service center contacted
- Technician assigned
- Part pending
- Customer confirmed closure

Recommended change: add `Lavanya Ticket Activity Log` child table on HD Ticket with action type, channel, actor, datetime, next action, customer-visible note, internal note, and attachment.

### 3.9 No outbound WhatsApp/SMS/email automation layer

Lavanya’s real workflow depends heavily on WhatsApp and phone calls. The current code records service data, but does not automate acknowledgements or follow-up messages.

Recommended addon:

- WhatsApp acknowledgement after ticket creation.
- Brand registration pending message.
- Brand ticket number message.
- Ready for pickup message.
- Spare pending message.
- Closure confirmation message.
- Negative feedback escalation.

### 3.10 No owner dashboard or service control room

The model has fields for reporting, but no dashboard layer is visible.

Recommended dashboards:

- Today’s Follow-up
- Overdue Tickets
- Pending by Brand
- Pending by Service Center
- Pending by Age Bucket
- Spare Pending
- Registration Pending
- Product at Store Custody
- Ready for Pickup
- Repeated Complaints
- Closed Without Customer Confirmation

### 3.11 No separate workflows for ticket types

The validation recognizes ticket types, but real handling differs by type:

- Customer Complaint - Site
- Customer Product at Store
- Installation / Demo
- Replacement / DOA
- Stock Complaint
- Out of Warranty Local Service
- Free Service

Recommended change: define a workflow matrix. Each ticket type should have required fields, allowed statuses, required next action, default owner queue, SLA, and closure rule.

### 3.12 Warranty logic is still manual

Warranty status is a Select. Product items have default warranty months, but no code visibly calculates warranty status from purchase date + warranty months.

Recommended change:

- When product item + purchase date are set, calculate warranty end date.
- Add `warranty_end_date`.
- Add `warranty_source`: invoice, customer claim, ERP verified, unknown.
- Add manager override for doubtful warranty.

### 3.13 Local service cost flow is incomplete

Service Product Receipt has estimated, approved, and final cost, but there is no payment collection or approval ledger.

Recommended addon:

- Customer estimate approval record.
- Service cost collection status.
- Technician payout/commission status.
- Customer payment mode.
- Link to POS/cashier collection if implemented later.

### 3.14 Repeated complaint logic is manual

There is `is_repeated_complaint` and `previous_ticket_link`, but no automatic similarity detection.

Recommended change:

- Auto-detect repeat complaint by normalized mobile + brand + product type + serial number within 30/60/90 days.
- Flag repeat after service within 2 days as urgent.
- Auto-escalate to manager when repeated complaint is found.

### 3.15 Customer profile uniqueness may be too strict for family/alternate numbers

Primary mobile is unique. Alternate mobile is not unique. That is acceptable, but in retail, one mobile can represent a family or multiple purchases. The current design may create ambiguity if multiple customer profiles share a number as alternate.

Recommended change:

- Add household/company profile concept only if needed.
- Add customer merge tool.
- Add duplicate profile report.
- Add explicit primary/secondary owner relation if multiple names use one number.

### 3.16 Permission model needs branch/showroom readiness

The current roles are good for a single service team. Lavanya has multiple counters/floors and may operate more than one showroom/GST. There is no branch/store dimension in tickets.

Recommended fields:

- Store / Branch
- Floor / Counter
- Created By Counter
- Assigned Department
- GST entity / company if service crosses branches

### 3.17 No attachment governance

Real complaints need invoice photos, product photos, installation photos, service reports, estimate approvals, and return proof. No attachment policy is visible.

Recommended change:

- Required attachment rules by status.
- Attachment category field.
- Customer consent and privacy policy note.
- Maximum file size and allowed file types.

### 3.18 No migration/test matrix visible in README

README is too basic for a production helpdesk customization. It lacks Frappe/Helpdesk version, setup order, migrations, test commands, fixtures, roles, and expected seed results.

Recommended change: expand README with installation, migration, supported versions, setup verification checklist, role setup, sample test cases, and rollback notes.

## 4. Highest-priority changes

### Phase 1: Hardening before showroom pilot

1. Expand install orchestration so all required custom fields, templates, form scripts, masters, permissions, and SLA records are installed from one command.
2. Add unique public reference number for QR submissions.
3. Add branch/store/counter fields.
4. Add activity log child table.
5. Add Today’s Work view based on `next_follow_up_date`.
6. Add overdue escalation scheduler.
7. Add attachment support for invoice/product proof.
8. Expand product and brand master seed list.
9. Add warranty end date calculation.
10. Expand README and setup verification checklist.

### Phase 2: Automation

1. WhatsApp acknowledgement and update templates.
2. Daily manager digest.
3. Service center delay reminders.
4. Customer closure confirmation link.
5. Repeat complaint auto-detection.
6. Brand registration recommendation queue.
7. Spare pending daily follow-up queue.

### Phase 3: Management reporting

1. Pending by age, brand, service center, product type, and staff.
2. SLA breach report.
3. First response time and resolution time.
4. Repeated complaint report.
5. Product-at-store custody report.
6. Customer satisfaction and negative feedback report.
7. Brand performance ranking.

## 5. Suggested additional DocTypes

| DocType | Purpose |
|---|---|
| Lavanya Ticket Activity Log | Structured call/WhatsApp/brand/service-center follow-up history |
| Lavanya Ticket Public Reference | Unique external reference for customer-facing tracking |
| Lavanya Branch / Counter | Multi-counter and multi-showroom routing |
| Lavanya Brand Escalation Contact | Brand manager / service head escalation path |
| Lavanya WhatsApp Message Log | Outbound/inbound template tracking |
| Lavanya Warranty Verification | Invoice/warranty proof and verification status |
| Lavanya Service Estimate Approval | Customer approval for paid local service |
| Lavanya Ticket SLA Event | SLA breach and escalation audit trail |
| Lavanya Customer Feedback | CSAT, negative feedback, closure confirmation |

## 6. Suggested HD Ticket fields to add

| Field | Type | Reason |
|---|---|---|
| public_reference | Data / unique | Customer-safe unique reference |
| branch | Link | Multi-showroom readiness |
| counter | Link / Select | Counter-level accountability |
| product_location | Select | Customer home / showroom / service center |
| invoice_no | Data | Brand registration requirement |
| invoice_attachment_required | Check | Proof control |
| warranty_end_date | Date | Auto warranty decision |
| warranty_verified | Check | Prevent false claims |
| warranty_verified_by | Link User | Audit |
| next_action | Select | Push-work engine |
| next_action_owner | Link User / Role | Accountability |
| escalation_level | Select | Staff / coordinator / manager / owner |
| customer_update_required | Check | Prevent silent pending |
| last_customer_update_at | Datetime | Communication SLA |
| brand_last_contacted_at | Datetime | Brand follow-up control |
| service_center_last_contacted_at | Datetime | Service center follow-up control |

## 7. Suggested status model

Keep Helpdesk status simple, but add `pending_reason`, `next_action`, and `next_action_owner` for operational detail.

Recommended statuses:

1. Open
2. Registration Pending
3. Brand Registered
4. Assigned to Service Center
5. Technician Visit Pending
6. Waiting on Customer
7. Waiting on Part / Approval
8. Product at Store
9. Handed to Service Center
10. Ready for Pickup
11. Resolved
12. Closed
13. Cancelled

## 8. Suggested workflow matrix

| Ticket type | Mandatory fields | Default next action |
|---|---|---|
| Customer Complaint - Site | customer, mobile, product, brand, complaint, address | Register with brand |
| Customer Product at Store | customer, mobile, product, brand, serial, receipt | Create product receipt |
| Installation / Demo | customer, mobile, product, brand, address, purchase proof | Register installation/demo |
| Replacement / DOA | invoice, serial, product photos, brand ticket | Escalate to manager/brand |
| Stock Complaint | brand, product, serial/batch, supplier/stock reference | Assign to purchase/store team |
| Out of Warranty Local Service | estimate, approval, technician | Get customer approval |
| Free Service | invoice/purchase date, product, brand, service rule | Schedule free service |

## 9. Technical refactoring suggestions

1. Remove duplicate product type constants from multiple files and expose one source of truth.
2. Avoid manual `frappe.db.commit()` inside setup helpers unless the setup orchestrator controls transaction boundaries.
3. Replace Administrator context in QR intake with a dedicated service user or a narrowly permissioned internal method.
4. Add tests for every business rule: brand registered requires brand ticket/date, follow-up statuses require pending reason/date, closure requires narration/confirmation, QR rate limiting, QR validation, customer profile sync, duplicate mobile conflict, and role field guard.
5. Add CI command in README.
6. Add migration idempotency test: run setup twice and compare records.
7. Add fixture/data validation report after install.
8. Use constants for statuses, ticket types, and role names in one module.
9. Add indexes for normalized mobile, next follow-up date, brand, service center, pending reason, public reference, and branch.
10. Add structured logging around QR intake and customer profile sync.

## 10. Business recommendation

The code is currently good for an internal pilot, but it should not be considered complete for real showroom operations until follow-up automation, dashboards, customer communication logs, and branch/counter accountability are added.

The correct target is not a generic Helpdesk. The target is:

`Customer -> Product -> Complaint -> Brand Registration -> Follow-up -> Resolution -> Customer Confirmation -> Feedback -> Brand/Staff Performance Report`

Any workflow that does not enforce this chain will eventually recreate the old ledger problem inside a digital system.
