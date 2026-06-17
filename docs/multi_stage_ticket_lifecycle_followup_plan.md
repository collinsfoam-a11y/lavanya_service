# Lavanya eMart Multi-Stage Ticket Lifecycle Follow-up Plan

Date: 2026-06-16
Purpose: Define a real-world, multi-stage ticket workflow where one ticket can move through many service stages and no follow-up is missed at any stage.

## 1. Core operating rule

One customer complaint should remain one controlled ticket from intake to closure.

The ticket may pass through many stages:

`Intake -> Verification -> Brand Registration -> Service Coordination -> Technician / Service Center -> Spare / Approval -> Resolution -> Customer Confirmation -> Closure -> Feedback`

At every active stage, the system must enforce:

1. who owns the next action
2. what must be done next
3. when it must be done
4. when staff must be warned before overdue
5. what happens if it is not done
6. what log entry proves the follow-up happened

The system must not only show overdue cases. It must create a pre-overdue queue so staff acts before delay.

## 2. Required fields for multi-stage control

Add or enforce these fields on HD Ticket.

| Field | Type | Purpose |
|---|---|---|
| current_service_stage | Select | Present operational stage |
| previous_service_stage | Select | Stage movement audit |
| stage_started_at | Datetime | When current stage began |
| stage_due_at | Datetime | Hard deadline for stage |
| pre_overdue_alert_at | Datetime | Warning time before deadline |
| next_follow_up_at | Datetime | Staff work time |
| follow_up_required | Check | Active-stage enforcement |
| next_action | Select | Exact work to be done |
| next_action_owner_type | Select | User / Role / Team |
| next_action_owner | Link User | Assigned person |
| next_action_role | Data | Fallback role queue |
| pending_reason | Select | Why ticket is not closed |
| escalation_level | Select | None / Coordinator / Manager / Owner |
| overdue_status | Select | Not Due / Due Soon / Overdue / Breached |
| last_activity_at | Datetime | Last actual follow-up |
| last_customer_update_at | Datetime | Last customer communication |
| last_brand_update_at | Datetime | Last brand follow-up |
| last_service_center_update_at | Datetime | Last service-center follow-up |

## 3. Stage groups

Use stage groups to keep reports simple.

| Group | Stages |
|---|---|
| Intake | New, Customer Details Pending, Product Details Pending |
| Verification | Invoice Proof Pending, Warranty Verification Pending |
| Brand | Registration Pending, Brand Line Busy, Brand Registered |
| Service | Service Center Assigned, Technician Visit Pending, Local Technician Pending |
| Waiting | Waiting on Customer, Waiting on Part / Approval, Spare Pending, Estimate Approval Pending |
| Custody | Product at Store, Handed to Service Center, Returned to Store, Ready for Pickup |
| Resolution | Resolved, Closure Confirmation Pending |
| Final | Closed, Cancelled |

## 4. Stage lifecycle matrix

| Stage | Trigger | Next action | Owner | Follow-up before overdue |
|---|---|---|---|---|
| New | Ticket created | Verify customer/product details | Front Desk | 30 min |
| Customer Details Pending | Mobile/address missing | Call customer for missing details | Front Desk | 2 hours |
| Product Details Pending | Brand/product/model unclear | Confirm product details | Front Desk | 2 hours |
| Invoice Proof Pending | Warranty claim without proof | Request invoice proof | Front Desk | 4 hours |
| Warranty Verification Pending | Invoice received | Verify warranty | Service Coordinator | 4 hours |
| Registration Pending | In-warranty brand case | Register with brand | Service Coordinator | 4 hours |
| Brand Line Busy | Brand call failed | Retry brand registration | Service Coordinator | 2 hours |
| Brand Registered | Brand ticket number entered | Follow up service center | Service Coordinator | 24 hours |
| Service Center Assigned | Service center selected | Confirm appointment | Service Coordinator | 24 hours |
| Technician Visit Pending | Visit expected | Confirm visit status | Service Coordinator | 24 hours |
| Local Technician Pending | Local service needed | Assign/call technician | Service Coordinator | 24 hours |
| Waiting on Customer | Need customer response | Call or WhatsApp customer | Front Desk | 24 hours |
| Customer Not Reachable | Call failed | Retry customer contact | Front Desk | 24 hours |
| Waiting on Part / Approval | Approval or part awaited | Follow up approval/part | Service Coordinator | 24 hours |
| Spare Pending | Spare unavailable | Follow up spare status | Service Coordinator | 24 hours |
| Estimate Approval Pending | Paid service estimate sent | Get customer approval | Service Coordinator | 24 hours |
| Product at Store | Item received at counter | Move to service center/technician | Service Coordinator | 24 hours |
| Handed to Service Center | Product sent out | Follow up repair status | Service Coordinator | 24 hours |
| Returned to Store | Product returned | Inform customer | Front Desk | 4 hours |
| Ready for Pickup | Item ready | Remind customer to collect | Front Desk | 24 hours |
| Resolved | Work completed | Confirm customer satisfaction | Service Coordinator | 24 hours |
| Closure Confirmation Pending | Customer confirmation needed | Get final confirmation | Front Desk | 24 hours |
| Closed | Confirmed closed | No follow-up | None | None |
| Cancelled | Cancelled | No follow-up | None | None |

## 5. Real-world scenario flows

## Scenario A — Site complaint for in-warranty appliance

Example: Customer calls for LG refrigerator cooling issue.

Stages:

1. New
2. Customer Details Pending, if address or phone is incomplete
3. Invoice Proof Pending, if warranty proof is missing
4. Warranty Verification Pending
5. Registration Pending
6. Brand Line Busy, if toll-free/portal fails
7. Brand Registered
8. Service Center Assigned
9. Technician Visit Pending
10. Waiting on Part / Approval, if part or approval is required
11. Resolved
12. Closure Confirmation Pending
13. Closed

Follow-up control:

- Registration must be attempted within 4 hours.
- If brand line is busy, retry within 2 hours.
- After brand registration, service-center follow-up must occur within 24 hours.
- Customer must be updated if the ticket is waiting more than 24 hours.
- Closure is blocked until customer confirmation is Yes or Not Required.

## Scenario B — Customer brings product to showroom

Example: Customer brings mixer/induction cooker to store.

Stages:

1. New
2. Product at Store
3. Invoice Proof Pending, if warranty claim requires invoice
4. Registration Pending, if brand-backed service
5. Handed to Service Center or Local Technician Pending
6. Waiting on Part / Approval, if repair is delayed
7. Returned to Store
8. Ready for Pickup
9. Closure Confirmation Pending
10. Closed

Follow-up control:

- Product-at-store case must move within 24 hours.
- Custody log is mandatory for every movement.
- Ready-for-pickup customer reminder is mandatory every 24 hours.
- Ticket cannot close unless custody status is Delivered to Customer, Customer Collected, or Cancelled.

## Scenario C — Installation / Demo

Example: Customer bought AC or washing machine and needs installation/demo.

Stages:

1. New
2. Product Details Pending, if model/product information is incomplete
3. Invoice Proof Pending, if purchase proof is needed
4. Registration Pending
5. Brand Registered
6. Technician Visit Pending
7. Resolved
8. Closure Confirmation Pending
9. Closed

Follow-up control:

- Installation/demo registration must be done within 4 hours.
- Technician visit must be checked every 24 hours.
- Customer confirmation is mandatory before closure.

## Scenario D — Stock complaint

Example: Damaged appliance in stock or DOA item discovered before sale.

Stages:

1. New
2. Product Details Pending
3. Registration Pending or Supplier Approval Pending
4. Brand Registered
5. Waiting on Part / Approval
6. Resolved
7. Closed

Follow-up control:

- Stock complaints should be assigned to manager/service coordinator.
- Brand or supplier approval follow-up every 24 hours.
- Closure must include work narration and approval outcome.

## Scenario E — Out-of-warranty local service

Example: Customer asks Lavanya to arrange local technician.

Stages:

1. New
2. Customer Details Pending
3. Estimate Approval Pending
4. Local Technician Pending
5. Technician Visit Pending
6. Resolved
7. Closure Confirmation Pending
8. Closed

Follow-up control:

- Estimate approval follow-up every 24 hours.
- Local technician assignment follow-up every 24 hours.
- Paid work must not proceed if customer approval is required but not received.

## Scenario F — Repeat complaint after recent service

Example: Product fails again within 2 days after service.

Stages:

1. New
2. Repeat Complaint Review
3. Manager Escalation
4. Registration Pending or Service Center Assigned
5. Technician Visit Pending
6. Resolved
7. Closure Confirmation Pending
8. Closed

Follow-up control:

- Repeat complaint within 7 days goes directly to Manager escalation.
- Complaint after service within 2 days is high priority.
- Closure requires detailed narration and customer confirmation.

## Scenario G — Spare pending

Example: Brand/service center says spare will take time.

Stages:

1. Brand Registered or Service Center Assigned
2. Spare Pending
3. Waiting on Part / Approval
4. Resolved
5. Closure Confirmation Pending
6. Closed

Follow-up control:

- Spare pending must be followed up every 24 hours.
- If spare pending exceeds 3 days, escalate to Manager.
- If spare pending exceeds 7 days, escalate to Owner.
- Customer update is required at least every 24 hours or on every meaningful status change.

## Scenario H — Customer not reachable

Stages:

1. Customer Not Reachable
2. Waiting on Customer
3. Closure Confirmation Pending or Cancelled after manager approval

Follow-up control:

- Retry after 24 hours.
- Use phone and WhatsApp.
- After repeated failed attempts, escalate to Manager.
- Do not close automatically without a configured manager-approved rule.

## 6. Stage transition validation

When stage changes, the system must:

1. set `previous_service_stage`
2. set `current_service_stage`
3. set `stage_started_at = now`
4. calculate `stage_due_at`
5. calculate `pre_overdue_alert_at`
6. set `next_follow_up_at = pre_overdue_alert_at`
7. set `next_action`
8. set `next_action_owner` or `next_action_role`
9. set `follow_up_required = 1`
10. append activity log row

If the target stage is Closed or Cancelled:

1. set `follow_up_required = 0`
2. clear `next_follow_up_at`
3. clear `next_action_owner`
4. require closure fields

## 7. Pre-overdue work queue logic

The queue should not wait for breach.

Ticket state rules:

- Not Due: `now < pre_overdue_alert_at`
- Due Soon: `pre_overdue_alert_at <= now < stage_due_at`
- Overdue: `now >= stage_due_at`
- Breached: overdue beyond escalation threshold

Due Soon tickets must appear in staff work queue before overdue.

## 8. Escalation rules

| Condition | Action |
|---|---|
| Due Soon and no activity | Show in Due Soon queue |
| Overdue short SLA by 1 hour | Escalate to Coordinator |
| Overdue by 1 day | Escalate to Manager |
| Overdue by 3 days | Escalate to Owner |
| Spare Pending over 3 days | Manager escalation |
| Spare Pending over 7 days | Owner escalation |
| Product at Store over 7 days | Manager escalation |
| Ready for Pickup over 3 days | Manager escalation |
| Repeat complaint within 7 days | Manager escalation immediately |
| Complaint after service within 2 days | Manager escalation immediately |

## 9. Mandatory activity log

Every follow-up must create an activity log entry.

Minimum fields:

- ticket
- action datetime
- action type
- stage before action
- stage after action
- staff user
- contacted party
- communication channel
- outcome
- note
- next follow-up time
- next action owner

The ticket should not allow silent stage changes.

## 10. Staff work queues

Create these queues:

1. My Due Soon
2. My Overdue
3. My Follow-ups Today
4. Registration Pending
5. Invoice Proof Pending
6. Brand Line Busy Retry
7. Brand Ticket Pending
8. Technician Visit Pending
9. Spare Pending
10. Product at Store Movement Pending
11. Ready for Pickup Reminder
12. Closure Confirmation Pending
13. Manager Escalation
14. Owner Escalation

## 11. Implementation modules

Create:

`lavanya_service/stage_rules.py`

Contents:

- stage constants
- stage SLA config
- default next action config
- owner role config
- escalation config

Create:

`lavanya_service/tasks/stage_followup.py`

Functions:

- `refresh_stage_followup_status()`
- `escalate_overdue_tickets()`
- `create_daily_followup_digest()`

Create:

`lavanya_service/api/stage_actions.py`

Functions:

- `move_stage(ticket, next_stage, note=None)`
- `complete_followup(ticket, action_type, note, next_stage=None)`
- `reschedule_followup(ticket, next_follow_up_at, reason)`
- `get_my_due_soon()`
- `get_my_overdue()`

## 12. Backend validation rules

Block save if:

1. active stage has no next action
2. active stage has no next follow-up time
3. active stage has no owner or owner role
4. pending status has no pending reason
5. overdue ticket is rescheduled without reason
6. Closed ticket has no closure type
7. Closed ticket has no work narration
8. Closed ticket has no customer confirmation
9. Product-at-store ticket is closed before custody is completed
10. Brand Registered stage lacks brand ticket number and registration date

## 13. First implementation sprint

Implement in this order:

1. Add stage fields to HD Ticket.
2. Add `stage_rules.py`.
3. Add stage transition helper.
4. Add validation in `validations/hd_ticket.py`.
5. Add activity log child table.
6. Add scheduler tasks.
7. Add Due Soon and Overdue queues.
8. Add quick actions for common stage movements.
9. Add tests for stage defaults and overdue behavior.

## 14. Acceptance criteria

The system passes when:

1. A new ticket automatically gets a stage, owner, next action, and follow-up time.
2. A stage change resets stage SLA correctly.
3. Due Soon tickets appear before overdue.
4. Overdue tickets escalate automatically.
5. Staff cannot save an active ticket without next follow-up.
6. Every follow-up has an activity log.
7. Managers can see all risky tickets.
8. Closed tickets are removed from follow-up queues.
9. Repeat complaints are escalated immediately.
10. No ticket can become a forgotten ledger entry.
