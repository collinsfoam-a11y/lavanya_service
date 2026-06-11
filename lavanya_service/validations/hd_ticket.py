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


def _value(doc, fieldname):
	return getattr(doc, fieldname, None)


def _has_value(doc, fieldname):
	value = _value(doc, fieldname)
	return value is not None and str(value).strip() != ""


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
	validate_phone_numbers(doc)
	validate_brand_registration(doc)
	validate_follow_up_required(doc)
	validate_serial_number_required(doc)
	validate_closure_required(doc)


def validate_phone_numbers(doc):
	for fieldname in ["phone_1", "phone_2"]:
		if hasattr(doc, fieldname):
			_validate_phone(fieldname, _value(doc, fieldname))


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
