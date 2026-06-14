# Lavanya Service — UAT Pilot Execution Script

Hands-on acceptance script for the **internal pilot**. These cases are run by real
staff in the live UI and signed off by the manager. They complement (do not
replace) the automated suites (`acceptance_phase1`, `workflow_quick_actions`,
`reports_dashboard`, etc.) — automation proves the backend; this proves the
real screens and the human workflow.

- Stack: frappe 15.110.0, helpdesk 1.25.1, lavanya_service.
- Pilot ticket types only: **Customer Complaint - Site**, **Customer Product at Store**,
  **Installation / Demo**. Do NOT exercise other types with real customers.
- Mark each case **PASS / FAIL / BLOCKED** and capture a screenshot on FAIL.

---

## 0. Preconditions (manager sets up once)

| # | Step | Expected | Result |
|---|------|----------|--------|
| P1 | Create one test user per role using the documented mapping (native `Agent` role + `HD Agent` record + exactly one Lavanya role). See `role_mapping_decision.md`. | 5 users: Manager, Service Coordinator, Helpdesk Agent, Front Desk, Viewer | ☐ |
| P2 | Confirm each non-viewer user can log in to the Helpdesk portal and see the ticket list. | Portal loads; agent sees tickets | ☐ |
| P3 | Confirm scheduler is enabled and the daily reminder job is present. | `scheduler status` = Enabled | ☐ |

---

## 1. Front Desk — fast complaint intake (target < 60s)

| # | Step | Expected | Result |
|---|------|----------|--------|
| F1 | As **Front Desk**, create a new ticket, type = Customer Complaint - Site. | New ticket form opens | ☐ |
| F2 | Enter mobile in Phone 1, tab out. | If the customer exists, name/address auto-fill (mobile autofill) | ☐ |
| F3 | Enter `+91 98765 43210` in Phone 1 and save. | Phone normalises to `9876543210` | ☐ |
| F4 | Enter `12345` (too short) in Phone 1 and save. | Save blocked: "must be a valid 10 digit phone number" | ☐ |
| F5 | Observe visible fields on the intake form. | Brand-Service and closure fields are **hidden** (status-aware); ~10 fields visible, not ~47 | ☐ |
| F6 | Fill customer/product/complaint, Save. | Ticket created, status New | ☐ |
| F7 | Confirm Front Desk does **not** see Register Brand / Close actions. | Those actions absent or blocked for Front Desk | ☐ |

---

## 2. Service Coordinator — advance a ticket with quick actions

Use the **"Lavanya Actions"** button on the ticket (opens a modal — no browser prompts).

| # | Step | Expected | Result |
|---|------|----------|--------|
| C1 | Open a New ticket, click Lavanya Actions → **Register Brand Complaint**. | Modal opens with Brand Ticket Number, Registration Date, Next Follow-up Date, Service Center | ☐ |
| C2 | Submit the modal empty. | Inline error "Required: …"; modal stays open | ☐ |
| C3 | Fill required fields, submit. | Status → Brand Registered; ticket reloads | ☐ |
| C4 | Lavanya Actions → **Follow Up Service Center**, result "Part pending", set follow-up date, submit. | Status → Waiting on Part / Approval; pending reason set | ☐ |
| C5 | Lavanya Actions → **Need Invoice from Customer**, set follow-up, submit. | Status → Waiting on Customer; pending reason "Invoice Pending" | ☐ |
| C6 | Try to advance an **open** ticket leaving Next Follow-up Date blank (edit form directly). | Save blocked: requires Pending Reason + Next Follow-up Date | ☐ |
| C7 | Confirm closure fields appear only now that status is advanced and you are coordinator/manager. | Closure section visible to coordinator at Resolved/Ready/Closed; hidden for agent/front-desk | ☐ |

---

## 3. Product-at-Store — custody + token slip

| # | Step | Expected | Result |
|---|------|----------|--------|
| S1 | Create a Customer Product at Store ticket **without** a serial number, save. | Blocked: "Serial No is required" | ☐ |
| S2 | Add serial, save; then Lavanya Actions → **Create Product Receipt**. | Receipt created, name like `LV-SR-2026-0001`; linked to ticket | ☐ |
| S3 | Try Create Product Receipt again on the same ticket. | Blocked: receipt already exists | ☐ |
| S4 | Open the Service Product Receipt, print **Lavanya Service Product Receipt Token**. | Token slip renders with customer/product/custody + signature lines | ☐ |
| S5 | Add a custody log row (e.g. Handed to Service Center) and set Current Custody Status to match. | Saves; if status ≠ latest log row, save is blocked | ☐ |
| S6 | Lavanya Actions → **Product Ready**. | Status → Ready for Pickup | ☐ |

---

## 4. Closure with evidence

| # | Step | Expected | Result |
|---|------|----------|--------|
| K1 | As **Helpdesk Agent**, try Lavanya Actions → Close Ticket. | Blocked / not permitted (close is Manager/Coordinator only) | ☐ |
| K2 | As **Coordinator**, Lavanya Actions → **Close Ticket** with confirmation = No. | Blocked: confirmation must be Yes | ☐ |
| K3 | Close Ticket with confirmation = Yes, work narration, closure type. | Status → Closed; Closed By + Closure Date set | ☐ |
| K4 | Confirm a Closed ticket cannot be advanced by quick actions. | Quick actions blocked on Closed/Cancelled | ☐ |

---

## 5. Repeat complaint suggestion

| # | Step | Expected | Result |
|---|------|----------|--------|
| R1 | Create a ticket with the same mobile + brand as an earlier one. Lavanya Actions → **Check Repeat Complaint**. | Modal lists previous ticket(s) with match reasons | ☐ |
| R2 | Pick a candidate, Confirm Repeat. | Is Repeated Complaint = Yes; Previous Ticket Link set | ☐ |
| R3 | As Manager/Coordinator, Lavanya Actions → **Clear Repeat Link**. | Flag cleared; link removed | ☐ |
| R4 | As **Viewer**, attempt any write or quick action. | All blocked (read-only) | ☐ |

---

## 6. Today's Work page (Coordinator / Agent / Front Desk)

| # | Step | Expected | Result |
|---|------|----------|--------|
| T1 | Open **Lavanya Today's Work** (`/app/lavanya-today-work`). | Stitch-styled page: metric cards + colored bucket cards | ☐ |
| T2 | Confirm bucket counts match reality and cards expand/collapse. | Counts correct; chevron toggles | ☐ |
| T3 | Click a ticket's Open Ticket link. | Opens the Helpdesk ticket | ☐ |
| T4 | Compare role views: Front Desk sees fewer buckets than Coordinator. | Front Desk = new/ready/receipt-missing; Coordinator = all | ☐ |

---

## 7. Reminders & Manager reports

| # | Step | Expected | Result |
|---|------|----------|--------|
| M1 | Set a ticket's Next Follow-up Date to today/overdue; wait for (or trigger) the daily reminder job. | HD Notification appears; **no** email/SMS/WhatsApp sent | ☐ |
| M2 | As **Manager**, open the manager dashboard/reports. | Summary counts + report tables load | ☐ |
| M3 | Verify a Cancelled ticket is **not** counted as a successful closure. | Cancelled appears only in the Cancelled report | ☐ |
| M4 | Confirm Manager can open all reports; Front Desk only its allowed subset. | Role-aware access enforced | ☐ |

---

## Sign-off

| Role tester | Name | Date | All cases PASS? | Notes |
|-------------|------|------|-----------------|-------|
| Front Desk | | | ☐ | |
| Helpdesk Agent | | | ☐ | |
| Service Coordinator | | | ☐ | |
| Manager | | | ☐ | |
| Viewer | | | ☐ | |

**Go-live rule:** all sections PASS for the three pilot ticket types, no CRITICAL
defects open, and the production hardening checklist (`production_hardening_checklist.md`)
gate is green. Any FAIL → log a defect, fix, re-run the affected section. Do **not**
expand to other ticket types until the pilot is stable.
