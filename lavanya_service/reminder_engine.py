"""Reminder Rule Resolution Engine (reminder engine, Step 3).

Rule-FIRST, compute-only, non-destructive. Given a ticket, this resolves which
`Lavanya Reminder Rule` applies (by brand / product / ticket-type / flow / stage /
warranty-route / pending-reason / customer-priority), then derives follow-up,
due-soon, stage-due, escalation level and customer-update-due — all as plain
computation. Nothing here closes tickets, sends messages, writes AI fields, or
touches payment / stock / warranty docs.

It reuses `stage_rules` for the shared Due-Soon / overdue / promise primitives so
there is no second escalation engine, and it falls back to the existing
`next_follow_up_date` behaviour for old tickets without rules or stage fields.

Persistence is OFF by default: `refresh_ticket_reminder_state` only writes when
called with `save=True` (the Step-4 scheduler will opt in); a manually entered
`next_follow_up_date` is never overwritten unless `force=True`.
"""

import frappe
from frappe.utils import add_to_date, get_datetime, now_datetime

from lavanya_service import stage_rules as sr

REMINDER_RULE = "Lavanya Reminder Rule"

# Safe hardcoded fallback (minutes) when no rule — and no global fallback rule —
# matches. Mirrors the values called out in the Step-3 spec.
FALLBACK_FIRST_FOLLOWUP_MIN = 24 * 60
FALLBACK_REPEAT_MIN = 24 * 60
FALLBACK_DUE_SOON_BEFORE_MIN = 4 * 60
FALLBACK_MANAGER_ESCALATE_MIN = 48 * 60
FALLBACK_OWNER_ESCALATE_MIN = 96 * 60

# Specificity bonus per matched rule field (Step-3 spec).
SPECIFICITY = {
	"brand": 20,
	"product_type": 15,
	"ticket_type": 15,
	"service_flow_type": 10,
	"current_service_stage": 20,
	"warranty_route": 10,
	"pending_reason": 10,
	"customer_priority": 10,
}
MATCH_FIELDS = list(SPECIFICITY.keys())

# Rule fields fetched once per request for in-memory resolution.
_RULE_FIELDS = [
	"name", "priority", "modified",
	*MATCH_FIELDS,
	"first_followup_after_minutes", "repeat_every_minutes", "due_soon_before_minutes",
	"overdue_after_minutes", "manager_escalate_after_minutes", "owner_escalate_after_minutes",
	"customer_update_required", "customer_update_every_minutes",
	"pause_when_sla_paused", "business_hours_only",
]

_ESCALATION_ORDER = {"None": 0, "Coordinator": 1, "Manager": 2, "Owner": 3}
_PRODUCT_AT_STORE_FLOW = "Customer Product at Store"
_SPARE_PENDING_STAGE = "Spare Pending"


# ── small helpers ──────────────────────────────────────────────────────────────
def _tv(ticket, field):
	"""Read a field from a ticket whether it is a Document or a plain dict."""
	if hasattr(ticket, "get"):
		return ticket.get(field)
	return getattr(ticket, field, None)


def _blank(value):
	return value is None or str(value).strip() == ""


def _minutes(rule, field, default):
	if rule:
		val = rule.get(field)
		if not _blank(val):
			try:
				return int(val)
			except (TypeError, ValueError):
				pass
	return default


def _checked(rule, field):
	return bool(rule and int(rule.get(field) or 0))


def _iso(value):
	if value is None:
		return None
	if hasattr(value, "isoformat"):
		return value.isoformat()
	return value


def _max_level(*levels):
	best = "None"
	for lvl in levels:
		if _ESCALATION_ORDER.get(lvl, 0) > _ESCALATION_ORDER.get(best, 0):
			best = lvl
	return best


# ── rule resolution ────────────────────────────────────────────────────────────
def get_active_rules():
	"""Enabled rules, fetched once per request (cheap in-memory resolution)."""
	if not frappe.db.exists("DocType", REMINDER_RULE):
		return []
	cached = getattr(frappe.local, "_lavanya_reminder_rules", None)
	if cached is not None:
		return cached
	rules = frappe.get_all(REMINDER_RULE, filters={"enabled": 1}, fields=_RULE_FIELDS)
	frappe.local._lavanya_reminder_rules = rules
	return rules


def _rule_specificity(rule, ticket):
	"""Return (matches, specificity). A rule matches only if every field it
	constrains (non-blank) equals the ticket's value; specificity is the sum of
	the bonuses for those constrained fields."""
	score = 0
	for field in MATCH_FIELDS:
		rule_val = rule.get(field)
		if _blank(rule_val):
			continue  # wildcard — does not constrain
		if str(rule_val) != str(_tv(ticket, field) or ""):
			return False, 0
		score += SPECIFICITY[field]
	return True, score


def resolve_reminder_rule(ticket, rules=None):
	"""Pick the best enabled rule for a ticket, or None for fallback.

	Ranking (Step-3 spec): higher priority first (lower `priority` number wins —
	per the DocType's "Lower wins" semantics), then most specific match, then
	newest modified. The conceptual hierarchy (brand+stage > brand+product >
	calltype+stage > flow default > global fallback) is expressed by specificity,
	so equal-priority rules resolve in that order."""
	rules = rules if rules is not None else get_active_rules()
	candidates = []
	for rule in rules:
		matches, score = _rule_specificity(rule, ticket)
		if matches:
			candidates.append((rule, score))
	if not candidates:
		return None

	def sort_key(item):
		rule, score = item
		priority = rule.get("priority")
		priority = priority if priority is not None else 100
		modified = rule.get("modified")
		modified_ts = get_datetime(modified).timestamp() if modified else 0
		# lower priority number first; then higher specificity; then newer.
		return (priority, -score, -modified_ts)

	candidates.sort(key=sort_key)
	return candidates[0][0]


# ── timing computations (pure) ──────────────────────────────────────────────────
def _stage_anchor(ticket):
	"""Best available proxy for "when the ticket entered the current stage".
	No stage-entry timestamp exists yet, so use modified (changes when the stage
	is updated) and fall back to creation."""
	return get_datetime(_tv(ticket, "modified") or _tv(ticket, "creation") or now_datetime())


def _stage_sla_minutes(ticket, rule):
	"""Minutes until the current stage is due, or None when there is genuinely no
	stage SLA to apply (no stage and no rule override) — so old tickets fall back
	to the existing next_follow_up_date behaviour instead of a fabricated due."""
	rule_override = _minutes(rule, "overdue_after_minutes", None)
	if rule_override is not None:
		return rule_override
	stage = _tv(ticket, "current_service_stage")
	if _blank(stage):
		return None
	return sr.STAGE_SLA_MINUTES.get(stage, sr.DEFAULT_SLA_MINUTES)


def calculate_stage_due_at(ticket, rule, now=None):
	"""When the current stage is due = stage entry + stage SLA. None if no SLA."""
	sla = _stage_sla_minutes(ticket, rule)
	if sla is None:
		return None
	return add_to_date(_stage_anchor(ticket), minutes=sla)


def calculate_due_soon_at(ticket, rule, now=None):
	"""Pre-overdue alert time = stage due - lead. Always before stage due."""
	due = calculate_stage_due_at(ticket, rule, now)
	if due is None:
		return None
	sla = _stage_sla_minutes(ticket, rule)
	lead = _minutes(rule, "due_soon_before_minutes", sr.pre_overdue_lead_minutes(sla))
	return add_to_date(due, minutes=-lead)


def calculate_next_followup(ticket, rule, now=None, force=False):
	"""Staff-facing follow-up time. A manually entered `next_follow_up_date` is
	preserved unless force=True; otherwise = creation + first-follow-up minutes."""
	manual = _tv(ticket, "next_follow_up_date")
	if manual and not force:
		return get_datetime(manual)
	anchor = get_datetime(_tv(ticket, "creation") or now or now_datetime())
	mins = _minutes(rule, "first_followup_after_minutes", FALLBACK_FIRST_FOLLOWUP_MIN)
	return add_to_date(anchor, minutes=mins)


# ── derivations (pure) ───────────────────────────────────────────────────────────
def _effective_due(ticket, rule, now):
	"""Stored stage_due_at if present, else computed — keeps old tickets working."""
	stored = _tv(ticket, "stage_due_at")
	return get_datetime(stored) if stored else calculate_stage_due_at(ticket, rule, now)


def _effective_pre_overdue(ticket, rule, now):
	stored = _tv(ticket, "pre_overdue_alert_at")
	return get_datetime(stored) if stored else calculate_due_soon_at(ticket, rule, now)


def _overdue_status(ticket, rule, now):
	return sr.compute_overdue_status(
		_effective_due(ticket, rule, now),
		_effective_pre_overdue(ticket, rule, now),
		_tv(ticket, "next_follow_up_date"),
		now,
	)


def derive_escalation_level(ticket, rule=None, now=None):
	"""Escalation from overdue age + risk flags (Step-3 mapping). Reporting/filter
	signal only — not a second escalation engine."""
	now = now or now_datetime()
	status = _overdue_status(ticket, rule, now)
	od = sr.overdue_days(_effective_due(ticket, rule, now), _tv(ticket, "next_follow_up_date"), now)

	if status == "Overdue":
		base = "Owner" if od > 3 else ("Manager" if od >= 1 else "Coordinator")
	else:
		base = "None"  # Not Due / Due Soon stay calm

	bumps = [base]
	if _tv(ticket, "is_repeated_complaint") == "Yes":
		bumps.append("Manager")  # repeat → at least Manager

	promise = sr.compute_promise_status(
		_tv(ticket, "customer_promised_update_at"), _tv(ticket, "customer_promise_status"), now
	)
	if promise == "Breached":
		bumps.append("Manager" if status == "Overdue" else "Coordinator")

	if _tv(ticket, "service_flow_type") == _PRODUCT_AT_STORE_FLOW and status == "Overdue":
		bumps.append("Manager")  # product-at-store ageing

	if _tv(ticket, "current_service_stage") == _SPARE_PENDING_STAGE and status == "Overdue":
		bumps.append("Owner" if od > 3 else "Manager")  # spare pending ageing

	return _max_level(*bumps)


def derive_customer_update_due(ticket, rule=None, now=None):
	"""True when the rule requires customer updates and one is now due:
	none yet, the last is older than the cadence, or a promise has breached."""
	if not _checked(rule, "customer_update_required"):
		return False
	now = now or now_datetime()

	promise = sr.compute_promise_status(
		_tv(ticket, "customer_promised_update_at"), _tv(ticket, "customer_promise_status"), now
	)
	if promise == "Breached":
		return True

	last = _tv(ticket, "customer_informed_at")
	if _blank(last):
		return True

	every = _minutes(rule, "customer_update_every_minutes", 0)
	if every and (now - get_datetime(last)).total_seconds() / 60.0 > every:
		return True
	return False


# ── state refresh ────────────────────────────────────────────────────────────────
def refresh_ticket_reminder_state(ticket, now=None, save=False, force=False, rules=None):
	"""Compute the full reminder state for a ticket. Compute-only by default;
	persists the safe stage fields only when save=True (never the manual
	next_follow_up_date unless force=True)."""
	now = now or now_datetime()
	rule = resolve_reminder_rule(ticket, rules=rules)

	stage_due = calculate_stage_due_at(ticket, rule, now)
	due_soon = calculate_due_soon_at(ticket, rule, now)
	next_followup = calculate_next_followup(ticket, rule, now, force=force)
	status = _overdue_status(ticket, rule, now)
	escalation = derive_escalation_level(ticket, rule, now)
	update_due = derive_customer_update_due(ticket, rule, now)
	promise = sr.compute_promise_status(
		_tv(ticket, "customer_promised_update_at"), _tv(ticket, "customer_promise_status"), now
	)

	state = {
		"reminder_rule_applied": rule.get("name") if rule else None,
		"computed_next_followup_at": _iso(next_followup),
		"computed_due_soon_at": _iso(due_soon),
		"computed_stage_due_at": _iso(stage_due),
		"overdue_status": status,
		"computed_escalation_level": escalation,
		"customer_update_due": update_due,
		"customer_promise_status": promise,
	}

	if save:
		_persist_state(ticket, stage_due, due_soon, escalation, status, next_followup, force)
	return state


def _persist_state(ticket, stage_due, due_soon, escalation, status, next_followup, force):
	"""Write only the safe, computed stage fields. Guarded so it is a no-op for
	unsaved/in-memory tickets used in tests."""
	name = _tv(ticket, "name")
	if not name or not frappe.db.exists("HD Ticket", name):
		return
	meta = frappe.get_meta("HD Ticket")
	values = {}
	if meta.has_field("stage_due_at"):
		values["stage_due_at"] = stage_due
	if meta.has_field("pre_overdue_alert_at"):
		values["pre_overdue_alert_at"] = due_soon
	if meta.has_field("escalation_level"):
		values["escalation_level"] = escalation
	if meta.has_field("overdue_status"):
		values["overdue_status"] = status
	# Manual follow-up is sacred unless force=True was explicitly requested.
	if force and meta.has_field("next_follow_up_date"):
		values["next_follow_up_date"] = next_followup
	if values:
		frappe.db.set_value("HD Ticket", name, values, update_modified=False)


# ── safe read API ────────────────────────────────────────────────────────────────
@frappe.whitelist()
def get_reminder_state(ticket_name):
	"""Read-only: resolve + compute the reminder state for one ticket. Never
	writes. Permission-checked via the standard HD Ticket read permission."""
	if not frappe.has_permission("HD Ticket", "read", doc=ticket_name):
		frappe.throw("Not permitted to read this ticket.", frappe.PermissionError)
	doc = frappe.get_doc("HD Ticket", ticket_name)
	return refresh_ticket_reminder_state(doc, save=False)
