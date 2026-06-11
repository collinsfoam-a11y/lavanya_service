# Lavanya eMart Helpdesk — Staff Quick Guide (Phase 1 Pilot)

Pilot scope: **Customer Complaint - Site** tickets only. Other ticket types go
live after manager approval.

## 1. Create a ticket

1. Helpdesk portal > Tickets > New (or use the customer portal form).
2. Subject: short problem summary, e.g. "Voltas AC not cooling".
3. Select Ticket Type = Customer Complaint - Site, Priority (default Medium).

## 2. Enter customer and product details

Required habit — fill these on first contact:

- Customer Name, Phone 1 (10 digits — the system strips +91/spaces and rejects
  anything that is not 10 digits), Address, Pincode
- Product Type, Brand, Model No, Serial No (serial is MANDATORY for
  Replacement / DOA and Customer Product at Store)
- Purchased from Lavanya? + Invoice Source / Old ERP Reference if yes
- Warranty Status

## 3. Register with the brand

When the brand/service-center complaint is lodged:

1. Set Brand Ticket Number and Registration Date.
2. Then change status to **Brand Registered**.
   (The system blocks Brand Registered without both fields.)

## 4. Keep the ticket alive — pending reason + follow-up

Any ticket in Registration Pending, Brand Registered, In Progress, Waiting on
Customer, Waiting on Part / Approval, or Ready for Pickup MUST have:

- **Pending Reason** — why it is stuck (e.g. "Part ordered, ETA 3 days")
- **Next Follow-up Date** — when you will chase it next

The system blocks saving these statuses without both. Daily reminders are
generated from Next Follow-up Date — an empty date means a forgotten customer.

## 5. Status changes — what each means

| Status                     | Use when                                        |
| -------------------------- | ----------------------------------------------- |
| New                        | Just created, nothing done yet                  |
| Registration Pending       | Waiting to lodge with brand / verify purchase   |
| Brand Registered           | Brand ticket number received                    |
| In Progress                | Technician / service work underway              |
| Waiting on Customer        | Customer must respond / be available            |
| Waiting on Part / Approval | Part, estimate approval, or replacement pending |
| Ready for Pickup           | Store product repaired, customer informed       |
| Resolved                   | Work done, awaiting closure confirmation        |
| Closed                     | Evidence complete (see below)                   |
| Cancelled                  | Duplicate / withdrawn / guidance-only           |

## 6. Product received at store

1. Create a **Service Product Receipt** linked to the ticket.
2. Record physical condition and accessories honestly — this protects you.
3. Print the **Lavanya Service Product Receipt Token** and give it to the
   customer; file the signed copy.
4. Every handover (to service center / technician / back / delivered) gets a
   Custody Log row; keep Current Custody Status matching the latest log row
   (the system enforces this).

## 7. Close with evidence

To set status **Closed** you must fill:

- Closure Type
- Work Narration (what was actually done)
- Customer Confirmation Received = Yes (or Not Required, with reason in narration)

The system blocks closing without these. No narration = not closed.
