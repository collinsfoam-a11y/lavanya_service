# Lavanya eMart Helpdesk — Manager Daily Checklist

Run this every morning (target: under 15 minutes) using the Lavanya saved views
and the daily reminder notifications.

## Morning queue review

| # | Check                                   | Where                                          | Action threshold                          |
|---|------------------------------------------|------------------------------------------------|-------------------------------------------|
| 1 | Registration Pending                     | View: Lavanya - Registration Pending           | Anything older than 1 working day          |
| 2 | Brand Registered without progress        | View: Lavanya - Brand Registered               | No update for 2+ days → call service center|
| 3 | Follow-up Due Today                      | Daily reminder notification                    | Every item assigned to a named person      |
| 4 | Overdue Follow-ups                       | Daily reminder notification                    | ZERO tolerance — chase same day            |
| 5 | Waiting on Customer                      | View: Lavanya - Waiting on Customer            | 3+ days → call customer, else move status  |
| 6 | Waiting on Part / Approval               | View: Lavanya - Waiting on Part / Approval     | Check ETA realism, escalate stale parts    |
| 7 | Product at Store aging                   | View: Lavanya - Customer Product at Store      | 7+ days in store → escalate                |
| 8 | Ready for Pickup not collected           | View: Lavanya - Ready for Pickup               | 3+ days → pickup reminder to customer      |
| 9 | Repeat complaints                        | View: Lavanya - Repeated Complaints            | Review root cause before next visit        |
| 10| Yesterday's closures audit (spot check)  | View: Lavanya - Closed / Resolved              | Narration quality + customer confirmation  |

## Weekly (Monday)

- Review SLA breaches and near-breaches for the past week.
- Review Cancelled tickets — confirm none were real complaints dropped.
- Check open ticket count trend vs last week.
- Verify the daily reminder scheduler ran every day (Scheduled Job Log).

## Pilot guardrail

Pilot is limited to **Customer Complaint - Site**. Other ticket types may be
created for testing but must not be given to customers until the manager
approves stage 2.
