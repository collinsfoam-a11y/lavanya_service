# Lavanya Service — UI/UX Upgrade Suggestions (MVP, real-world workflows)

Goal: make daily work faster and lower-error for real staff, **without** building a
custom guided wizard before production (per BSR 12A). Everything here is achievable with
standard Frappe configuration + light HD Form Scripts (no SPA, upgrade-safe).

Priority key: **P0** = do before/at go-live · **P1** = first pilot iteration · **P2** = after pilot feedback.
Effort: ⚙️ config-only · ✍️ form-script · 🧩 small code.

---

## The 5 real-world workflows (and the one screen each role lives on)

| Role | Lives on | One job |
|---|---|---|
| Front Desk | New Ticket form | Log the complaint in < 60s |
| Helpdesk Agent | Today's Work | "Who do I call today?" |
| Service Coordinator | Today's Work + ticket | Move each ticket one step forward |
| Manager | Manager Dashboard | "What's stuck / breaching?" |
| Customer | /qr-complaint | Report a problem in 4 fields |

The upgrades below make each of those one job obvious and fast.

---

## P0 — Do before go-live

### 1. Status-aware form: hide fields that don't apply yet ✍️
**Real-world friction:** the HD Ticket has ~47 custom fields. A Front Desk user logging a phone
complaint sees closure, commission, replacement, supplier fields they must ignore → slow, error-prone.
**Upgrade:** use `depends_on` / `collapsible` so each section only shows when relevant:
- Closure section → show only when `status` in (Resolved, Closed).
- Brand Service section → show only when `warranty_status = In Warranty` or registration required.
- Replacement / Supplier / Commission → collapsed by default, expand on demand.
- Product-at-store custody → show only for ticket type `Customer Product at Store`.
**Result:** intake screen drops from ~47 fields to ~10 visible. Biggest single adoption win.

### 2. Make Quick Actions the primary control, ordered by "what's next" ✍️
**Friction:** staff currently must know which fields to edit to advance a ticket.
**Upgrade:** the quick-action buttons already exist (Register Brand, Need Invoice, Follow Up Service Center,
Waiting for Part, Product Ready, Customer Confirmed, Close). Surface only the **valid-next** buttons for the
current status, in left-to-right "happy path" order, with the most likely action highlighted. Hide actions the
role can't run (don't show then error).
**Result:** the ticket becomes "press the next button," not "edit 6 fields correctly."

### 3. Today's Work: counts + color + one-click into the bucket ⚙️/✍️
**Friction:** agents don't know where to start.
**Upgrade:** on the existing `lavanya_today_work` page show each bucket as a **card with a live count and a
color**: 🔴 Overdue Follow-up, 🟡 Due Today, 🟣 Registration Pending, 🔵 Waiting on Customer, ⏳ Waiting on
Part, 📦 Ready for Pickup. Click a card → filtered ticket list. Make this the **role home page**
(`role_home_page`) for Agent / Coordinator / Front Desk.
**Result:** "clear the inbox" model; no hunting through queues.

### 4. Front Desk intake: phone-first, 8-field happy path ✍️
**Friction:** intake is the highest-volume action and must be the fastest.
**Upgrade:** a "New Complaint" shortcut that opens the ticket with focus on **Mobile**; on blur, auto-lookup
fills customer name/address (already supported by the autofill form script). Then only: Ticket Type → Product
Type → Brand → short complaint text → Save. Everything else deferred to the coordinator.
**Result:** repeatable < 60s intake even for a new staff member.

---

## P1 — First pilot iteration

### 5. Required-before-save hints, inline (not just on submit) ✍️
Show a small inline note ("Next follow-up date required while ticket is open") next to the field as soon as the
status implies it, instead of only throwing on save. Reduces save-fail frustration.

### 6. "Customer card" header on the ticket ✍️
A compact read-only banner at the top: customer name, phone (click-to-call `tel:`), product + brand, warranty
badge (🟢 In Warranty / 🔴 Out / ❓ Unknown), and repeat-complaint flag. Staff see context without scrolling.

### 7. Token slip + "Product Ready" SMS-less notification ⚙️
Product-at-store already prints a token slip. Add a one-click **"Notify customer ready"** that records a
follow-up + sets Ready for Pickup (no SMS/WhatsApp per current policy — just an internal reminder for staff to
call). Keeps custody flow tight.

### 8. Manager dashboard as a real landing page 🧩
Surface the existing manager reports (brand-pending, waiting-on-customer/part, SLA breach, repeat) as number
cards + drill-down on one workspace. Manager opens one page and sees what's stuck.

### 9. List view polish ⚙️
For the 12 saved HD Views: pick 4–5 meaningful columns (Customer, Phone, Brand, Pending Reason, Next Follow-up),
enable the warranty/priority as colored indicators, default sort by Next Follow-up. Makes queues scannable.

---

## P2 — After pilot feedback (only if data says it's needed)

### 10. Optional guided intake wizard
If pilot shows Front Desk still struggles, *then* consider a lightweight guided wizard (3 steps: Customer →
Product → Complaint) as a separate page that creates the ticket via the existing API. Build it only with
evidence — the BSR explicitly defers this. Keep the standard form as the fallback/power path.

### 11. Mobile-friendly Today's Work
A responsive view for coordinators walking the service area on a phone/tablet.

---

## QR public form (already live) — small polish ✍️
- Add a one-line "valid 10-digit mobile" helper under the phone field.
- Disable the submit button until required fields are filled (client-side) to cut server round-trips.
- Show the reference number prominently with a "screenshot this" hint.
- (Already done: dropdown brand/product, honeypot, rate limit, safe response.)

---

## What NOT to do now
- ❌ No custom SPA / heavy front end before pilot feedback.
- ❌ No WhatsApp/SMS/email automation (policy).
- ❌ No new mandatory fields — reduce visible fields, don't add.

## Suggested sequence
P0 (1–4) is mostly form scripts + `depends_on` config: highest impact, lowest risk, ship with go-live.
P1 (5–9) after the first week of real use. P2 only if the pilot proves the need.

## Acceptance for the P0 batch
- New complaint logged by a new Front Desk user in under a minute using ≤ 10 visible fields.
- Agent opens Today's Work and works tickets without manually building filters.
- A ticket advances end-to-end using only quick-action buttons.
- No role sees an action it cannot perform.
