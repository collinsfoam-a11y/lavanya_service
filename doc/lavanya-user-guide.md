# Lavanya Service Console — User Guide

A guide to using the Service Console for day-to-day service work. The console is
the staff workspace for handling customer complaints about appliances — from the
moment a complaint is logged through brand registration, repair, and handover.

> **Open the console:** go to **`/frontend`** on your Lavanya site and sign in with
> your staff account. What you see depends on your role (see [Roles](#roles--who-can-do-what)).

---

## The layout

Every screen shares the same frame:

- **Left sidebar** — your main menu: **Today's Work**, **Tickets**, **Reports**,
  **New Ticket**. On a phone these move to a bar at the bottom.
- **Top bar** — a **search box** (type a ticket number, customer name, or phone and
  press Enter to jump to the Tickets list filtered to it) and your profile icon.
- **Logout** is at the bottom of the sidebar.

---

## Today's Work — your daily queue

This is the home screen and the first thing to check each day. It answers *"what
needs my attention right now?"*

**The six cards at the top** are live counts of work waiting on you:

| Card | What it means |
|---|---|
| **Overdue Follow-up** | Tickets whose follow-up date has passed. The second line shows how old the oldest one is. |
| **Due Today** | Follow-ups scheduled for today. |
| **Reg Pending** | Tickets waiting for brand/manufacturer registration. |
| **Wait Customer** | Paused, waiting on the customer (invoice, approval, pickup). |
| **Ready Pickup** | Repaired products ready to hand back. |
| **New Complaint** | Freshly logged complaints to triage. |

Click any card to jump to that section in the **Action Queue** below, which lists the
actual tickets grouped by what needs doing, most urgent first. **Click any ticket row
to open it.**

> What you see here is tailored to your role — a Front Desk user sees pickup/intake
> work, an Agent sees follow-up work, and managers see everything.

---

## Tickets — find and browse

The **Tickets** screen lists every ticket you're allowed to see.

- **Search** by ticket number, subject, customer, or phone.
- **Filter** by status using the chips (All, New, Registration Pending, In Progress,
  Waiting on Customer, Ready for Pickup, and so on).
- **Load more** at the bottom pages through long lists.
- Click a row to open the ticket.

Each row shows the status, the **SLA badge** (see below), the pending reason, and the
next follow-up date (overdue dates are red).

### Reading the badges

- **Status chip** — the ticket's current stage (New, In Progress, Waiting on Customer,
  Ready for Pickup, Resolved, Closed…).
- **SLA badge** — your service-level commitment:
  - 🔴 **SLA breached** — the deadline was missed.
  - 🟢 **SLA met** — fulfilled.
  - ⚪ **SLA paused** — the clock is paused.
  - **Resp/Resln due Xh / Xd** — first-response or resolution due in that time
    (amber within 24 hours, red if overdue). Hover for the exact deadline.

---

## New Ticket — logging a complaint

Click **New Ticket** in the sidebar (or the **+ New Ticket** button on the Tickets
screen) to log a complaint without leaving the console.

Fill in the form:

- **Required:** Customer Name, Mobile, Brand, Product Type, Complaint Details.
- **Optional:** Ticket Type, Warranty, Model No., Serial No., Source, Address, Pincode.

> **Returning customer?** Type the **mobile number first** — if the customer is on
> record, the console auto-fills their name, address, and pincode (and suggests their
> last brand/product), with a "returning customer" note. It only fills empty fields,
> so anything you've already typed is kept.

The **Create Ticket** button stays greyed out until the required fields are filled.
After you submit, you'll see a confirmation with the new ticket number and two choices:

- **Open ticket** — jump straight to it.
- **Create another** — clear the form for the next complaint.

New tickets appear immediately on **Today's Work** (under New Complaint) and in the
**Tickets** list.

---

## Working a ticket — the detail drawer

Clicking a ticket opens a drawer with everything about it on the left and **Quick
Actions** on the right.

### What's on the left

- **Header** — ticket number, status, priority, and the SLA badge.
- **Customer / Product / Workflow / Product Custody** — the key details at a glance.
- **Activity** — the ticket's history, newest first:
  - 🔵 **Notes** you and colleagues add.
  - ⚪ **System events** (status changes, assignments) logged automatically.
  - **Add an internal note** in the box at the top and click **Post note** — it appears
    instantly and is visible to the team (not the customer).

### Quick Actions (right panel)

One-click steps that move the ticket through its lifecycle. Each opens a short form,
then updates the ticket. **Actions are limited by your role** — if you can't run one,
you'll get a clear message naming who can.

| Action | What it does | Who can run it |
|---|---|---|
| **Register Brand Complaint** | Records the brand ticket number + registration; moves to *Brand Registered*. | Manager, Coordinator |
| **Need Invoice** | Asks the customer for the invoice; moves to *Waiting on Customer*. | Manager, Coordinator, Agent |
| **Follow Up Service Center** | Logs a service-centre follow-up; sets the next state from the result. | Manager, Coordinator, Agent |
| **Waiting for Part** | Marks the ticket held for a part/approval. | Manager, Coordinator, Agent |
| **Create Product Receipt** | Records a product taken into store custody (for *Customer Product at Store* tickets). | Manager, Coordinator, Front Desk |
| **Mark Ready for Pickup** | Marks the repaired product ready for the customer. | Manager, Coordinator, Front Desk |
| **Customer Confirmed** | Records customer confirmation and closes the ticket. | Manager, Coordinator |
| **Close Ticket** | Closes with a closure type and work summary. | Manager, Coordinator |
| **Reopen Ticket** | Reopens a closed/resolved ticket (e.g. the customer says it's still not fixed). Shown only on closed tickets. | Manager, Coordinator |

### Product custody (when a product is taken into the store)

For *Customer Product at Store* tickets, after **Create Product Receipt** the drawer
shows a **Product custody** group to track the item's journey:

| Step | What it records | Who can run it |
|---|---|---|
| **Send to Service Center** | Product handed to the brand/service centre (with expected return date). | Manager, Coordinator, Front Desk |
| **Returned from SC** | Product received back at the store (with actual return date). | Manager, Coordinator, Front Desk |
| **Mark Ready for Pickup** | Repaired product ready for the customer. | Manager, Coordinator, Front Desk |
| **Delivered to Customer** | Product handed back — completes the custody trail. | Manager, Coordinator, Front Desk |

So the full at-store journey is: **Receive → Send to SC → Returned from SC → Ready for
Pickup → Delivered.**

Every action checks the rules on the server — required fields, valid stage, and your
permission — so you can't accidentally skip a step.

### Repeat complaints

When you open a ticket, the console checks for **earlier tickets from the same
customer/product**. If it finds any, a banner appears at the top listing them with a
**Link as repeat** button. Once linked, the ticket shows a "repeat complaint" tag
(with a **Clear** option). This helps spot products that keep coming back.

---

## Reports — the manager view

The **Reports** screen (managers and coordinators) opens with an **overview**:

- **Last 30 days** — a trend line of tickets **created** vs **resolved** per day.
- **By status** and **By closure type** — bar breakdowns of the current workload.

Below the overview is the **report catalog** — a card per report (Daily Follow-Up,
Brand Pending, Waiting on Customer/Part, Ready for Pickup, Product-at-Store Aging,
Closure, Repeat Complaints, Warranty Overrides), each showing a live count.

- **Click a card** to drill into its exact list of tickets.
- **Click a row** to open that ticket.
- **Export CSV** downloads the report's rows for spreadsheets or sharing.
- **Back to reports** returns to the catalog.

A card's count always matches the list it opens.

---

## Roles — who can do what

| Role | Sees on Today's Work | Can run |
|---|---|---|
| **Manager** | Everything | All actions + Reports |
| **Service Coordinator** | Everything | All actions + Reports |
| **Helpdesk Agent** | Follow-up, due-today, registration, waiting work | Need Invoice, Follow Up SC, Waiting for Part |
| **Front Desk** | Pickups, receipts, new complaints | Create Product Receipt, Mark Ready for Pickup |
| **Viewer** | Everything (read-only) | Nothing — view only |

---

## Tips & common questions

- **An action gave an error like "Please refresh the page."** Your page was open while
  the server was updated. Just refresh (Ctrl/Cmd + R) and try again.
- **"You're not permitted to run this."** That action is for another role — the message
  lists who can do it. Ask a Manager or Coordinator.
- **A new ticket isn't showing.** Refresh the page; the lists always re-read live data.
- **Notes are internal.** Anything you post in the ticket's Activity is for the team,
  not the customer.
- **Dates in red** mean overdue (follow-ups or SLA deadlines) — handle these first.

---

*The console runs alongside the full Helpdesk Desk; for advanced operations not shown
here, use the standard Helpdesk (the "Open in Standard Helpdesk" link in a ticket).*
