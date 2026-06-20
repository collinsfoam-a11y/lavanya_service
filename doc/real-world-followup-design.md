# Real-World Follow-up Design — Lavanya Service

Source: Real consumer court cases (Times of India, June 2026) analyzed against
the current app to identify gaps in follow-up tracking, service-path clarity,
and customer-satisfaction gating.

## Core insight

The app must **prove follow-up**, not just track ticket status. Consumer cases
are won/lost on whether the intermediary (Lavanya) can demonstrate active
follow-up, customer communication, and escalation.

## What real cases prove

| Case | Risk | What must be tracked |
|------|------|---------------------|
| Spare part delay (washing machine hinge) | Brand/reseller held liable even though technician visited | Part required, part expected date, part delay reason, last SC follow-up, customer informed |
| Repeated defect (Lenovo laptop) | Ticket closed prematurely — court found "no effective resolution" | Customer confirmation required before close, reopen reason, same-issue flag |
| Unauthorized paid repair (Ola scooter) | Customer charged for what should be warranty | Service charge type (brand warranty / local paid / goodwill / commission) |
| Silent delay (car spare parts, Coimbatore) | Vehicle taken back unrepaired, compensation awarded | Last update date, next follow-up date, delay reason, who was contacted, escalation level |

## Design decision: auxiliary fields, NOT new statuses

**Do not create 30 new ticket statuses.** Keep existing lifecycle (New →
Registration Pending → Brand Registered → In Progress → Waiting on Customer
→ Waiting on Part → Ready for Pickup → Resolved → Closed).

Add these auxiliary fields instead:

### `service_path` — which workflow is this ticket on?
- `brand_warranty` — brand service center handles repair, Lavanya coordinates
- `local_paid` — out-of-warranty, local technician, customer pays
- `goodwill` — Lavanya covers cost as goodwill
- `demo_installation` — not a complaint, just setup

### `followup_stage` — granular stage within the service path
- `registration_done` — brand ticket number recorded
- `technician_call_pending` — waiting for SC/technician to call customer
- `technician_called` — technician has called customer
- `technician_visit_pending` — waiting for visit
- `technician_visited` — visit done, awaiting outcome
- `no_technician_update` — no update from technician/SC
- `sc_followup_done` — Lavanya followed up with SC
- `customer_informed` — customer was given an update
- `part_pending` — spare part required, not yet available
- `customer_confirmation_pending` — repair done, awaiting customer sign-off
- `customer_satisfied` — customer confirmed issue resolved
- `customer_not_satisfied` — issue persists, needs escalation/reopen

### `service_charge_type` — payment model
- `Brand Warranty - No Charge`
- `Customer Paid Local Service`
- `Customer Pays Technician Directly`
- `Customer Pays Lavanya`
- `Lavanya Pays Technician`
- `Commission Receivable`
- `Goodwill / Free Service`
- `Brand Reimbursement Expected`

### `customer_satisfaction_status`
- `pending` — not yet asked
- `satisfied` — customer confirmed resolved
- `not_satisfied` — issue persists
- `partial` — partly resolved

### `followup_timeline` — structured log
Auto-logged entries (always tagged `[Follow-up]` for filtering):
- `Lavanya followed up with {service_center} — {outcome}`
- `Technician {name} called customer — {notes}`
- `Technician {name} visited — {result}`
- `Customer informed — {message}`
- `Escalated to {level} — {reason}`
- `Part {name} required — expected {date}`

## Required quick actions (new)

| Action | Updates |
|--------|---------|
| Verify Technician Called | `followup_stage = technician_called` + timeline entry |
| Verify Technician Visit | `followup_stage = technician_visited` + timeline entry |
| Record Service Center Follow-up | `followup_stage = sc_followup_done` + timeline entry |
| Inform Customer | `followup_stage = customer_informed`, `customer_informed_status = yes` |
| Mark No Update | `followup_stage = no_technician_update` + escalation bump |
| Escalate Case | increment `escalation_level` + timeline entry |
| Record Part Pending | `followup_stage = part_pending`, `part_name`, `part_expected_date` |
| Record Customer Satisfaction | `customer_satisfaction_status` + close/reopen |
| Set Service Charge Type | `service_charge_type` |

## Brand warranty workflow (most critical)

```
Ticket Created
│
└─→ Warranty Verified
    │
    └─→ Complaint Registered with Brand
        │  [service_path = brand_warranty]
        │  [followup_stage = registration_done]
        │
        └─→ Customer Informed
        │   [followup_stage = customer_informed]
        │
        └─→ 24h Check: Did technician call?
            │  YES → [followup_stage = technician_called]
            │  NO  → Follow up SC → [followup_stage = sc_followup_done]
            │                      → Customer informed → escalate
            │
            └─→ Visit Check: Did technician visit?
                │  YES → [followup_stage = technician_visited]
                │  NO  → Follow up SC + escalate
                │
                ├─→ Part pending? → [followup_stage = part_pending]
                │                    Follow up every 2 days
                │
                └─→ Completed → [followup_stage = customer_confirmation_pending]
                              → Customer confirmation
                                ├─ Satisfied → CLOSE
                                └─ Not satisfied → [followup_stage = customer_not_satisfied]
                                                   Reopen / escalate
```

## Link to existing codebase

- `service_path` → new field on HD Ticket
- `followup_stage` → new field on HD Ticket
- `followup_timeline` → reuse existing `[Follow-up]` tag in activity entries
- `service_charge_type` → new field on HD Ticket
- `customer_satisfaction_status` → new field on HD Ticket
- `part_name` / `part_expected_date` / `part_delay_reason` → new fields
- `last_service_center_followup` / `customer_informed_about_part_delay` → new fields

The existing `Follow Up Service Center` / `Waiting for Part` / `Customer Confirmed`
quick actions remain — they map to the new `followup_stage` values. The key gap
is the missing granular stages (technician call/visit verification, customer
informed logging) and the `service_charge_type` field.
