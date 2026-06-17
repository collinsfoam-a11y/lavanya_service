# Lavanya eMart Stock Issue and Remaining Real-World Case Workflows

Date: 2026-06-16
Purpose: Add stock issue handling and verify remaining showroom service cases that can occur in real operations.

## 1. Stock issue workflow

Stock issue is different from a customer complaint. It is an internal showroom/godown/purchase issue involving unsold stock, display stock, returned stock, supplier replacement, brand approval, missing accessories, or commercial settlement.

Recommended ticket type:

`Stock Complaint`

Recommended service flow type:

`Stock Issue`

## 2. Stock issue subtypes

| Subtype | Example |
|---|---|
| Transit Damage | Damage noticed after delivery from supplier |
| Supplier Damage | Damage found while opening carton |
| Display Damage | Display piece damaged in showroom |
| Missing Accessory | Remote, stand, jar, pipe, manual, warranty card missing |
| Wrong Model / Wrong Item | Supplier sent wrong item/model |
| Serial Mismatch | Invoice/carton/product serial mismatch |
| Non-working Stock | Product not working before sale |
| AC Indoor / Outdoor Mismatch | Split AC unit mismatch |
| Installation Kit Missing | Stand, pipe, bracket, kit missing |
| Customer Return to Stock | Returned item needs decision |
| Internal Handling Damage | Issue caused during showroom/godown handling |
| Supplier Credit Note Pending | Commercial credit pending |
| Replacement Pending | Replacement from supplier/brand pending |

## 3. Stock issue stage flow

`Stock Issue Found -> Proof Capture -> Responsibility Check -> Supplier / Brand Follow-up -> Inspection / Approval -> Replacement / Credit / Repair / Stock Decision -> Closure`

## 4. Stock issue stages

| Stage | Owner | Follow-up before overdue |
|---|---|---|
| Stock Issue Found | Store / Front Desk | 30 minutes |
| Proof Capture Pending | Store / Manager | 2 hours |
| Responsibility Check Pending | Manager | 4 hours |
| Supplier Follow-up Pending | Purchase / Manager | 24 hours |
| Brand Registration Pending - Stock | Service Coordinator | 4 hours |
| Supplier / Brand Reference Created | Purchase / Coordinator | 24 hours |
| Inspection Pending | Service Coordinator / Manager | 24 hours |
| Replacement Pending | Purchase / Manager | 24 hours |
| Credit Note Pending | Purchase / Accounts | 24 hours |
| Repair Approval Pending | Manager | 24 hours |
| Discount Sale / Stock Adjustment Approval Pending | Manager / Owner | 24 hours |
| Stock Decision Pending | Manager | 24 hours |
| Resolved | Manager | 24 hours |
| Closed | None | None |

## 5. Required fields for stock issue

| Field | Purpose |
|---|---|
| stock_issue_subtype | Damage, missing accessory, wrong model, serial mismatch, etc. |
| item_name | Product identification |
| brand | Brand |
| model_no | Model |
| serial_no | Product serial |
| invoice_no | Supplier invoice or purchase bill |
| purchase_invoice_date | Supplier invoice date |
| supplier | Supplier/distributor |
| supplier_contact | Contact person/phone |
| received_date | Goods received date |
| issue_discovered_date | Date issue found |
| issue_discovered_by | Staff who found issue |
| location_found | Showroom/godown/display/delivery |
| stock_location | Rack/godown/floor |
| issue_type | Dent, scratch, missing item, non-working, mismatch, etc. |
| proof_status | Pending / Captured / Verified |
| carton_condition | Good / Damaged / Opened / Wet / Torn |
| product_condition | New / Display / Damaged / Returned |
| responsibility | Supplier / Transport / Brand / Internal / Customer Return / Unknown |
| supplier_reference_no | Supplier case reference |
| brand_ticket_no | Brand case number |
| expected_claim_amount | Expected claim/settlement amount |
| approved_claim_amount | Approved amount |
| resolution_type | Replacement / Credit Note / Repair / Discount Sale / Stock Adjustment / Returned to Supplier |
| commercial_status | Pending / Approved / Rejected / Settled |
| manager_approval_status | Required approval status |
| owner_approval_status | High-value approval status |

## 6. Proof capture rule

A stock issue should not move forward without proof.

Required proof checklist:

- product photo
- serial number photo
- carton photo
- issue photo/video
- supplier invoice or purchase reference
- opening/discovery date
- staff name who found issue

If proof is missing, keep stage as:

`Proof Capture Pending`

Follow-up: within 2 hours.

## 7. Responsibility decision

Before supplier/brand follow-up, manager should mark likely responsibility:

- Supplier
- Transport
- Brand
- Internal handling
- Customer return issue
- Unknown / needs checking

This controls who should be followed up.

## 8. Stock issue outcome paths

### 8.1 Supplier replacement

`Proof Captured -> Supplier Follow-up -> Replacement Pending -> Replacement Received -> Stock Updated -> Closed`

Required:

- supplier reference number
- replacement promised date
- replacement received date
- old item return status
- replacement item serial number

### 8.2 Credit note

`Proof Captured -> Supplier Follow-up -> Credit Note Pending -> Credit Note Received -> Accounts Verified -> Closed`

Required:

- expected credit amount
- approved credit amount
- credit note number
- credit note date
- accounts verified

### 8.3 Brand stock service / approval

`Proof Captured -> Brand Registration Pending -> Brand Ticket Created -> Inspection Pending -> Approved / Rejected -> Replacement / Repair / Credit -> Closed`

Required:

- brand ticket number
- inspection date
- approval status
- approval reference
- replacement/repair/credit status

### 8.4 Internal handling / discount sale / stock adjustment

`Proof Captured -> Responsibility Check -> Discount Sale or Stock Adjustment Approval -> Approved -> Stock Action Completed -> Closed`

Required:

- internal reason
- estimated value impact
- manager approval
- owner approval for high value cases
- final action taken

### 8.5 Missing accessory

`Missing Accessory -> Supplier/Brand Follow-up -> Accessory Received or Credit Approved -> Item Made Saleable -> Closed`

Required:

- missing accessory list
- accessory requested date
- accessory received date
- item saleable status

## 9. Follow-up rules

| Condition | Follow-up |
|---|---|
| Proof not captured | every 2 hours until completed |
| Supplier contacted but no reply | every 24 hours |
| Brand registration pending | every 4 hours until registered |
| Inspection pending | every 24 hours |
| Replacement pending | every 24 hours |
| Credit note pending | every 24 hours |
| Approval pending | every 24 hours |
| High-value issue | immediate manager/owner queue |

## 10. Closure validation

Block closure if:

- proof status is not Captured or Verified
- serial number is missing where applicable
- supplier/brand reference is missing for external claims
- resolution type is blank
- commercial status is Pending
- replacement/credit/repair/stock decision is blank
- manager approval is missing for value-impact cases
- owner approval is missing for high-value cases
- final narration is missing

## 11. Stock issue queues and reports

Queues:

1. Stock Issue Found Today
2. Proof Capture Pending
3. Supplier Follow-up Pending
4. Brand Registration Pending - Stock
5. Inspection Pending - Stock
6. Replacement Pending
7. Credit Note Pending
8. Missing Accessory Pending
9. Stock Adjustment Approval Pending
10. High Value Stock Risk

Reports:

- Stock Issue Ageing
- Supplier-wise Stock Issue
- Brand-wise Stock Issue
- Credit Note Pending
- Replacement Pending
- Internal Handling Issue
- Missing Accessory
- Stock Value Impact

## 12. Other real-world cases to support

After complaint, product-at-store, installation/demo, periodic service, and stock issue, the system should also support the following cases.

## 13. Customer declined / cancelled service

Use when customer refuses estimate, does not want service, or cancels request.

Required fields:

- declined reason
- declined date
- customer informed by
- manager approval if work had already started

Closure type:

`Customer Declined / Cancelled`

## 14. Customer not reachable

Rules:

- try phone and WhatsApp
- log every attempt
- retry every 24 hours
- after configured attempts, escalate to manager
- closure only with manager-approved reason

Fields:

- contact attempt count
- last contact attempt at
- last contact channel
- manager closure reason

## 15. Brand or service center refused service

Use when brand/service center refuses because of area, warranty rejection, invalid invoice, old product, unsupported installation, or other reason.

Fields:

- refusal reason
- refused by
- refusal date
- proof/narration
- customer informed
- alternate route offered: paid brand service / local technician / customer declined

## 16. Service center delay / no response

If service center is repeatedly not responding:

- move to `Service Center Delay Escalation`
- show to manager
- use escalation contact
- inform customer

Fields:

- delay reason
- escalation contact
- escalation date
- customer update note

## 17. Replacement / exchange customer case

Use when customer asks for replacement due to repeated complaint, approval, or product issue.

Fields:

- replacement requested by customer
- replacement reason
- manager approval
- brand/supplier approval
- old item custody status
- new item serial number
- price difference, if any
- final customer acceptance

## 18. Refund case

Rare but possible.

Fields:

- refund requested reason
- approved by
- refund amount
- payment mode
- finance sale impact, if any
- old product returned status
- accounts verification

## 19. Finance sale service issue

Use when replacement/refund/service has finance partner impact.

Fields:

- finance partner
- finance invoice/reference
- customer down payment
- replacement/refund finance impact
- accounts verification

## 20. Installation extra charge dispute

Common for AC, chimney, hob, wall mount, pipe, stand, bracket.

Fields:

- extra charge type
- quoted amount
- collected amount
- collected by
- customer accepted charges
- dispute reason
- resolution narration

## 21. Demo not completed / customer or site not available

Fields:

- site not ready reason
- customer unavailable reason
- rescheduled date
- technician visit proof, if any
- customer informed

## 22. Product misuse / external damage diagnosis

Use when technician/brand reports customer-caused issue.

Fields:

- diagnosis reason
- technician diagnosis
- photo proof
- customer informed
- paid repair estimate
- customer decision

## 23. Reopened ticket after closure

If customer says issue is not actually solved after closure:

- reopen original ticket if inside configured period
- create linked repeat ticket if outside configured period
- manager escalation for repeat within 7 days

Fields:

- reopened reason
- reopened date
- previous closure narration
- manager review

## 24. Required final service flow types

The system should support at least these service flow types:

1. Customer Complaint - Site
2. Customer Product at Store
3. Installation / Demo
4. Periodic / Free Service
5. Stock Complaint
6. Out of Warranty Local Service
7. Replacement / Exchange
8. Customer Cancellation / Declined
9. Finance Sale Service Issue
10. Refund Case
11. Reopened / Repeat Complaint

## 25. Implementation recommendation

Do not create separate systems for each case.

Use one HD Ticket with:

- ticket_type
- service_flow_type
- current_service_stage
- next_action
- next_follow_up_at
- next_action_owner
- pending_reason
- child tables for activity, custody, payment, stock issue, and communication logs

## 26. Definition of done

Full workflow coverage is complete when:

1. customer site complaint is handled
2. customer product at store is handled
3. installation/demo is handled
4. periodic/free service is handled
5. stock complaint is handled
6. replacement/exchange is handled
7. paid local technician case is handled
8. customer declined/cancelled case is handled
9. refund case has a path
10. finance sale service issue has a path
11. every active case has next action, owner, due time, narration, and customer update
12. no case can close without correct proof, narration, settlement, and confirmation
