# Workflow Verification: Missing Addons and Improvements

Date: 2026-06-16
Related document: `docs/warranty_out_warranty_service_workflow.md`

## 1. Verification result

The current warranty and out-of-warranty workflow is logically correct and matches the real Lavanya eMart service process:

1. complaint is received
2. warranty is checked
3. in-warranty cases go to brand registration
4. out-of-warranty cases go to paid brand service or local technician
5. service center, customer, and technician follow-up repeats until solved
6. narration and customer update are mandatory
7. spare, part, DOA, and replacement cases get separate pending control
8. closure requires customer confirmation
9. out-of-warranty/local technician work tracks amount, narration, technician, and commission

The flow is suitable as the base operating model.

However, a few practical gaps should be added before coding.

## 2. Missing decision points

### 2.1 Purchased from Lavanya vs not purchased from Lavanya

The current flow asks for `purchased_from_lavanya`, but the workflow should define what happens for each case.

Recommended values:

- Yes
- No
- Unknown

Recommended behavior:

| Value | System behavior |
|---|---|
| Yes | Full service coordination allowed |
| No | Guided support only or paid local service, manager setting required |
| Unknown | Invoice proof pending / manual verification |

If not purchased from Lavanya, the system should still allow help, but closure type should clearly say:

- Not Purchased From Lavanya - Guided Only
- Paid Local Service Arranged
- Customer Referred to Brand

### 2.2 Warranty source

Warranty status alone is not enough.

Add field:

`warranty_source`

Options:

- Lavanya Invoice Verified
- Old ERP Verified
- Manual Bill Verified
- Customer Claim Only
- Brand Confirmed
- Unknown
- Not Applicable

This prevents staff from marking warranty as valid without proof.

### 2.3 Extended warranty route

Current warranty decision includes Extended Warranty, but no route is defined.

Add separate path:

`Extended Warranty -> Extended Warranty Provider Registration -> Provider Follow-up -> Resolution -> Customer Verification -> Closure`

Required fields:

- extended warranty provider
- policy/certificate number
- claim number
- claim registration date
- provider contact
- approval status

### 2.4 Brand denied warranty path

If brand denies warranty, ticket should not stop.

Add route:

`Brand Denied -> Inform Customer -> Offer Paid Brand Service / Local Technician / Customer Declined -> Closure`

Required fields:

- denial reason
- denied by
- denial date
- customer informed
- customer decision

## 3. Missing stages to add

Add these stages to improve real-world coverage:

| Missing stage | Why needed |
|---|---|
| Duplicate / Existing Ticket Review | Avoid duplicate complaint handling |
| Repeat Complaint Review | Detect issue after recent service |
| Customer Not Reachable | Common follow-up outcome |
| Brand Denied Warranty | Warranty rejection path |
| Extended Warranty Registration Pending | Separate extended warranty handling |
| Estimate Rejected / Customer Declined | Paid service may not proceed |
| Payment Verification Pending | Amount may be collected by staff/technician |
| Refund / Return / Replacement Pending | Retail cases may need replacement/refund path |
| Ready for Customer Pickup | For product received at store |
| Delivered / Product Returned to Customer | Custody closure proof |

## 4. Missing fields to add

### 4.1 Service center and technician fields

Add:

- service_center_contact_person
- service_center_phone
- brand_escalation_contact
- technician_name
- technician_phone
- technician_visit_scheduled_at
- technician_visited_at
- technician_visit_status
- technician_diagnosis

### 4.2 Spare and DOA fields

Add:

- spare_required
- spare_name
- spare_order_number
- spare_ordered_date
- spare_expected_date
- spare_received_date
- DOA_requested
- DOA_approved_status
- DOA_reference
- replacement_item_status

### 4.3 Customer update fields

Add:

- customer_informed
- customer_informed_channel
- customer_informed_at
- customer_informed_by
- customer_response
- customer_satisfaction_status

### 4.4 Amount and commission fields

The current flow has amount and commission fields. Add stronger audit fields:

- amount_expected
- amount_collected
- amount_collection_status
- payment_mode
- collected_by
- technician_charge
- technician_paid_status
- lavanya_commission_applicable
- lavanya_commission_amount
- commission_collected
- commission_collected_by
- commission_collection_date

## 5. Critical improvement: separate status, stage, and next action

Do not overload Helpdesk status with too many meanings.

Use three layers:

| Layer | Example | Purpose |
|---|---|---|
| Helpdesk Status | Open / In Progress / Waiting / Resolved / Closed | Broad lifecycle |
| Service Stage | Spare Pending / Technician Visit Pending | Operational position |
| Next Action | Call Service Center / Inform Customer | Exact staff work |

This avoids status explosion and makes reports cleaner.

## 6. Follow-up improvement

Every active stage should create a follow-up before overdue.

Recommended fields:

- stage_due_at
- pre_overdue_alert_at
- next_follow_up_at
- next_action
- next_action_owner
- overdue_status

Recommended state movement:

`Not Due -> Due Soon -> Overdue -> Escalated`

The `Due Soon` queue is more important than the overdue queue because it prevents missed service before customers complain.

## 7. Missing automation rules

Add automation rules:

| Trigger | System action |
|---|---|
| Ticket created | Set Warranty Check Pending |
| Warranty In Warranty | Set Brand Registration Pending |
| Warranty Out of Warranty | Set Out of Warranty Confirmed |
| Brand ticket number entered | Set Brand Registered |
| Technician visit date passed without result | Move to Technician Visit Follow-up |
| Spare expected date passed | Escalate to Manager |
| DOA pending over 24 hours | Show in Manager queue |
| Ready for pickup over 3 days | Escalate to Manager |
| Customer confirmation pending over 2 days | Escalate to Manager |
| Repeat complaint within 7 days | Immediate Manager escalation |

## 8. Missing quick actions

Add these quick actions beyond the current list:

1. Mark Duplicate / Link Existing Ticket
2. Mark Repeat Complaint
3. Warranty Verified
4. Warranty Denied by Brand
5. Extended Warranty Claim Registered
6. Technician Assigned
7. Technician Visit Scheduled
8. Technician Visited and Solved
9. Technician Visited but Not Solved
10. Spare Ordered
11. Spare Received
12. DOA Requested
13. DOA Approved
14. Replacement Completed
15. Customer Declined Paid Service
16. Payment Verified
17. Product Returned to Customer
18. Manager Override Close

## 9. Missing reports

Add reports:

- Warranty Check Pending
- Brand Registration Pending
- Brand Registered but Technician Not Visited
- Technician Visited but Not Solved
- Spare Pending Ageing
- DOA / Replacement Pending
- Brand Denied Warranty
- Out-of-Warranty Local Service Revenue
- Technician Commission Pending
- Amount Collection Pending
- Customer Not Reachable
- Repeat Complaint within 7 Days
- Closure Confirmation Pending
- Service Center Delay Ranking
- Brand Complaint Ratio by Product

## 10. Product-at-store add-on

For products physically received at the showroom, add mandatory custody controls:

- received condition
- accessories received
- received by
- rack/location
- handover to technician/service center
- return from technician/service center
- ready for pickup date
- delivered to customer date
- customer signature/photo proof

Ticket must not close until product custody is completed.

## 11. Risk controls

### 11.1 Staff cannot close without proof

Block closure if:

- customer confirmation is missing
- work narration is missing
- paid amount status is missing
- commission status is missing for local work
- product custody is incomplete
- brand ticket number missing for in-warranty brand cases

### 11.2 Manager override must be traceable

Any override should require:

- override reason
- override by
- override date/time
- internal narration

### 11.3 No silent reschedule

If a staff member changes next follow-up date, require:

- reschedule reason
- old follow-up date
- new follow-up date
- rescheduled by

## 12. Final recommendation

The current flow is correct, but before implementation it should be upgraded with these controls:

1. Add purchased-from-Lavanya decision routing.
2. Add warranty source and verification audit.
3. Add extended warranty and brand-denied paths.
4. Add duplicate/repeat complaint review.
5. Separate Helpdesk Status, Service Stage, and Next Action.
6. Add Due Soon queue before overdue.
7. Add no-silent-reschedule rule.
8. Add product custody completion rule.
9. Add manager override audit.
10. Add amount/commission/payment verification fields.

These improvements will make the system stronger than a normal helpdesk and closer to Lavanya eMart's real service desk requirement.
