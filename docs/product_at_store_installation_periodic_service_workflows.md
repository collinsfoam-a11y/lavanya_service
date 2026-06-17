# Lavanya eMart Addon Workflows: Product at Store, Installation/Demo, and Periodic Service

Date: 2026-06-16
Purpose: Add the remaining real-world service workflows that must be handled inside the same Lavanya Helpdesk control system.

## 1. Why these workflows are required

Lavanya eMart service is not only customer complaints at site. The system must also handle:

1. Complained product physically brought to showroom
2. Installation and demo requests
3. Periodic/free service reminders

These should not be treated as side notes. They need separate stages, required fields, follow-up dates, customer communication, proof, and closure rules.

## 2. Ticket type design

Use one HD Ticket model, but route by `ticket_type`.

Recommended ticket types:

| Ticket Type | Purpose |
|---|---|
| Customer Complaint - Site | Product complaint at customer location |
| Customer Product at Store | Product physically received at showroom |
| Installation / Demo | Installation or product demo request |
| Periodic / Free Service | Scheduled service reminder or customer-requested free service |
| Stock Complaint | Internal stock or supplier/brand issue |
| Out of Warranty Local Service | Paid/local technician support |
| Replacement / DOA | Dead-on-arrival or replacement approval case |

## 3. Customer Product at Store workflow

### 3.1 Real-world use case

Customer brings a mixer, induction cooker, iron box, gas stove, TV, or other product to the showroom for complaint handling.

The showroom receives the item, records its condition and accessories, gives a receipt, sends/assigns it to service center or local technician, follows up until return, informs customer, and closes only after customer collects the product.

### 3.2 Stages

| Stage | Owner | Follow-up before overdue |
|---|---|---|
| Product Received at Store | Front Desk | 30 min |
| Receipt / Custody Verification | Front Desk | 1 hour |
| Warranty Check Pending | Front Desk / Coordinator | 4 hours |
| Brand Registration Pending | Service Coordinator | 4 hours |
| Handed to Service Center | Service Coordinator | 24 hours |
| With Local Technician | Service Coordinator | 24 hours |
| Repair Status Follow-up | Service Coordinator | 24 hours |
| Spare / Part Pending | Service Coordinator | 24 hours |
| Estimate Approval Pending | Service Coordinator | 24 hours |
| Returned to Store | Front Desk | 4 hours |
| Ready for Pickup | Front Desk | 24 hours |
| Delivered to Customer | Front Desk | Same day |
| Closure Confirmation Pending | Front Desk | 24 hours |
| Closed | None | None |

### 3.3 Required fields

| Field | Purpose |
|---|---|
| service_product_receipt | Link to receipt |
| receipt_no | Customer receipt reference |
| received_datetime | When product received |
| received_by | Staff user |
| product_storage_location | Rack/shelf/location |
| physical_condition | Condition at receiving |
| accessories_received | Charger, jar, remote, stand, pipe, etc. |
| customer_claimed_issue | Complaint as told by customer |
| estimated_return_date | Expected return date |
| custody_status | Current custody |
| handed_to | Service center / technician |
| handover_datetime | Handover time |
| returned_to_store_at | Product return time |
| customer_pickup_informed_at | Customer informed time |
| delivered_to_customer_at | Customer collection time |
| customer_signature_or_proof | Collection proof |

### 3.4 Custody statuses

Use controlled custody statuses:

1. Received at Store
2. Awaiting Warranty Check
3. Awaiting Brand Registration
4. Handed to Service Center
5. With Local Technician
6. Spare Pending
7. Estimate Approval Pending
8. Returned to Store
9. Ready for Customer Pickup
10. Delivered to Customer
11. Cancelled / Returned Without Service

### 3.5 Follow-up logic

- Product received at store must create a product receipt immediately.
- If warranty applies, brand registration must happen within 4 hours.
- If handed to service center, follow up every 24 hours.
- If with local technician, follow up every 24 hours.
- If returned to store, customer must be informed within 4 hours.
- If ready for pickup, customer reminder repeats every 24 hours.
- If not collected within 3 days, manager escalation.
- Ticket cannot close unless custody is Delivered to Customer or Cancelled.

### 3.6 Closure validation

Block closure if:

- service product receipt is missing
- custody status is not Delivered to Customer / Cancelled
- customer collection proof is missing, unless manager override
- work narration is missing
- final customer confirmation is missing
- amount/payment/commission status is missing for paid work

## 4. Installation / Demo workflow

### 4.1 Real-world use case

Customer buys AC, washing machine, refrigerator, chimney, hob, water purifier, TV, or other appliance requiring installation or demo.

The showroom must register the request with brand/service center, track technician visit, confirm installation/demo completion, and verify customer satisfaction.

### 4.2 Stages

| Stage | Owner | Follow-up before overdue |
|---|---|---|
| Installation / Demo Request Received | Front Desk | 30 min |
| Product / Invoice Verification Pending | Front Desk | 2 hours |
| Brand Installation Registration Pending | Service Coordinator | 4 hours |
| Installation Registered | Service Coordinator | 24 hours |
| Technician Visit Scheduled | Service Coordinator | 24 hours |
| Technician Visit Pending | Service Coordinator | 24 hours |
| Installation / Demo Completed | Front Desk / Coordinator | 24 hours |
| Customer Verification Pending | Front Desk | 24 hours |
| Closed | None | None |

### 4.3 Required fields

| Field | Purpose |
|---|---|
| installation_type | Installation / Demo / Both |
| invoice_no | Purchase proof |
| purchase_date | Purchase date |
| delivery_date | Delivery date |
| preferred_installation_date | Customer preference |
| installation_address | Site address |
| landmark | Location guidance |
| product_serial_no | Product serial |
| indoor_serial_no | AC indoor unit, if applicable |
| outdoor_serial_no | AC outdoor unit, if applicable |
| brand_registration_no | Brand/service request number |
| registered_with_brand_at | Registration date/time |
| service_center | Assigned service center |
| technician_name | Technician |
| technician_phone | Technician contact |
| visit_scheduled_at | Planned visit |
| technician_visited_at | Actual visit |
| installation_completed_at | Completion date/time |
| extra_charges_collected | Stand/pipe/extra material amount if any |
| customer_confirmation | Completion confirmation |

### 4.4 Installation-specific checks

For AC installation:

- indoor serial number
- outdoor serial number
- installation stand requirement
- copper pipe extra length
- drainage condition
- power point/stabilizer requirement
- extra amount collected
- customer informed about extra charges

For chimney/hob/gas stove:

- cutout/site readiness
- ducting requirement
- gas connection readiness
- installation accessory requirement

For washing machine/water purifier:

- inlet/outlet availability
- tap/water pressure condition
- electrical point condition

### 4.5 Follow-up logic

- Request must be registered with brand/service center within 4 hours.
- If visit is scheduled, follow up on visit date.
- If technician does not visit, follow up with service center and inform customer.
- If installation is completed, verify customer satisfaction within 24 hours.
- If extra charges were collected, amount and narration must be recorded.

### 4.6 Closure validation

Block closure if:

- brand/service request number missing for brand installation
- technician visit status missing
- completion confirmation missing
- customer confirmation missing
- extra charges status missing, if applicable
- work narration missing

## 5. Periodic / Free Service workflow

### 5.1 Real-world use case

Some products require free service or periodic service after sale. Example: AC free service reminder, chimney cleaning, water purifier service, or demo follow-up.

The system should generate or allow creation of service reminders, contact the customer, schedule the service, track completion, and close only after customer confirmation.

### 5.2 Trigger types

| Trigger | Example |
|---|---|
| Auto reminder | AC free service after defined days |
| Manual creation | Customer requests service |
| Campaign import | Service reminder list from sales data |
| QR/WhatsApp request | Customer requests periodic service |

### 5.3 Stages

| Stage | Owner | Follow-up before overdue |
|---|---|---|
| Periodic Service Due | System / Front Desk | Same day |
| Customer Contact Pending | Front Desk | 24 hours |
| Customer Not Interested / Deferred | Front Desk | Reschedule date required |
| Service Scheduling Pending | Service Coordinator | 24 hours |
| Brand / Technician Assignment Pending | Service Coordinator | 24 hours |
| Technician Visit Pending | Service Coordinator | 24 hours |
| Service Completed | Front Desk / Coordinator | 24 hours |
| Customer Feedback Pending | Front Desk | 24 hours |
| Closed | None | None |

### 5.4 Required fields

| Field | Purpose |
|---|---|
| periodic_service_type | AC Free Service / Chimney Service / Water Purifier Service / Demo Follow-up |
| service_due_date | Due date |
| reminder_source | Auto / Manual / Campaign / QR / WhatsApp |
| previous_service_done | Yes / No / Unknown |
| last_service_date | Previous service date |
| customer_contacted | Yes / No |
| customer_preferred_date | Preferred visit date |
| customer_interest_status | Interested / Deferred / Not Interested / Not Reachable |
| deferred_until | Future reminder date |
| assigned_service_provider | Brand / Service Center / Local Technician |
| technician_name | Technician |
| technician_phone | Technician phone |
| visit_scheduled_at | Visit schedule |
| service_completed_at | Completion time |
| feedback | Customer feedback |

### 5.5 Follow-up logic

- When service is due, contact customer same day.
- If customer is not reachable, retry within 24 hours.
- If customer defers, set deferred date. Ticket should sleep until deferred date.
- If customer is interested, assign service center or technician within 24 hours.
- After assignment, follow up every 24 hours until visit completion.
- After completion, collect feedback within 24 hours.

### 5.6 Closure validation

Block closure if:

- customer interest status is blank
- service completed status is blank, unless customer declined
- technician/service provider is blank for completed service
- feedback/customer confirmation is missing
- next deferred date is missing for deferred cases

## 6. Common fields across all three workflows

Add these shared fields to HD Ticket or linked child tables:

| Field | Applies to |
|---|---|
| service_flow_type | Complaint / Product at Store / Installation Demo / Periodic Service |
| current_service_stage | All |
| next_action | All |
| next_action_owner | All |
| next_follow_up_at | All |
| pre_overdue_alert_at | All |
| stage_due_at | All |
| customer_informed | All waiting stages |
| customer_informed_channel | All waiting stages |
| customer_informed_at | All waiting stages |
| work_narration | All follow-ups |
| closure_type | All closures |
| customer_confirmation_received | All closures |

## 7. Required queues

Create separate work queues:

1. Product at Store - Received Today
2. Product at Store - Handover Pending
3. Product at Store - Service Center Follow-up
4. Product at Store - Ready for Pickup
5. Installation / Demo Registration Pending
6. Installation / Demo Technician Visit Pending
7. Installation / Demo Customer Confirmation Pending
8. Periodic Service Due Today
9. Periodic Service Customer Contact Pending
10. Periodic Service Deferred
11. Periodic Service Technician Visit Pending
12. Periodic Service Feedback Pending

## 8. Quick actions to add

### Product at Store

- Create Product Receipt
- Hand Over to Service Center
- Assign Local Technician
- Mark Returned to Store
- Mark Ready for Pickup
- Customer Collected Product
- Close Product-at-Store Case

### Installation / Demo

- Register Installation with Brand
- Mark Installation Registered
- Schedule Technician Visit
- Technician Not Visited
- Installation Completed
- Customer Confirmed Installation

### Periodic Service

- Contact Customer
- Customer Interested
- Customer Deferred
- Customer Not Interested
- Assign Service Provider
- Mark Service Completed
- Record Feedback
- Close Periodic Service

## 9. Reports

Add reports:

| Report | Purpose |
|---|---|
| Product at Store Ageing | Items lying in showroom/service center |
| Product Ready for Pickup Ageing | Customers not collecting products |
| Custody Movement Report | Product handover audit |
| Installation Pending Report | Pending installations/demo |
| Technician Not Visited Report | Brand/service center delay |
| Periodic Service Due Report | Services due today/this week |
| Periodic Service Conversion Report | Interested/deferred/not interested |
| Service Feedback Report | Customer satisfaction after service |

## 10. Implementation priority

Add in this order:

1. Ticket type and `service_flow_type` routing.
2. Product-at-store custody enforcement.
3. Installation/demo registration and technician visit tracking.
4. Periodic service due/reminder workflow.
5. Queue/views for each workflow.
6. Quick actions.
7. Reports.
8. Tests.

## 11. Acceptance criteria

This addon is complete when:

1. Product-at-store cases cannot close without custody completion.
2. Installation/demo requests cannot close without customer confirmation.
3. Periodic service can be created manually or by reminder.
4. Every workflow has next action, owner, and due time.
5. Due Soon queues exist for all three workflows.
6. Customer is informed at every waiting stage.
7. Narration is mandatory for every follow-up.
8. Manager can see ageing and overdue cases separately for complaint, product at store, installation/demo, and periodic service.
