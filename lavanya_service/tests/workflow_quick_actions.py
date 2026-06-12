"""Rollback-safe tests for Phase 1N-6B quick workflow actions.

Run with:
    bench --site <site> execute lavanya_service.tests.workflow_quick_actions.run

Every record is created inside the current transaction and rolled back by
``run`` so the database is left untouched.
"""

import frappe
from frappe.utils import add_days, today


RESULTS = []

FORBIDDEN_SIDE_EFFECT_DOCTYPES = [
	"HD Notification",
	"Email Queue",
	"Notification Log",
	"Communication",
	"ToDo",
	"Comment",
]

ROLLBACK_DOCTYPES = [
	"HD Ticket",
	"Service Product Receipt",
	"User",
	"Has Role",
	"HD Agent",
] + FORBIDDEN_SIDE_EFFECT_DOCTYPES

USERS = {}


def _record(test_id, description, passed, detail=""):
	RESULTS.append((test_id, description, bool(passed), detail))
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {test_id} - {description}" + (f" | {detail}" if detail else ""))


def _count(doctype):
	return frappe.db.count(doctype) if frappe.db.exists("DocType", doctype) else 0


def _make_user(key, role, agent=True):
	email = f"qa-{key}@example.com"
	if frappe.db.exists("User", email):
		return email
	user = frappe.new_doc("User")
	user.email = email
	user.first_name = f"QA {key.title()}"
	user.enabled = 1
	user.user_type = "System User"
	user.append("roles", {"role": role})
	# Helpdesk record-level permission requires the actor to be an agent
	# (or ticket owner). Grant the standard Agent role so ticket-level
	# has_permission passes; quick-action authorization is still governed by
	# the Lavanya role gate, not by the Agent role.
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


def _insert_ticket(subject, ticket_type="Customer Complaint - Site", status="New", **overrides):
	doc = frappe.new_doc("HD Ticket")
	doc.subject = subject
	doc.raised_by = overrides.pop("raised_by", "qa-customer@example.com")
	doc.status = status
	doc.ticket_type = ticket_type
	doc.priority = overrides.pop("priority", "Medium")
	doc.complaint_source = overrides.pop("complaint_source", "Phone Call")
	doc.customer_name = overrides.pop("customer_name", "QA Customer")
	doc.phone_1 = overrides.pop("phone_1", "9876500000")
	doc.product_type = overrides.pop("product_type", "AC")
	doc.brand = overrides.pop("brand", "LG")
	doc.purchased_from_lavanya = overrides.pop("purchased_from_lavanya", "Unknown")
	doc.warranty_status = overrides.pop("warranty_status", "Unknown")
	if ticket_type in {"Customer Product at Store", "Replacement / DOA"}:
		doc.serial_no = overrides.pop("serial_no", "QA-SERIAL-001")
	doc.update(overrides)
	doc.insert(ignore_permissions=True)
	return doc.name


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


def _forbidden_counts():
	return {dt: _count(dt) for dt in FORBIDDEN_SIDE_EFFECT_DOCTYPES}


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
			"QA-020",
			"automated test records roll back cleanly",
			all(rollback_ok.values()),
			rollback_ok,
		)
		print("\nTRANSACTION ROLLED BACK - no records persisted")

	failed = [row for row in RESULTS if not row[2]]
	print(f"\nTOTAL: {len(RESULTS)} | PASS: {len(RESULTS) - len(failed)} | FAIL: {len(failed)}")
	if failed:
		print("FAILED TESTS:")
		for test_id, description, _passed, detail in failed:
			print(f"  - {test_id}: {description} | {detail}")
	print("OVERALL:", "PASS" if not failed else "FAIL")
	return {"total": len(RESULTS), "failed": len(failed)}


def _run_all():
	from lavanya_service.api import workflow_actions as wa
	from lavanya_service.api.today_work import get_today_work

	_ensure_users()

	# QA-001 Coordinator can register brand complaint
	t = _insert_ticket("QA Brand Register")
	res = _call_as(
		USERS["coordinator"],
		wa.register_brand_complaint,
		ticket_name=t,
		brand_ticket_number="BR-1001",
		registration_date=today(),
		next_follow_up_date=add_days(today(), 3),
	)
	doc = frappe.get_doc("HD Ticket", t)
	_record(
		"QA-001",
		"Service Coordinator can register brand complaint",
		res.get("ok")
		and doc.status == "Brand Registered"
		and doc.manufacturer_registered == "Yes"
		and doc.brand_ticket_number == "BR-1001",
		f"status={doc.status}",
	)

	# QA-002 Register brand complaint requires brand_ticket_number
	t = _insert_ticket("QA Brand Register Missing")
	blocked, err = _blocks(
		USERS["coordinator"],
		wa.register_brand_complaint,
		ticket_name=t,
		brand_ticket_number="",
		registration_date=today(),
		next_follow_up_date=add_days(today(), 3),
	)
	_record("QA-002", "register brand complaint requires brand_ticket_number", blocked, err)

	# QA-003 Need Invoice sets Waiting on Customer + Invoice Pending + follow-up date
	t = _insert_ticket("QA Need Invoice")
	follow = add_days(today(), 2)
	_call_as(
		USERS["coordinator"],
		wa.need_invoice_from_customer,
		ticket_name=t,
		next_follow_up_date=follow,
	)
	doc = frappe.get_doc("HD Ticket", t)
	_record(
		"QA-003",
		"Need Invoice sets Waiting on Customer + Invoice Pending + follow-up date",
		doc.status == "Waiting on Customer"
		and doc.pending_reason == "Invoice Pending"
		and str(doc.next_follow_up_date) == str(follow),
		f"status={doc.status}, pending={doc.pending_reason}",
	)

	# QA-004 Need Invoice requires next_follow_up_date
	t = _insert_ticket("QA Need Invoice Missing")
	blocked, err = _blocks(
		USERS["coordinator"],
		wa.need_invoice_from_customer,
		ticket_name=t,
		next_follow_up_date="",
	)
	_record("QA-004", "Need Invoice requires next_follow_up_date", blocked, err)

	# QA-005 Follow Up with Part pending -> Waiting on Part / Approval
	t = _insert_ticket("QA Follow Up Part")
	_call_as(
		USERS["coordinator"],
		wa.follow_up_service_center,
		ticket_name=t,
		follow_up_result="Part pending",
		next_follow_up_date=add_days(today(), 4),
	)
	doc = frappe.get_doc("HD Ticket", t)
	_record(
		"QA-005",
		"Follow Up Service Center with Part pending moves to Waiting on Part / Approval",
		doc.status == "Waiting on Part / Approval" and doc.pending_reason == "Part Pending",
		f"status={doc.status}, pending={doc.pending_reason}",
	)

	# QA-006 Waiting for Part requires pending_reason and follow-up date
	t = _insert_ticket("QA Waiting Part Missing")
	blocked, err = _blocks(
		USERS["coordinator"],
		wa.waiting_for_part,
		ticket_name=t,
		pending_reason="",
		next_follow_up_date="",
	)
	_record("QA-006", "Waiting for Part requires pending_reason and follow-up date", blocked, err)

	# QA-007 Product Ready sets Ready for Pickup
	t = _insert_ticket("QA Product Ready")
	_call_as(USERS["coordinator"], wa.mark_product_ready, ticket_name=t)
	doc = frappe.get_doc("HD Ticket", t)
	_record(
		"QA-007",
		"Product Ready sets Ready for Pickup",
		doc.status == "Ready for Pickup" and doc.pending_reason == "Customer Pickup Pending",
		f"status={doc.status}",
	)

	# QA-008 Customer Confirmed closes ticket with required closure fields
	t = _insert_ticket("QA Customer Confirmed")
	_call_as(
		USERS["coordinator"],
		wa.customer_confirmed,
		ticket_name=t,
		work_narration="Repaired and returned to customer",
		closure_type="Customer Collected Product",
	)
	doc = frappe.get_doc("HD Ticket", t)
	_record(
		"QA-008",
		"Customer Confirmed closes ticket with required closure fields",
		doc.status == "Closed"
		and doc.customer_confirmation_received == "Yes"
		and doc.closure_type == "Customer Collected Product"
		and doc.closed_by == USERS["coordinator"],
		f"status={doc.status}, closed_by={doc.closed_by}",
	)

	# QA-009 Close Ticket blocks if customer_confirmation_received is not Yes
	t = _insert_ticket("QA Close No Confirm")
	blocked, err = _blocks(
		USERS["manager"],
		wa.close_ticket,
		ticket_name=t,
		work_narration="Closing",
		closure_type="Closed After Manager Approval",
		customer_confirmation_received="No",
	)
	_record("QA-009", "Close Ticket blocks if customer_confirmation_received is not Yes", blocked, err)

	# QA-010 Front Desk cannot register brand complaint
	t = _insert_ticket("QA FrontDesk Brand")
	blocked, err = _blocks(
		USERS["front_desk"],
		wa.register_brand_complaint,
		ticket_name=t,
		brand_ticket_number="BR-2002",
		registration_date=today(),
		next_follow_up_date=add_days(today(), 3),
	)
	_record("QA-010", "Front Desk cannot register brand complaint", blocked, err)

	# QA-011 Front Desk cannot close ticket
	t = _insert_ticket("QA FrontDesk Close")
	blocked, err = _blocks(
		USERS["front_desk"],
		wa.close_ticket,
		ticket_name=t,
		work_narration="Closing",
		closure_type="Closed After Manager Approval",
		customer_confirmation_received="Yes",
	)
	_record("QA-011", "Front Desk cannot close ticket", blocked, err)

	# QA-012 Front Desk can create product receipt for Customer Product at Store
	store_ticket = _insert_ticket(
		"QA Store Product", ticket_type="Customer Product at Store", serial_no="QA-STORE-1"
	)
	res = _call_as(
		USERS["front_desk"],
		wa.create_product_receipt,
		ticket_name=store_ticket,
		accessories_received="Remote",
		physical_condition="Minor scratch",
	)
	linked = frappe.db.get_value("HD Ticket", store_ticket, "service_product_receipt")
	_record(
		"QA-012",
		"Front Desk can create product receipt for Customer Product at Store",
		res.get("ok")
		and res.get("receipt")
		and linked == res.get("receipt")
		and frappe.db.exists("Service Product Receipt", res.get("receipt")),
		f"receipt={res.get('receipt')}, linked={linked}",
	)

	# QA-013 Helpdesk Agent can follow up service center
	t = _insert_ticket("QA Agent Follow Up")
	res = _call_as(
		USERS["agent"],
		wa.follow_up_service_center,
		ticket_name=t,
		follow_up_result="Service center contacted",
		next_follow_up_date=add_days(today(), 1),
	)
	doc = frappe.get_doc("HD Ticket", t)
	_record(
		"QA-013",
		"Helpdesk Agent can follow up service center",
		res.get("ok") and doc.status == "In Progress",
		f"status={doc.status}",
	)

	# QA-014 Helpdesk Agent cannot close ticket
	t = _insert_ticket("QA Agent Close")
	blocked, err = _blocks(
		USERS["agent"],
		wa.close_ticket,
		ticket_name=t,
		work_narration="Closing",
		closure_type="Closed After Manager Approval",
		customer_confirmation_received="Yes",
	)
	_record("QA-014", "Helpdesk Agent cannot close ticket", blocked, err)

	# QA-015 Viewer cannot run any write action
	t = _insert_ticket("QA Viewer Block")
	blocked, err = _blocks(
		USERS["viewer"],
		wa.need_invoice_from_customer,
		ticket_name=t,
		next_follow_up_date=add_days(today(), 2),
	)
	_record("QA-015", "Viewer cannot run any write action", blocked, err)

	# QA-016 Create Product Receipt blocks duplicate receipt
	blocked, err = _blocks(
		USERS["front_desk"],
		wa.create_product_receipt,
		ticket_name=store_ticket,
	)
	_record("QA-016", "Create Product Receipt blocks duplicate receipt", blocked, err)

	# QA-017 Create Product Receipt blocks wrong ticket type
	wrong = _insert_ticket("QA Wrong Type Receipt")  # Customer Complaint - Site
	blocked, err = _blocks(
		USERS["front_desk"],
		wa.create_product_receipt,
		ticket_name=wrong,
	)
	_record("QA-017", "Create Product Receipt blocks wrong ticket type", blocked, err)

	# QA-018 Today's Work reflects action result after update
	t = _insert_ticket("QA Today Work Reflect")
	_call_as(
		USERS["coordinator"],
		wa.need_invoice_from_customer,
		ticket_name=t,
		next_follow_up_date=today(),
	)
	data = get_today_work(limit=200)
	waiting = set()
	for group in data.get("groups", []):
		if group.get("key") == "waiting_on_customer":
			waiting = {row.get("name") for row in group.get("tickets", [])}
	_record(
		"QA-018",
		"Today's Work reflects ticket state after action",
		t in waiting,
		f"in_waiting_on_customer={t in waiting}",
	)

	# QA-019 No forbidden side effects (except allowed Service Product Receipt)
	t = _insert_ticket("QA Side Effects")
	before = _forbidden_counts()
	_call_as(
		USERS["coordinator"],
		wa.need_invoice_from_customer,
		ticket_name=t,
		next_follow_up_date=today(),
	)
	after = _forbidden_counts()
	receipt_ticket = _insert_ticket(
		"QA Side Effects Receipt", ticket_type="Customer Product at Store", serial_no="QA-SE-1"
	)
	receipt_before = _count("Service Product Receipt")
	before_receipt_forbidden = _forbidden_counts()
	_call_as(USERS["front_desk"], wa.create_product_receipt, ticket_name=receipt_ticket)
	after_receipt_forbidden = _forbidden_counts()
	receipt_after = _count("Service Product Receipt")
	_record(
		"QA-019",
		"no forbidden side effects; only receipt action creates a document",
		before == after
		and before_receipt_forbidden == after_receipt_forbidden
		and receipt_after == receipt_before + 1,
		f"need_invoice_delta={ {k: after[k]-before[k] for k in before} }, "
		f"receipt_delta={receipt_after - receipt_before}",
	)
