# Lavanya eMart Detailed Service Flow Implementation Plan

Date: 2026-06-16
Target: Frappe v15 + Frappe Helpdesk v1.25.1 custom app `lavanya_service`
Purpose: Convert all real-world showroom service cases into one controlled Helpdesk-based workflow with mandatory stage follow-up, proof, narration, customer communication, and closure validation.

## 1. Implementation goal

Build one service control system for these flows:

1. Customer Complaint - Site
2. Customer Product at Store
3. Installation / Demo
4. Periodic / Free Service
5. Stock Complaint
6. Brand Warranty Complaint
7. Extended Warranty Provider Claim
8. Out-of-Warranty Local Service
9. Replacement / Exchange
10. Customer Declined / Cancelled
11. Refund Case
12. Finance Sale Service Issue
13. Reopened / Repeat Complaint

Do not create separate systems. Use one HD Ticket model with controlled fields, child tables, quick actions, and stage rules.

## 2. Core architecture

### 2.1 Three-layer workflow model

Do not overload Helpdesk status.

Use three separate concepts:

| Layer | Example | Purpose |
|---|---|---|
| Helpdesk Status | Open / Waiting / Resolved / Closed | Broad lifecycle |
| Service Flow Type | Product at Store / Installation / Stock Complaint | Business flow |
| Service Stage | Brand Registered / Spare Pending / Ready for Pickup | Exact operational stage |
| Next Action | Call Service Center / Inform Customer | Staff work to perform |

### 2.2 Mandatory active-ticket rule

Every active ticket must always have:

- `service_flow_type`
- `current_service_stage`
- `next_action`
- `next_action_owner` or `next_action_role`
- `next_follow_up_at`
- `stage_due_at`
- `pre_overdue_alert_at`
- `pending_reason`
- `overdue_status`
- latest activity log

A ticket must never stay pending without a next follow-up owner and due time.

## 3. Data model changes

## 3.1 HD Ticket fields to add

| Field | Type | Mandatory condition | Purpose |
|---|---|---|---|
| service_flow_type | Select | Always | Main business flow |
| current_service_stage | Select | Active tickets | Exact service stage |
| previous_service_stage | Select | Stage changes | Audit |
| stage_started_at | Datetime | Active tickets | Stage age |
| stage_due_at | Datetime | Active tickets | Stage deadline |
| pre_overdue_alert_at | Datetime | Active tickets | Due Soon queue |
| next_follow_up_at | Datetime | Active tickets | Staff work time |
| next_action | Select | Active tickets | Exact next work |
| next_action_owner | Link User | If user-specific | Assigned staff |
| next_action_role | Data | If role queue | Assigned role/team |
| follow_up_required | Check | Active tickets | Follow-up enforcement |
| overdue_status | Select | Active tickets | Not Due / Due Soon / Overdue / Breached |
| escalation_level | Select | Active tickets | None / Coordinator / Manager / Owner |
| public_reference | Data | All tickets | Customer-safe reference |
| branch | Link/Data | Multi-branch | Showroom/GST unit |
| counter | Data/Select | Front desk/counter | Accountability |
| product_location | Select | Complaint/product cases | Customer Home / Store / Service Center / Technician |
| warranty_route | Select | Warranty check | Brand / Extended / Out of Warranty / Unknown |
| warranty_source | Select | Warranty check | Invoice/ERP/Brand/Customer claim |
| warranty_verified | Check | Warranty cases | Proof validation |
| warranty_verified_by | Link User | Warranty verified | Audit |
| warranty_end_date | Date | Warranty known | Brand warranty end |
| customer_informed | Select | Waiting stages | Yes / No / Not Required |
| customer_informed_channel | Select | Customer update | Phone / WhatsApp / Direct / SMS |
| customer_informed_at | Datetime | Customer update | Update audit |
| customer_informed_by | Link User | Customer update | Staff audit |
| manager_override_reason | Small Text | Override cases | Override audit |

## 3.2 Child tables / linked DocTypes

Create these supporting tables:

| DocType | Type | Purpose |
|---|---|---|
| Lavanya Ticket Activity Log | Child table | Every call, WhatsApp, status update, narration |
| Lavanya Product Custody Log | Child table | Product-at-store movement |
| Lavanya Payment and Commission Log | Child table | Paid/local service amount and commission |
| Lavanya Stock Issue Detail | Linked/child | Stock complaint proof and settlement |
| Lavanya Extended Warranty Claim | Linked/child | Extended warranty policy and provider claim |
| Lavanya Communication Log | Child/linked | WhatsApp/SMS/email/customer messages |
| Extended Warranty Provider Master | Master | Provider details and claim channels |

## 4. Service flow types and stage maps

## 4.1 Customer Complaint - Site

Flow:

`Complaint Received -> Warranty Check Pending -> Brand Registration / Extended Warranty / Out-of-Warranty Route -> Follow-up Loop -> Customer Verification -> Closed`

Stages:

1. Complaint Received
2. Customer/Product Details Pending
3. Warranty Check Pending
4. Brand Registration Pending
5. Brand Registered
6. Service Center Follow-up
7. Technician Visit Pending
8. Technician Visited - Issue Pending
9. Spare / Part Pending
10. Issue Solved - Customer Verification
11. Closure Confirmation Pending
12. Closed

## 4.2 Customer Product at Store

Flow:

`Product Received at Store -> Receipt/Custody -> Warranty Check -> Brand/Local Route -> Repair Follow-up -> Returned to Store -> Ready for Pickup -> Delivered -> Closed`

Stages:

1. Product Received at Store
2. Receipt / Custody Verification
3. Warranty Check Pending
4. Brand Registration Pending
5. Handed to Service Center
6. With Local Technician
7. Repair Status Follow-up
8. Spare / Part Pending
9. Returned to Store
10. Ready for Pickup
11. Delivered to Customer
12. Closure Confirmation Pending
13. Closed

Closure block:

- product custody must be Delivered to Customer or Cancelled
- product receipt must exist
- customer pickup proof required unless manager override

## 4.3 Installation / Demo

Flow:

`Installation/Demo Request -> Invoice/Product Verification -> Brand Registration -> Technician Visit -> Completion -> Customer Confirmation -> Closed`

Stages:

1. Installation / Demo Request Received
2. Product / Invoice Verification Pending
3. Brand Installation Registration Pending
4. Installation Registered
5. Technician Visit Scheduled
6. Technician Visit Pending
7. Installation / Demo Completed
8. Customer Verification Pending
9. Closed

Special fields:

- installation type
- installation address
- preferred installation date
- brand request number
- technician visit scheduled at
- installation completed at
- extra charges collected
- customer confirmation

## 4.4 Periodic / Free Service

Flow:

`Service Due -> Customer Contact -> Schedule -> Assign Provider/Technician -> Visit -> Completion -> Feedback -> Closed`

Stages:

1. Periodic Service Due
2. Customer Contact Pending
3. Customer Deferred
4. Service Scheduling Pending
5. Provider / Technician Assignment Pending
6. Technician Visit Pending
7. Service Completed
8. Feedback Pending
9. Closed

Special rule:

If customer defers, require `deferred_until`. Ticket sleeps until deferred date.

## 4.5 Stock Complaint

Flow:

`Stock Issue Found -> Proof Capture -> Responsibility Check -> Supplier/Brand Follow-up -> Inspection/Approval -> Replacement/Credit/Repair/Stock Decision -> Closed`

Stages:

1. Stock Issue Found
2. Proof Capture Pending
3. Responsibility Check Pending
4. Supplier Follow-up Pending
5. Brand Registration Pending - Stock
6. Inspection Pending - Stock
7. Replacement Pending
8. Credit Note Pending
9. Repair Approval Pending
10. Stock Adjustment Approval Pending
11. Stock Decision Pending
12. Closed

Closure block:

- proof status must be captured/verified
- resolution type required
- commercial status settled or approved
- manager approval for value-impact cases
- owner approval for high-value write-off/stock adjustment

## 4.6 Extended Warranty Provider Claim

Flow:

`Warranty Check -> Extended Warranty Check -> Document Pending -> Provider Registration -> Provider Follow-up -> Provider Technician/Service -> Customer Verification -> Closed`

Stages:

1. Extended Warranty Check Pending
2. Extended Warranty Document Pending
3. Extended Warranty Registration Pending
4. Extended Warranty Claim Registered
5. Provider Review Pending
6. Provider Service Assigned
7. Provider Technician Visit Pending
8. Provider Repair / Approval Pending
9. Extended Warranty Denied
10. Customer Decision Pending
11. Issue Solved - Customer Verification
12. Closure Confirmation Pending
13. Closed

Closure block:

- if extended warranty sold is Yes, provider route must be checked
- if claim registered, final provider result required
- if provider denied, denial reason and customer update required

## 4.7 Out-of-Warranty Local Service

Flow:

`Out of Warranty Confirmed -> Estimate Approval -> Local Technician -> Visit -> Work Completed -> Payment/Commission -> Customer Verification -> Closed`

Stages:

1. Out of Warranty Confirmed
2. Estimate Approval Pending
3. Local Technician Assigned
4. Technician Visit Pending
5. Local Work Completed - Payment Pending
6. Amount / Commission Verification Pending
7. Issue Solved - Customer Verification
8. Closure Confirmation Pending
9. Closed

Closure block:

- technician name required
- work narration required
- amount/payment status required
- commission status required if applicable
- customer confirmation required

## 5. Warranty decision logic

When complaint is received, warranty route must be decided in this order:

1. Check normal brand warranty.
2. If active, route to Brand Warranty.
3. If brand warranty expired, check extended warranty sold.
4. If extended warranty sold and active, route to Extended Warranty Provider.
5. If no valid warranty, route to Out-of-Warranty.
6. If any route is denied, inform customer and offer paid brand service/local technician/customer declined route.

Required values:

| Field | Values |
|---|---|
| warranty_status | In Warranty / Out of Warranty / Unknown / Extended Warranty / Brand Denied |
| warranty_route | Brand Warranty / Extended Warranty / Out of Warranty / Brand Denied / Extended Warranty Denied / Unknown |
| warranty_source | Lavanya Invoice Verified / Old ERP Verified / Manual Bill Verified / Customer Claim Only / Brand Confirmed / Provider Confirmed / Unknown |

## 6. Follow-up SLA matrix

| Stage category | First follow-up before overdue |
|---|---|
| New complaint / request | 30 minutes |
| Missing customer/product details | 2 hours |
| Warranty / invoice proof pending | 4 hours |
| Brand registration pending | 4 hours |
| Extended warranty registration pending | 4 hours |
| Brand/Provider/Service center follow-up | 24 hours |
| Technician visit pending | 24 hours |
| Spare/part/approval pending | 24 hours |
| Product at store movement pending | 24 hours |
| Returned to store | 4 hours |
| Ready for pickup | 24 hours |
| Periodic service customer contact | 24 hours |
| Stock proof capture | 2 hours |
| Stock supplier/credit/replacement follow-up | 24 hours |
| Customer verification / closure confirmation | 24 hours |

## 7. Due Soon and overdue logic

State calculation:

- Not Due: current time is before `pre_overdue_alert_at`
- Due Soon: current time is between `pre_overdue_alert_at` and `stage_due_at`
- Overdue: current time is after `stage_due_at`
- Breached: overdue has crossed escalation threshold

Pre-overdue timing:

| SLA | Pre-overdue alert |
|---|---|
| 30 minutes | 10 minutes before due |
| 2 hours | 30 minutes before due |
| 4 hours | 1 hour before due |
| 24 hours | 4 hours before due |

## 8. Quick action implementation

Create quick actions by flow.

### 8.1 Common quick actions

- Check Warranty
- Request Missing Details
- Customer Informed
- Customer Not Reachable
- Reschedule Follow-up
- Manager Override
- Customer Confirmed Solved
- Close Ticket

### 8.2 Brand warranty actions

- Register with Brand
- Brand Line Busy / Retry
- Brand Registered
- Service Center Contacted
- Technician Not Visited
- Technician Visited - Not Solved
- Spare Pending
- Replacement / Approval Pending

### 8.3 Extended warranty actions

- Mark Extended Warranty Sold
- Verify Extended Warranty
- Request Extended Warranty Documents
- Register Claim with Provider
- Claim Registered
- Provider Asked More Documents
- Provider Approved Service
- Provider Technician Assigned
- Provider Denied Claim

### 8.4 Product-at-store actions

- Create Product Receipt
- Hand Over to Service Center
- Assign Local Technician
- Mark Returned to Store
- Mark Ready for Pickup
- Customer Collected Product

### 8.5 Installation/demo actions

- Register Installation with Brand
- Mark Installation Registered
- Schedule Technician Visit
- Installation Completed
- Customer Confirmed Installation

### 8.6 Periodic service actions

- Contact Customer
- Customer Interested
- Customer Deferred
- Customer Not Interested
- Assign Service Provider
- Mark Service Completed
- Record Feedback

### 8.7 Stock complaint actions

- Capture Proof
- Mark Responsibility
- Contact Supplier
- Register Brand Stock Complaint
- Mark Inspection Pending
- Mark Replacement Pending
- Mark Credit Note Pending
- Mark Stock Decision Approved
- Close Stock Issue

Every quick action must:

1. verify role permission
2. require narration where needed
3. update stage
4. update next action
5. update next owner
6. update next follow-up
7. add activity log
8. update customer informed fields when applicable

## 9. Scheduler implementation

Enable in `hooks.py`:

```python
scheduler_events = {
    "hourly": [
        "lavanya_service.tasks.stage_followup.refresh_stage_followup_status",
        "lavanya_service.tasks.stage_followup.escalate_overdue_tickets",
    ],
    "daily": [
        "lavanya_service.tasks.stage_followup.create_daily_manager_digest",
        "lavanya_service.tasks.periodic_service.create_due_service_tickets",
    ],
}
```

Modules:

| Module | Purpose |
|---|---|
| lavanya_service/stage_rules.py | Stage constants, SLA, next action rules |
| lavanya_service/api/stage_actions.py | Quick action APIs |
| lavanya_service/tasks/stage_followup.py | Due soon, overdue, escalation |
| lavanya_service/tasks/periodic_service.py | Periodic/free service generation |
| lavanya_service/validations/stage_validation.py | Mandatory stage/follow-up validation |

## 10. Views and queues

Create these HD Views / work queues:

1. My Due Soon
2. My Overdue
3. Manager Escalation
4. Owner Escalation
5. Warranty Check Pending
6. Brand Registration Pending
7. Extended Warranty Pending
8. Service Center Follow-up
9. Technician Visit Pending
10. Spare / Part Pending
11. Product at Store - Handover Pending
12. Product at Store - Ready for Pickup
13. Installation / Demo Pending
14. Periodic Service Due Today
15. Stock Issue - Proof Pending
16. Stock Issue - Supplier Follow-up
17. Stock Issue - Credit Note Pending
18. Amount / Commission Pending
19. Customer Verification Pending
20. Closure Confirmation Pending

## 11. Reports

Required script reports:

| Report | Purpose |
|---|---|
| Service Pending Ageing | Overall ageing |
| Brand-wise Pending | Brand service pressure |
| Service Center Delay | Service center performance |
| Technician Visit Pending | Visit not completed |
| Spare Pending Ageing | Spare delay control |
| Extended Warranty Claim Ageing | Provider delay control |
| Product at Store Ageing | Custody risk |
| Installation Pending | Installation/demo delay |
| Periodic Service Due | Free/periodic service tracking |
| Stock Issue Ageing | Stock complaint tracking |
| Credit Note Pending | Commercial settlement |
| Local Technician Amount and Commission | Paid service audit |
| Repeat Complaint | Quality risk |
| Customer Not Reachable | Stuck customer cases |
| Closure Without Confirmation Exception | Override audit |

## 12. Validation rules

Block save/stage transition if:

1. active ticket has no current service stage
2. active ticket has no next action
3. active ticket has no next follow-up time
4. active ticket has no owner or owner role
5. waiting stage has no customer informed status
6. follow-up action has no narration
7. brand registered stage lacks brand ticket number and registration date
8. extended warranty sold but provider route not checked
9. product-at-store case has incomplete custody
10. stock complaint lacks proof/resolution decision
11. local paid service lacks amount/payment/commission status
12. closure lacks final narration and customer confirmation
13. follow-up is rescheduled without reason
14. manager override lacks reason

## 13. Sprint implementation order

### Sprint 1: Foundation

1. Add new HD Ticket fields.
2. Add `service_flow_type` and `current_service_stage` options.
3. Add stage constants and SLA config in `stage_rules.py`.
4. Add stage transition helper.
5. Add validation rules.
6. Add public reference generation if not already complete.

### Sprint 2: Activity and follow-up engine

1. Add `Lavanya Ticket Activity Log`.
2. Enable scheduler events.
3. Implement Due Soon / Overdue calculation.
4. Implement escalation rules.
5. Create My Due Soon / My Overdue / Manager Escalation views.

### Sprint 3: Warranty routes

1. Implement brand warranty route.
2. Implement extended warranty route.
3. Add Extended Warranty Provider Master.
4. Add claim registration and denial handling.
5. Add warranty decision validation.

### Sprint 4: Product at store and local paid service

1. Strengthen Service Product Receipt.
2. Add custody validation.
3. Add local technician amount/payment/commission log.
4. Add product-at-store quick actions.
5. Add paid service closure rules.

### Sprint 5: Installation/demo and periodic service

1. Add installation/demo stage actions.
2. Add installation-specific fields.
3. Add periodic service rule generation.
4. Add deferred service logic.
5. Add relevant views/reports.

### Sprint 6: Stock complaint

1. Add stock issue fields or `Lavanya Stock Issue Detail`.
2. Add proof capture flow.
3. Add supplier/brand follow-up stages.
4. Add credit/replacement/stock decision validation.
5. Add stock issue reports.

### Sprint 7: Reports and final hardening

1. Add all operational reports.
2. Add owner dashboard cards.
3. Add tests for every flow.
4. Update README.
5. Run fresh-site install/migrate verification.

## 14. Test plan

Tests required:

- new ticket gets default stage and follow-up
- warranty decision routes correctly
- in-warranty cannot bypass brand registration without reason
- extended warranty sold cannot bypass provider check
- out-of-warranty local service requires amount/payment fields
- product-at-store cannot close without custody completion
- installation cannot close without customer confirmation
- periodic service deferred requires deferred date
- stock complaint cannot close without proof and resolution type
- Due Soon state appears before Overdue
- overdue escalation updates correctly
- reschedule requires reason
- manager override requires reason
- closure requires narration and customer confirmation

## 15. Definition of done

The implementation is complete when:

1. every real-world service case has a controlled service flow
2. every active ticket has next action, owner, and due time
3. Due Soon queue prevents missed follow-ups
4. overdue cases escalate automatically
5. warranty, extended warranty, and out-of-warranty routes are correctly separated
6. product-at-store custody is enforced
7. installation/demo and periodic service are handled
8. stock complaint proof and commercial settlement are handled
9. paid/local service amount and commission are auditable
10. closure always requires proper narration, proof, and customer confirmation
