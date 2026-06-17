"""Hourly reminder-state refresh (reminder engine, Step 4).

Persists the Step-3 computed reminder state for active HD Tickets so Today's Work,
reports, and manager views don't have to recompute everything live. Safe by
design: idempotent, batched (commit per batch), per-ticket failures logged
without aborting the run, never overwrites a manual next_follow_up_date, sends no
messages, and writes at most ONE structured breach Comment per ticket.

It reuses `reminder_engine.refresh_ticket_reminder_state(..., save=True)` for the
stage fields; promise-status persistence + the one-time breach Comment are owned
here because they are transition-aware side effects, not pure computation.
"""

import frappe

from lavanya_service import reminder_engine as re

TICKET_DOCTYPE = "HD Ticket"

# Statuses treated as inactive (skipped). Extra values (Spam/Archived) are
# harmless if the status doesn't exist — they simply match nothing.
INACTIVE_STATUSES = ["Closed", "Resolved", "Cancelled", "Spam", "Archived"]

DEFAULT_BATCH_SIZE = 50
DEFAULT_MAX_PER_RUN = 500

BREACH_REASON = "Promised update time passed without being marked met"
BREACH_COMMENT = "[Customer Promise Breach] promised update missed"

# Engine read-inputs we try to select (only those that exist are fetched).
_ENGINE_FIELDS = [
	"current_service_stage", "service_flow_type", "stage_due_at", "pre_overdue_alert_at",
	"next_follow_up_date", "is_repeated_complaint", "customer_promised_update_at",
	"customer_promise_status", "customer_informed_at", "brand", "product_type",
	"ticket_type", "warranty_route", "pending_reason", "customer_priority",
	"overdue_status", "escalation_level",
]


def get_active_ticket_names(limit=None, offset=0):
	"""Names of active HD Tickets (oldest-modified first), for batched processing."""
	return frappe.get_all(
		TICKET_DOCTYPE,
		filters=[["status", "not in", INACTIVE_STATUSES]],
		order_by="modified asc",
		pluck="name",
		limit_page_length=limit or 0,  # 0 == no limit in Frappe
		limit_start=offset or 0,
	)


def _select_fields(meta):
	fields = ["name", "modified", "creation", "status"]
	for fieldname in _ENGINE_FIELDS:
		if meta.has_field(fieldname) and fieldname not in fields:
			fields.append(fieldname)
	return fields


def _state_changed(row, state, meta):
	"""Best-effort change detection for reporting (storage no-ops identical writes)."""
	checks = [
		("stage_due_at", "computed_stage_due_at"),
		("overdue_status", "overdue_status"),
		("escalation_level", "computed_escalation_level"),
	]
	for stored_field, state_key in checks:
		if not meta.has_field(stored_field):
			continue
		stored = row.get(stored_field)
		stored = stored.isoformat() if hasattr(stored, "isoformat") else stored
		if (stored or None) != (state.get(state_key) or None):
			return True
	return False


def _mark_breach(name, stats):
	"""On a Pending→Breached transition: stamp a reason (if empty) and add ONE
	structured Comment. Both guarded so repeat runs never duplicate."""
	meta = frappe.get_meta(TICKET_DOCTYPE)
	if meta.has_field("promise_breach_reason"):
		if not (frappe.db.get_value(TICKET_DOCTYPE, name, "promise_breach_reason") or "").strip():
			frappe.db.set_value(TICKET_DOCTYPE, name, "promise_breach_reason", BREACH_REASON, update_modified=False)

	already = frappe.db.exists(
		"Comment",
		{"reference_doctype": TICKET_DOCTYPE, "reference_name": name,
		 "content": ["like", "%" + BREACH_COMMENT + "%"]},
	)
	if not already:
		frappe.get_doc(TICKET_DOCTYPE, name).add_comment("Comment", BREACH_COMMENT)
		stats["comments"] += 1


def _process_ticket(row, rules, now, dry_run, meta, stats):
	name = row.get("name")
	old_promise = row.get("customer_promise_status")

	state = re.refresh_ticket_reminder_state(row, now=now, save=(not dry_run), rules=rules)
	if _state_changed(row, state, meta):
		stats["changed"] += 1

	new_promise = state.get("customer_promise_status")
	if not dry_run and meta.has_field("customer_promise_status") and new_promise != old_promise:
		frappe.db.set_value(TICKET_DOCTYPE, name, "customer_promise_status", new_promise, update_modified=False)

	# Breach transition (Pending → Breached). Guarded so it fires once per ticket.
	if new_promise == "Breached" and old_promise != "Breached":
		stats["breaches"] += 1
		if not dry_run:
			_mark_breach(name, stats)


def refresh_active_ticket_reminders(batch_size=DEFAULT_BATCH_SIZE, max_tickets=DEFAULT_MAX_PER_RUN, dry_run=False, now=None):
	"""Hourly job: refresh + persist reminder state for active tickets, batched.

	Idempotent: storage no-ops identical writes, manual follow-ups are never
	touched, and a breach Comment is written at most once per ticket. Per-ticket
	errors are logged and skipped so one bad ticket never aborts the run."""
	batch_size = max(1, int(batch_size or DEFAULT_BATCH_SIZE))
	max_tickets = max(1, int(max_tickets or DEFAULT_MAX_PER_RUN))
	dry_run = bool(dry_run)

	# Fresh rule cache for this run.
	frappe.local._lavanya_reminder_rules = None
	rules = re.get_active_rules()
	meta = frappe.get_meta(TICKET_DOCTYPE)
	fields = _select_fields(meta)

	names = get_active_ticket_names(limit=max_tickets)
	stats = {"scanned": 0, "changed": 0, "breaches": 0, "comments": 0, "errors": 0,
			 "dry_run": dry_run, "batch_size": batch_size, "candidates": len(names)}

	for start in range(0, len(names), batch_size):
		batch = names[start:start + batch_size]
		rows = frappe.get_all(TICKET_DOCTYPE, filters=[["name", "in", batch]], fields=fields)
		for row in rows:
			try:
				_process_ticket(row, rules, now, dry_run, meta, stats)
				stats["scanned"] += 1
			except Exception:
				stats["errors"] += 1
				frappe.log_error(
					title="lavanya reminder_refresh: " + str(row.get("name")),
					message=frappe.get_traceback(),
				)
		if not dry_run:
			frappe.db.commit()

	frappe.logger("lavanya").info("reminder_refresh %s" % stats)
	return stats
