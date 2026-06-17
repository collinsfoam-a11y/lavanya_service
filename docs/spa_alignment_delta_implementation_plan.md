# SPA Alignment Delta Implementation Plan

Date: 2026-06-17
Purpose: Reconcile the existing SPA/service work already built with the broader Lavanya eMart real-world service flow plan, so implementation does not create duplicate systems.

## 1. Executive decision

The current SPA implementation is not wrong. It should be treated as the operating base.

The detailed service-flow plan should not replace the existing SPA work. It should be reduced into a delta plan:

1. Preserve existing Comment-based activity log.
2. Preserve existing Today’s Work and escalation framework.
3. Preserve existing custody actions and appointments.
4. Add missing foundation fields: `service_flow_type`, `current_service_stage`, `next_action`.
5. Add missing business routes: warranty, extended warranty, stock, finance/refund, local paid service.
6. Add missing structured logs only where Comments are not enough: payment/commission, stock issue, extended warranty claim, custody proof, communication status.

## 2. Current SPA work vs plan

| Area | Current SPA state | Decision |
|---|---|---|
| Activity log | Built using standard Comment plus structured `[Follow-up]` entries | Keep. Do not create separate activity child table now. |
| Follow-up | Built using Today’s Work overdue/due-today | Keep and extend with optional stage SLA fields. |
| Escalation | Built via escalation report and daily notify | Keep. Add `escalation_level` only if needed for filtering. |
| Custody | Built with receipt plus sent/returned/delivered actions | Keep. Add validation and proof fields. |
| Appointment / technician visit | Built with `Lavanya Service Appointment` | Keep and link to service stages. |
| WhatsApp | Built as `wa.me` action | Keep. Add communication status logging. |
| Repeat complaint | Built detect and link | Keep. Add manager escalation rule. |
| Reports | Framework built with catalog, drill-down, escalation | Keep. Add missing report definitions into existing framework. |
| service_flow_type/current_service_stage/next_action | Not built | Add as net-new foundation. |
| Warranty/stock/extended warranty/finance/refund flows | Not modeled | Add as net-new business routes. |
| Payment/commission/stock/extended warranty doctypes | Not built | Add as net-new structured records. |

## 3. Revised architecture decision

### 3.1 Activity log

Do not build `Lavanya Ticket Activity Log` immediately.

Use current Comment-based approach as canonical activity stream:

- standard Comment
- structured tags such as `[Follow-up]`, `[Stage]`, `[Customer Informed]`, `[Escalation]`, `[Payment]`, `[Warranty]`
- existing `get_ticket_activity` and `add_ticket_note`

Reason:

A separate child table would create two activity systems and confuse users.

Future option:

Only add child table if reporting from Comment becomes too slow or too unstructured.

### 3.2 Follow-up engine

Do not replace date-based Today’s Work immediately.

Current date-based model is good for pilot:

- due today
- overdue
- manager notification
- escalation report

Add stage SLA fields gradually:

- `service_flow_type`
- `current_service_stage`
- `next_action`
- `stage_due_at`
- `pre_overdue_alert_at`
- `overdue_status`

Important decision:

`next_follow_up_date` remains the practical staff-facing follow-up date.

`stage_due_at` and `pre_overdue_alert_at` should support Due Soon/Overdue calculation, not replace Today’s Work immediately.

### 3.3 Escalation

Use existing escalation report and daily notification as the base.

Add field:

`escalation_level`

Options:

- None
- Coordinator
- Manager
- Owner

Use this mainly for filtering, dashboards, and owner view.

Do not create a second escalation system.

## 4. Revised Sprint 1: Net-new foundation only

Sprint 1 should avoid rebuilding what already exists.

### 4.1 Add HD Ticket fields

Add these fields:

| Field | Type | Required |
|---|---|---|
| service_flow_type | Select | Yes for all service tickets |
| current_service_stage | Select | Yes for active tickets |
| next_action | Select | Yes for active tickets |
| next_action_owner | Link User | If assigned to person |
| next_action_role | Data/Select | If assigned to role queue |
| stage_due_at | Datetime | Optional first, mandatory after stabilization |
| pre_overdue_alert_at | Datetime | Optional first, mandatory after stabilization |
| overdue_status | Select | Derived |
| escalation_level | Select | Derived/manual override |
| customer_informed | Select | Waiting stages |
| customer_informed_channel | Select | Waiting stages |
| customer_informed_at | Datetime | Waiting stages |
| customer_informed_by | Link User | Waiting stages |

### 4.2 Service flow type options

Start with these options:

1. Customer Complaint - Site
2. Customer Product at Store
3. Installation / Demo
4. Periodic / Free Service
5. Stock Complaint
6. Out of Warranty Local Service
7. Extended Warranty Claim
8. Replacement / Exchange
9. Refund Case
10. Finance Sale Service Issue
11. Reopened / Repeat Complaint

### 4.3 Current service stage options

Do not add hundreds of stages first. Start controlled:

| Group | Stages |
|---|---|
| Intake | Complaint Received, Details Pending, Warranty Check Pending |
| Brand Warranty | Brand Registration Pending, Brand Registered, Service Center Follow-up |
| Extended Warranty | Extended Warranty Check Pending, Claim Registration Pending, Provider Follow-up, Provider Denied |
| Technician | Technician Visit Pending, Technician Visited - Issue Pending |
| Waiting | Spare Pending, Estimate Approval Pending, Customer Not Reachable, Waiting on Customer |
| Product at Store | Product Received at Store, Handed to Service Center, Returned to Store, Ready for Pickup, Delivered to Customer |
| Installation | Installation Registration Pending, Installation Technician Visit Pending, Installation Completed |
| Periodic Service | Periodic Service Due, Customer Contact Pending, Service Scheduled, Feedback Pending |
| Stock | Stock Proof Pending, Supplier Follow-up Pending, Credit Note Pending, Replacement Pending, Stock Decision Pending |
| Closure | Customer Verification Pending, Closure Confirmation Pending, Closed, Cancelled |

## 5. Revised Sprint 2: Add stage mapping without breaking existing SPA

Create module:

`lavanya_service/stage_rules.py`

Contents:

- service flow options
- stage options
- default next action per stage
- default owner role per stage
- default follow-up interval per stage
- escalation thresholds

Do not force every old ticket into strict stage rules at once.

Migration behavior:

- New tickets get default service flow/stage.
- Existing tickets get fallback stage based on current status and existing fields.
- Existing tickets missing stage should appear in a cleanup report, not break migration.

## 6. Revised Sprint 3: Extend Today’s Work instead of replacing it

Use existing Today’s Work as primary screen.

Add new filters/groups:

- My Due Soon
- My Overdue
- Warranty Check Pending
- Brand Registration Pending
- Extended Warranty Pending
- Product at Store Pending
- Installation Pending
- Periodic Service Due
- Stock Complaint Pending
- Amount / Commission Pending
- Customer Verification Pending

Due Soon calculation:

- If `pre_overdue_alert_at` exists and current time is after it, show Due Soon.
- If not, fall back to existing `next_follow_up_date` due-today logic.

This makes upgrade safe.

## 7. Revised Sprint 4: Structured child records only where necessary

Do not create a duplicate general activity table.

Create only these structured records:

| DocType | Reason |
|---|---|
| Lavanya Payment and Commission Log | Money/commission needs structured audit |
| Lavanya Stock Issue Detail | Stock proof/settlement needs structured fields |
| Lavanya Extended Warranty Claim | Provider/policy/claim needs structured fields |
| Extended Warranty Provider Master | Provider master required |
| Lavanya Communication Log | Optional, for WhatsApp/SMS status beyond `wa.me` |

Activity narration remains in Comment.

## 8. Business routes to add

### 8.1 Brand warranty route

Add route:

`Warranty Check Pending -> Brand Registration Pending -> Brand Registered -> Service Center Follow-up -> Technician Visit Pending -> Customer Verification Pending -> Closed`

Must require:

- brand ticket number
- registration date
- service center
- customer informed status

### 8.2 Extended warranty route

Add route:

`Warranty Check Pending -> Extended Warranty Check Pending -> Claim Registration Pending -> Provider Follow-up -> Provider Technician Visit Pending -> Customer Verification Pending -> Closed`

Must require:

- extended warranty sold
- provider
- policy/certificate no
- claim no
- provider result
- denial reason if rejected

### 8.3 Product at store route

Keep existing receipt and sent/returned/delivered actions.

Add validation:

- cannot close unless custody status is Delivered or Cancelled
- receipt required
- returned/ready/pickup transitions must log Comment

### 8.4 Installation/demo route

Use existing appointment model where possible.

Add:

- installation registration number
- visit scheduled at
- technician visit status
- completion confirmation
- extra charge status if applicable

### 8.5 Periodic/free service route

Add:

- service due date
- customer interest status
- deferred until
- assigned provider/technician
- feedback status

Use daily scheduler only to create due service tickets when rules exist.

### 8.6 Stock complaint route

Add `Lavanya Stock Issue Detail`.

Must require:

- proof status
- issue subtype
- supplier/brand reference where external
- resolution type
- commercial status
- manager/owner approval where value impact exists

### 8.7 Local paid service route

Add `Lavanya Payment and Commission Log`.

Must require:

- technician name
- amount collected or not collected
- payment mode
- technician charge
- commission applicable/status
- customer confirmation

## 9. Validation strategy

Phase validation in three levels.

### Level 1: Soft warning

Use for first pilot:

- missing service flow
- missing stage
- missing next action
- missing customer informed

### Level 2: Block critical transitions

Block only these initially:

- Brand Registered without brand ticket number/date
- Closed without customer confirmation/work narration
- Product-at-store close without delivered/cancelled custody
- Local paid service close without payment status
- Extended warranty close without provider result
- Stock complaint close without resolution type

### Level 3: Full enforcement

After pilot stabilizes:

- active ticket cannot save without next action
- active ticket cannot save without next follow-up
- waiting stage cannot save without customer informed status
- reschedule requires reason
- manager override requires reason

## 10. Report alignment

Existing report framework should host these reports instead of creating another reporting layer.

Priority reports:

1. Today’s Work by Service Flow
2. Due Soon / Overdue by Stage
3. Brand Registration Pending
4. Extended Warranty Pending
5. Product at Store Ageing
6. Installation Pending
7. Periodic Service Due
8. Stock Complaint Pending
9. Amount / Commission Pending
10. Closure Confirmation Pending

## 11. Implementation order after SPA work

### Delta Sprint 1

1. Add `service_flow_type`, `current_service_stage`, `next_action` fields.
2. Add `stage_rules.py`.
3. Add default stage assignment for new tickets.
4. Add cleanup report for tickets missing stage.

### Delta Sprint 2

1. Extend Today’s Work to group by service flow and stage.
2. Add Due Soon calculation using `pre_overdue_alert_at` where available.
3. Add `escalation_level` field mapped from existing escalation logic.

### Delta Sprint 3

1. Add Extended Warranty Provider Master.
2. Add Extended Warranty Claim record.
3. Add extended warranty route validation.

### Delta Sprint 4

1. Add Payment and Commission Log.
2. Add stock issue detail record.
3. Add closure validation for stock and paid service.

### Delta Sprint 5

1. Add installation/demo route fields.
2. Add periodic/free service route fields.
3. Add missing reports into existing report framework.

## 12. Decisions to avoid duplication

| Topic | Decision |
|---|---|
| Activity log | Use Comment as canonical log. No child activity table now. |
| Follow-up | Extend Today’s Work. Do not replace. |
| Escalation | Keep current report/notify. Add field only for filtering. |
| Custody | Keep existing receipt/actions. Add validation. |
| Appointment | Keep `Lavanya Service Appointment`. Link to stages. |
| WhatsApp | Keep wa.me action. Add optional log/status fields. |
| Reports | Use existing report framework. Add missing report definitions. |

## 13. Definition of done for this alignment

The alignment is complete when:

1. Existing SPA features continue working.
2. No duplicate activity system exists.
3. Today’s Work supports service flow/stage grouping.
4. Stage fields exist and default correctly for new tickets.
5. Critical closures are blocked when proof/payment/provider/custody/confirmation is missing.
6. Extended warranty, stock complaint, local paid service, installation/demo, and periodic service are modeled.
7. Existing reports framework hosts the new business reports.
