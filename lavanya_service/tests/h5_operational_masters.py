"""Rollback-safe tests for H5 operational masters + service data foundation.

Run with:
    bench --site <site> execute lavanya_service.tests.h5_operational_masters.run
"""

import frappe
from frappe.utils import now_datetime


RESULTS = []


def _record(test_id, description, passed, detail=""):
	RESULTS.append((test_id, description, bool(passed), detail))
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {test_id} - {description}" + (f" | {detail}" if detail else ""))


def _assert(test_id, description, condition, detail=""):
	_record(test_id, description, bool(condition), detail)


def _has_field(doctype, fieldname):
	return bool(frappe.get_meta(doctype).get_field(fieldname))


def _make_user(role):
	email = "h5-" + role.lower().replace(" ", "-") + "@example.com"
	if frappe.db.exists("User", email):
		frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	user = frappe.new_doc("User")
	user.email = email
	user.first_name = "H5 Tester"
	user.enabled = 1
	user.user_type = "System User"
	user.append("roles", {"role": role})
	if role != "Lavanya Viewer":
		user.append("roles", {"role": "Agent"})
	user.insert(ignore_permissions=True)
	return email


def _ticket(phone, serial_no, **overrides):
	doc = frappe.new_doc("HD Ticket")
	doc.subject = overrides.pop("subject", "H5 customer product test")
	doc.description = "Created by h5_operational_masters, rolled back"
	doc.ticket_type = overrides.pop("ticket_type", "Customer Product at Store")
	doc.priority = overrides.pop("priority", "Medium")
	doc.complaint_source = overrides.pop("complaint_source", "Direct Visit")
	doc.customer_name = overrides.pop("customer_name", "H5 Customer")
	doc.phone_1 = phone
	doc.address = overrides.pop("address", "H5 Test Address")
	doc.pincode = overrides.pop("pincode", "673001")
	doc.product_type = overrides.pop("product_type", "Mixer")
	doc.product_category = overrides.pop("product_category", None)
	doc.product_item = overrides.pop("product_item", None)
	doc.brand = overrides.pop("brand", "Preethi")
	doc.model_no = overrides.pop("model_no", "H5-MX-01")
	doc.serial_no = serial_no
	doc.purchase_date = overrides.pop("purchase_date", "2026-01-10")
	doc.warranty_status = overrides.pop("warranty_status", "In Warranty")
	doc.update(overrides)
	return doc


def _insert_service_center(name, brand="Preethi", **overrides):
	if frappe.db.exists("Service Center Master", name):
		frappe.delete_doc("Service Center Master", name, force=True, ignore_permissions=True)
	doc = frappe.new_doc("Service Center Master")
	doc.service_center_name = name
	doc.brand = brand
	doc.phone = overrides.pop("phone", "9999301000")
	doc.coverage_pincodes = overrides.pop("coverage_pincodes", "673001\n673002")
	doc.status = overrides.pop("status", "Active")
	doc.update(overrides)
	doc.insert(ignore_permissions=True)
	return doc.name


def _insert_technician(name, **overrides):
	if frappe.db.exists("Local Technician Master", name):
		frappe.delete_doc("Local Technician Master", name, force=True, ignore_permissions=True)
	doc = frappe.new_doc("Local Technician Master")
	doc.technician_name = name
	doc.phone = overrides.pop("phone", "9999302000")
	doc.skills = overrides.pop("skills", "Mixer, AC")
	doc.active = overrides.pop("active", 1)
	doc.update(overrides)
	doc.insert(ignore_permissions=True)
	return doc.name


def _expect_block(test_id, description, fn, expected_text):
	try:
		fn()
		_record(test_id, description, False, "operation unexpectedly succeeded")
	except Exception as exc:  # noqa: BLE001 - the test asserts the validation block
		message = str(exc)
		_record(test_id, description, expected_text.lower() in message.lower(), message[:220])


def _unique_mobile_and_serial():
	stamp = now_datetime().strftime("%H%M%S%f")
	mobile = "9" + stamp[:9]
	return mobile, "H5-SERIAL-" + stamp


def run():
	RESULTS.clear()
	from lavanya_service.api.operational_masters import (
		create_service_appointment,
		get_customer_product_history,
		get_master_suggestions,
		list_local_technicians,
		list_service_centers,
		sync_customer_product_from_ticket,
		update_service_appointment_status,
		validate_proof_category,
	)
	from lavanya_service.setup.operational_masters import ensure_h5_operational_data_foundation

	baseline = {
		"HD Ticket": frappe.db.count("HD Ticket"),
		"Lavanya Customer Profile": frappe.db.count("Lavanya Customer Profile"),
		"Lavanya Customer Product": frappe.db.count("Lavanya Customer Product")
		if frappe.db.exists("DocType", "Lavanya Customer Product")
		else 0,
		"Service Product Receipt": frappe.db.count("Service Product Receipt"),
		"Lavanya Service Appointment": frappe.db.count("Lavanya Service Appointment")
		if frappe.db.exists("DocType", "Lavanya Service Appointment")
		else 0,
		"Communication": frappe.db.count("Communication"),
		"Email Queue": frappe.db.count("Email Queue") if frappe.db.exists("DocType", "Email Queue") else 0,
		"Notification Log": frappe.db.count("Notification Log")
		if frappe.db.exists("DocType", "Notification Log")
		else 0,
	}

	try:
		ensure_h5_operational_data_foundation()
		_run_all(
			create_service_appointment,
			get_customer_product_history,
			get_master_suggestions,
			list_local_technicians,
			list_service_centers,
			sync_customer_product_from_ticket,
			update_service_appointment_status,
			validate_proof_category,
			baseline,
		)
	finally:
		frappe.set_user("Administrator")
		frappe.db.rollback()
		print("\nTRANSACTION ROLLED BACK - H5 test records not persisted")

	failed = [row for row in RESULTS if not row[2]]
	print(f"\nTOTAL: {len(RESULTS)} | PASS: {len(RESULTS) - len(failed)} | FAIL: {len(failed)}")
	if failed:
		print("FAILED TESTS:")
		for test_id, description, _passed, detail in failed:
			print(f"  - {test_id}: {description} | {detail}")
	print("OVERALL:", "PASS" if not failed else "FAIL")
	return {"total": len(RESULTS), "failed": len(failed)}


def _run_all(
	create_service_appointment,
	get_customer_product_history,
	get_master_suggestions,
	list_local_technicians,
	list_service_centers,
	sync_customer_product_from_ticket,
	update_service_appointment_status,
	validate_proof_category,
	baseline,
):
	_test_structural_foundation()

	mobile, serial_no = _unique_mobile_and_serial()
	ticket = _ticket(mobile, serial_no)
	ticket.insert(ignore_permissions=True)
	second = _ticket(mobile, serial_no, subject="H5 repeat same appliance", warranty_status="Out of Warranty")
	second.insert(ignore_permissions=True)
	h5_side_effect_baseline = _side_effect_counts()

	first_sync = sync_customer_product_from_ticket(ticket.name)
	product_name = first_sync.get("product")
	product = frappe.get_doc("Lavanya Customer Product", product_name)

	_assert(
		"H5-002",
		"ticket sync creates customer product linked to profile and source ticket",
		first_sync.get("ok")
		and product.primary_mobile == mobile
		and product.serial_no == serial_no
		and product.source_ticket == ticket.name
		and product.last_ticket == ticket.name
		and product.customer_profile,
		{"sync": first_sync, "product": product.as_dict()},
	)

	second_sync = sync_customer_product_from_ticket(second.name)
	product.reload()
	_assert(
		"H5-003",
		"same mobile and serial updates existing customer product instead of duplicating",
		second_sync.get("product") == product_name
		and frappe.db.count("Lavanya Customer Product", {"primary_mobile": mobile, "serial_no": serial_no}) == 1
		and product.last_ticket == second.name
		and int(product.ticket_count or 0) >= 2,
		{"sync": second_sync, "ticket_count": product.ticket_count, "last_ticket": product.last_ticket},
	)

	_assert(
		"H5-004",
		"customer product stores warranty history rows",
		len(product.get("warranty_history") or []) >= 2
		and {row.warranty_status for row in product.warranty_history}.issuperset({"In Warranty", "Out of Warranty"}),
		[(row.ticket, row.warranty_status) for row in product.warranty_history],
	)

	history = get_customer_product_history(mobile)
	_assert(
		"H5-005",
		"product history API returns normalized mobile product timeline",
		history.get("ok")
		and history.get("mobile") == mobile
		and history.get("products")
		and history["products"][0]["serial_no"] == serial_no
		and history["products"][0]["warranty_history"],
		history,
	)

	_insert_service_center("H5 Active SC", area="Kozhikode", city="Kozhikode", email="sc@example.com")
	_insert_service_center("H5 Blacklisted SC", status="Blacklisted", area="Kozhikode", city="Kozhikode")
	centers = list_service_centers(brand="Preethi", pincode="673001")
	center_names = {row["name"] for row in centers}
	_assert(
		"H5-006",
		"service center lookup filters by brand/pincode and excludes blacklisted centers",
		"H5 Active SC" in center_names and "H5 Blacklisted SC" not in center_names,
		centers,
	)

	_insert_technician("H5 Active Tech", area="Kozhikode", specialization="Mixer", rating=4.5)
	_insert_technician("H5 Inactive Tech", active=0, area="Kozhikode", specialization="Mixer")
	technicians = list_local_technicians(product_type="Mixer", area="Kozhikode")
	tech_names = {row["name"] for row in technicians}
	_assert(
		"H5-007",
		"technician lookup filters active technicians by skill/area",
		"H5 Active Tech" in tech_names and "H5 Inactive Tech" not in tech_names,
		technicians,
	)

	appointment = create_service_appointment(
		ticket.name,
		"2026-06-25 10:30:00",
		technician="H5 Active Tech",
		service_center="H5 Active SC",
		notes="H5 appointment",
	)
	appointment_doc = frappe.get_doc("Lavanya Service Appointment", appointment.get("appointment"))
	updated = update_service_appointment_status(appointment_doc.name, "Completed", outcome="Resolved at home")
	appointment_doc.reload()
	_assert(
		"H5-008",
		"appointment API stores technician/service-center links and supports safe completion transition",
		appointment.get("ok")
		and updated.get("ok")
		and appointment_doc.technician_link == "H5 Active Tech"
		and appointment_doc.service_center == "H5 Active SC"
		and appointment_doc.status == "Completed"
		and appointment_doc.visit_outcome == "Resolved at home",
		appointment_doc.as_dict(),
	)

	proof = validate_proof_category("Invoice Copy", context="Customer Product at Store")
	_assert("H5-009", "controlled proof category accepts seeded invoice proof", proof.get("ok"), proof)
	_expect_block(
		"H5-010",
		"unknown proof category is blocked",
		lambda: validate_proof_category("Random Screenshot", context="Customer Product at Store"),
		"Proof category",
	)

	suggestions = get_master_suggestions(query="preet", product_type="Mixer", area="Kozhikode")
	_assert(
		"H5-011",
		"master suggestions combine brands, service centers, technicians, and proof categories",
		any(row.get("name") == "Preethi" for row in suggestions.get("brands", []))
		and any(row.get("name") == "H5 Active SC" for row in suggestions.get("service_centers", []))
		and any(row.get("name") == "H5 Active Tech" for row in suggestions.get("technicians", []))
		and any(row.get("name") == "Invoice Copy" for row in suggestions.get("proof_categories", [])),
		suggestions,
	)

	_no_side_effects(h5_side_effect_baseline)


def _test_structural_foundation():
	required_doctypes = [
		"Lavanya Customer Product",
		"Lavanya Warranty History Entry",
		"Lavanya Proof Category",
	]
	_assert(
		"H5-001",
		"H5 customer product and proof DocTypes exist",
		all(frappe.db.exists("DocType", doctype) for doctype in required_doctypes),
		required_doctypes,
	)

	field_checks = [
		("Lavanya Customer Product", "customer_profile"),
		("Lavanya Customer Product", "primary_mobile"),
		("Lavanya Customer Product", "serial_no"),
		("Lavanya Customer Product", "warranty_history"),
		("Brand Service Master", "escalation_phone"),
		("Brand Service Master", "escalation_email"),
		("Service Center Master", "area"),
		("Service Center Master", "city"),
		("Service Center Master", "email"),
		("Local Technician Master", "area"),
		("Local Technician Master", "specialization"),
		("Local Technician Master", "rating"),
		("Lavanya Service Appointment", "technician_link"),
		("Lavanya Service Appointment", "service_center"),
		("Lavanya Service Appointment", "visit_outcome"),
		("Service Product Receipt", "proof_category"),
		("Service Product Receipt", "storage_location"),
	]
	missing = [(doctype, fieldname) for doctype, fieldname in field_checks if not _has_field(doctype, fieldname)]
	_assert("H5-001b", "H5 extension fields exist on existing masters", not missing, missing)


def _side_effect_counts():
	return {
		"Communication": frappe.db.count("Communication"),
		"Email Queue": frappe.db.count("Email Queue") if frappe.db.exists("DocType", "Email Queue") else 0,
		"Notification Log": frappe.db.count("Notification Log")
		if frappe.db.exists("DocType", "Notification Log")
		else 0,
	}


def _no_side_effects(baseline):
	current = _side_effect_counts()
	diffs = {key: current[key] - baseline.get(key, 0) for key in current}
	_assert(
		"H5-012",
		"H5 foundation creates no communication/email/notification side effects",
		all(value == 0 for value in diffs.values()),
		{"baseline": baseline, "current": current, "diffs": diffs},
	)
