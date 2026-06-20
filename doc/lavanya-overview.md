# Lavanya Service App Overview for AI Agents

## Introduction

This document provides a comprehensive overview of the Lavanya Service application, a custom solution built on the Frappe Framework. It is intended as a reference for AI agents and developers who need to understand the full context of the app when performing tasks or making decisions. The app extends Frappe's open‑source Helpdesk system to manage after‑sales service and complaint workflows for Lavanya eMart, a home‑appliance retailer. The goal is to streamline complaint intake, warranty verification, brand service registration, technician dispatch, spare management and customer follow‑up, while keeping the system flexible and upgrade‑safe.

## Purpose & Scope

Lavanya Service is designed to handle everything from the moment a customer reports an issue to the point when the product is repaired and returned. The app must support:

- **Complaint intake** – capturing customer details, product type, warranty status and complaint type.
- **Brand registration** – recording the brand ticket number and coordinating with the manufacturer's service centre.
- **Technician management** – assigning requests to either an authorised service centre or a local technician, depending on warranty and product.
- **Product custody** – tracking the physical movement of products between the store, service centre and technician via receipts and custody logs.
- **Follow‑ups and spares** – scheduling follow‑ups with service centres, monitoring spare parts and approvals, and escalating when delays occur.
- **Closure & customer feedback** – documenting the final outcome, ensuring the customer's confirmation and gathering closure type (repaired, replaced, refunded, etc.).

The system is built on the Frappe Framework, which offers strong data modelling, workflow automation and customization capabilities. Frappe Helpdesk allows teams to add custom fields, create custom views, and automate ticket routing and reminders. These features are critical for tailoring the service process to Lavanya's needs.

## Domain Model

The app uses a mix of built‑in Helpdesk doctypes and custom doctypes to represent all service entities:

- **HD Ticket (extended)** – the central document for each complaint. Extended fields include `warranty_status`, `manufacturer_registered`, `brand_ticket_number`, `registration_date`, `next_follow_up_date`, `pending_reason`, `service_center`, `service_product_receipt`, `closure_type`, `customer_confirmation_received`, `is_repeated_complaint`, `previous_ticket_link`, `work_narration`, `closed_by` and `closure_date`. These capture the entire after‑sales workflow.
- **Brand Service Master** – lists the authorised service centres for each brand and product category.
- **Service Center Master** – stores contact and address details for individual service centres.
- **Local Technician Master** – tracks local technicians who can handle out‑of‑warranty or brand‑denied repairs.
- **Free Service Rule** – defines eligibility rules for free service (e.g., warranty extensions or special campaigns).
- **Service Product Receipt** – represents the product receipt when customers drop off items at the store; includes custody status and accessory list.
- **Custody Log Entry** – child table of Service Product Receipt capturing transfers between store, service centre and technician.
- **Lavanya Customer Profile, Product Category and Product Item** – reference tables for customer demographics, product lines and specific models.

## Roles & Permissions

Roles control which actions users can perform and which tickets they see. The key roles are:

| Role | Capabilities |
|------|-------------|
| Lavanya Manager | Full control: all quick actions, all work buckets |
| Lavanya Service Coordinator | Same as Manager, used for day‑to‑day control |
| Lavanya Helpdesk Agent | Can mark tickets needing invoice, follow up with service centres, set waiting‑for‑part status |
| Lavanya Front Desk | Creates product receipts, marks product ready for pickup |
| Lavanya Viewer | Read‑only access to all buckets |

Every quick action checks the acting user's role, the ticket status and required fields on the server. Client‑side UI gating is never trusted; all logic is enforced in the backend.

## Ticket Lifecycle & Business Rules

Each ticket progresses through a defined lifecycle:

1. **New** – A complaint is logged but not yet categorised.
2. **Registration Pending** – Warranty case where no brand ticket number is recorded. The system's "registration recommended" logic flags tickets that meet this condition (in warranty, not yet registered).
3. **Brand Registered** – Brand ticket number recorded; waiting for updates from the manufacturer.
4. **In Progress** – Service centre or technician assigned and working.
5. **Waiting on Customer** – Action required from the customer (e.g., invoice, payment, availability).
6. **Waiting on Part / Approval** – Awaiting spare parts or manufacturer approval.
7. **Ready for Pickup** – Service completed and product returned to the store.
8. **Resolved** – Work done but awaiting closure confirmation.
9. **Closed / Cancelled** – Ticket resolved and confirmed (or cancelled).

Quick actions update fields and statuses accordingly. For example, "Register Brand Complaint" requires a brand ticket number and sets status to Brand Registered; "Need Invoice from Customer" sets status to Waiting on Customer and logs the reason "Invoice Pending".

## UI & UX Requirements

The front‑desk SPA is built using Frappe UI (Tailwind CSS and Vue 3) to ensure a clean, responsive interface. Key UX elements include:

- **Dashboard cards** – At the top of the SPA, show cards summarising counts of "Overdue follow‑ups", "Due today", "Registration pending", "Waiting on customer", "Waiting on part", "Ready for pickup", "Resolved today", etc. Clicking a card filters the list below.
- **Today's Work buckets** – Tickets are grouped into priority buckets (overdue follow‑up, due today, registration recommended, registration pending, waiting on customer, waiting on part, ready for pickup, product receipt missing, closure pending, new complaints). A fallback bucket should appear last for tickets that do not match any category.
- **Urgency badges** – Display coloured badges (e.g., red for overdue, orange for due today) next to each ticket in both the Today's Work section and the global Tickets list.
- **Ticket form wizard** – When creating a ticket, the form adapts to the selected ticket type. Buttons such as "Find Customer", "Find Invoice", "Check Warranty", "Register Brand Ticket", "Add Follow‑up", "Set Spare Pending", "Escalate" call server methods to perform those actions.
- **Dark mode** – Provide a dark theme option across the SPA for user comfort and brand consistency.

### Current SPA state (2026-06-19)

The SPA currently has 3 live pages + Ticket Detail drawer, all on the frappe-ui Tailwind preset:

- **Today's Work** (`/frontend/`) — 6 metric cards + priority buckets + Reminder Intelligence + collapsible filters
- **Tickets** (`/frontend/tickets`) — sortable table with search/status filters + infinite scroll
- **New Ticket** (`/frontend/new-ticket`) — flat intake form with customer lookup
- **Reports** (`/frontend/reports`) — catalog + report drill-down + trend charts + CSV export
- **Ticket Detail drawer** — left panel sections + right Quick Actions sidebar with 15+ actions

Fully built features: customer promise tracking, reminder engine, stage layer (flow/stage/next-action), SLA badges, WhatsApp integration, repeat-complaint detection, keyboard shortcuts, toast notifications, loading skeletons, dark mode not yet implemented.

See [`lavanya-spa-status.md`](lavanya-spa-status.md) for the detailed build log and pending work.

## Reporting & Dashboards

Managers need insight into the service operation. The app includes:

- **Daily follow‑up report** – Lists all tickets with follow‑ups due or overdue.
- **Brand pending** – Shows tickets waiting for the manufacturer's response.
- **Waiting on customer / part** – Identifies tickets stalled due to customer actions or parts shortages.
- **Product‑at‑store aging** – Flags products kept in store beyond defined timeframes.
- **Ready‑for‑pickup & closure pending** – Tracks items ready for customer collection and tickets awaiting final confirmation.

Charts display ticket counts by status, average resolution time, SLA compliance and repeat complaints. Frappe Helpdesk's custom views and saved filters help teams stay organised.

## Integrations & Extensions

Lavanya Service can integrate with other modules to create a unified platform:

- **ERPNext (optional)** – If ERPNext is installed, sync customers, items, serial numbers and sales invoices to populate warranty information. Integrate with stock and accounting modules for repair costs and spare part inventory.
- **Frappe HR** – Manage employee data, shifts, attendance and payroll. Frappe HR is highly customisable and integrates seamlessly with ERPNext's accounting. It allows you to create custom forms and workflows and build reports and dashboards.
- **Frappe CRM** – Capture leads from walk‑ins, calls, WhatsApp and social media. Frappe CRM is built on the same framework and makes it easy to add custom fields and automate processes. It integrates with WhatsApp, Facebook and Instagram to pull leads directly into your pipeline. Key features include contact & deal management, communications tracking, workflow automation and reports & analytics.
- **Messaging & WhatsApp** – Use Frappe's WhatsApp integration to send status updates and reminders to customers; ensure messaging adheres to privacy policies. Email notifications should preserve the thread using Message‑ID and In‑Reply‑To headers.
- **POS & E‑commerce** – For point‑of‑sale operations, integrate a modern POS app such as POS Next or POS Awesome (both Frappe‑based) to trigger service tickets when items are sold. For online sales, use Frappe Webshop or WooCommerce Fusion to synchronise orders and stock levels.

## Customisation & Low‑Code Configuration

Frappe's low‑code, no‑code capabilities are central to the app's flexibility. Helpdesk lets you add custom fields, control what customers see on the portal, route tickets automatically and define SLAs. You can save custom views and share them with the team to stay organised. The underlying Frappe Framework allows you to build forms, set advanced approval workflows, manage roles and permissions, and build dashboards without writing much code. Python scripts can be added to automate routine tasks.

### Key principles for customisation:

- **Don't modify core** – Place all business logic in the `lavanya_service` app. Override or extend behaviour via hooks, scripts and API endpoints.
- **Use server‑side validations** – Always enforce rules on the server, even if the UI prevents invalid input.
- **Write tests** – Implement unit tests for each server method and integration tests for workflows. Use Playwright or similar to test the SPA across browsers.

## Implementation Guidelines

### Phase 1 (Core functionality)
Set up the custom doctypes, extend HD Ticket fields, implement quick actions and build a minimal SPA with Today's Work buckets and basic ticket form. Ensure authentication, authorization and audit logging are correct. Integrate optional ERPNext if needed.

### Phase 2 (Adoption & polish)
Add native Helpdesk features like saved replies, bulk replies, attachments, signatures and multiple outbound email accounts. Implement dashboards, dark mode, and advanced metrics. Add saved views and automation rules. Provide portal settings for administrators.

### Phase 3 (Advanced analytics & integrations)
Integrate Frappe HR, CRM and messaging modules. Add AI or predictive analytics (e.g., auto‑classification, estimated resolution time) once data quality is high. Evaluate migration to Frappe v16 for improved performance and UI.

## Future Considerations

Frappe v16 introduces a completely new desk with a full‑width layout, sticky list headers and unlimited columns in tables, along with significant performance improvements and security enhancements. Migrating should be treated as a separate project after the Lavanya Service app stabilises. Monitor Frappe's roadmap for features like knowledge‑base engagement metrics and improved multi‑channel support.

## Reality notes (current codebase vs. this doc)

- **Dark mode** is listed in UX requirements but not yet implemented in the SPA.
- **Ticket form wizard** — the current `NewTicket.vue` is a flat form, not a multi-step wizard.
- **ERPNext integration** is noted as optional and not yet wired.
- **Frappe v16 migration** is a future concern; we remain on Frappe v15 / current Helpdesk.
- **Phase 2 items** (dashboards, saved views, dark mode, automation rules) are still pending.
- **Playwright E2E** tests are referenced but not yet written (only puppeteer screenshot scripts exist at `D:\lav_shots`).
