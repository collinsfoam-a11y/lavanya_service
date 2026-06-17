# Lavanya eMart Extended Warranty Provider Workflow

Date: 2026-06-16
Purpose: Add workflow for products where extended warranty was sold to the customer and the complaint must be registered with the extended warranty provider instead of, or after, brand warranty handling.

## 1. Why this workflow is required

Some customers buy an extended warranty plan at the time of sale. When the normal brand warranty is over, the service responsibility may shift to the extended warranty provider.

The system must therefore record:

1. whether extended warranty was sold
2. who the warranty provider is
3. policy/certificate details
4. validity period
5. provider claim registration
6. approval/rejection status
7. service provider or technician action
8. customer update and closure confirmation

Without this, staff may wrongly route an eligible extended warranty case to out-of-warranty paid service.

## 2. Warranty decision hierarchy

When a complaint is received, warranty check should follow this order:

1. Is product under normal brand warranty?
2. If no, was extended warranty sold?
3. If yes, is extended warranty active?
4. If active, register with extended warranty provider.
5. If not active or rejected, move to out-of-warranty paid/local service route.

Recommended warranty route values:

| Warranty Route | Meaning |
|---|---|
| Brand Warranty | Normal manufacturer warranty active |
| Extended Warranty | Extended warranty provider claim applicable |
| Out of Warranty | No valid brand or extended warranty |
| Brand Denied | Brand rejected normal warranty |
| Extended Warranty Denied | Provider rejected extended warranty claim |
| Unknown | Proof/check pending |

## 3. Extended warranty fields

Add these fields to HD Ticket or linked child DocType.

| Field | Type | Purpose |
|---|---|---|
| extended_warranty_sold | Check | Whether extended warranty was sold |
| extended_warranty_provider | Link / Data | Provider name |
| extended_warranty_plan_name | Data | Plan/package name |
| extended_warranty_policy_no | Data | Policy/certificate number |
| extended_warranty_invoice_no | Data | Warranty sale invoice/reference |
| extended_warranty_start_date | Date | Coverage start date |
| extended_warranty_end_date | Date | Coverage end date |
| extended_warranty_status | Select | Active / Expired / Unknown / Rejected |
| extended_warranty_document_status | Select | Pending / Received / Verified |
| extended_warranty_claim_no | Data | Provider claim number |
| extended_warranty_claim_registered_at | Datetime | Claim registration time |
| extended_warranty_claim_status | Select | Not Registered / Registered / Under Review / Approved / Rejected / Service Assigned / Closed |
| extended_warranty_approval_reference | Data | Approval reference |
| provider_service_center | Data / Link | Assigned provider/service center |
| provider_technician_name | Data | Technician assigned by provider |
| provider_technician_phone | Data | Technician phone |
| provider_denial_reason | Small Text | Reason if rejected |
| provider_customer_care_no | Data | Provider contact |
| provider_portal_url | Data | Claim portal |

## 4. Extended warranty provider master

Create master DocType:

`Extended Warranty Provider Master`

Fields:

| Field | Purpose |
|---|---|
| provider_name | Provider name |
| customer_care_no | Customer care number |
| dealer_support_no | Dealer support number |
| portal_url | Claim portal |
| email | Provider email |
| claim_registration_channel | Phone / Portal / WhatsApp / Email |
| required_documents | Invoice, policy certificate, serial photo, complaint photo, etc. |
| default_claim_sla_hours | Default registration/check SLA |
| escalation_contact | Escalation person/contact |
| active | Enable/disable provider |

## 5. Extended warranty workflow stages

| Stage | Owner | Follow-up before overdue |
|---|---|---|
| Extended Warranty Check Pending | Front Desk / Coordinator | 4 hours |
| Extended Warranty Document Pending | Front Desk | 4 hours |
| Extended Warranty Registration Pending | Service Coordinator | 4 hours |
| Extended Warranty Claim Registered | Service Coordinator | 24 hours |
| Provider Review Pending | Service Coordinator | 24 hours |
| Provider Service Assigned | Service Coordinator | 24 hours |
| Provider Technician Visit Pending | Service Coordinator | 24 hours |
| Provider Repair / Approval Pending | Service Coordinator | 24 hours |
| Extended Warranty Denied | Manager / Coordinator | 24 hours |
| Customer Decision Pending | Front Desk / Coordinator | 24 hours |
| Issue Solved - Customer Verification | Front Desk / Coordinator | 24 hours |
| Closure Confirmation Pending | Front Desk | 24 hours |
| Closed | None | None |

## 6. Extended warranty flow

### 6.1 Complaint received

During warranty check, system must ask:

- Is brand warranty active?
- Was extended warranty sold?
- Is extended warranty active?
- Is policy/certificate available?
- Is invoice/warranty sale reference available?

If extended warranty is marked as sold but details are missing, move to:

`Extended Warranty Document Pending`

### 6.2 Document pending

Required documents may include:

- product purchase invoice
- extended warranty invoice/reference
- policy/certificate number
- product serial number photo
- complaint photo/video if required
- customer mobile/address

Follow-up:

- contact customer within 4 hours
- if document not received, repeat follow-up every 24 hours
- do not move to registration until required details are available or manager overrides

### 6.3 Register claim with provider

When documents are available:

- register claim through provider channel
- record claim number
- record registration date/time
- record provider response
- set next follow-up within 24 hours

Validation:

Ticket cannot move to `Extended Warranty Claim Registered` unless:

- provider is selected
- policy/certificate number exists or manager override exists
- claim number exists
- registration date/time exists

### 6.4 Provider review / approval

Provider may:

- approve service
- assign service center
- assign technician
- ask for more documents
- reject claim
- approve replacement/repair

Every provider response must be logged in activity log.

### 6.5 Provider denied claim

If provider rejects:

Move to:

`Extended Warranty Denied`

Required fields:

- denial reason
- denied by / provider reference
- denial date
- customer informed status
- alternate route offered

Next route options:

- paid brand service
- local technician
- customer declined
- manager escalation

## 7. Follow-up loop

After claim registration, follow-up repeats until closed:

1. Check with provider/service center
2. Check whether technician is assigned
3. Check whether technician visited
4. Check whether issue is solved
5. Record narration
6. Inform customer
7. Set next follow-up
8. Repeat until customer confirms closure

Follow-up outcomes:

| Outcome | Next stage | Follow-up |
|---|---|---|
| Provider asks for documents | Extended Warranty Document Pending | 24 hours |
| Provider reviewing claim | Provider Review Pending | 24 hours |
| Service assigned | Provider Service Assigned | 24 hours |
| Technician not visited | Provider Technician Visit Pending | 24 hours |
| Repair/approval pending | Provider Repair / Approval Pending | 24 hours |
| Claim rejected | Extended Warranty Denied | 24 hours |
| Customer says solved | Issue Solved - Customer Verification | 24 hours |
| Customer not reachable | Customer Not Reachable | 24 hours |

## 8. Customer information rule

Customer must be informed when:

- extended warranty document is pending
- claim is registered
- provider asks for more documents
- claim is approved
- technician visit is scheduled
- provider rejects claim
- service is completed

Required fields:

- customer_informed
- informed_channel
- informed_at
- informed_by
- customer_visible_note

## 9. Amount and charges

Extended warranty cases can still include charges.

Track:

- inspection charge
- excluded part charge
- service charge requested by provider
- amount collected by Lavanya, if any
- amount collected by technician/provider, if known
- customer approval for charge
- payment status

This prevents disputes when customer says extended warranty was sold but provider asks for extra amount.

## 10. Closure validation

Block closure if:

- extended warranty sold is Yes but provider route was not checked
- active extended warranty exists but claim registration is missing, unless manager override exists
- claim registered but final provider status is blank
- provider denied claim but denial reason is blank
- customer was not informed of provider decision
- technician/service outcome is blank
- customer confirmation is missing
- final narration is missing
- amount/payment status is missing where charge was involved

## 11. Reports and queues

Queues:

1. Extended Warranty Check Pending
2. Extended Warranty Document Pending
3. Extended Warranty Registration Pending
4. Extended Warranty Claim Registered
5. Provider Review Pending
6. Provider Technician Visit Pending
7. Extended Warranty Denied
8. Extended Warranty Customer Decision Pending
9. Extended Warranty Closure Confirmation Pending

Reports:

- Extended Warranty Claim Ageing
- Provider-wise Pending Claims
- Provider Denied Claims
- Extended Warranty Documents Pending
- Extended Warranty Extra Charge Cases
- Extended Warranty Closure Report

## 12. Quick actions

Add quick actions:

1. Mark Extended Warranty Sold
2. Verify Extended Warranty
3. Request Extended Warranty Documents
4. Register Claim with Provider
5. Claim Registered
6. Provider Asked More Documents
7. Provider Approved Service
8. Provider Technician Assigned
9. Provider Technician Not Visited
10. Provider Denied Claim
11. Offer Paid Service / Local Technician
12. Customer Accepted Paid Route
13. Customer Declined After Denial
14. Customer Confirmed Solved
15. Close Extended Warranty Case

Every quick action must:

- add activity log
- set next stage
- set next action
- set next owner
- set next follow-up time
- require narration where needed
- inform customer where required

## 13. Integration with existing warranty path

The complaint workflow should route like this:

`Complaint Received -> Warranty Check -> Brand Warranty OR Extended Warranty OR Out of Warranty`

Decision logic:

1. If brand warranty active: use Brand Warranty route.
2. If brand warranty expired and extended warranty sold + active: use Extended Warranty route.
3. If both unavailable: use Out of Warranty route.
4. If brand/extended warranty denied: offer paid brand service or local technician.

## 14. Definition of done

Extended warranty workflow is complete when:

1. extended warranty sold can be marked on ticket
2. provider, policy, and validity are recorded
3. claim registration is tracked
4. provider follow-up repeats until resolved or denied
5. customer is informed at every provider stage
6. extra charges are tracked
7. denied claims route to paid/local/customer-declined path
8. closure is blocked without final provider result and customer confirmation
