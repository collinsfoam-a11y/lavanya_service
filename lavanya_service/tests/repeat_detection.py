"""Rollback-safe tests for Phase 1N-5 repeat complaint suggestion.

Run with:
    bench --site <site> execute lavanya_service.tests.repeat_detection.run

All writes happen in the current transaction and are rolled back by ``run``.
"""

import frappe

from lavanya_service.workflow.repeat_complaints import (
	clear_repeat_complaint,
	confirm_repeat_complaint,
	find_repeat_candidates,
)

RESULTS = []
USERS = {}

PHONE_MAIN = "9876500001"
PHONE_OTHER = "9876500002"
PHONE_UNRELATED = "9123400000"
SERIAL_MAIN = "SN-RPT-MAIN-1"
MODEL_MAIN = "MX-100"

SAFE_PAYLOAD_KEYS = {
	"ticket",
	"score",
	"match_reasons",
	"subject",
	"status",
	"customer_name",
	"brand",
	"product_type",
	"product_item",
	"model_no",
	"serial_no",
	"creation",
}

FORBIDDEN_SIDE_EFFECT_DOCTYPES = [
	"Email Queue",
	"Notification Log",
	"Communication",
	"ToDo",
	"Comment",
]

ROLLBACK_DOCTYPES = [
	"HD Ticket",
	"User",
	"HD Agent",
	"Service Product Receipt",
] + FORBIDDEN_SIDE_EFFECT_DOCTYPES


def _record(test_id, description, passed, detail=""):
	RESULTS.append((test_id, description, bool(passed), detail))
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {test_id} - {description}" + (f" | {detail}" if detail else ""))


def _count(doctype):
	return frappe.db.count(doctype) if frappe.db.exists("DocType", doctype) else 0


def _make_user(key, role, agent=True):
	email = f"qa-rpt-{key}@example.com"
	if frappe.db.exists("User", email):
		frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	user = frappe.new_doc("User")
	user.email = email
	user.first_name = f"QA Repeat {key.title()}"
	user.enabled = 1
	user.user_type = "System User"
	user.append("roles", {"role": role})
	# Helpdesk record-level permission requires the actor to be an agent
	# (or ticket owner); Lavanya role gates still govern the repeat actions.
	if agent:
		user.append("roles", {"role": "Agent"})
	user.insert(ignore_permissions=True)
	return email


def _ensure_users():
	USERS["manager"] = _make_user("manager", "Lavanya Manager")
	USERS["coordinator"] = _make_user("coordinator", "Lavanya Service Coordinator")
	USERS["agent"] = _make_user("agent", "Lavanya Helpdesk Agent")
	USERS["front_desk"] = _make_user("frontdesk", "Lavanya Front Desk")
	USERS["viewer"] = _make_user("viewer", "Lavanya Viewer", agent=False)


def _insert_ticket(subject, **overrides):
	doc = frappe.new_doc("HD Ticket")
	doc.subject = subject
	doc.description = "Created by repeat_detection, rolled back"
	doc.ticket_type = overrides.pop("ticket_type", "Customer Complaint - Site")
	doc.priority = overrides.pop("priority", "Medium")
	doc.customer_name = overrides.pop("customer_name", "QA Repeat Customer")
	doc.update(overrides)
	doc.insert(ignore_permissions=True)
	return doc.name


def _force_status(ticket_name, status):
	frappe.db.set_value("HD Ticket", ticket_name, "status", status)


def _call_as(user, fn, **kwargs):
	frappe.set_user(user)
	try:
		return fn(**kwargs)
	finally:
		frappe.set_user("Administrator")


def _blocks(user, fn, **kwargs):
	"""Return (was_blocked, error_text)."""
	frappe.set_user(user)
	try:
		fn(**kwargs)
		return False, ""
	except Exception as exc:  # noqa: BLE001 - intentional: we assert on the block
		return True, str(exc)[:200]
	finally:
		frappe.set_user("Administrator")


def run():
	RESULTS.clear()
	baseline = {dt: _count(dt) for dt in ROLLBACK_DOCTYPES}
	try:
		_run_all()
	finally:
		frappe.set_user("Administrator")
		frappe.db.rollback()
		rollback_ok = {dt: _count(dt) == baseline[dt] for dt in ROLLBACK_DOCTYPES}
		_record(
			"RPT-018",
			"automated test records roll back cleanly",
			all(rollback_ok.values()),
			str({dt: ok for dt, ok in rollback_ok.items() if not ok}),
		)

	failed = [r for r in RESULTS if not r[2]]
	print(f"\nTOTAL: {len(RESULTS)} | PASS: {len(RESULTS) - len(failed)} | FAIL: {len(failed)}")
	if failed:
		for test_id, description, _passed, detail in failed:
			print(f"  FAILED: {test_id} - {description} | {detail}")
	print("OVERALL:", "PASS" if not failed else "FAIL")
	return {"total": len(RESULTS), "failed": len(failed)}


def _run_all():
	_ensure_users()

	# Fixture tickets. The controller resets status on insert; closed and
	# cancelled history is forced via db.set_value to bypass closure guards.
	current = _insert_ticket(
		"RPT current complaint",
		phone_1=PHONE_MAIN,
		brand="Preethi",
		product_type="Mixer",
		model_no=MODEL_MAIN,
		serial_no=SERIAL_MAIN,
	)
	mobile_brand = _insert_ticket(
		"RPT previous: same mobile + brand",
		phone_1=PHONE_MAIN,
		brand="Preethi",
		product_type="Refrigerator",
	)
	serial_only = _insert_ticket(
		"RPT previous: same serial, different mobile",
		phone_1=PHONE_OTHER,
		brand="Bajaj",
		product_type="Refrigerator",
		serial_no=SERIAL_MAIN,
	)
	mobile_model = _insert_ticket(
		"RPT previous: same mobile + model",
		phone_1=PHONE_MAIN,
		brand="LG",
		product_type="Refrigerator",
		model_no=MODEL_MAIN,
	)
	unrelated = _insert_ticket(
		"RPT unrelated: different mobile and product",
		phone_1=PHONE_UNRELATED,
		brand="LG",
		product_type="TV",
		serial_no="SN-RPT-OTHER",
	)
	below_threshold = _insert_ticket(
		"RPT below threshold: same mobile only",
		phone_1=PHONE_MAIN,
		brand="LG",
		product_type="TV",
	)
	closed_history = _insert_ticket(
		"RPT closed history: same mobile + brand",
		phone_1=PHONE_MAIN,
		brand="Preethi",
		product_type="Washing Machine",
	)
	_force_status(closed_history, "Closed")
	cancelled_weak = _insert_ticket(
		"RPT cancelled: same mobile + brand (no serial)",
		phone_1=PHONE_MAIN,
		brand="Preethi",
		product_type="Chimney",
	)
	_force_status(cancelled_weak, "Cancelled")
	cancelled_serial = _insert_ticket(
		"RPT cancelled: same serial",
		phone_1=PHONE_OTHER,
		brand="Bajaj",
		product_type="Hob",
		serial_no=SERIAL_MAIN,
	)
	_force_status(cancelled_serial, "Cancelled")

	result = _call_as(
		USERS["coordinator"], find_repeat_candidates, ticket_name=current, limit=10
	)
	candidates = result["candidates"]
	by_ticket = {c["ticket"]: c for c in candidates}

	# 1. Same normalized mobile + same brand suggests previous ticket
	row = by_ticket.get(mobile_brand)
	_record(
		"RPT-001",
		"same mobile + same brand suggests previous ticket",
		bool(row)
		and "same mobile" in row["match_reasons"]
		and "same brand" in row["match_reasons"],
		f"row={row and {k: row[k] for k in ('score', 'match_reasons')}}",
	)

	# 2. Same serial gives strong match
	row = by_ticket.get(serial_only)
	_record(
		"RPT-002",
		"same serial_no gives strong match",
		bool(row) and row["score"] >= 60 and "same serial" in row["match_reasons"],
		f"row={row and {k: row[k] for k in ('score', 'match_reasons')}}",
	)

	# 3. Same model + mobile suggests candidate
	row = by_ticket.get(mobile_model)
	_record(
		"RPT-003",
		"same model_no + mobile suggests candidate",
		bool(row)
		and "same mobile" in row["match_reasons"]
		and "same model" in row["match_reasons"],
		f"row={row and {k: row[k] for k in ('score', 'match_reasons')}}",
	)

	# 4. Different mobile/product does not suggest; below-threshold excluded
	_record(
		"RPT-004",
		"different mobile/product does not suggest",
		unrelated not in by_ticket,
	)
	_record(
		"RPT-004b",
		"same mobile alone stays below threshold and is excluded",
		below_threshold not in by_ticket,
	)

	# 5. Current ticket excluded
	_record("RPT-005", "current ticket excluded from candidates", current not in by_ticket)

	# 6. Closed old ticket suggested as history
	_record(
		"RPT-006",
		"closed old ticket suggested as history",
		closed_history in by_ticket
		and by_ticket[closed_history]["status"] == "Closed",
	)

	# 7. Cancelled handling
	_record(
		"RPT-007",
		"cancelled ticket excluded unless serial exact match",
		cancelled_weak not in by_ticket and cancelled_serial in by_ticket,
		f"weak_in={cancelled_weak in by_ticket}, serial_in={cancelled_serial in by_ticket}",
	)

	# 8. Sorted by score (non-increasing)
	scores = [c["score"] for c in candidates]
	_record(
		"RPT-008",
		"candidates sorted by score descending",
		scores == sorted(scores, reverse=True),
		f"scores={scores}",
	)

	# 9. Safe fields only
	leaked = set()
	for c in candidates:
		leaked |= set(c.keys()) - SAFE_PAYLOAD_KEYS
	_record("RPT-009", "candidate payload exposes only safe fields", not leaked, f"leaked={sorted(leaked)}")

	# 9b. Unsaved form data path reuses the canonical phone normalizer
	data_result = _call_as(
		USERS["coordinator"],
		find_repeat_candidates,
		data={"phone_1": "+91 98765 00001", "brand": "Preethi"},
		limit=10,
	)
	data_tickets = {c["ticket"] for c in data_result["candidates"]}
	_record(
		"RPT-009b",
		"unsaved form data with raw phone (+91) finds candidates",
		mobile_brand in data_tickets,
		f"found={sorted(data_tickets)}",
	)

	# 10/11. Confirm sets flag and link (coordinator)
	outcome = _call_as(
		USERS["coordinator"],
		confirm_repeat_complaint,
		ticket_name=current,
		previous_ticket_link=mobile_brand,
	)
	flag, link = frappe.db.get_value(
		"HD Ticket", current, ["is_repeated_complaint", "previous_ticket_link"]
	)
	_record("RPT-010", "confirm sets is_repeated_complaint = Yes", flag == "Yes", f"flag={flag}")
	_record(
		"RPT-011",
		"confirm sets previous_ticket_link",
		link == mobile_brand and outcome.get("ok") is True,
		f"link={link}",
	)

	# 12. Self-link blocked
	blocked, err = _blocks(
		USERS["coordinator"],
		confirm_repeat_complaint,
		ticket_name=current,
		previous_ticket_link=current,
	)
	_record("RPT-012", "confirm blocks self-link", blocked, err)

	# 13. Nonexistent previous ticket blocked
	blocked, err = _blocks(
		USERS["coordinator"],
		confirm_repeat_complaint,
		ticket_name=current,
		previous_ticket_link="HD-DOES-NOT-EXIST-0001",
	)
	_record("RPT-013", "confirm blocks nonexistent previous ticket", blocked, err)

	# 14. Viewer cannot confirm
	blocked, err = _blocks(
		USERS["viewer"],
		confirm_repeat_complaint,
		ticket_name=current,
		previous_ticket_link=serial_only,
	)
	_record("RPT-014", "viewer cannot confirm repeat complaint", blocked, err)

	# 15. Front Desk blocked (documented decision: intake-correction policy
	# unconfirmed, so the spec's "block Front Desk when uncertain" rule applies)
	blocked, err = _blocks(
		USERS["front_desk"],
		confirm_repeat_complaint,
		ticket_name=current,
		previous_ticket_link=serial_only,
	)
	_record("RPT-015", "front desk blocked from confirm (documented rule)", blocked, err)

	# 15b. Helpdesk Agent CAN confirm (allowed role)
	outcome = _call_as(
		USERS["agent"],
		confirm_repeat_complaint,
		ticket_name=current,
		previous_ticket_link=serial_only,
	)
	link = frappe.db.get_value("HD Ticket", current, "previous_ticket_link")
	_record(
		"RPT-015b",
		"helpdesk agent can confirm repeat complaint",
		outcome.get("ok") is True and link == serial_only,
		f"link={link}",
	)

	# 15c. Agent cannot clear (clear is Manager/Coordinator only)
	blocked, err = _blocks(USERS["agent"], clear_repeat_complaint, ticket_name=current)
	_record("RPT-015c", "agent blocked from clear (manager/coordinator only)", blocked, err)

	# 16. Clear works for coordinator
	outcome = _call_as(USERS["coordinator"], clear_repeat_complaint, ticket_name=current)
	flag, link = frappe.db.get_value(
		"HD Ticket", current, ["is_repeated_complaint", "previous_ticket_link"]
	)
	_record(
		"RPT-016",
		"clear resets repeat flag and previous link",
		flag == "No" and not link and outcome.get("ok") is True,
		f"flag={flag}, link={link}",
	)

	# 17. No forbidden side effects from the repeat workflow
	before = {dt: _count(dt) for dt in FORBIDDEN_SIDE_EFFECT_DOCTYPES}
	_call_as(USERS["coordinator"], find_repeat_candidates, ticket_name=current)
	_call_as(
		USERS["coordinator"],
		confirm_repeat_complaint,
		ticket_name=current,
		previous_ticket_link=mobile_brand,
	)
	_call_as(USERS["coordinator"], clear_repeat_complaint, ticket_name=current)
	after = {dt: _count(dt) for dt in FORBIDDEN_SIDE_EFFECT_DOCTYPES}
	diffs = {dt: (before[dt], after[dt]) for dt in after if before[dt] != after[dt]}
	_record("RPT-017", "no forbidden side effects", not diffs, f"diffs={diffs}")
