"""Rollback-safe tests for Phase 1N-6A derived Today Work API.

Run with:
    bench --site <site> execute lavanya_service.tests.today_work.run
"""

import frappe
from frappe.utils import add_days, today


RESULTS = []

GROUP_KEYS = [
	"overdue_follow_up",
	"due_today",
	"registration_recommended",
	"registration_pending",
	"waiting_on_customer",
	"waiting_on_part",
	"ready_for_pickup",
	"product_receipt_missing",
	"closure_pending",
	"new_complaints",
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
	"agreement_status",
	"response_by",
	"resolution_by",
	"first_responded_on",
	"service_flow_type",
	"current_service_stage",
	"next_action",
	"next_action_owner",
	"next_action_role",
	"stage_due_at",
	"pre_overdue_alert_at",
	"overdue_status",
	"escalation_level",
	"customer_informed",
	"customer_promised_update_at",
	"customer_promise_status",
	# Reminder-engine resolver output (Step 3) — additive, non-sensitive.
	"reminder_rule_applied",
	"computed_next_followup_at",
	"computed_due_soon_at",
	"computed_stage_due_at",
	"computed_escalation_level",
	"customer_update_due",
}

FOLLOW_UP_STATUSES = {
	"Registration Pending",
	"Brand Registered",
	"In Progress",
	"Waiting on Customer",
	"Waiting on Part / Approval",
	"Ready for Pickup",
}

SIDE_EFFECT_DOCTYPES = [
	"HD Notification",
	"Email Queue",
	"Notification Log",
	"Communication",
	"ToDo",
	"Comment",
	"Service Product Receipt",
	"Lavanya Customer Profile",
]

ROLLBACK_DOCTYPES = [
	"HD Ticket",
	"Free Service Rule",
	"User",
	"Has Role",
] + SIDE_EFFECT_DOCTYPES


def _record(test_id, description, passed, detail=""):
	RESULTS.append((test_id, description, bool(passed), detail))
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {test_id} - {description}" + (f" | {detail}" if detail else ""))


def _assert(test_id, description, condition, detail=""):
	_record(test_id, description, bool(condition), detail)


def _count(doctype):
	return frappe.db.count(doctype) if frappe.db.exists("DocType", doctype) else 0


def _make_user(role):
	email = "today-work-" + role.lower().replace(" ", "-") + "@example.com"
	user = frappe.new_doc("User")
	user.email = email
	user.first_name = "Today Work"
	user.enabled = 1
	user.user_type = "System User"
	user.append("roles", {"role": role})
	user.insert(ignore_permissions=True)
	return email


def _base_ticket(subject, status="New", ticket_type="Customer Complaint - Site", **overrides):
	doc = frappe.new_doc("HD Ticket")
	doc.subject = subject
	doc.raised_by = overrides.pop(
		"raised_by",
		"today-work-" + "".join(ch for ch in subject.lower() if ch.isalnum()) + "@example.com",
	)
	doc.status = status
	doc.ticket_type = ticket_type
	doc.priority = overrides.pop("priority", "Medium")
	doc.complaint_source = overrides.pop("complaint_source", "Phone Call")
	doc.customer_name = overrides.pop("customer_name", "Today Work Customer")
	doc.phone_1 = overrides.pop("phone_1", "0495-2222222 ext 4")
	doc.product_type = overrides.pop("product_type", "AC")
	doc.brand = overrides.pop("brand", "LG")
	doc.purchased_from_lavanya = overrides.pop("purchased_from_lavanya", "Unknown")
	doc.warranty_status = overrides.pop("warranty_status", "Unknown")

	if ticket_type in {"Customer Product at Store", "Replacement / DOA"}:
		doc.serial_no = overrides.pop("serial_no", "TW-ROLLBACK-001")

	if status in FOLLOW_UP_STATUSES:
		doc.pending_reason = overrides.pop("pending_reason", "Service Follow-up Required")
		doc.next_follow_up_date = overrides.pop("next_follow_up_date", today())

	if status == "Closed":
		doc.closure_type = overrides.pop("closure_type", "Closed After Manager Approval")
		doc.work_narration = overrides.pop("work_narration", "Rollback Today Work closure")
		doc.customer_confirmation_received = overrides.pop("customer_confirmation_received", "Yes")

	doc.update(overrides)
	return doc


def _insert_ticket(subject, status="New", ticket_type="Customer Complaint - Site", **overrides):
	doc = _base_ticket(subject, status=status, ticket_type=ticket_type, **overrides)
	doc.insert(ignore_permissions=True)
	doc = frappe.get_doc("HD Ticket", doc.name)
	if doc.status != status:
		doc.status = status
		doc.save(ignore_permissions=True)
		doc.reload()
	return doc


def _ensure_brand_backed_rule():
	doc = frappe.new_doc("Free Service Rule")
	doc.brand = "LG"
	doc.product_type = "AC"
	doc.service_type = "AC Free Service"
	doc.due_after_days = 180
	doc.reminder_before_days = 7
	doc.active = 1
	doc.brand_backed = 1
	doc.insert(ignore_permissions=True)
	return doc.name


def _group(data, key):
	for group in data.get("groups", []):
		if group.get("key") == key:
			return group
	return None


def _names(data, key):
	group = _group(data, key)
	if not group:
		return set()
	return {ticket.get("name") for ticket in group.get("tickets", [])}


def _group_keys(data):
	return [group.get("key") for group in data.get("groups", [])]


def _side_effect_counts():
	return {doctype: _count(doctype) for doctype in SIDE_EFFECT_DOCTYPES}


def _call_as(user, fn, *args, **kwargs):
	frappe.set_user(user)
	try:
		return fn(*args, **kwargs)
	finally:
		frappe.set_user("Administrator")


def run():
	RESULTS.clear()
	baseline = {doctype: _count(doctype) for doctype in ROLLBACK_DOCTYPES}

	try:
		from lavanya_service.api.today_work import get_today_work

		_run_all(get_today_work, baseline)
	finally:
		frappe.set_user("Administrator")
		frappe.db.rollback()

		rollback_ok = {doctype: _count(doctype) == baseline[doctype] for doctype in ROLLBACK_DOCTYPES}
		_assert(
			"TW-017",
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
	print("BASELINE:", baseline)
	print("OVERALL:", "PASS" if not failed else "FAIL")
	return {"total": len(RESULTS), "failed": len(failed)}


def _run_all(get_today_work, baseline):
	overdue = _insert_ticket(
		"TW Overdue Follow-up",
		status="In Progress",
		pending_reason="Service Follow-up Required",
		next_follow_up_date=add_days(today(), -1),
	)
	due_today = _insert_ticket(
		"TW Due Today",
		status="In Progress",
		pending_reason="Service Follow-up Required",
		next_follow_up_date=today(),
	)
	closed = _insert_ticket("TW Closed", status="Closed")
	cancelled = _insert_ticket("TW Cancelled", status="Cancelled")
	resolved_incomplete = _insert_ticket(
		"TW Resolved Incomplete",
		status="Resolved",
		closure_type="",
		customer_confirmation_received="No",
	)
	resolved_complete = _insert_ticket(
		"TW Resolved Complete",
		status="Resolved",
		closure_type="Closed After Manager Approval",
		customer_confirmation_received="Yes",
	)
	registration_recommended = _insert_ticket(
		"TW Registration Recommended",
		ticket_type="Customer Complaint - Site",
		warranty_status="In Warranty",
	)
	registration_override = _insert_ticket(
		"TW Registration Override",
		ticket_type="Customer Complaint - Site",
		warranty_status="In Warranty",
		brand_registration_override_reason="Customer wants local service",
	)
	stock_complaint = _insert_ticket(
		"TW Stock Complaint",
		ticket_type="Stock Complaint",
		warranty_status="In Warranty",
	)
	_ensure_brand_backed_rule()
	free_service = _insert_ticket(
		"TW Free Service Brand Backed",
		ticket_type="Free Service",
		warranty_status="In Warranty",
	)
	product_missing = _insert_ticket(
		"TW Product Receipt Missing",
		ticket_type="Customer Product at Store",
		warranty_status="Unknown",
	)
	waiting_customer = _insert_ticket(
		"TW Waiting Customer",
		status="Waiting on Customer",
		pending_reason="Invoice Pending",
		next_follow_up_date=today(),
	)
	waiting_part = _insert_ticket(
		"TW Waiting Part",
		status="Waiting on Part / Approval",
		pending_reason="Part Pending",
		next_follow_up_date=today(),
	)
	ready_pickup = _insert_ticket(
		"TW Ready Pickup",
		status="Ready for Pickup",
		pending_reason="Customer Pickup Pending",
		next_follow_up_date=today(),
	)
	new_ticket = _insert_ticket("TW New Complaint", status="New")
	# Helpdesk's native "Open" status (assigned by the standard new-ticket form)
	# is not part of the Lavanya status set; an Open ticket must still surface on
	# Today's Work instead of vanishing. Regression for the "new ticket not
	# showing after refresh" report.
	open_ticket = _insert_ticket("TW Helpdesk Open Status", status="Open")
	# "Replied" (Helpdesk-native, status_category "Paused") must also stay visible.
	replied_ticket = _insert_ticket("TW Helpdesk Replied Status", status="Replied")

	before_api_counts = _side_effect_counts()
	data = get_today_work(limit=200)
	after_api_counts = _side_effect_counts()

	_assert("TW-001", "overdue follow-up appears in overdue group", overdue.name in _names(data, "overdue_follow_up"))
	_assert("TW-002", "follow-up due today appears in due_today group", due_today.name in _names(data, "due_today"))
	_assert(
		"TW-003",
		"closed ticket does not appear",
		not any(closed.name in _names(data, key) for key in GROUP_KEYS),
	)
	_assert(
		"TW-004",
		"cancelled ticket does not appear",
		not any(cancelled.name in _names(data, key) for key in GROUP_KEYS),
	)
	_assert(
		"TW-005",
		"resolved ticket with incomplete closure appears in closure_pending",
		resolved_incomplete.name in _names(data, "closure_pending"),
	)
	_assert(
		"TW-006",
		"resolved ticket with completed closure does not appear",
		resolved_complete.name not in _names(data, "closure_pending"),
	)
	_assert(
		"TW-007",
		"in-warranty complaint without brand registration appears in registration_recommended",
		registration_recommended.name in _names(data, "registration_recommended"),
	)
	_assert(
		"TW-008",
		"warranty override reason removes ticket from registration_recommended",
		registration_override.name not in _names(data, "registration_recommended"),
	)
	_assert(
		"TW-009",
		"stock complaint does not appear in registration_recommended",
		stock_complaint.name not in _names(data, "registration_recommended"),
	)
	_assert(
		"TW-009b",
		"free service brand-backed rule appears in registration_recommended",
		free_service.name in _names(data, "registration_recommended"),
	)
	_assert(
		"TW-010",
		"customer product at store without receipt appears in product_receipt_missing",
		product_missing.name in _names(data, "product_receipt_missing"),
	)
	_assert(
		"TW-011",
		"waiting on customer appears in waiting_on_customer",
		waiting_customer.name in _names(data, "waiting_on_customer"),
	)
	_assert(
		"TW-012",
		"waiting on part appears in waiting_on_part",
		waiting_part.name in _names(data, "waiting_on_part"),
	)
	_assert(
		"TW-013",
		"ready for pickup appears in ready_for_pickup",
		ready_pickup.name in _names(data, "ready_for_pickup"),
	)
	_assert("TW-014", "new ticket appears in new_complaints", new_ticket.name in _names(data, "new_complaints"))
	_assert(
		"TW-014b",
		"active ticket with Helpdesk-native 'Open' status surfaces in new_complaints (was invisible on Today's Work)",
		open_ticket.name in _names(data, "new_complaints"),
	)
	_assert(
		"TW-014c",
		"active ticket with Helpdesk-native 'Replied' status (category Paused) stays visible",
		any(replied_ticket.name in _names(data, key) for key in GROUP_KEYS),
	)
	_assert("TW-015", "API returns expected group order", _group_keys(data) == GROUP_KEYS, _group_keys(data))

	all_ticket_keys_safe = all(
		set(ticket).issubset(SAFE_TICKET_FIELDS)
		for group in data.get("groups", [])
		for ticket in group.get("tickets", [])
	)
	_assert("TW-015b", "ticket rows expose only safe operator fields", all_ticket_keys_safe)

	front_desk = _make_user("Lavanya Front Desk")
	front_desk_data = _call_as(front_desk, get_today_work, limit=200)
	_assert(
		"TW-015c",
		"front desk receives only front-desk work groups",
		_group_keys(front_desk_data) == ["ready_for_pickup", "product_receipt_missing", "new_complaints"],
		_group_keys(front_desk_data),
	)

	viewer = _make_user("Lavanya Viewer")
	viewer_data = _call_as(viewer, get_today_work, limit=200)
	viewer_rows_safe = all(
		set(ticket).issubset(SAFE_TICKET_FIELDS)
		for group in viewer_data.get("groups", [])
		for ticket in group.get("tickets", [])
	)
	_assert("TW-015d", "viewer receives read-only safe rows", viewer_rows_safe)

	_assert(
		"TW-016",
		"API creates no forbidden side effects",
		before_api_counts == after_api_counts,
		{"before": before_api_counts, "after": after_api_counts},
	)

	_assert(
		"TW-016b",
		"baseline forbidden side-effect counts are unchanged during API calls",
		all(after_api_counts[doctype] >= baseline[doctype] for doctype in SIDE_EFFECT_DOCTYPES),
		after_api_counts,
	)
