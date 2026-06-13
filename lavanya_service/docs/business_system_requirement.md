# Lavanya Service — Business System Requirement (BSR)

Companion to `final_phase1_readiness_report.md` and `production_hardening_checklist.md`.
Scope: Lavanya eMart after-sales service on Frappe Helpdesk (no Helpdesk core changes).

---

## Section 12: Main Business Workflows

The system supports these primary workflows (implemented and regression-tested):

1. **Customer intake** — phone-first lookup/normalization, auto customer-profile sync, brand/category/item selection.
2. **Ticket lifecycle** — status flow: New → Registration Pending → Brand Registered → In Progress → Waiting on Customer / Waiting on Part / Approval → Ready for Pickup → Resolved → Closed (Cancelled as needed).
3. **Brand/manufacturer registration** — warranty-driven recommendation, brand ticket number capture, registration pending reasons.
4. **Service routing** — service centre, local technician, out-of-warranty paid service with estimate approval gate.
5. **Product custody** — Service Product Receipt + Custody Log for product-at-store.
6. **Repeat complaint** — identity-anchored suggestion (mobile/serial), suggest-then-confirm.
7. **Follow-up & SLA** — pending reason + next follow-up enforced on open statuses; SLA breach reminders.
8. **Closure** — closure type + work narration + customer confirmation evidence required.
9. **Free service** — warranty/brand-backed recommendation hints.
10. **Public QR intake** — guest complaint submission with server-side validation, dropdown-constrained brand/product, honeypot + rate limiting.
11. **Manager reporting** — daily follow-up, brand-pending, waiting-on-customer/part, dashboard API.
12. **System reminders** — daily in-app HD Notifications (no email/SMS/WhatsApp side effects).

---

## 12A. UI/UX and User Ticket Entry Workflows

### UI/UX Objective
Make staff ticket entry and daily operations fast, low-error, and role-appropriate **using the standard Frappe/Helpdesk desk UI** — not a bespoke front end — so the system stays upgrade-safe and easy to maintain while pilot feedback is gathered.

### Main UI Principles
- **Standard desk form, organized.** Use the HD Ticket form with clear Section Breaks (Customer, Product, Purchase/Warranty, Brand Service, Follow-up, Closure) already shipped via custom fields + ticket template.
- **Role-aware visibility.** Service-coordination and closure fields are permlevel/role-gated; Front Desk and Viewer see/edit only what their role allows. No field is editable by a role that must not change it.
- **Action over navigation.** Common transitions are one-click **Quick Action** buttons (HD Form Scripts) rather than manual field edits.
- **One primary screen.** "Today's Work" is the staff home screen; everything else is reachable from a ticket or a saved HD View.
- **No free-text where a controlled value exists.** Brand = link to Brand Service Master; product type = Select; statuses/types/closure reasons are controlled lists.

### Recommended Navigation Structure
- **Today's Work** (default landing for Agent / Coordinator / Front Desk).
- **HD Ticket list** with the 12 saved Lavanya HD Views (New Complaints, Registration Pending, Brand Registered, In Progress, Waiting on Customer, Waiting on Part/Approval, Ready for Pickup, Customer Product at Store, Stock Complaint, Installation/Demo, Repeated Complaints, Closed/Resolved).
- **Manager reports** (Manager only).
- **Masters** (Brand Service Master, Service Center Master, etc.) — admin/manager maintenance.

### Ticket Entry Screen Layout (MVP — standard form)
Top → bottom sections on the HD Ticket form:
1. Subject + Ticket Type + Priority (Helpdesk standard).
2. **Lavanya Customer Details** — phone (auto-normalized), customer name, address, pincode.
3. **Lavanya Product Details** — product type (Select), category/item (link), brand (link), model/serial.
4. **Purchase / Warranty** — purchased-from-Lavanya, invoice source, purchase date, warranty status.
5. **Brand Service** — registration required/done, brand ticket number, service centre, local technician (role-gated).
6. **Follow-up** — pending reason, next follow-up date (required while open).
7. **Closure** — closure type, work narration, customer confirmation (role-gated; required to close).
Quick Action buttons appear contextually at the top of the form.

### Today's Work UX
- Buckets: **Overdue Follow-up**, **Due Today**, **Registration Recommended/Pending**, **Waiting on Customer**, **Waiting on Part/Approval**, **Ready for Pickup**.
- Click a bucket → filtered ticket list → open ticket → run a Quick Action. "Clear the inbox" model.

### Staff Ticket Entry Workflow (Front Desk / Agent)
1. Enter 10-digit mobile → system normalizes and fetches/creates customer profile.
2. Pick Ticket Type, Product Type, Category/Item, Brand (all from controlled lists).
3. Save → ticket routed to the correct queue with SLA attached.
4. For product-at-store: **Product Receipt** quick action → token slip print → status auto-moves to Registration Pending.

### Service Coordinator Workflow
- From Today's Work / queue, open ticket → Quick Actions: Register Brand Complaint, Need Invoice, Follow Up Service Center, Waiting for Part, Product Ready, Customer Confirmed, Close Ticket.
- Each action enforces role, required fields, valid status transition, and preserves the real actor in `modified_by`.

### Public QR Complaint UX
- `/qr-complaint` loads without login.
- Brand and Product Type are **dropdowns** populated from a safe public options endpoint (no free text).
- Honeypot + rate limiting; server-side validation; only a safe acknowledgement (reference = last-4 of mobile) is returned — no internal ticket id.
- Submission creates an internal HD Ticket (`complaint_source = Customer QR Form`) visible in New Complaints / Today's Work.

### MVP Acceptance Criteria
- Staff can create, follow up, route, and close a ticket using **only** the standard form + quick actions.
- Role blocks hold (Agent cannot close; Front Desk cannot close/register brand/confirm repeat; Viewer read-only).
- Today's Work surfaces the correct actionable tickets.
- QR public intake works end-to-end with controlled inputs.
- No custom guided wizard is required to operate the system.

### Recommended UI Decision
- **For MVP, use the improved standard Frappe/Helpdesk form with sections and role-aware buttons.**
- **Do not build a custom guided ticket wizard before production.**
- **A custom guided wizard may be considered in Phase 2 after staff pilot feedback.**
- Rationale: lower risk, faster staff adoption, easier permission control, easier maintenance, and less chance of breaking on Helpdesk upgrades.
