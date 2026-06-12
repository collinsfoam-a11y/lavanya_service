"""Rollback-safe tests for Phase 1N-4 warranty brand-registration recommendation.

Run with:
    bench --site <site> execute lavanya_service.tests.warranty_recommendation.run
"""

import frappe
from frappe.utils import today


RESULTS = []

RECOMMENDED_TYPES = [
	"Customer Complaint - Site",
	"Customer Product at Store",
	"Installation / Demo",
	"Replacement / DOA",
]
EXEMPT_TYPES = [
	"Stock Complaint",
	"Out of Warranty Local Service",
]
EXPECTED_HD_TICKET_FIELDS = {
	"brand_registration_recommended",
	"brand_registration_override_reason",
	"brand_registration_recommended_at",
}
EXPECTED_FREE_SERVICE_RULE_FIELDS = {
	"brand_backed",
}
SIDE_EFFECT_DOCTYPES = [
	"Email Queue",
	"Notification Log",
	"Communication",
	"ToDo",
	"Comment",
]


def _record(test_id, description, passed, detail=""):
	RESULTS.append((test_id, description, bool(passed), detail))
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {test_id} - {description}" + (f" | {detail}" if detail else ""))


def _assert(test_id, description, condition, detail=""):
	_record(test_id, description, bool(condition), detail)


def _count(doctype):
	return frappe.db.count(doctype) if frappe.db.exists("DocType", doctype) else 0


def _make_user(role):
	email = "warranty-recommendation-" + role.lower().replace(" ", "-") + "@example.com"
	user = frappe.new_doc("User")
	user.email = email
	user.first_name = "Warranty Recommendation"
	user.enabled = 1
	user.user_type = "System User"
	user.append("roles", {"role": role})
	user.insert(ignore_permissions=True)
	return email


def _base_ticket(ticket_type, **overrides):
	doc = frappe.new_doc("HD Ticket")
	slug = ticket_type.lower().replace(" ", "-").replace("/", "-")
	doc.subject = overrides.pop("subject", f"Warranty recommendation {ticket_type}")
	doc.raised_by = overrides.pop("raised_by", f"warranty-{slug}@example.com")
	doc.ticket_type = ticket_type
	doc.priority = overrides.pop("priority", "Medium")
	doc.complaint_source = overrides.pop("complaint_source", "Phone Call")
	doc.customer_name = overrides.pop("customer_name", "Warranty Recommendation Tester")
	doc.phone_1 = overrides.pop("phone_1", "0495-2222222 ext 4")
	doc.product_type = overrides.pop("product_type", "AC")
	doc.brand = overrides.pop("brand", "LG")
	doc.purchased_from_lavanya = overrides.pop("purchased_from_lavanya", "Unknown")
	doc.warranty_status = overrides.pop("warranty_status", "In Warranty")
	if ticket_type in {"Customer Product at Store", "Replacement / DOA"}:
		doc.serial_no = overrides.pop("serial_no", "WR-ROLLBACK-001")
	doc.update(overrides)
	return doc


def _insert_ticket(ticket_type, **overrides):
	doc = _base_ticket(ticket_type, **overrides)
	doc.insert(ignore_permissions=True)
	return frappe.get_doc("HD Ticket", doc.name)


def _insert_ticket_as_user(user, ticket_type, **overrides):
	frappe.set_user(user)
	try:
		doc = _base_ticket(ticket_type, raised_by=user, **overrides)
		doc.insert()
		return frappe.get_doc("HD Ticket", doc.name)
	finally:
		frappe.set_user("Administrator")


def _expect_block(test_id, description, fn, expected_text):
	try:
		fn()
		_record(test_id, description, False, "operation unexpectedly succeeded")
	except Exception as exc:
		message = str(exc)
		_record(test_id, description, expected_text.lower() in message.lower(), message[:300])


def _attempt_user_update(user, ticket_name, updates):
	frappe.set_user(user)
	try:
		doc = frappe.get_doc("HD Ticket", ticket_name)
		doc.update(updates)
		doc.save()
		return True, ""
	except Exception as exc:
		return False, str(exc)[:300]
	finally:
		frappe.set_user("Administrator")


def _ensure_brand_backed_rule(brand_backed):
	doc = frappe.new_doc("Free Service Rule")
	doc.brand = "LG"
	doc.product_type = "AC"
	doc.service_type = "AC Free Service"
	doc.due_after_days = 180
	doc.reminder_before_days = 7
	doc.active = 1
	doc.brand_backed = 1 if brand_backed else 0
	doc.insert(ignore_permissions=True)
	return doc.name


def _field_exists(doctype, fieldname):
	return bool(frappe.get_meta(doctype).get_field(fieldname))


def run():
	RESULTS.clear()
	baseline = {
		"HD Ticket": frappe.db.count("HD Ticket"),
		"Free Service Rule": _count("Free Service Rule"),
		"User": frappe.db.count("User"),
		"Has Role": _count("Has Role"),
	}
	for doctype in SIDE_EFFECT_DOCTYPES:
		baseline[doctype] = _count(doctype)

	try:
		_run_all(baseline)
	finally:
		frappe.set_user("Administrator")
		frappe.db.rollback()

		cleanup_ok = {
			"HD Ticket": frappe.db.count("HD Ticket") == baseline["HD Ticket"],
			"Free Service Rule": _count("Free Service Rule") == baseline["Free Service Rule"],
			"User": frappe.db.count("User") == baseline["User"],
			"Has Role": _count("Has Role") == baseline["Has Role"],
		}
		for doctype in SIDE_EFFECT_DOCTYPES:
			cleanup_ok[doctype] = _count(doctype) == baseline[doctype]

		_assert(
			"WR-015",
			"test records and side effects roll back cleanly",
			all(cleanup_ok.values()),
			cleanup_ok,
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


def _run_all(baseline):
	missing_ticket_fields = sorted(
		field for field in EXPECTED_HD_TICKET_FIELDS if not _field_exists("HD Ticket", field)
	)
	missing_rule_fields = sorted(
		field for field in EXPECTED_FREE_SERVICE_RULE_FIELDS if not _field_exists("Free Service Rule", field)
	)
	_assert(
		"WR-000",
		"required recommendation fields exist",
		not missing_ticket_fields and not missing_rule_fields,
		{"HD Ticket": missing_ticket_fields, "Free Service Rule": missing_rule_fields},
	)
	if missing_ticket_fields or missing_rule_fields:
		return

	for idx, ticket_type in enumerate(RECOMMENDED_TYPES, start=1):
		ticket = _insert_ticket(ticket_type)
		_assert(
			f"WR-00{idx}",
			f"In Warranty + {ticket_type} recommends brand registration",
			int(ticket.brand_registration_recommended or 0) == 1
			and ticket.pending_reason == "Brand Registration Recommended"
			and str(ticket.next_follow_up_date) == str(today()),
			ticket.as_dict(),
		)

	for offset, ticket_type in enumerate(EXEMPT_TYPES, start=5):
		ticket = _insert_ticket(ticket_type)
		_assert(
			f"WR-00{offset}",
			f"{ticket_type} does not recommend by default",
			int(ticket.brand_registration_recommended or 0) == 0
			and not ticket.pending_reason
			and not ticket.next_follow_up_date,
			ticket.as_dict(),
		)

	non_brand_rule = _ensure_brand_backed_rule(brand_backed=False)
	ticket = _insert_ticket("Free Service")
	_assert(
		"WR-007a",
		"Free Service without brand-backed rule does not recommend",
		int(ticket.brand_registration_recommended or 0) == 0,
		{"rule": non_brand_rule, "ticket": ticket.as_dict()},
	)

	frappe.delete_doc("Free Service Rule", non_brand_rule, ignore_permissions=True, force=True)
	brand_rule = _ensure_brand_backed_rule(brand_backed=True)
	ticket = _insert_ticket("Free Service")
	_assert(
		"WR-007b",
		"Free Service recommends when matching rule is brand-backed",
		int(ticket.brand_registration_recommended or 0) == 1
		and ticket.pending_reason == "Brand Registration Recommended",
		{"rule": brand_rule, "ticket": ticket.as_dict()},
	)

	def save_brand_registered_without_details():
		doc = _insert_ticket("Customer Complaint - Site")
		doc.status = "Brand Registered"
		doc.manufacturer_registered = "Yes"
		doc.pending_reason = "Brand Registration Recommended"
		doc.next_follow_up_date = today()
		doc.save(ignore_permissions=True)

	_expect_block(
		"WR-008",
		"Brand Registered with manufacturer_registered Yes requires brand details",
		save_brand_registered_without_details,
		"Brand Registered status requires",
	)

	def save_invoice_pending_without_followup():
		doc = _insert_ticket("Customer Complaint - Site")
		doc.status = "Waiting on Customer"
		doc.pending_reason = "Invoice Pending"
		doc.next_follow_up_date = None
		doc.save(ignore_permissions=True)

	_expect_block(
		"WR-009",
		"Waiting on Customer + Invoice Pending requires next follow-up",
		save_invoice_pending_without_followup,
		"Next Follow-up Date",
	)

	users = {
		"manager": _make_user("Lavanya Manager"),
		"coordinator": _make_user("Lavanya Service Coordinator"),
		"front_desk": _make_user("Lavanya Front Desk"),
		"viewer": _make_user("Lavanya Viewer"),
	}

	for test_id, role_key, label in [
		("WR-010", "coordinator", "Service Coordinator"),
		("WR-011", "manager", "Manager"),
	]:
		ticket = _insert_ticket_as_user(users[role_key], "Customer Complaint - Site")
		ok, error = _attempt_user_update(
			users[role_key],
			ticket.name,
			{
				"manufacturer_registration_required": "No",
				"brand_registration_override_reason": "Customer wants local service",
			},
		)
		_assert(test_id, f"{label} can override with reason", ok, error)

	ticket = _insert_ticket("Customer Complaint - Site")
	ok, error = _attempt_user_update(
		users["front_desk"],
		ticket.name,
		{
			"manufacturer_registration_required": "No",
			"brand_registration_override_reason": "Minor issue handled in showroom",
		},
	)
	_assert("WR-012", "Front Desk cannot edit brand registration / override fields", not ok, error)

	ticket = _insert_ticket("Customer Complaint - Site")
	ok, error = _attempt_user_update(users["viewer"], ticket.name, {"customer_name": "Viewer Edit"})
	_assert("WR-013", "Viewer remains read-only", not ok, error)

	side_effects = {doctype: _count(doctype) - baseline[doctype] for doctype in SIDE_EFFECT_DOCTYPES}
	for allowed_core_doctype in ["Communication", "Comment"]:
		side_effects.pop(allowed_core_doctype, None)
	_assert(
		"WR-014",
		"no custom notification/task/email side effects",
		all(delta == 0 for delta in side_effects.values()),
		side_effects,
	)
