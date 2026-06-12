"""Regression checks for Phase 1M-1 role-browser UAT fixes.

Run with:
    bench --site <site> execute lavanya_service.tests.role_browser_uat_permissions.run

All writes happen in the current transaction and are rolled back by ``run``.
"""

import frappe


INTAKE_FIELD = "address"
FOLLOW_UP_FIELD = "work_narration"
SERVICE_FIELD = "brand_ticket_number"
CLOSURE_FIELD = "closure_type"

REQUIRED_TEMPLATE_FIELDS = {
	"manufacturer_registration_required",
	"manufacturer_registered",
	"brand_ticket_number",
	"registration_date",
	"registration_pending_reason",
	"brand_registration_recommended",
	"brand_registration_override_reason",
	"brand_registration_recommended_at",
	"service_center",
	"local_technician",
	"is_repeated_complaint",
	"previous_ticket_link",
	"pending_reason",
	"next_follow_up_date",
	"service_product_receipt",
	"work_narration",
	"closure_type",
	"customer_confirmation_received",
	"closed_by",
	"closure_date",
}

TEST_USERS = {
	"manager": "uat.manager@lavanya.local",
	"agent": "uat.agent@lavanya.local",
	"front_desk": "uat.frontdesk@lavanya.local",
	"coordinator": "uat.coordinator@lavanya.local",
	"viewer": "uat.viewer@lavanya.local",
}


def _record(results, name, passed, detail=""):
	results[name] = {"passed": bool(passed), "detail": detail}
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {name}" + (f" | {detail}" if detail else ""))


def _make_ticket():
	ticket = frappe.new_doc("HD Ticket")
	ticket.subject = "UAT Regression Role Browser Ticket"
	ticket.description = "Created by role_browser_uat_permissions, rolled back"
	ticket.ticket_type = "Customer Complaint - Site"
	ticket.priority = "Medium"
	ticket.customer_name = "UAT Regression Customer"
	ticket.phone_1 = "9876543210"
	ticket.product_type = "Mixer"
	ticket.brand = "Preethi"
	ticket.insert(ignore_permissions=True)
	return ticket.name


def _attempt_save(user, ticket_name, updates):
	frappe.set_user(user)
	try:
		doc = frappe.get_doc("HD Ticket", ticket_name)
		for fieldname, value in updates.items():
			doc.set(fieldname, value)
		doc.save()
		return True, ""
	except Exception as exc:
		return False, str(exc)[:300]
	finally:
		frappe.set_user("Administrator")


def _template_fields():
	return {
		row.fieldname
		for row in frappe.get_all(
			"HD Ticket Template Field",
			filters={"parent": "Default"},
			fields=["fieldname"],
		)
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
	print("OVERALL:", "PASS" if not failed else "FAIL")
	return {"total": len(results), "failed": len(failed), "results": results}


def _run(results):
	users = TEST_USERS
	missing_users = sorted([user for user in users.values() if not frappe.db.exists("User", user)])
	_record(results, "pilot_users_exist", not missing_users, f"missing={missing_users}")
	if missing_users:
		return

	ticket_name = _make_ticket()

	missing_template_fields = sorted(REQUIRED_TEMPLATE_FIELDS - _template_fields())
	_record(
		results,
		"template_includes_service_and_closure_fields",
		not missing_template_fields,
		f"missing={missing_template_fields}",
	)

	checks = [
		(
			"manager_closure_edit",
			users["manager"],
			{CLOSURE_FIELD: "Closed After Manager Approval"},
			True,
		),
		(
			"coordinator_service_edit",
			users["coordinator"],
			{SERVICE_FIELD: "UAT-REGRESSION-001"},
			True,
		),
		(
			"coordinator_closure_edit",
			users["coordinator"],
			{CLOSURE_FIELD: "Closed After Manager Approval"},
			True,
		),
		(
			"agent_follow_up_edit",
			users["agent"],
			{FOLLOW_UP_FIELD: "UAT regression agent follow-up"},
			True,
		),
		(
			"agent_closure_block",
			users["agent"],
			{CLOSURE_FIELD: "Customer Cancelled"},
			False,
		),
		(
			"front_desk_intake_edit",
			users["front_desk"],
			{INTAKE_FIELD: "UAT regression address"},
			True,
		),
		(
			"front_desk_closure_block",
			users["front_desk"],
			{CLOSURE_FIELD: "Duplicate Ticket"},
			False,
		),
		(
			"viewer_write_block",
			users["viewer"],
			{INTAKE_FIELD: "UAT viewer address"},
			False,
		),
	]

	for name, user, updates, expected_ok in checks:
		ok, error = _attempt_save(user, ticket_name, updates)
		_record(
			results,
			name,
			ok == expected_ok,
			f"expected_ok={expected_ok}, actual_ok={ok}, error={error}",
		)
