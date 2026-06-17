# Lavanya eMart Stage Follow-up SLA Matrix

Date: 2026-06-16
Purpose: Define mandatory follow-up at every ticket stage and force action before a ticket becomes overdue.

## 1. Rule

Every active ticket must always have:

1. current stage
2. pending reason
3. next action
4. next action owner
5. next follow-up date/time
6. stage due time
7. escalation level
8. last activity log entry

A ticket must not sit in an active stage without a next follow-up. The system must create work before overdue, not after overdue.

## 2. Core control fields

Add or enforce these HD Ticket fields:

| Field | Type | Purpose |
|---|---|---|
| current_service_stage | Select | Operational stage |
| stage_started_at | Datetime | Stage age calculation |
| stage_due_at | Datetime | Stage deadline |
| follow_up_required | Check | Always true for active stages |
| next_follow_up_at | Datetime | Next staff action time |
| pre_overdue_alert_at | Datetime | Reminder before due time |
| next_action | Select | Required action |
| next_action_owner | Link User | Responsible user |
| pending_reason | Select | Why the ticket is not closed |
| escalation_level | Select | None / Coordinator / Manager / Owner |
| last_activity_at | Datetime | Latest action trace |
| last_customer_update_at | Datetime | Customer communication control |
| overdue_status | Select | Not Due / Due Soon / Overdue / Breached |

## 3. Stage SLA matrix

| Stage | Follow-up before overdue | Owner |
|---|---|---|
| New / Open | 30 minutes | Front Desk |
| Customer Details Pending | 2 hours | Front Desk |
| Invoice Proof Pending | 4 hours | Front Desk |
| Registration Pending | 4 hours | Service Coordinator |
| Brand Line Busy | 2 hours | Service Coordinator |
| Brand Registered | 24 hours | Service Coordinator |
| Service Center Assigned | 24 hours | Service Coordinator |
| Technician Visit Pending | 24 hours | Service Coordinator |
| Customer Not Reachable | 24 hours | Front Desk |
| Waiting on Customer | 24 hours | Front Desk |
| Waiting on Part / Approval | 24 hours | Service Coordinator |
| Spare Pending | 24 hours | Service Coordinator |
| Estimate Approval Pending | 24 hours | Service Coordinator |
| Local Technician Pending | 24 hours | Service Coordinator |
| Product at Store | 24 hours | Service Coordinator |
| Handed to Service Center | 24 hours | Service Coordinator |
| Returned to Store | 4 hours | Front Desk |
| Ready for Pickup | 24 hours | Front Desk |
| Resolved | 24 hours | Service Coordinator |
| Closure Confirmation Pending | 24 hours | Front Desk |
| Closed | No follow-up | None |
| Cancelled | No follow-up | None |

## 4. Pre-overdue reminder rule

Do not wait until the due time.

Recommended reminder timing:

| Stage SLA | Pre-overdue alert |
|---|---|
| 30 minutes | 10 minutes before due |
| 2 hours | 30 minutes before due |
| 4 hours | 1 hour before due |
| 24 hours | 4 hours before due |
| 48 hours | 8 hours before due |

Logic:

- If `now >= pre_overdue_alert_at` and ticket is not completed, show in `Due Soon` queue.
- If `now >= stage_due_at`, show in `Overdue` queue.
- If overdue exceeds escalation threshold, raise escalation level.

## 5. Stage transition rules

When a ticket enters a new active stage, system must automatically set:

1. `stage_started_at = now`
2. `stage_due_at = now + stage_sla`
3. `pre_overdue_alert_at = stage_due_at - reminder_offset`
4. `follow_up_required = 1`
5. `next_follow_up_at = pre_overdue_alert_at`
6. `next_action = default action for stage`
7. `next_action_owner = role/user based on stage`
8. append activity log row

If stage is Closed or Cancelled:

1. `follow_up_required = 0`
2. clear next action owner
3. clear next follow-up time
4. require closure fields

## 6. Default next actions by stage

| Stage | Default next action |
|---|---|
| New / Open | Verify customer and product details |
| Customer Details Pending | Call customer for missing details |
| Invoice Proof Pending | Request invoice or purchase proof |
| Registration Pending | Register complaint with brand |
| Brand Line Busy | Retry brand registration |
| Brand Registered | Follow up with service center |
| Service Center Assigned | Confirm technician visit schedule |
| Technician Visit Pending | Confirm technician visit status |
| Customer Not Reachable | Retry customer call / WhatsApp |
| Waiting on Customer | Follow up with customer |
| Waiting on Part / Approval | Check approval or part status |
| Spare Pending | Follow up spare availability |
| Estimate Approval Pending | Get customer approval |
| Local Technician Pending | Assign or call technician |
| Product at Store | Move product to service center or technician |
| Handed to Service Center | Follow up repair status |
| Returned to Store | Inform customer for pickup |
| Ready for Pickup | Remind customer to collect |
| Resolved | Confirm customer satisfaction |
| Closure Confirmation Pending | Get final customer confirmation |

## 7. Escalation matrix

| Condition | Escalation |
|---|---|
| Due soon and no activity | Show in Due Soon queue |
| Overdue by 1 hour for short SLA stages | Coordinator |
| Overdue by 1 day | Manager |
| Overdue by 3 days | Owner |
| Spare pending over 3 days | Manager |
| Product at store over 7 days | Manager |
| Repeat complaint within 7 days | Manager immediately |
| Complaint after service within 2 days | Manager immediately |
| Ready for pickup over 3 days | Manager |
| Closure confirmation pending over 2 days | Manager |

## 8. Required queues

Create these HD Views or work queues:

1. Due Soon
2. Overdue Now
3. My Follow-ups Today
4. Registration Pending
5. Invoice Proof Pending
6. Brand Ticket Pending
7. Technician Visit Pending
8. Spare Pending
9. Product at Store
10. Ready for Pickup
11. Closure Confirmation Pending
12. Manager Escalation
13. Owner Escalation

## 9. Scheduler design

Add scheduler events in `hooks.py`:

```python
scheduler_events = {
    "hourly": [
        "lavanya_service.tasks.stage_followup.refresh_stage_followup_status",
        "lavanya_service.tasks.stage_followup.escalate_overdue_tickets",
    ],
    "daily": [
        "lavanya_service.tasks.stage_followup.create_daily_followup_digest",
    ],
}
```

## 10. Required backend functions

Create module:

`lavanya_service/tasks/stage_followup.py`

Functions:

1. `apply_stage_followup_defaults(doc)`
2. `calculate_stage_due_at(stage, started_at)`
3. `calculate_pre_overdue_alert_at(stage, due_at)`
4. `refresh_stage_followup_status()`
5. `escalate_overdue_tickets()`
6. `create_daily_followup_digest()`

Create module:

`lavanya_service/api/stage_actions.py`

Functions:

1. `set_stage(ticket, stage, pending_reason=None)`
2. `complete_followup(ticket, action_type, note, next_stage=None)`
3. `reschedule_followup(ticket, next_follow_up_at, reason)`
4. `get_due_soon()`
5. `get_overdue()`

## 11. Validation rules

Backend validation must block saving active tickets when:

- stage is active and `next_follow_up_at` is empty
- stage is active and `next_action` is empty
- stage is active and `next_action_owner` is empty
- pending status has no pending reason
- overdue ticket is rescheduled without reason
- Closed ticket has no closure type
- Closed ticket has no work narration
- Closed ticket has no customer confirmation

## 12. Quick-action behavior

Every quick action must set the next follow-up before saving.

Example:

| Quick action | Next stage | Follow-up |
|---|---|---|
| Brand Line Busy | Brand Line Busy | 2 hours |
| Brand Registered | Brand Registered | 24 hours |
| Customer Not Reachable | Customer Not Reachable | 24 hours |
| Spare Pending | Spare Pending | 24 hours |
| Ready for Pickup | Ready for Pickup | 24 hours |
| Closure Confirmation Pending | Closure Confirmation Pending | 24 hours |

## 13. Definition of done

This stage follow-up system is complete when:

1. Every active stage has mandatory follow-up.
2. Tickets appear in Due Soon before becoming overdue.
3. Overdue tickets escalate automatically.
4. Staff cannot save pending tickets without next action.
5. Manager can view overdue and due-soon cases in one screen.
6. Owner can see high-risk service delay cases.
7. Every follow-up completion creates an activity log.
8. Stage change resets SLA clock correctly.
9. Closed and cancelled tickets are excluded from follow-up queues.
