# Advanced AI Reminder Engine Plan

Date: 2026-06-17
Purpose: Add an advanced auto-reminder system for Lavanya eMart Helpdesk where reminder days/hours are configurable by brand, product, call type, service stage, warranty route, and customer risk. The goal is to prevent customer disappointment by warning staff before delay, not after delay.

## 1. Goal

The reminder engine must make sure no active ticket is forgotten.

It should automatically decide:

1. when the next reminder is needed
2. who should follow up
3. whether the customer must be informed
4. when the case should move to Due Soon
5. when it becomes overdue
6. when manager/owner escalation is required
7. whether AI should suggest a better next action or message

The system should be rule-first and AI-assisted. AI should not replace mandatory rules.

## 2. Core principle

Never depend only on manual follow-up dates.

Use this priority order:

1. Explicit manual next follow-up, if staff entered one
2. Brand/call-type/stage reminder rule
3. Product/category default rule
4. Global fallback rule
5. AI suggestion only as recommendation, not final authority

## 3. Reminder configuration hierarchy

Reminder timing should be resolved in this order:

| Priority | Source | Example |
|---|---|---|
| 1 | Manual override | Manager sets follow-up tomorrow 11 AM |
| 2 | Brand + call type + stage rule | LG + Brand Warranty + Technician Visit Pending = 24 hours |
| 3 | Brand + product category rule | Daikin + AC = 12 hours for installation follow-up |
| 4 | Call type + stage rule | Installation + Technician Visit Pending = 24 hours |
| 5 | Service flow default | Product at Store = 24 hours |
| 6 | Global default | Follow up every 24 hours |

## 4. New DocType: Lavanya Reminder Rule

Create DocType:

`Lavanya Reminder Rule`

Fields:

| Field | Type | Purpose |
|---|---|---|
| rule_name | Data | Human readable rule name |
| enabled | Check | Active/inactive |
| priority | Int | Higher priority wins |
| brand | Link/Data | Optional brand-specific rule |
| product_type | Link/Data | Optional product type/category |
| ticket_type | Select | Complaint, installation, stock, periodic, etc. |
| service_flow_type | Select | Customer Complaint, Product at Store, etc. |
| current_service_stage | Select | Stage this rule applies to |
| warranty_route | Select | Brand / Extended / Out of Warranty |
| pending_reason | Select | Optional matching reason |
| customer_priority | Select | Normal / High / VIP / Repeat Complaint |
| first_followup_after_minutes | Int | First reminder after stage starts |
| repeat_every_minutes | Int | Repeat interval while pending |
| due_soon_before_minutes | Int | When to show Due Soon before due |
| overdue_after_minutes | Int | Deadline after stage starts |
| manager_escalate_after_minutes | Int | Manager escalation timing |
| owner_escalate_after_minutes | Int | Owner escalation timing |
| customer_update_required | Check | Whether customer must be updated |
| customer_update_every_minutes | Int | How often customer must be informed |
| pause_when_sla_paused | Check | Whether reminder pauses with SLA |
| business_hours_only | Check | Restrict reminders to business hours |
| notes | Small Text | Rule explanation |

## 5. Reminder examples

### 5.1 Brand warranty complaint

| Brand | Product | Stage | First follow-up | Repeat | Escalation |
|---|---|---|---|---|---|
| LG | Refrigerator | Brand Registered | 24h | 24h | Manager after 48h |
| Samsung | TV | Technician Visit Pending | 24h | 24h | Manager after 48h |
| Daikin | AC | Installation Registered | 12h | 12h | Manager after 24h |
| Voltas | AC | Technician Visit Pending | 24h | 24h | Manager after 48h |

### 5.2 Product at store

| Stage | First follow-up | Repeat | Escalation |
|---|---|---|---|
| Product Received at Store | 30 min | 2h | Manager after 4h |
| Handed to Service Center | 24h | 24h | Manager after 72h |
| Returned to Store | 4h | 24h | Manager after 24h |
| Ready for Pickup | 24h | 24h | Manager after 72h |

### 5.3 Installation / demo

| Stage | First follow-up | Repeat | Escalation |
|---|---|---|---|
| Brand Installation Registration Pending | 4h | 4h | Manager after 8h |
| Technician Visit Scheduled | On visit day | 12h | Manager after missed visit |
| Technician Visit Pending | 24h | 24h | Manager after 48h |
| Customer Verification Pending | 24h | 24h | Manager after 48h |

### 5.4 Extended warranty

| Stage | First follow-up | Repeat | Escalation |
|---|---|---|---|
| Extended Warranty Document Pending | 4h | 24h | Manager after 48h |
| Claim Registration Pending | 4h | 4h | Manager after 8h |
| Provider Review Pending | 24h | 24h | Manager after 72h |
| Provider Technician Visit Pending | 24h | 24h | Manager after 48h |

### 5.5 Stock complaint

| Stage | First follow-up | Repeat | Escalation |
|---|---|---|---|
| Proof Capture Pending | 2h | 2h | Manager after 4h |
| Supplier Follow-up Pending | 24h | 24h | Manager after 72h |
| Credit Note Pending | 24h | 24h | Manager after 72h |
| Replacement Pending | 24h | 24h | Manager after 72h |

## 6. AI-assisted reminder intelligence

AI should be used only as assistant logic, not as the final rule engine.

AI can help with:

1. classify complaint severity
2. suggest service flow type
3. suggest current stage from latest narration
4. suggest next action
5. draft customer update message
6. detect customer disappointment risk
7. detect service center delay risk
8. detect repeat complaint or escalation requirement
9. summarize ticket history for manager
10. recommend whether to call customer or service center next

AI must not:

- close tickets automatically
- override mandatory validation
- decide warranty eligibility without proof
- send customer messages without approval unless explicitly enabled
- change payment/commission/stock settlement without staff action

## 7. AI risk score

Add derived field:

`customer_disappointment_risk`

Options:

- Low
- Medium
- High
- Critical

Suggested scoring factors:

| Factor | Risk increase |
|---|---|
| Ticket overdue | High |
| Repeat complaint | High |
| Product at store > 7 days | High |
| Spare pending > 3 days | Medium/High |
| Customer not reachable repeatedly | Medium |
| Brand/service center not responding | High |
| Customer negative note in narration | High |
| Installation missed | High |
| Extended warranty denied | Medium/High |
| Payment/charge dispute | High |
| High-value product | Medium |

## 8. AI suggested next action

Add optional fields:

| Field | Purpose |
|---|---|
| ai_suggested_next_action | AI recommendation |
| ai_suggested_customer_message | Draft message for customer |
| ai_risk_reason | Why AI marked risk |
| ai_last_reviewed_at | Last AI evaluation time |
| ai_review_status | Not Reviewed / Suggested / Accepted / Ignored |

Staff should see AI suggestions but must approve action.

## 9. Customer update automation

Every reminder rule can specify whether customer update is mandatory.

For waiting stages, customer update should be required:

- Brand Registered
- Service Center Follow-up
- Technician Visit Pending
- Spare Pending
- Extended Warranty Provider Review
- Product Ready for Pickup
- Installation Visit Pending
- Stock issue affecting customer delivery

Customer update channels:

- Phone
- WhatsApp
- Direct
- SMS

For WhatsApp, use existing wa.me first. Later integrate provider API.

## 10. Advanced reminder calculation

Create function:

`resolve_reminder_rule(ticket)`

It should:

1. find enabled rules matching brand/product/type/stage/warranty route
2. sort by priority
3. apply first matching rule
4. calculate next_follow_up_at
5. calculate pre_overdue_alert_at
6. calculate stage_due_at
7. calculate manager/owner escalation thresholds
8. fallback to default rule if no match

Create function:

`refresh_ticket_reminder_state(ticket)`

It should update:

- next_follow_up_at
- stage_due_at
- pre_overdue_alert_at
- overdue_status
- escalation_level
- customer_update_due
- customer_disappointment_risk

## 11. Scheduler design

Use scheduler:

```python
scheduler_events = {
    "hourly": [
        "lavanya_service.tasks.reminder_engine.refresh_due_soon_and_overdue",
        "lavanya_service.tasks.reminder_engine.escalate_high_risk_tickets",
    ],
    "daily": [
        "lavanya_service.tasks.reminder_engine.create_manager_service_digest",
    ],
}
```

Optional AI scheduler:

```python
scheduler_events = {
    "daily": [
        "lavanya_service.tasks.ai_review.review_high_risk_service_tickets",
    ],
}
```

AI review should only run on high-risk or overdue tickets to control cost and avoid noise.

## 12. Manager digest

Daily digest should show:

- overdue tickets
- Due Soon high-priority tickets
- repeat complaints
- product at store ageing
- spare pending ageing
- extended warranty pending
- installation missed
- stock issue high-value pending
- customer disappointment risk High/Critical

## 13. Customer promise tracking

Add field:

`customer_promised_update_at`

When staff tells customer they will call/update by a time, system must track that promise.

If promised update time passes, ticket should show:

`Customer Promise Breach`

This is important to avoid disappointment.

Required fields:

| Field | Purpose |
|---|---|
| customer_promised_update_at | Time promised to customer |
| customer_promise_status | Pending / Met / Breached / Not Applicable |
| promise_breach_reason | Reason if missed |

## 14. Efficiency design

To make the system efficient:

1. Staff should work from Today’s Work only.
2. Tickets should auto-group by next action.
3. Quick actions should set next reminder automatically.
4. AI should summarize old history before staff calls.
5. Manager should see only exception/risk cases.
6. Owner should see only high-risk or repeated failures.

## 15. UI changes

Add cards:

- Due Soon
- Customer Promise Breach
- High Risk Customers
- Extended Warranty Pending
- Product at Store Ageing
- Installation Missed
- Spare Pending Ageing

Add filters:

- Brand
- Product Type
- Call Type / Ticket Type
- Service Flow
- Stage
- Risk Level
- Escalation Level

Add drawer section:

`Reminder Intelligence`

Fields:

- Reminder Rule Applied
- Next Follow-up
- Due Soon At
- Stage Due At
- Customer Update Due
- Risk Level
- AI Suggested Next Action

## 16. Validation rules

Block or warn:

- active ticket without reminder rule/fallback
- waiting stage without customer update due time
- promised customer update missed without reason
- manual follow-up rescheduled without reason
- high-risk ticket closed without manager review

## 17. Implementation order

### Sprint R1: Rule engine foundation

1. Create `Lavanya Reminder Rule` DocType.
2. Create default global rules.
3. Add fields for rule applied, due soon, stage due, customer update due.
4. Build `resolve_reminder_rule()`.
5. Build fallback logic.

### Sprint R2: Today’s Work integration

1. Add Due Soon card.
2. Add reminder rule grouping.
3. Add risk level grouping.
4. Add customer promise breach queue.

### Sprint R3: Customer update and promise tracking

1. Add customer promised update fields.
2. Add quick action `Customer Informed`.
3. Add promise breach detection.
4. Add customer communication report.

### Sprint R4: AI assist

1. Add AI review only for overdue/high-risk tickets.
2. Generate AI suggested next action.
3. Generate customer message draft.
4. Add manager summary.
5. Keep human approval mandatory.

### Sprint R5: Brand/product tuning

1. Add brand-wise rules.
2. Add product-wise rules.
3. Add call-type rules.
4. Tune using real data after pilot.

## 18. Definition of done

Reminder engine is complete when:

1. every active ticket has a reminder rule or fallback rule
2. rules can differ by brand, product, call type, and stage
3. Due Soon appears before overdue
4. customer update promise is tracked
5. manager sees risk before customer complains
6. AI suggests next action but does not bypass rules
7. every quick action automatically sets the next reminder
8. no customer is left without update while waiting
