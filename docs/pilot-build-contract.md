# Lavanya Service Control — Pilot Build Contract v1

Status: **S1 implemented & verified** (2026-06). This document is the canonical
build contract. Where earlier analyses listed two pilot-gate lists or a separate
"biggest gap," this file supersedes them.

## §0 · The Control Law (single invariant)

> Every recorded remark or event must deterministically resolve exactly one open
> *next action* — either close it or spawn its successor with a due date derived
> from config — and a ticket may not reach a terminal state while any open next
> action or unsatisfied gate exists.

Every rule below is a projection of this one law.

## §1 · Canonical pilot gate (authoritative)

A ticket type is pilot-eligible **iff** the Control Law holds end-to-end:

| # | Gate | Status |
|---|------|--------|
| G-A | Closure blocked unless `customer_confirmation_received=Yes` ∧ satisfaction documented ∧ no part pending ∧ no open verification stage ∧ flow records complete | ✅ done |
| G-B | Every follow-up action commits a successor due-date; overdue surfaces automatically (hourly `reminder_refresh`) | ✅ done |
| G-C | Successor date is a function of config (Reminder Rule), not operator free-choice; loop is bounded against a silent customer | ✅ done (S1) |
| G-D | `customer_confirmed` enforces the same gates as `close_ticket` (no side-door) | ✅ done (S1) |

## §2 · Lifecycle = four orthogonal dimensions

Encoded as independent fields, not one flat status list:

| Dimension | Field(s) | States |
|-----------|----------|--------|
| Ticket | `status` | Open → In Progress → Brand Registered → Resolved → Closed/Cancelled |
| Verification | `followup_stage` | registration_done → call/visit pending → visited → confirmation_pending → satisfied/not_satisfied |
| Part | `part_required`, `part_fitted_confirmed`, `part_expected_date` | none / pending / fitted |
| Custody | `Service Product Receipt.current_custody_status` + `Custody Log Entry` | at_store → with_sc/tech → returned → handed_over |
| Appointment | `confirm_appointment` / `mark_appointment_missed` / `mark_technician_visited` | scheduled → confirmed → missed → visited |

Closure (`_assert_closure_gates`) checks ticket + verification + part + flow/custody
prerequisites. A multi-axis state is a tuple, never a new status — no combinatorial
status explosion.

## §3 · Determinism (config-driven dates)

`quick_actions._default_next_followup(doc, first=)` derives the next date from the
ticket's resolved `Lavanya Reminder Rule` (`first_followup_after_minutes` /
`repeat_every_minutes`), falling back to engine constants. Applied to
`register_brand_complaint` (D+2 verification), `follow_up_service_center` (all
branches), and `set_reverification_date`. Operator value always overrides; the date
is never blank and never a coin-flip.

**Config action:** set the brand-warranty Reminder Rule
`first_followup_after_minutes = 2880` to make the documented "D+2" literal.

## §4 · Idempotency

The "next action" is a single field (`next_follow_up_date`), not a spawned row —
re-setting a field is a no-op on retry, and schedulers already dedupe
(`reminder_refresh` is idempotent; notifications dedupe per-day). **No duplicate-task
hazard exists in pilot scope.** When the P2 `FollowUpLog`/task-row engine lands,
every spawned row MUST carry deterministic key `{ticket}:{loop_type}:{cycle_n}` with
a unique index, and spawn becomes an upsert. P2 precondition, not a P0 blocker.

## §5 · Bounded non-response (parking)

`mark_no_update` increments `no_update_count`; at `Reminder Rule.max_followup_attempts`
(default 5, `0 = unbounded`) the ticket parks: `parked_pending_customer=1`,
status `Waiting on Customer`. Parked tickets are excluded from Today's Work
(`classify_ticket` returns `[]`) so an unbounded loop against a silent customer
cannot manufacture zombie tickets. `resume_followup` (customer responded) clears the
flag, resets the counter, and sets a fresh config-derived date — re-entering the loop.

## §6 · Closure evidence tiers (P1)

Routine brand-warranty closes on the lightweight staff tick. Paid / high-value /
custody-mismatch / repeat bands must bind closure to a customer-side artifact
(WhatsApp confirmation reply or signed token slip) via a `closure_evidence_type`
field gated by `service_charge_type`/value band. Scheduled for the paid-service sprint.

## §7 · Sprint plan with the gate marked

| Sprint | Content | Gate |
|--------|---------|------|
| **S1** ✅ | G-C config dates · G-D `customer_confirmed` fix · §5 bounded non-response · §2 axis doc + custody close-gate | done |
| **S1 end** | **◄ PILOT GATE OPENS for Brand Warranty** | ✅ |
| S2 | Paid-service: approval-before-assignment, settlement log, §6 evidence | Pilot+ (paid) |
| S3 | Demo/Installation (UAT-C) + In-showroom custody (UAT-D) — scope in or annex out | Pilot+ |
| S4 | Repeat detection (UAT-E1) — code exists (`repeat_complaints.py`), schedule it | Pilot+ |
| P2 | FollowUpLog/Comm/Escalation/Reopen child tables (+ §4 spawn keys), attachments, safety/value enums | post |

Pilot smoke test = **UAT A1–A5 only**. C/D/E cases are post-pilot UAT until their
sprints land.

## §8 · The single testable property

> For any sequence of valid events on a ticket, at every step exactly one of
> {open next-action with a config-derived due date, terminal state with all gates
> satisfied} holds; and no terminal state is reachable while any §2 axis is unresolved.

S1 verification (14/14) asserts: closure gates (G-A), `customer_confirmed` physical
gate + attestation (G-D), parking at cap + resume (§5), and config-derived dates (§3).
Re-run the harness on each migrate to keep the Control Law a property test.
