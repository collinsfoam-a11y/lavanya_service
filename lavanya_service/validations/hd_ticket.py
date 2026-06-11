import frappe

from lavanya_service.utils.phone import normalize_phone


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
		if current_value in (None, "", 0, False):
			return False
		if str(current_value).strip() in {"", "0"}:
			return False

		df = frappe.get_meta(doc.doctype).get_field(fieldname)
		if df and frappe.utils.cstr(current_value) == frappe.utils.cstr(df.default):
			return False
		if df and df.fieldtype == "Select" and not df.default:
			first_option = next((option for option in (df.options or "").split("\n") if option), "")
			if first_option and frappe.utils.cstr(current_value) == frappe.utils.cstr(first_option):
				return False

		return True

	if not doc.name or not frappe.db.exists("HD Ticket", doc.name):
		return False

	stored_value = frappe.db.get_value("HD Ticket", doc.name, fieldname)
	return frappe.utils.cstr(current_value) != frappe.utils.cstr(stored_value)


def normalize_ticket_phone_numbers(doc, method=None):
	for fieldname in ["phone_1", "phone_2"]:
		if hasattr(doc, fieldname):
			raw_field = f"{fieldname}_raw"
			normalized_field = f"{fieldname}_normalized"
			current_value = _value(doc, fieldname)
			phone = normalize_phone(current_value)

			if hasattr(doc, raw_field):
				existing_raw = _value(doc, raw_field)
				if phone["raw"] and (not existing_raw or phone["raw"] != phone["normalized"]):
					doc.set(raw_field, phone["raw"])
				elif not phone["raw"]:
					doc.set(raw_field, "")

			if hasattr(doc, normalized_field):
				doc.set(normalized_field, phone["normalized"] or "")

			if phone["is_valid_mobile"]:
				doc.set(fieldname, phone["normalized"])
			else:
				doc.set(fieldname, phone["raw"])


def validate_ticket(doc, method=None):
	validate_protected_field_permissions(doc)
	validate_phone_numbers(doc)
	validate_brand_registration(doc)
	validate_follow_up_required(doc)
	validate_serial_number_required(doc)
	validate_closure_required(doc)


def validate_phone_numbers(doc):
	# Invalid or raw-only contact numbers are intentionally allowed for ticket intake.
	# They are preserved in *_raw fields and skipped for customer-profile uniqueness.
	return


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
