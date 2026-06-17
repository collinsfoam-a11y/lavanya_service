# Reminder Engine — Implementation Plan (Delta Sprint 3)

Date: 2026-06-17
Builds on: Delta Sprint 1 (stage fields) + Delta Sprint 2 (Today's Work flow/stage
filters, Due-Soon, drawer Service Stage) — both shipped on the SPA branch.
Principle: **rule-first, AI-assisted-suggestion-only**. Do not replace the SPA,
Today's Work, status model, Comment activity log, or escalation report. Add on top.

> Reference study (Awesome Frappe — patterns only, nothing installed):
> ServiceMS (service stage modeling), Mail Reminder / Background Tasks Unleashed
> (scheduler-driven reminders → native `scheduler_events` + `frappe.enqueue`),
> Auto Repeat (recurring rule resolution → our Reminder Rule), Frappe Insights
> (reporting → existing catalog framework), Enhanced Kanban (work-queue grouping →
> Today's Work groups/filters), WhatsApp Cloud / ERPNext OCR (customer comms &
> proof — deferred; native minimal versions later).

---

## 1. Current code verification summary

Already in place and to be reused as canonical (verified in this codebase):

| Capability | Where | Status |
|---|---|---|
| Today's Work queue + 6 metric cards + Action Queue | `pages/TodayWork.vue`, `workflow/today_work.py` | ✅ canonical |
| Today's Work flow/stage/due/escalation **filters** + Due chip | `pages/TodayWork.vue` (Sprint 2) | ✅ done |
| Due-Soon / overdue compute (+ fallback to `next_follow_up_date`) | `stage_rules.compute_overdue_status` (Sprint 2) | ✅ done |
| `escalation_level` derivation | `stage_rules.compute_escalation_level` (Sprint 2) | ✅ done (filtering only) |
| Stage fields (`service_flow_type`/`current_service_stage`/`next_action` + 10 more) | `setup/service_stages.py` (programmatic, not the shared fixture) | ✅ done |
| Drawer "Service Stage" read section (blank-safe) | `components/TicketDetail.vue` (Sprint 2) | ✅ done |
| Comment-based activity log (`[Follow-up]`, `[Stage]`…) | `stitch_console.get_ticket_activity` / `add_ticket_note` | ✅ canonical |
| Escalation report + daily manager notification | `reports/manager_dashboard.get_escalation_report`, `reminders/notification_output` | ✅ canonical |
| Stage Missing cleanup report | `manager_reports` REPORTS | ✅ done |

Gap this sprint fills: reminders are currently a single `next_follow_up_date` +
a date-based daily pass. There is **no per-brand/product/stage reminder interval**,
no **customer-promise** tracking, and no **AI-assisted suggestion** for high-risk
tickets. The Reminder Engine adds those — rule-driven, with AI as advisory only.

## 2. File-level implementation plan

| File | Change |
|---|---|
| `lavanya_service/setup/reminder_rule.py` (new) | Programmatic `Lavanya Reminder Rule` DocType (config/master). Wired via `hooks.after_install/after_migrate` (NOT `install.py`). |
| `lavanya_service/setup/service_stages.py` | Add HD Ticket fields: `customer_promised_update_at`, `customer_promise_status`, `promise_breach_reason`, `ai_suggested_next_action`, `ai_suggested_customer_message`, `ai_risk_reason`, `ai_last_reviewed_at`, `ai_review_status` (programmatic, same path as the stage fields). |
| `lavanya_service/reminder_engine.py` (new) | Rule resolution + reminder-state calc (see §4). Pure functions; no side effects beyond setting ticket fields on save/refresh. |
| `lavanya_service/api/reminders.py` (new) | Whitelisted: `get_due_soon_tickets`, `get_customer_promise_breaches`, `apply_ai_suggestion` (review/accept), `set_customer_promise`. SPA-safe (read + explicit accept only). |
| `lavanya_service/tasks/reminder_refresh.py` (new) | Scheduled (hourly): `refresh_open_ticket_reminders` — recompute `stage_due_at` / `pre_overdue_alert_at` / `customer_update` due / `escalation_level` from the resolved rule. Uses `frappe.enqueue` for batches. |
| `lavanya_service/reports/manager_dashboard.py` | Add `get_customer_promise_breach_report`, `get_due_soon_report` (reuse existing report framework). |
| `lavanya_service/api/manager_reports.py` | Register the two new reports in the catalog (manager-gated). |
| `lavanya_service/overrides/hd_ticket.py` | On validate: after `assign_defaults`, call `reminder_engine.refresh_ticket_reminder_state(self)` (rule-driven due times) + detect promise breach. |
| `lavanya_service/ai/next_action.py` (new, optional this sprint) | `suggest_for_ticket(ticket)` — rule-first heuristic that writes `ai_*` suggestion fields ONLY. No state change. Pluggable LLM later. |
| `frontend/src/pages/TodayWork.vue` | Add groups/cards: Due Soon, Customer Promise Breach, High Risk; add filters: Brand, Product Type, Risk Level. (Additive to Sprint 2 filters.) |
| `frontend/src/components/TicketDetail.vue` | Add "Reminder Intelligence" read section (rule applied, due times, promise status, AI suggestion + accept button). |
| `lavanya_service/tests/reminder_engine.py` (new) | The 10 required tests (see §6). |
| `hooks.py` | Add the hourly reminder-refresh job to `scheduler_events`. |

## 3. Exact fields / DocTypes to add

### 3.1 New DocType — `Lavanya Reminder Rule` (config/master, created programmatically)

| Field | Type | Notes |
|---|---|---|
| rule_name | Data | reqd, unique |
| enabled | Check | default 1 |
| priority | Int | tie-break; lower = wins |
| brand | Link → Brand Service Master | match |
| product_type | Data | match |
| ticket_type | Data | match |
| service_flow_type | Select (stage_rules) | match |
| current_service_stage | Select (stage_rules) | match |
| warranty_route | Data | match |
| pending_reason | Data | match |
| customer_priority | Select: Low/Normal/High/VIP | match |
| first_followup_after_minutes | Int | |
| repeat_every_minutes | Int | |
| due_soon_before_minutes | Int | |
| overdue_after_minutes | Int | |
| manager_escalate_after_minutes | Int | |
| owner_escalate_after_minutes | Int | |
| customer_update_required | Check | |
| customer_update_every_minutes | Int | |
| pause_when_sla_paused | Check | default 1 |
| business_hours_only | Check | |
| notes | Small Text | |

Permissions: System Manager, Lavanya Manager (read/write/create); Coordinator (read).

### 3.2 New HD Ticket fields (programmatic, additive)

Customer promise: `customer_promised_update_at` (Datetime), `customer_promise_status`
(Select: None/Pending/Kept/Breached, default None), `promise_breach_reason` (Small Text).

AI suggestion (advisory, never acted on automatically): `ai_suggested_next_action`
(Data), `ai_suggested_customer_message` (Small Text), `ai_risk_reason` (Small Text),
`ai_last_reviewed_at` (Datetime), `ai_review_status` (Select: New/Accepted/Dismissed,
default New).

## 4. APIs / functions to add

**Resolution & calc (`reminder_engine.py`, pure):**
- `resolve_reminder_rule(ticket)` → the winning `Lavanya Reminder Rule` by priority order:
  1. manual manager override (a ticket-level override flag/field) → 2. brand+ (call type/stage) → 3. brand+product → 4. call type+stage → 5. service-flow default → 6. global fallback. Most-specific match wins; `priority` breaks ties.
- `calculate_next_followup(ticket, rule)`, `calculate_due_soon_at(ticket, rule)`, `calculate_stage_due_at(ticket, rule)` — minute offsets from `stage_started_at`/now, honoring `pause_when_sla_paused` and `business_hours_only`.
- `refresh_ticket_reminder_state(ticket)` → resolve rule, set `stage_due_at`/`pre_overdue_alert_at`/customer-update due/`escalation_level`; detect promise breach. Idempotent; only fills/updates derived fields.
- `derive_customer_disappointment_risk(ticket)` → Low/Medium/High from overdue depth, repeat flag, promise breach, store ageing.
- `derive_escalation_level(ticket)` → reuse `stage_rules.compute_escalation_level` (no second engine).

**Queries / whitelisted (`api/reminders.py`):**
- `get_due_soon_tickets()`, `get_customer_promise_breaches()` (permission-scoped).
- `set_customer_promise(ticket, promised_at)` — staff records a promised update time.
- `apply_ai_suggestion(ticket, action)` — sets `ai_review_status`; **accept** copies the suggested next_action into `next_action` only on explicit staff action.

**Scheduled (`tasks/reminder_refresh.py`):** `refresh_open_ticket_reminders` (hourly,
batched via `frappe.enqueue`).

## 5. UI changes — Today's Work & drawer

**Today's Work (additive to Sprint 2):**
- New groups/cards: **Due Soon**, **Customer Promise Breach**, **High Risk Customers** (plus the existing flow-specific buckets surfaced via filters: Extended Warranty Pending, Product at Store Ageing, Spare Pending Ageing, etc.).
- New filters: **Brand**, **Product Type**, **Risk Level** (extending the Sprint-2 flow/stage/due/escalation filters).

**Drawer — "Reminder Intelligence" read section (blank-safe):**
- rule applied · next follow-up · due soon at · stage due at · customer update due · customer promised update at · promise status · risk level · AI suggested next action · AI risk reason — with an **Accept suggestion** button (the only AI write path, staff-initiated).

## 6. Tests to add / run (`tests/reminder_engine.py`)

1. Old tickets without `stage_due_at` still work via existing Today's Work logic (fallback).
2. Due Soon appears before Overdue.
3. Reminder-rule priority resolves correctly (override > brand+stage > … > global).
4. Brand/product/stage-specific rule overrides the global default.
5. Customer promise breach is detected (now > `customer_promised_update_at`, status Pending → Breached).
6. High-risk repeat complaint → manager escalation level.
7. AI suggestion fields never change ticket state automatically (only `apply_ai_suggestion` accept does).
8. Drawer/detail renders reminder fields safely when blank.
9. Today's Work grouping by `service_flow_type` / `current_service_stage` works (already green; keep).
10. Comment activity log remains canonical (no new activity table created).

## 7. Migration impact

- **Additive only.** New config DocType + new HD Ticket fields, all created
  programmatically (idempotent `create_custom_fields` / `_ensure_doctype`) via
  `after_install`/`after_migrate` — **not** the shared `custom_field.json` fixture,
  so no collision with the other agent's field set.
- No change to existing fields, status, or `next_follow_up_date` (kept as fallback).
- Reminder due times are recomputed by the hourly job + on save; existing tickets
  get rule-driven times on next refresh and continue working via fallback until then.
- New scheduled job is idempotent and batched (no heavy migration step).

## 8. Compatibility risks

- **Two due systems** if not careful: mitigated — `next_follow_up_date` stays the
  staff-facing date and the *fallback*; `stage_due_at`/`pre_overdue_alert_at` only
  refine Due-Soon. Never replace, only layer.
- **Fixture collision**: avoided by programmatic field/doctype creation (never edit
  `custom_field.json`, `install.py`, or the other agent's setup files).
- **Scheduler load**: batch with `frappe.enqueue`, only open tickets, hourly.
- **AI safety**: AI writes only `ai_*` fields; it cannot close, message, change
  warranty/payment/stock, or move stage. Enforced server-side (no AI write path to
  state) + tested (#7).
- **SLA pause**: honour `pause_when_sla_paused` so paused tickets don't false-alarm.

## 9. What NOT to implement in this sprint

- `Extended Warranty Provider Master`, `Lavanya Extended Warranty Claim`,
  `Lavanya Payment and Commission Log`, `Lavanya Stock Issue Detail`,
  `Lavanya Communication Log` — **skeleton/plan references only** (these are Delta
  Sprint 4/5).
- No external app install (WhatsApp/OCR/Insights/Metabase). Native minimal versions
  only, later.
- No LLM call wired yet — `ai/next_action.py` is a rule-first heuristic with a
  documented plug-in point; real model integration is a later, approved step.
- No second activity log / escalation engine.

## 10. Final next-step recommendation

Implement in this safe order, committing + testing each:
1. **`Lavanya Reminder Rule` DocType skeleton** (config/master) — zero risk, unblocks rule authoring. *(Doing now as Sprint-3 prep.)*
2. **Customer-promise fields + `set_customer_promise` + promise-breach detection** — small, high staff value, testable.
3. **`reminder_engine.resolve_reminder_rule` + `refresh_ticket_reminder_state`** + hourly job — the core, behind the fallback.
4. **Today's Work cards (Due Soon / Promise Breach / High Risk) + Brand/Product/Risk filters** and the **drawer Reminder Intelligence** section.
5. **AI suggestion fields + `ai/next_action.py` (rule-first) + Accept-only path** — advisory, last.

Seed one **global fallback** Reminder Rule so resolution always returns something.
Keep every step additive and fallback-guarded so old tickets never break.
