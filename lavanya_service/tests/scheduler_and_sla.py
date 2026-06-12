"""Rollback-safe scheduler proof and SLA pause tests.

Run with:
    bench --site <site> execute lavanya_service.tests.scheduler_and_sla.run
"""

import frappe
from frappe.utils import add_days, now_datetime, today


RESULTS = []

SCHEDULER_HOOK = (
	"lavanya_service.reminders.notification_output."
	"run_daily_reminder_notifications_dry_safe"
)
PAUSED_STATUSES = [
	"Waiting on Customer",
	"Waiting on Part / Approval",
	"Ready for Pickup",
]


def _record(test_id, description, passed, detail=""):
	RESULTS.append((test_id, description, bool(passed), detail))
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {test_id} - {description}" + (f" | {detail}" if detail else ""))


def _assert(test_id, description, condition, detail=""):
	_record(test_id, description, bool(condition), detail)


def _count(doctype):
	return frappe.db.count(doctype) if frappe.db.exists("DocType", doctype) else 0


def run():
	RESULTS.clear()

	baseline = {
		"HD Ticket": frappe.db.count("HD Ticket"),
		"Email Queue": _count("Email Queue"),
		"Notification Log": _count("Notification Log"),
		"Communication": _count("Communication"),
		"ToDo": _count("ToDo"),
		"Comment": _count("Comment"),
		"HD Notification": _count("HD Notification"),
	}

	try:
		_test_scheduler_hook_and_heartbeat(baseline)
		_test_status_category_mapping()
		_test_sla_pause_breach_candidates()
	finally:
		frappe.set_user("Administrator")
		frappe.db.rollback()
		print("\nTRANSACTION ROLLED BACK - no records persisted")

	failed = [row for row in RESULTS if not row[2]]
	print(f"\nTOTAL: {len(RESULTS)} | PASS: {len(RESULTS) - len(failed)} | FAIL: {len(failed)}")
	if failed:
		print("FAILED TESTS:")
		for test_id, description, _passed, detail in failed:
			print(f"  - {test_id}: {description} | {detail}")
	print("BASELINE:", baseline)
	print("OVERALL:", "PASS" if not failed else "FAIL")
	return {"total": len(RESULTS), "failed": len(failed)}


def _test_scheduler_hook_and_heartbeat(baseline):
	from lavanya_service.reminders.ticket_reminders import (
		get_last_reminder_scan_heartbeat,
		run_daily_reminder_scan_dry_run,
	)

	daily_hooks = frappe.get_hooks("scheduler_events").get("daily") or []
	_assert(
		"SS-001",
		"scheduler hook includes Lavanya reminder output",
		SCHEDULER_HOOK in daily_hooks,
		daily_hooks,
	)

	callable_ = frappe.get_attr(SCHEDULER_HOOK)
	_assert("SS-002", "scheduler callable imports", callable(callable_), callable_)

	snapshot = run_daily_reminder_scan_dry_run()
	heartbeat = get_last_reminder_scan_heartbeat()

	_assert(
		"SS-003",
		"manual dry-run scanner returns snapshot counts",
		isinstance(snapshot, dict) and bool(snapshot.get("counts")),
		snapshot.get("counts") if isinstance(snapshot, dict) else snapshot,
	)
	_assert(
		"SS-004",
		"manual dry-run scanner writes heartbeat proof",
		bool(heartbeat and heartbeat.get("counts") == snapshot.get("counts")),
		heartbeat,
	)

	unchanged = {
		"Email Queue": _count("Email Queue") == baseline["Email Queue"],
		"Notification Log": _count("Notification Log") == baseline["Notification Log"],
		"Communication": _count("Communication") == baseline["Communication"],
		"ToDo": _count("ToDo") == baseline["ToDo"],
		"Comment": _count("Comment") == baseline["Comment"],
		"HD Notification": _count("HD Notification") == baseline["HD Notification"],
	}
	_assert("SS-005", "manual dry-run scanner creates no side effects", all(unchanged.values()), unchanged)


def _test_status_category_mapping():
	expected = {
		"New": "Open",
		"Registration Pending": "Open",
		"Brand Registered": "Open",
		"In Progress": "Open",
		"Waiting on Customer": "Paused",
		"Waiting on Part / Approval": "Paused",
		"Ready for Pickup": "Paused",
		"Resolved": "Resolved",
		"Closed": "Resolved",
		"Cancelled": "Resolved",
	}

	actual = {
		row.name: row.category
		for row in frappe.get_all(
			"HD Ticket Status",
			fields=["name", "category"],
			filters={"name": ["in", list(expected)]},
		)
	}
	mismatches = {
		name: {"expected": category, "actual": actual.get(name)}
		for name, category in expected.items()
		if actual.get(name) != category
	}

	_assert("SS-006", "HD Ticket status categories match approved mapping", not mismatches, mismatches)


def _test_sla_pause_breach_candidates():
	from lavanya_service.reminders.ticket_reminders import get_reminder_snapshot

	paused_ticket_names = []

	for status in PAUSED_STATUSES:
		ticket = _make_overdue_ticket(status)
		paused_ticket_names.append(ticket.name)

	active_ticket = _make_overdue_ticket("In Progress")

	snapshot = get_reminder_snapshot(limit=500)
	response_candidates = _names(snapshot["tickets"]["sla_response_breach_candidates"])
	resolution_candidates = _names(snapshot["tickets"]["sla_resolution_breach_candidates"])

	paused_response_hits = sorted(set(paused_ticket_names) & response_candidates)
	paused_resolution_hits = sorted(set(paused_ticket_names) & resolution_candidates)

	_assert(
		"SS-007",
		"paused tickets excluded from active SLA response breach candidates",
		not paused_response_hits,
		paused_response_hits,
	)
	_assert(
		"SS-008",
		"paused tickets excluded from active SLA resolution breach candidates",
		not paused_resolution_hits,
		paused_resolution_hits,
	)
	_assert(
		"SS-009",
		"active In Progress overdue ticket detected as response breach candidate",
		active_ticket.name in response_candidates,
		{"ticket": active_ticket.name, "candidates": sorted(response_candidates)},
	)
	_assert(
		"SS-010",
		"active In Progress overdue ticket detected as resolution breach candidate",
		active_ticket.name in resolution_candidates,
		{"ticket": active_ticket.name, "candidates": sorted(resolution_candidates)},
	)


def _make_overdue_ticket(status):
	ticket = frappe.new_doc("HD Ticket")
	slug = status.lower().replace(" ", "-").replace("/", "-")
	ticket.subject = f"ROLLBACK Scheduler SLA {status}"
	ticket.raised_by = f"scheduler-sla-{slug}@example.com"
	ticket.ticket_type = "Customer Complaint - Site"
	ticket.priority = "Medium"
	ticket.complaint_source = "Phone Call"
	ticket.customer_name = "Scheduler SLA Tester"
	ticket.phone_1 = "0495-2222222 ext 4"
	ticket.product_type = "AC"
	ticket.brand = "LG"
	ticket.purchased_from_lavanya = "Unknown"
	ticket.warranty_status = "Unknown"
	ticket.insert(ignore_permissions=True)

	category = frappe.db.get_value("HD Ticket Status", status, "category")
	old_time = add_days(now_datetime(), -3)
	frappe.db.set_value(
		"HD Ticket",
		ticket.name,
		{
			"status": status,
			"status_category": category,
			"pending_reason": "Rollback scheduler SLA test",
			"next_follow_up_date": add_days(today(), -2),
			"response_by": old_time,
			"resolution_by": old_time,
		},
		update_modified=False,
	)

	return frappe.get_doc("HD Ticket", ticket.name)


def _names(rows):
	return {row.name for row in rows}
