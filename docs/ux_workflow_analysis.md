# UI/UX Workflow Analysis: Practical Cases

This document analyzes the practical UI/UX workflows implemented in the Lavanya eMart Helpdesk system, breaking down how different roles interact with the system during day-to-day operations.

## 1. Front Desk: Customer Intake (Walk-in or Phone)
**Scenario:** A customer walks into the store or calls to report a broken appliance.
* **The Old Way:** Staff manually create a customer record, then manually create a ticket, typing out all details.
* **The New UX:** 
  * The Front Desk enters the 10-digit phone number.
  * The system automatically normalizes the phone number and fetches the `Lavanya Customer Profile`. If it's a new customer, a profile is auto-generated in the background.
  * Staff select the `Ticket Type` (e.g., *Customer Product at Store*).
  * Staff select the `Product Category` and `Product Item` (e.g., *Prestige Mixer*).
  * The ticket is submitted and automatically routed to the correct queue with default SLAs attached.

## 2. Front Desk / Coordinator: Receiving a Product
**Scenario:** The customer leaves their defective mixer at the store for repair.
* **The Old Way:** Staff write a paper receipt, or type notes into the ticket comments which easily get lost.
* **The New UX:** 
  * Staff click the **Product Receipt** quick action on the ticket.
  * They log the *Physical Condition* (e.g., "Scratches on the side") and *Accessories Received* (e.g., "Power cable, 2 jars").
  * The system generates a dedicated `Service Product Receipt` (e.g., `LV-SR-2026-0001`).
  * Staff click the **Print** icon to generate a formatted Token Slip to hand to the customer.
  * The ticket status automatically transitions to *Registration Pending*.

## 3. Helpdesk Agent: Daily Follow-ups
**Scenario:** Agents need to know who to call today without manually searching through hundreds of open tickets.
* **The Old Way:** Agents create manual list views and filter by status, often missing tickets that need follow-up today.
* **The New UX (Today's Work):**
  * Agents navigate to the **Today's Work** dashboard.
  * They see clear, actionable buckets: 
    * 🔴 **Overdue Follow Up**
    * 🟡 **Due Today**
    * 🔵 **Waiting on Customer**
    * 🟣 **Registration Pending**
  * Clicking a bucket immediately shows the relevant tickets, turning their workflow into a simple "clear the inbox" paradigm.

## 4. Service Coordinator: Managing the Repair Lifecycle
**Scenario:** A product needs to be sent to the brand's service center, and later followed up on.
* **The Old Way:** Coordinators manually change the ticket status, type a comment, and manually calculate the next follow-up date.
* **The New UX (Quick Actions):**
  * Instead of raw field edits, Coordinators use distinct action buttons:
    * **Follow Up Service Center**: Prompts for a follow-up date and auto-updates the status to *In Progress*.
    * **Need Invoice**: Auto-updates status to *Waiting on Customer* and prompts for a note.
    * **Mark Product Ready**: Updates the custody log, changes status to *Ready for Pickup*, and schedules a customer notification.
  * These actions enforce business logic (e.g., requiring a serial number for DOAs) without cluttering the UI with validation error popups during raw saves.

## 5. Store Manager: Oversight and Exception Handling
**Scenario:** The Manager needs to ensure SLAs are met and handle difficult customer situations.
* **The Old Way:** Managers run complex Frappe reports manually, exporting to Excel to find bottlenecks.
* **The New UX:**
  * **Dashboard:** The Manager views the Manager Reports dashboard, instantly seeing metrics like *Tickets exceeding SLA* or *Products waiting > 7 days*.
  * **Repeat Complaints:** When viewing a ticket, the system surfaces a warning if the customer has reported the same issue recently, prompting the Manager to prioritize it.
  * **Exception Handling:** Only Managers (and Coordinators) have the permission to formally **Close** a ticket, requiring them to input *Closure Evidence*, *Closure Type*, and *Work Narration*, ensuring high data quality for closed cases.

## Summary of UX Principles Applied
1. **Action-Driven over Data-Driven:** Users click "Mark Ready for Pickup" instead of manually changing the Status field to "Ready for Pickup" and typing a comment.
2. **Contextual Surfacing:** The "Today's Work" page removes the cognitive load of searching for work.
3. **Automated Linking:** Products, receipts, and customer profiles are linked invisibly without requiring the user to copy-paste IDs.
4. **Strict Boundaries:** Viewers can only view, Front Desk can only intake, and only Managers can close—simplifying the UI for each role by hiding unnecessary options.
