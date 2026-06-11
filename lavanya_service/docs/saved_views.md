# Lavanya Helpdesk — Saved Views (Staff Queues)

The following 12 HD Views are shipped as fixtures (`hd_view.json`) and appear in
the Helpdesk agent portal sidebar. They are the Phase 1 replacement for a
dashboard-card model.

| View                                  | Filter intent                                  |
| ------------------------------------- | ---------------------------------------------- |
| Lavanya - New Complaints              | status = New                                   |
| Lavanya - Registration Pending        | status = Registration Pending                  |
| Lavanya - Brand Registered            | status = Brand Registered                      |
| Lavanya - In Progress                 | status = In Progress                           |
| Lavanya - Waiting on Customer         | status = Waiting on Customer                   |
| Lavanya - Waiting on Part / Approval  | status = Waiting on Part / Approval            |
| Lavanya - Ready for Pickup            | status = Ready for Pickup                      |
| Lavanya - Customer Product at Store   | ticket_type = Customer Product at Store        |
| Lavanya - Stock Complaint             | ticket_type = Stock Complaint                  |
| Lavanya - Installation / Demo         | ticket_type = Installation / Demo              |
| Lavanya - Repeated Complaints         | is_repeated_complaint = Yes                    |
| Lavanya - Closed / Resolved           | status in (Closed, Resolved)                   |

## Date-driven queues (not static views)

Frappe/Helpdesk saved views cannot express "today" relative dates statically.
These queues are therefore covered by the daily reminder scanner
(`lavanya_service.reminders`) which emits HD Notifications instead:

| Queue                | Mechanism                                          |
| -------------------- | -------------------------------------------------- |
| Follow-up Due Today  | reminder scan on next_follow_up_date = today       |
| Overdue Follow-ups   | reminder scan on next_follow_up_date < today       |
| New Today            | use "Lavanya - New Complaints" + sort by created   |
| Closed Today         | use "Lavanya - Closed / Resolved" + sort by closed |
| Brand Ticket Missing | reminder scan: Brand Registered w/o ticket number  |

Managers needing precise day-bounded lists should use the list filter UI with
an explicit date until the reports/dashboard phase lands.
