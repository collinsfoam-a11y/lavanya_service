"""Delta Sprint 2 tests — stage layer Due-Soon / escalation / payload.

Run: bench --site <site> execute lavanya_service.tests.stage_layer.run
Covers: Due Soon before Overdue, fallback for old tickets without stage_due_at,
escalation_level derivation, Today's Work payload exposes stage fields, and
get_ticket_detail returns a blank-safe stage dict.
"""

import frappe
from frappe.utils import add_to_date, add_days, now_datetime, today

from lavanya_service import stage_rules as sr


def _assert(cond, msg):
	if not cond:
		raise AssertionError(msg)


def run():
	print("Running stage-layer (delta Sprint 2) tests…")
	frappe.set_user("Administrator")
	now = now_datetime()

	# 1. Stage-SLA: Due Soon (pre-overdue passed, due in future) vs Overdue.
	_assert(
		sr.compute_overdue_status(stage_due_at=add_to_date(now, hours=2), pre_overdue_alert_at=add_to_date(now, minutes=-60), now=now) == "Due Soon",
		"expected Due Soon",
	)
	_assert(
		sr.compute_overdue_status(stage_due_at=add_to_date(now, hours=-1), pre_overdue_alert_at=add_to_date(now, hours=-3), now=now) == "Overdue",
		"expected Overdue",
	)
	_assert(
		sr.compute_overdue_status(stage_due_at=add_to_date(now, hours=10), pre_overdue_alert_at=add_to_date(now, hours=5), now=now) == "Not Due",
		"expected Not Due",
	)

	# 2. Due Soon shows BEFORE Overdue: due in 1h with pre-overdue passed is Due Soon.
	_assert(
		sr.compute_overdue_status(stage_due_at=add_to_date(now, hours=1), pre_overdue_alert_at=add_to_date(now, minutes=-30), now=now) == "Due Soon",
		"Due Soon must precede Overdue",
	)

	# 3. Fallback for old tickets without stage_due_at (date-based).
	_assert(sr.compute_overdue_status(next_follow_up_date=add_days(today(), -2), now=now) == "Overdue", "fallback overdue")
	_assert(sr.compute_overdue_status(next_follow_up_date=today(), now=now) == "Due Soon", "fallback due-soon")
	_assert(sr.compute_overdue_status(next_follow_up_date=add_days(today(), 3), now=now) == "Not Due", "fallback not-due")
	_assert(sr.compute_overdue_status(now=now) == "Not Due", "no dates -> Not Due")

	# 4. escalation_level derivation.
	_assert(sr.compute_escalation_level(next_follow_up_date=today(), now=now) == "None", "esc None")
	_assert(sr.compute_escalation_level(next_follow_up_date=add_days(today(), -1), now=now) == "Coordinator", "esc Coordinator")
	_assert(sr.compute_escalation_level(next_follow_up_date=add_days(today(), -2), now=now) == "Manager", "esc Manager")
	_assert(sr.compute_escalation_level(next_follow_up_date=add_days(today(), -5), now=now) == "Owner", "esc Owner")
	_assert(sr.compute_escalation_level(next_follow_up_date=today(), is_repeat=True, now=now) == "Manager", "esc repeat -> Manager")

	# 5. Today's Work payload exposes stage fields; every active ticket has a computed
	#    overdue_status (so old tickets without stage_due_at still appear/work).
	from lavanya_service.workflow.today_work import get_today_work_data

	wd = get_today_work_data(user="Administrator", include_counts=True, limit=200)
	rows = [t for g in wd["groups"] for t in g.get("tickets", [])]
	_assert(rows, "today_work returned no tickets")
	for f in ("service_flow_type", "current_service_stage", "next_action", "overdue_status", "escalation_level"):
		_assert(f in rows[0], f"payload missing {f}")
	_assert(all(t.get("overdue_status") for t in rows), "an active ticket has no computed overdue_status")

	# 6. get_ticket_detail returns a blank-safe stage dict (nulls don't error).
	det = frappe.call("lavanya_service.api.stitch_console.get_ticket_detail", ticket_id=rows[0]["name"])
	_assert(isinstance(det.get("stage"), dict), "detail missing stage dict")
	_assert("overdue_status" in det["stage"] and "current_service_stage" in det["stage"], "stage dict incomplete")

	# 7. Existing escalation report still works (not a second engine).
	rep = frappe.call("lavanya_service.api.manager_reports.get_report", report="escalations")
	_assert("rows" in rep and "count" in rep, "escalation report broken")

	frappe.set_user("Administrator")
	print("✅ stage-layer tests passed")
