# Internal Pilot Readiness - Phase 1P

## Pilot Scope
This phase serves as a readiness gate for a controlled internal pilot of the Lavanya eMart Helpdesk system. It targets limited showroom staff workflows.
**Excluded:** QR public intake, WhatsApp/SMS/email automation, full production operations, and external customer self-service.

## Allowed Ticket Types
- Customer Complaint - Site
- Customer Product at Store
- Installation / Demo

## Staff Roles
- **Manager** (`Lavanya Manager`): Full visibility, reporting, and closure override capabilities.
- **Service Coordinator** (`Lavanya Service Coordinator`): Complete ticket lifecycle management, receipt actions, and advanced Today's Work visibility.
- **Helpdesk Agent** (`Lavanya Helpdesk Agent`): Focuses on follow-up, registration pending, waiting on customer, and overdue tickets.
- **Front Desk** (`Lavanya Front Desk`): Initial intake, quick ticket creation, product receipt handling, and front-line triage.
- **Viewer** (`Lavanya Viewer`): Read-only reporting access.

## Pilot Users
- `uat.manager@lavanya.local`
- `uat.coordinator@lavanya.local`
- `uat.agent@lavanya.local`
- `uat.frontdesk@lavanya.local`
- `uat.viewer@lavanya.local`

## Usage Instructions

### How to Create a Complaint
1. Log into the Frappe Helpdesk.
2. Select **Tickets** > **New Ticket**.
3. Set the Ticket Type to one of the allowed types.
4. Fill in customer details (phone numbers are normalized to 10 digits).
5. Specify the Product Category and Item.
6. Submit the ticket.

### How to Use Today's Work
1. Navigate to the **Today's Work** section.
2. Depending on your role, you will see a categorized list of tickets (e.g., *Due Today*, *Overdue Follow Up*, *Waiting on Customer*).
3. Click any category card to view its corresponding tickets.

### How to Use Quick Actions
1. Open a ticket.
2. In the ticket action menu or sidebar, use actions such as **Need Invoice**, **Follow Up Service Center**, or **Product Ready**.
3. This transitions the ticket status correctly without requiring manual edits.

### How to Create a Product Receipt
1. When a ticket is in *Registration Pending* or equivalent status, select the **Product Receipt** quick action.
2. Log the physical condition and any accessories received.
3. A unique `LV-SR` receipt is generated and linked to the ticket.

### How to Print Token Slip
1. Open the associated **Service Product Receipt**.
2. Click the print icon.
3. Select the **Lavanya Service Product Receipt Token** print format to generate the slip for the customer.

### How to Close a Ticket
1. Navigate to an open ticket.
2. Ensure you have the proper role (Manager or Service Coordinator).
3. Fill in the **Closure Evidence**, **Closure Type**, and **Work Narration**.
4. Confirm customer acceptance and change the status to **Closed**.

### How Manager Checks Reports
1. Navigate to the **Manager Dashboard**.
2. View metrics and aging summaries.
3. Drill down into specific datasets like *Brand Pending* or *Waiting on Part*.

## Known Limitations
- WhatsApp and SMS notifications are strictly disabled in this phase.
- Automated repeat complaint detection evaluates fields but requires manual linking by a Manager.
- True front-desk tablet/QR scanner interface is not yet available; all entry is manual.

## Rollback Plan
In the event of a critical failure during the pilot:
1. Cease system usage immediately.
2. Log out all active UAT users.
3. Restore the database and files using the pre-pilot backup.
4. Contact the administration team for investigation.

## Backup Path
`./lavanya-dev.localhost/private/backups/20260612_232500-lavanya-dev_localhost-database.sql.gz`

## Go / No-Go Decision
**Decision:** GO
All pre-pilot readiness checks have passed successfully. No forbidden side effects or data leaks were detected. The system is stable for internal usage by showroom staff.
