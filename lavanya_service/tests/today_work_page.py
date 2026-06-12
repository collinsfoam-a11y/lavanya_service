"""Rollback-safe tests for Phase 1N-7 Lavanya Today's Work workspace page.

Run with:
    bench --site <site> execute lavanya_service.tests.today_work_page.run

All writes happen in the current transaction and are rolled back by ``run``.
The Desk Page itself is file-defined (standard page) and synced by migrate;
these tests verify the record, role access, and that the page's data source
(`get_today_work`) behaves per role.
"""

import frappe

from lavanya_service.workflow.today_work import (
	FRONT_DESK_GROUPS,
	GROUPS,
	HELPDESK_AGENT_GROUPS,
	get_today_work_data,
)

PAGE_NAME = "lavanya-today-work"

PAGE_ROLES = {
	"System Manager",
	"Lavanya Manager",
	"Lavanya Service Coordinator",
	"Lavanya Helpdesk Agent",
	"Lavanya Front Desk",
	"Lavanya Viewer",
}

TEST_USERS = {
	"manager": ("twp.manager@lavanya.local", "Lavanya Manager"),
	"coordinator": ("twp.coordinator@lavanya.local", "Lavanya Service Coordinator"),
	"agent": ("twp.agent@lavanya.local", "Lavanya Helpdesk Agent"),
	"front_desk": ("twp.frontdesk@lavanya.local", "Lavanya Front Desk"),
	"viewer": ("twp.viewer@lavanya.local", "Lavanya Viewer"),
	"norole": ("twp.norole@lavanya.local", None),
}

SIDE_EFFECT_DOCTYPES = [
	"HD Notification",
	"Email Queue",
	"Notification Log",
	"Communication",
	"ToDo",
	"Comment",
	"HD Ticket",
	"Service Product Receipt",
]

SAFE_TICKET_FIELDS = {
	"name",
	"subject",
	"status",
	"ticket_type",
	"priority",
	"customer_name",
	"phone_1",
	"brand",
	"product_type",
	"product_item",
	"pending_reason",
	"next_follow_up_date",
	"service_product_receipt",
	"modified",
}


def _record(results, name, passed, detail=""):
	results[name] = {"passed": bool(passed), "detail": detail}
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {name}" + (f" | {detail}" if detail else ""))


def _ensure_user(email, role):
	if frappe.db.exists("User", email):
		frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	user = frappe.new_doc("User")
	user.email = email
	user.first_name = role or "No Role"
	user.send_welcome_email = 0
	user.insert(ignore_permissions=True)
	if role:
		user.add_roles(role)
	return email


def _page_permitted(user):
	frappe.set_user(user)
	try:
		page = frappe.get_doc("Page", PAGE_NAME)
		return bool(page.is_permitted())
	finally:
		frappe.set_user("Administrator")


def _today_work_as(user, **kwargs):
	frappe.set_user(user)
	try:
		return get_today_work_data(user=user, **kwargs)
	finally:
		frappe.set_user("Administrator")


def _side_effect_counts():
	return {
		dt: frappe.db.count(dt)
		for dt in SIDE_EFFECT_DOCTYPES
		if frappe.db.exists("DocType", dt)
	}


def run():
	results = {}
	try:
		_run(results)
	finally:
		frappe.db.rollback()
		frappe.set_user("Administrator")
		print("\nTRANSACTION ROLLED BACK - no records persisted")

	failed = [name for name, row in results.items() if not row["passed"]]
	print(f"\nTOTAL: {len(results)} | PASS: {len(results) - len(failed)} | FAIL: {len(failed)}")
	if failed:
		for name in failed:
			print(f"  FAILED: {name} | {results[name]['detail']}")
	print("OVERALL:", "PASS" if not failed else "FAIL")
	return {"total": len(results), "failed": len(failed)}


def _run(results):
	# 1. Page record exists, standard, correct module/title
	page_exists = frappe.db.exists("Page", PAGE_NAME)
	_record(results, "page_record_exists", bool(page_exists))
	if page_exists:
		page = frappe.get_doc("Page", PAGE_NAME)
		_record(
			results,
			"page_is_standard_lavanya_module",
			page.standard == "Yes" and page.module == "Lavanya Service",
			f"standard={page.standard}, module={page.module}",
		)
		page_roles = {row.role for row in page.roles}
		_record(
			results,
			"page_roles_match",
			page_roles == PAGE_ROLES,
			f"roles={sorted(page_roles)}",
		)

	users = {
		key: _ensure_user(email, role) for key, (email, role) in TEST_USERS.items()
	}

	# Side-effect baseline AFTER fixture users exist: user creation produces
	# role-change Comments (rolled back with everything else). The phase
	# guarantee is that PAGE DATA READS create nothing.
	before = _side_effect_counts()

	# 2/3. Role access to the page
	for key, expected in [
		("coordinator", True),
		("manager", True),
		("agent", True),
		("front_desk", True),
		("viewer", True),
		("norole", False),
	]:
		permitted = _page_permitted(users[key])
		_record(
			results,
			f"page_access_{key}",
			permitted == expected,
			f"permitted={permitted}, expected={expected}",
		)

	# 4. Coordinator sees all groups, in strict priority order
	data = _today_work_as(users["coordinator"])
	keys = [g["key"] for g in data["groups"]]
	priorities = [g["priority"] for g in data["groups"]]
	all_keys = [g["key"] for g in GROUPS]
	_record(
		results,
		"coordinator_sees_all_groups_ordered",
		keys == all_keys and priorities == sorted(priorities),
		f"keys={keys}",
	)

	# Manager parity
	data_mgr = _today_work_as(users["manager"])
	_record(
		results,
		"manager_sees_all_groups",
		[g["key"] for g in data_mgr["groups"]] == all_keys,
	)

	# 5. Front Desk limited groups
	data_fd = _today_work_as(users["front_desk"])
	fd_keys = {g["key"] for g in data_fd["groups"]}
	_record(
		results,
		"front_desk_groups_limited",
		fd_keys == FRONT_DESK_GROUPS,
		f"keys={sorted(fd_keys)}",
	)

	# Agent limited groups
	data_ag = _today_work_as(users["agent"])
	ag_keys = {g["key"] for g in data_ag["groups"]}
	_record(
		results,
		"agent_groups_limited",
		ag_keys == HELPDESK_AGENT_GROUPS,
		f"keys={sorted(ag_keys)}",
	)

	# 6. Viewer: read access to page data but no HD Ticket write
	data_viewer = _today_work_as(users["viewer"])
	_record(
		results,
		"viewer_gets_readonly_data",
		isinstance(data_viewer.get("groups"), list),
	)
	can_write = frappe.has_permission("HD Ticket", "write", user=users["viewer"])
	_record(results, "viewer_cannot_write_hd_ticket", not can_write)

	# 7. Payload rows only contain safe fields (enables link generation via name)
	sample_fields_ok = True
	detail = "no tickets in any group"
	for group in data["groups"]:
		for ticket in group["tickets"]:
			extra = set(ticket.keys()) - SAFE_TICKET_FIELDS
			missing_name = "name" not in ticket
			if extra or missing_name:
				sample_fields_ok = False
				detail = f"group={group['key']}, extra={sorted(extra)}, missing_name={missing_name}"
			break
	_record(results, "ticket_payload_safe_fields_with_name", sample_fields_ok, detail)

	# 8. Empty state: owner filter that matches nothing yields zero counts
	data_empty = _today_work_as(users["coordinator"], owner="nobody@nowhere.invalid")
	totals = sum(len(g["tickets"]) for g in data_empty["groups"])
	_record(
		results,
		"empty_state_zero_counts",
		totals == 0 and data_empty["summary"]["total"] == 0,
		f"totals={totals}",
	)

	# 9. Counts included for the page header chips
	_record(
		results,
		"groups_include_counts",
		all("count" in g for g in data["groups"]),
	)

	# 10. No forbidden side effects from reading the page data
	after = _side_effect_counts()
	diffs = {dt: (before.get(dt), after.get(dt)) for dt in after if before.get(dt) != after.get(dt)}
	# Test users are User docs (rolled back); none of the side-effect doctypes
	# may grow from page/data reads.
	_record(results, "no_side_effects", not diffs, f"diffs={diffs}")
