"""Hourly reminder-refresh task tests (reminder engine, Step 4).

Run: bench --site <site> execute lavanya_service.tests.reminder_refresh.run

Everything runs inside ONE transaction and rolls back at the end — the write-path
checks use `_process_ticket` (the same per-ticket logic the job runs) and verify
via same-transaction reads, so no commit and no cleanup are needed. Job-level
selection / batching / dry-run are verified through the real entry point in
dry_run mode (which never commits).
"""

import frappe
from frappe.utils import add_to_date, now_datetime

from lavanya_service.tasks import reminder_refresh as rr

_PASS = []
_FAIL = []


def _check(name, cond, detail=""):
	(_PASS if cond else _FAIL).append(name)
	print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" | {detail}" if detail else ""))


def _new_ticket(stage=None, **set_values):
	cust = frappe.get_all("HD Customer", limit=1)
	doc = frappe.new_doc("HD Ticket")
	doc.subject = "Step4 test ticket"
	doc.ticket_type = "Customer Complaint - Site"
	if cust:
		doc.customer = cust[0].name
	doc.insert(ignore_permissions=True)
	if stage is not None:
		frappe.db.set_value("HD Ticket", doc.name, "current_service_stage", stage, update_modified=False)
	for field, value in set_values.items():
		frappe.db.set_value("HD Ticket", doc.name, field, value, update_modified=False)
	return doc.name


def _row(name):
	meta = frappe.get_meta("HD Ticket")
	fields = rr._select_fields(meta)
	return frappe.get_all("HD Ticket", filters=[["name", "=", name]], fields=fields)[0]


def _process(name, now, dry_run=False):
	meta = frappe.get_meta("HD Ticket")
	rules = rr.re.get_active_rules()
	stats = {"scanned": 0, "changed": 0, "breaches": 0, "comments": 0, "errors": 0}
	rr._process_ticket(_row(name), rules, now, dry_run, meta, stats)
	return stats


def _breach_comment_count(name):
	return frappe.db.count("Comment", {
		"reference_doctype": "HD Ticket", "reference_name": name,
		"content": ["like", "%" + rr.BREACH_COMMENT + "%"],
	})


def run():
	print("Running reminder-refresh (Step 4) tests…")
	frappe.set_user("Administrator")
	frappe.local._lavanya_reminder_rules = None
	now = now_datetime()
	try:
		# 1 + 2. Active filter: active picked, closed/resolved ignored.
		active = _new_ticket()
		closed = _new_ticket()
		frappe.db.set_value("HD Ticket", closed, "status", "Closed", update_modified=False)
		names = rr.get_active_ticket_names()
		_check("RR-01 active ticket selected", active in names)
		_check("RR-02 closed ticket ignored", closed not in names)

		# 5. Stage fields persist when fields exist.
		staged = _new_ticket(stage="Brand Registered")
		_process(staged, now)
		vals = frappe.db.get_value("HD Ticket", staged,
			["stage_due_at", "pre_overdue_alert_at", "overdue_status", "escalation_level"], as_dict=True)
		_check("RR-05a stage_due_at persisted", bool(vals.stage_due_at), str(vals.stage_due_at))
		_check("RR-05b pre_overdue_alert_at persisted", bool(vals.pre_overdue_alert_at))
		_check("RR-05c overdue_status persisted", bool(vals.overdue_status), str(vals.overdue_status))

		# 4. Manual next_follow_up_date is never overwritten.
		manual_date = add_to_date(now, days=5).date()
		manual = _new_ticket(next_follow_up_date=manual_date)
		_process(manual, now)
		_check("RR-04 manual follow-up preserved",
			str(frappe.db.get_value("HD Ticket", manual, "next_follow_up_date")) == str(manual_date))

		# 6 + 7. Promise Pending → Breached + breach comment written exactly once.
		breach = _new_ticket(
			customer_promised_update_at=add_to_date(now, hours=-2),
			customer_promise_status="Pending",
		)
		s1 = _process(breach, now)
		new_status = frappe.db.get_value("HD Ticket", breach, "customer_promise_status")
		_check("RR-06 promise becomes Breached", new_status == "Breached", str(new_status))
		_check("RR-07a one breach comment after first run", _breach_comment_count(breach) == 1, s1)
		# Re-fetch (status now persisted Breached) → no second breach, no new comment.
		s2 = _process(breach, now)
		_check("RR-03 idempotent: no re-breach on refetch", s2["breaches"] == 0, s2)
		_check("RR-07b still exactly one breach comment", _breach_comment_count(breach) == 1)
		# Even a stale Pending row must not duplicate the comment (existence guard).
		stale = _row(breach)
		stale["customer_promise_status"] = "Pending"
		rr._process_ticket(stale, rr.re.get_active_rules(), now, False, frappe.get_meta("HD Ticket"),
			{"scanned": 0, "changed": 0, "breaches": 0, "comments": 0, "errors": 0})
		_check("RR-07c stale row still no duplicate comment", _breach_comment_count(breach) == 1)

		# 8. Dry run computes but writes nothing.
		dry = _new_ticket(stage="Brand Registered")
		res = rr.refresh_active_ticket_reminders(dry_run=True)
		_check("RR-08a dry_run flag echoed", res.get("dry_run") is True, res)
		_check("RR-08b dry run wrote nothing",
			frappe.db.get_value("HD Ticket", dry, "stage_due_at") in (None, ""),
			str(frappe.db.get_value("HD Ticket", dry, "stage_due_at")))

		# 9. Batch / max limit caps the candidate set.
		capped = rr.refresh_active_ticket_reminders(dry_run=True, max_tickets=2, batch_size=1)
		_check("RR-09 max_tickets caps candidates", capped.get("candidates", 0) <= 2, capped)

		print(f"\nTOTAL: {len(_PASS) + len(_FAIL)} | PASS: {len(_PASS)} | FAIL: {len(_FAIL)}")
		if _FAIL:
			print("FAILED: " + ", ".join(_FAIL))
		print("OVERALL: " + ("PASS" if not _FAIL else "FAIL"))
		return {"total": len(_PASS) + len(_FAIL), "failed": len(_FAIL)}
	finally:
		frappe.db.rollback()
		print("TRANSACTION ROLLED BACK - no records persisted")
