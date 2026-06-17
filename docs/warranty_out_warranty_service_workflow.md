# Lavanya eMart Warranty and Out-of-Warranty Service Workflow

Date: 2026-06-16
Purpose: Convert the real Lavanya eMart complaint process into a controlled multi-stage Helpdesk workflow where every stage has mandatory follow-up, narration, customer update, and closure verification.

## 1. Core business flow

Every complaint follows this base flow:

1. Complaint received
2. Check warranty status
3. If in warranty: register with brand service
4. If out of warranty: assign brand paid service or local technician
5. Follow up with service center, customer, and technician until resolved
6. Record work narration and customer update at every stage
7. If spare/part/DOA/replacement is involved, track that sub-stage separately
8. Verify with customer before closure
9. Record amount, commission, technician, and narration where applicable

The ticket must not be closed only because a brand or technician says it is closed. Customer confirmation is mandatory unless manager marks it as not required with reason.

## 2. One-ticket, multi-stage principle

Do not create separate tickets for brand registration, technician visit, spare pending, customer confirmation, and closure.

One HD Ticket should move through stages:

`Complaint Received -> Warranty Check -> Brand Registration or Local Service -> Follow-up Loop -> Resolution -> Customer Verification -> Closure`

Each stage must create a follow-up task before it becomes overdue.

## 3. Stage map

| Stage | Purpose | Follow-up owner | Due before overdue |
|---|---|---|---|
| Complaint Received | Capture complaint | Front Desk | 30 min |
| Customer/Product Details Pending | Missing details | Front Desk | 2 hours |
| Warranty Check Pending | Verify invoice/warranty | Front Desk / Coordinator | 4 hours |
| Warranty Confirmed | Decide route | Service Coordinator | 1 hour |
| Out of Warranty Confirmed | Decide paid/local route | Service Coordinator | 1 hour |
| Brand Registration Pending | Register with company/brand | Service Coordinator | 4 hours |
| Brand Registered | Brand ticket created | Service Coordinator | 24 hours |
| Service Center Follow-up | Check service center action | Service Coordinator | 24 hours |
| Technician Visit Pending | Check visit status | Service Coordinator | 24 hours |
| Technician Visited - Issue Pending | Visit done but not solved | Service Coordinator | 24 hours |
| Issue Solved - Customer Verification | Verify with customer | Front Desk / Coordinator | 24 hours |
| Spare / Part Pending | Part ordered or awaited | Service Coordinator | 24 hours |
| DOA / Replacement Approval Pending | Replacement approval awaited | Manager / Coordinator | 24 hours |
| Local Technician Assigned | Local technician assigned | Service Coordinator | 24 hours |
| Local Work Completed - Payment Pending | Work done, payment not settled | Service Coordinator / Cashier | 24 hours |
| Closure Confirmation Pending | Final customer check | Front Desk | 24 hours |
| Closed | Completed | None | None |

## 4. Complaint received stage

### Required capture fields

- customer name
- mobile number
- alternate mobile, if available
- address / location
- complaint source: phone, WhatsApp, direct visit, QR, staff entered
- product type
- brand
- model number, if available
- serial number, if available
- complaint description
- purchased from Lavanya: Yes / No / Unknown
- invoice number, if available
- purchase date, if available
- invoice proof status
- warranty status

### System action

After complaint creation:

- create public reference
- set stage as `Complaint Received`
- set next action as `Check warranty status`
- set owner as Front Desk or Service Coordinator
- set due time within 30 minutes
- add activity log entry

## 5. Warranty status check

### Warranty decision values

| Value | Meaning |
|---|---|
| In Warranty | Brand-backed service expected |
| Out of Warranty | Paid/local service route |
| Unknown | Invoice/proof pending |
| Extended Warranty | May require separate provider/process |
| Brand Denied | Brand rejected warranty |

### Required action

If warranty is unknown:

- ask customer for invoice or purchase proof
- check old ERP/manual bill/customer claim
- set stage `Warranty Check Pending`
- set follow-up within 4 hours

If in warranty:

- move to `Brand Registration Pending`

If out of warranty:

- move to `Out of Warranty Confirmed`

## 6. In-warranty path

### 6.1 Brand registration

When ticket is in warranty, service coordinator must register complaint with brand/company.

Required fields:

- manufacturer registration required
- manufacturer registered
- brand ticket number
- registration date
- registration channel
- service center
- registration pending reason, if not registered
- brand registration narration

### Stage rules

| Condition | Stage | Next action | Follow-up |
|---|---|---|---|
| Warranty confirmed | Brand Registration Pending | Register with brand | 4 hours |
| Brand line busy / portal issue | Brand Registration Pending | Retry registration | 2 hours |
| Brand ticket received | Brand Registered | Check service center action | 24 hours |

### Validation

A ticket cannot move to `Brand Registered` unless:

- brand ticket number exists
- registration date exists
- manufacturer registered is Yes

## 7. Brand/service-center follow-up loop

After brand registration, follow-up must continue until closure.

### Repeating loop

1. Check with service center
2. Check with customer
3. Check whether technician visited
4. Check whether issue solved
5. Record narration
6. Inform customer
7. Set next follow-up
8. Repeat until closed

### Required follow-up questions

For service center:

- Has technician been assigned?
- Technician name and phone?
- Visit date/time?
- Did technician visit?
- What was the diagnosis?
- Is spare required?
- Is part ordered?
- Is approval pending?
- Is DOA/replacement approved?
- Expected resolution date?

For customer:

- Did technician contact you?
- Did technician visit?
- Was the issue solved?
- Is any payment demanded?
- Is spare pending?
- Are you satisfied with service?

### Follow-up outcomes

| Outcome | Next stage | Next follow-up |
|---|---|---|
| Technician not assigned | Service Center Follow-up | 24 hours |
| Technician assigned but not visited | Technician Visit Pending | 24 hours |
| Technician visited but issue not solved | Technician Visited - Issue Pending | 24 hours |
| Spare needed | Spare / Part Pending | 24 hours |
| DOA/replacement pending | DOA / Replacement Approval Pending | 24 hours |
| Customer says solved | Issue Solved - Customer Verification | 24 hours |
| Customer not reachable | Customer Not Reachable | 24 hours |
| Service center not responding | Manager Escalation | 24 hours |

## 8. Spare, part, and DOA handling

### Spare / part pending

Required fields:

- part required: Yes / No
- part name
- part ordered by
- part ordered date
- expected part arrival date
- service center narration
- customer informed: Yes / No
- next follow-up date/time

Follow-up rule:

- follow up every 24 hours
- escalate to Manager after 3 days
- escalate to Owner after 7 days

### DOA / replacement approval

Required fields:

- DOA requested: Yes / No
- DOA approved: Yes / No / Pending / Rejected
- approval reference number
- approval date
- replacement item status
- manager narration
- customer informed

Follow-up rule:

- follow up every 24 hours
- manager must see every DOA/replacement pending case

## 9. Out-of-warranty path

Out-of-warranty complaints can follow two routes:

1. brand paid service / authorized service center
2. local technician assigned by Lavanya

### Required fields

- out-of-warranty route: Brand Paid Service / Local Technician / Customer Declined
- technician name
- technician phone
- service center, if brand paid route
- estimate amount
- customer approved estimate
- amount collected
- payment mode
- work narration
- technician work result
- technician commission applicable
- commission amount
- commission collected / payable
- final customer confirmation

## 10. Local technician workflow

Stages:

1. Out of Warranty Confirmed
2. Estimate Approval Pending
3. Local Technician Assigned
4. Technician Visit Pending
5. Local Work Completed - Payment Pending
6. Issue Solved - Customer Verification
7. Closure Confirmation Pending
8. Closed

### Required checks

Before assigning local technician:

- customer agrees to paid service
- estimate or inspection charge is explained
- technician is selected
- visit date/time is recorded

After work:

- technician narration is recorded
- amount collected is recorded
- payment mode is recorded
- commission is recorded, if applicable
- customer is contacted for verification

### Amount and commission fields

| Field | Type | Purpose |
|---|---|---|
| amount_collected | Currency | Customer payment |
| payment_mode | Select | Cash / UPI / Card / Bank / Not Collected |
| collected_by | Link User | Staff/cashier audit |
| technician_charge | Currency | Technician billed amount |
| lavanya_commission_amount | Currency | Commission from work |
| commission_collected | Check | Whether commission collected |
| commission_collection_date | Date | Audit |
| technician_payment_status | Select | Pending / Paid / Not Applicable |

## 11. Customer information rule

Whenever the ticket moves to any waiting stage, customer must be informed.

Waiting stages include:

- Brand Registered
- Service Center Follow-up
- Technician Visit Pending
- Spare / Part Pending
- DOA / Replacement Approval Pending
- Estimate Approval Pending
- Local Technician Assigned
- Ready for Pickup
- Closure Confirmation Pending

Required fields:

- customer informed: Yes / No
- informed channel: Phone / WhatsApp / Direct / SMS
- informed at
- informed by
- customer visible message/note

Validation:

A waiting stage should not be saved without either customer informed or a manager override reason.

## 12. Work narration rule

Every meaningful follow-up must have narration.

Narration must include:

- who was contacted
- what was said
- current issue status
- next promised action/date
- customer update status

Examples:

- `Called service center. Technician not assigned yet. They promised assignment by tomorrow 11 AM. Customer informed by WhatsApp. Next follow-up tomorrow 12 PM.`
- `Customer confirmed technician visited but cooling issue not solved. Service center informed. Spare request pending. Next follow-up tomorrow.`
- `Local technician Shaji visited and replaced switch. Collected Rs 350 from customer. Commission Rs 50 received. Customer confirmed issue solved.`

## 13. Closure rules

Ticket can close only when:

1. work narration is entered
2. final status is solved / cancelled / brand denied / customer declined / duplicate
3. customer confirmation is Yes or Not Required
4. amount collected is recorded for paid work
5. technician name is recorded for local work
6. commission status is recorded for local work
7. custody status is complete for product-at-store cases

Closure fields:

- closure type
- closure date
- closed by
- customer confirmation received
- final work narration
- final amount collected
- final payment status
- technician commission status

## 14. Required quick actions

Add quick-action buttons:

1. Check Warranty
2. Request Invoice Proof
3. Register with Brand
4. Brand Line Busy / Retry Later
5. Brand Registered
6. Service Center Contacted
7. Technician Not Visited
8. Technician Visited - Not Solved
9. Spare Pending
10. DOA / Replacement Pending
11. Customer Informed
12. Assign Local Technician
13. Estimate Sent
14. Estimate Approved
15. Local Work Completed
16. Amount Collected
17. Commission Collected
18. Customer Confirmed Solved
19. Close Ticket

Every quick action must:

- require narration where needed
- set next stage
- set next follow-up time
- set next owner
- add activity log
- update customer informed fields if applicable

## 15. Reports and queues

Create these operational queues:

1. Warranty Check Pending
2. Brand Registration Pending
3. Brand Registered - Service Center Follow-up
4. Technician Visit Pending
5. Technician Visited - Not Solved
6. Spare / Part Pending
7. DOA / Replacement Pending
8. Out-of-Warranty Local Service Pending
9. Estimate Approval Pending
10. Amount Collection Pending
11. Commission Collection Pending
12. Customer Verification Pending
13. Closure Confirmation Pending
14. Manager Escalation
15. Owner Escalation

## 16. Validation summary

Block save or stage transition if:

- active ticket has no next follow-up
- active ticket has no next action owner
- brand registered stage has no brand ticket number
- brand registered stage has no registration date
- waiting stage has no customer informed status
- follow-up action has no narration
- local technician work has no technician name
- paid service has no amount/payment status
- commission applicable but commission status is blank
- solved ticket has no customer confirmation

## 17. Definition of done

This workflow is ready when:

1. complaint received stage always leads to warranty check
2. warranty status decides brand route or out-of-warranty route
3. brand registration cannot be skipped for in-warranty cases without reason
4. service center/customer follow-up repeats until resolved
5. spare/part/DOA cases have separate pending control
6. out-of-warranty local technician cases track amount, narration, and commission
7. customer is informed at every waiting stage
8. customer verification is mandatory before closure
9. every follow-up has narration
10. no ticket can remain pending without a next follow-up owner and due time
