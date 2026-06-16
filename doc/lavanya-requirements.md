# Lavanya Service — Requirements (source-grounded)

> **Read this before building anything.** Per [`../AGENTS.md`](../AGENTS.md), AI
> agents must not **assume** requirements. Everything below is derived from the
> codebase as the source of truth and **cites the file it came from**. If a
> requirement you need is *not* stated here and not verifiable in code, treat it as
> an **open question** (§10) — ask a human; do not invent it.
>
> "How it is" = current implemented behaviour (cited). "How it should be" = the
> Stitch design intent + documented rules. Gaps between them are tracked in
> [`lavanya-spa-status.md`](lavanya-spa-status.md) §3.

---

## 1. Purpose & scope — what the app is for

Lavanya Service is a Frappe app extending the **Helpdesk** app to run the
**after-sales service / complaint workflow** for **Lavanya eMart** (a home-appliance
retailer). It tracks a customer complaint from intake through brand registration,
service-centre/technician handling, physical product custody, and closure.

Evidence (not assumption):
- Product types are home appliances — `setup/hd_ticket_fields.py` `PRODUCT_TYPE_OPTIONS`: AC, Refrigerator, Washing Machine, Mixer, Induction Cooker, Chimney, Hob, Gas Stove, TV, Water Purifier, Other.
- Domain doctypes for brand service, service centres, technicians, product custody (see §3, verified in DB).
- Ticket types and warranty/registration fields centred on appliance after-sales (§4).

> The precise corporate/business context beyond this (SLAs, branches, volumes,
> integrations) is **not** in the code → §10 open questions.

## 2. Personas / roles

Custom roles (`fixtures/role.json`), plus Frappe's **System Manager** which bypasses
action gates (`workflow/quick_actions.py` `BYPASS_ROLES`).

| Role | Can run (quick actions) | Today's Work groups |
|---|---|---|
| **Lavanya Manager** | all actions | all groups |
| **Lavanya Service Coordinator** | all actions | all groups |
| **Lavanya Helpdesk Agent** | Need Invoice, Follow Up SC, Waiting for Part | overdue/due-today/registration-pending/waiting-customer/waiting-part |
| **Lavanya Front Desk** | Create Product Receipt, Product Ready | ready-for-pickup/receipt-missing/new-complaints |
| **Lavanya Viewer** | none (read-only) | all groups (read) |

Sources: per-action `_require_roles(...)` sets in `workflow/quick_actions.py`;
group access in `workflow/today_work.py` (`HELPDESK_AGENT_GROUPS`,
`FRONT_DESK_GROUPS`, `_allowed_group_keys_for_user`).

## 3. Domain model (custom doctypes)

Verified present in DB (module "Lavanya Service"):
`Brand Service Master`, `Service Center Master`, `Local Technician Master`,
`Free Service Rule`, `Service Product Receipt`, `Custody Log Entry` (child),
`Lavanya Customer Profile`, `Lavanya Product Category`, `Lavanya Product Item`.

Plus the **HD Ticket** doctype is extended with Lavanya custom fields
(`setup/hd_ticket_fields.py`) — e.g. `warranty_status`, `manufacturer_registered`,
`brand_ticket_number`, `registration_date`, `next_follow_up_date`, `pending_reason`,
`service_center`, `service_product_receipt`, `closure_type`,
`customer_confirmation_received`, `is_repeated_complaint`, `previous_ticket_link`,
`work_narration`, `closed_by`, `closure_date`. (Confirm the full list against the
file before relying on a specific field.)

## 4. Reference data (authoritative option lists)

All from `setup/hd_ticket_fields.py` unless noted. **Do not invent new option
values** — these are validated server-side.

- **Product types:** AC, Refrigerator, Washing Machine, Mixer, Induction Cooker, Chimney, Hob, Gas Stove, TV, Water Purifier, Other.
- **Product subtypes:** Split AC, Window AC, Front Load, Semi Automatic, Other.
- **Ticket types** (`fixtures/hd_ticket_type.json`): Customer Complaint - Site, Customer Product at Store, Stock Complaint, Installation / Demo, Replacement / DOA, Out of Warranty Local Service, Free Service.
- **Warranty status:** In Warranty, Out of Warranty, Unknown, Extended Warranty, Brand Denied.
- **Ticket statuses** (`fixtures/hd_ticket_status.json`): New, Registration Pending, Brand Registered, In Progress, Waiting on Customer, Waiting on Part / Approval, Ready for Pickup, Resolved, Closed, Cancelled.
- **Pending reasons** (24 values) — see `PENDING_REASON_OPTIONS`.
- **Closure types** (11 values) — see `CLOSURE_TYPE_OPTIONS`.
- **Custody statuses** (`Service Product Receipt.current_custody_status`): Received at Store, Handed to Service Center, With Local Technician, Returned to Store, Ready for Customer Pickup.

## 5. Ticket lifecycle (status transitions)

From `workflow/quick_actions.py` — terminal statuses `Closed`/`Cancelled` block all
quick actions (`_block_if_final`). Each action's required fields and resulting state:

| Action | Roles | Required fields | Result |
|---|---|---|---|
| Register Brand Complaint | Manager, Coordinator | brand_ticket_number, registration_date, next_follow_up_date | status → **Brand Registered** |
| Need Invoice from Customer | Manager, Coordinator, Agent | next_follow_up_date | status → **Waiting on Customer**, reason "Invoice Pending" |
| Follow Up Service Center | Manager, Coordinator, Agent | follow_up_result (+ next_follow_up_date unless "Service completed") | "Service completed"→**Resolved**; "Part/Approval pending"→**Waiting on Part / Approval**; else **In Progress** |
| Waiting for Part | Manager, Coordinator, Agent | pending_reason, next_follow_up_date | status → **Waiting on Part / Approval** |
| Product Ready | Manager, Coordinator, Front Desk | — | status → **Ready for Pickup** |
| Customer Confirmed | Manager, Coordinator | work_narration, closure_type | status → **Closed** (confirmation=Yes) |
| Close Ticket | Manager, Coordinator | work_narration, closure_type, customer_confirmation_received="Yes" | status → **Closed** |
| Create Product Receipt | Manager, Coordinator, Front Desk | (accessories, condition) — ticket must be type "Customer Product at Store", no existing receipt | creates Service Product Receipt, custody "Received at Store" |

`follow_up_result` allowed values: Service center contacted, Technician assigned,
Customer not reachable, Service completed, Part pending, Approval pending.

## 6. Business rules (verifiable)

- **Brand-registration recommended** (`today_work.is_registration_recommended`): ticket is active, `warranty_status == "In Warranty"`, `manufacturer_registered != "Yes"`, no `brand_ticket_number`, no override reason, and ticket type ∈ {Customer Complaint - Site, Customer Product at Store, Installation / Demo, Replacement / DOA}; "Free Service" depends on a brand-backed `Free Service Rule`; {Stock Complaint, Out of Warranty Local Service} are exempt.
- **Today's Work grouping & priority** (`today_work.GROUPS`, `classify_ticket`): overdue follow-up (1) → due today (2) → registration recommended (3) → registration pending (4) → waiting on customer (5) → waiting on part (6) → ready for pickup (7) → product receipt missing (8) → closure pending (9) → new complaints (10).
- **Closure pending** = status "Resolved" AND (confirmation ≠ Yes OR no closure_type) (`today_work._is_closure_pending`).
- **Reports** (`reports/manager_dashboard.py`): daily follow-up, brand pending, waiting-on-customer, waiting-on-part, product-at-store aging, ready-for-pickup, closure, repeat-complaint, warranty-override, cancelled — each with explicit SQL filters that the SPA Reports drill-down reuses.

## 7. Permissions, audit & security (verifiable)

- Every quick action **independently** enforces role, status, and required-field
  checks server-side, regardless of any UI gating (`quick_actions.py` module
  docstring). Never rely on the browser for authorization.
- Writes go through `_save_ticket`, which does an explicit write-permission check
  for the acting user, then saves with a scoped guard-bypass flag so `modified_by`
  / comment authorship stay the **real** user (audit requirement, `quick_actions.py`).
- Protected-field rules live in `validations/hd_ticket.py`.
- SPA APIs are permission-scoped (`frappe.has_permission`) and org-wide reports are
  role-gated (`api/manager_reports.py`).

## 8. UI requirements (target = Stitch designs)

19 Stitch screens define the target UI ("Lavanya Service Console", project
`9558170131594450042`). Built vs pending is tracked in
[`lavanya-spa-status.md`](lavanya-spa-status.md) §2–§3. Design tokens: Material
Design 3, primary blue `#004ac6`, Inter, Material Symbols, base-8 spacing — realized
on the **frappe-ui** Tailwind preset.

## 9. Non-functional (verifiable)

- Two surfaces coexist: the **standard Helpdesk Desk** (full operations) and the
  **SPA at `/frontend`** (Stitch console). The SPA is additive, not a replacement.
- Build on the host; serve page auto-syncs; `/frontend` is no-cache (status doc §1).
- Cross-platform build constraint (status doc §1).

## 10. Open questions — DO NOT ASSUME

Not verifiable from the codebase. Confirm with a human before building anything that
depends on them; do not guess:

1. **SLA / response-time targets** per ticket type or priority — none found in code.
2. **Notifications** (SMS/WhatsApp/email to customer on status change) — intent
   unknown; `HD Notification` exists in Helpdesk but Lavanya-specific rules unconfirmed.
3. **Customer-facing surface** (QR intake form) — exact required fields, validation,
   and guest-permission policy: confirm against `api/qr_intake.py` / `customer_intake.py`
   and stakeholders before building (status doc P1).
4. **Aging thresholds** ("beyond standard processing time" in product-at-store aging)
   — the report has no numeric threshold; define with stakeholder if needed.
5. **Repeat-complaint definition** — code uses `is_repeated_complaint == 'Yes'` set by
   a separate flow (`api/repeat_complaints.py`); confirm the business rule for what
   *qualifies* as a repeat.
6. **Reporting period** for Closure/Cancelled (defaults to "today") — confirm whether
   managers need configurable date ranges in the SPA.
7. **Branch / multi-location** scope — single store vs many: not modelled in code.
8. The earlier pasted "Business Requirement" / phasewise spec is **not stored in this
   repo**. If a requirement traces only to that chat, capture it here (with the
   source) before acting on it — otherwise it's an assumption.

> When you resolve an open question, **move it into the relevant section above with
> its source**, and note it in the status doc. Keep this file the source of truth so
> the next agent never has to assume.
