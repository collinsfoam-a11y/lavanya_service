import re

import frappe


FOLLOW_UP_REQUIRED_STATUSES = {
	"Registration Pending",
	"Brand Registered",
	"In Progress",
	"Waiting on Customer",
	"Waiting on Part / Approval",
	"Ready for Pickup",
}

SERIAL_REQUIRED_TICKET_TYPES = {
	"Replacement / DOA",
	"Customer Product at Store",
}

CLOSED_STATUSES = {
	"Closed",
}

VALID_CUSTOMER_CONFIRMATION_FOR_CLOSE = {
	"Yes",
	"Not Required",
}

SERVICE_COORDINATION_FIELDS = {
	"manufacturer_registration_required",
	"manufacturer_registered",
	"brand_ticket_number",
	"registration_date",
	"registration_pending_reason",
	"service_center",
	"local_technician",
	"is_repeated_complaint",
	"previous_ticket_link",
	"pending_reason",
	"next_follow_up_date",
	"service_product_receipt",
	"work_narration",
}

CLOSURE_CONTROL_FIELDS = {
	"closure_type",
	"customer_confirmation_received",
	"closed_by",
	"closure_date",
}

SERVICE_COORDINATION_WRITE_ROLES = {
	"Lavanya Manager",
	"Lavanya Helpdesk Agent",
	"Lavanya Service Coordinator",
}

CLOSURE_CONTROL_WRITE_ROLES = {
	"Lavanya Manager",
	"Lavanya Service Coordinator",
}

BYPASS_ROLES = {
	"System Manager",
}


def _value(doc, fieldname):
	return getattr(doc, fieldname, None)


def _has_value(doc, fieldname):
	value = _value(doc, fieldname)
	return value is not None and str(value).strip() != ""


def _current_user_roles():
	if frappe.session.user == "Administrator":
		return {"Administrator"}

	return set(frappe.get_roles(frappe.session.user))


def _has_any_role(roles):
	user_roles = _current_user_roles()
	return bool(user_roles.intersection(roles)) or bool(user_roles.intersection(BYPASS_ROLES))


def _field_changed(doc, fieldname):
	if not hasattr(doc, fieldname):
		return False

	current_value = _value(doc, fieldname)

	if doc.is_new():
		return current_value is not None and str(current_value).strip() != ""

	if not doc.name or not frappe.db.exists("HD Ticket", doc.name):
		return False

	stored_value = frappe.db.get_value("HD Ticket", doc.name, fieldname)
	return frappe.utils.cstr(current_value) != frappe.utils.cstr(stored_value)


def _clean_phone(value):
	if not value:
		return value

	digits = re.sub(r"\D+", "", str(value))

	if digits.startswith("91") and len(digits) == 12:
		digits = digits[2:]

	if digits.startswith("0") and len(digits) == 11:
		digits = digits[1:]

	return digits


def _validate_phone(fieldname, value):
	if not value:
		return

	if not re.fullmatch(r"\d{10}", str(value)):
		frappe.throw(
			f'{fieldname.replace("_", " ").title()} must be a valid 10 digit phone number.'
		)


def normalize_ticket_phone_numbers(doc, method=None):
	for fieldname in ["phone_1", "phone_2"]:
		if hasattr(doc, fieldname):
			cleaned = _clean_phone(_value(doc, fieldname))
			if cleaned != _value(doc, fieldname):
				doc.set(fieldname, cleaned)


def validate_ticket(doc, method=None):
	validate_protected_field_permissions(doc)
	validate_phone_numbers(doc)
	validate_brand_registration(doc)
	validate_follow_up_required(doc)
	validate_serial_number_required(doc)
	validate_closure_required(doc)


def validate_phone_numbers(doc):
	for fieldname in ["phone_1", "phone_2"]:
		if hasattr(doc, fieldname):
			_validate_phone(fieldname, _value(doc, fieldname))


def validate_protected_field_permissions(doc):
	if frappe.session.user == "Administrator" or _has_any_role(BYPASS_ROLES):
		return

	changed_service_fields = sorted(
		fieldname for fieldname in SERVICE_COORDINATION_FIELDS if _field_changed(doc, fieldname)
	)
	changed_closure_fields = sorted(
		fieldname for fieldname in CLOSURE_CONTROL_FIELDS if _field_changed(doc, fieldname)
	)

	if changed_service_fields and not _has_any_role(SERVICE_COORDINATION_WRITE_ROLES):
		frappe.throw(
			"Only Lavanya Manager, Lavanya Helpdesk Agent, or Lavanya Service Coordinator "
			"can update service coordination fields: "
			+ ", ".join(changed_service_fields)
			+ ".",
			frappe.PermissionError,
		)

	if changed_closure_fields and not _has_any_role(CLOSURE_CONTROL_WRITE_ROLES):
		frappe.throw(
			"Only Lavanya Manager or Lavanya Service Coordinator can update closure fields: "
			+ ", ".join(changed_closure_fields)
			+ ".",
			frappe.PermissionError,
		)


def validate_brand_registration(doc):
	if _value(doc, "status") != "Brand Registered":
		return

	missing = []
	if not _has_value(doc, "brand_ticket_number"):
		missing.append("Brand Ticket Number")
	if not _has_value(doc, "registration_date"):
		missing.append("Registration Date")

	if missing:
		frappe.throw("Brand Registered status requires: " + ", ".join(missing) + ".")


def validate_follow_up_required(doc):
	status = _value(doc, "status")

	if status not in FOLLOW_UP_REQUIRED_STATUSES:
		return

	missing = []
	if not _has_value(doc, "pending_reason"):
		missing.append("Pending Reason")
	if not _has_value(doc, "next_follow_up_date"):
		missing.append("Next Follow-up Date")

	if missing:
		frappe.throw(f"{status} status requires: " + ", ".join(missing) + ".")


def validate_serial_number_required(doc):
	ticket_type = _value(doc, "ticket_type")

	if ticket_type not in SERIAL_REQUIRED_TICKET_TYPES:
		return

	if not _has_value(doc, "serial_no"):
		frappe.throw(f"Serial No is required for {ticket_type} tickets.")


def validate_closure_required(doc):
	status = _value(doc, "status")

	if status not in CLOSED_STATUSES:
		return

	missing = []
	if not _has_value(doc, "closure_type"):
		missing.append("Closure Type")
	if not _has_value(doc, "work_narration"):
		missing.append("Work Narration")

	confirmation = _value(doc, "customer_confirmation_received")
	if confirmation not in VALID_CUSTOMER_CONFIRMATION_FOR_CLOSE:
		missing.append("Customer Confirmation Received must be Yes or Not Required")

	if missing:
		frappe.throw("Closed status requires: " + ", ".join(missing) + ".")
