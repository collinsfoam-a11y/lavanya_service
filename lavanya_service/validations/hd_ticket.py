import frappe
from frappe.utils import now_datetime, today

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

BRAND_REGISTRATION_RECOMMENDED_TICKET_TYPES = {
	"Customer Complaint - Site",
	"Customer Product at Store",
	"Installation / Demo",
	"Replacement / DOA",
}

BRAND_REGISTRATION_EXEMPT_TICKET_TYPES = {
	"Stock Complaint",
	"Out of Warranty Local Service",
}

BRAND_REGISTRATION_RECOMMENDED_REASON = "Brand Registration Recommended"
INVOICE_PENDING_REASON = "Invoice Pending"

IMPLICIT_SELECT_EMPTY_VALUES = {
	"pending_reason": {"Invoice Proof Pending"},
	"registration_pending_reason": {"Brand Line Busy"},
}

BRAND_REGISTRATION_SKIP_VALUES = {
	"manufacturer_registration_required": {"No", "Not Applicable"},
	"manufacturer_registered": {"No", "Failed"},
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
	"brand_registration_recommended",
	"brand_registration_recommended_at",
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

BRAND_REGISTRATION_OVERRIDE_FIELDS = {
	"brand_registration_override_reason",
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

BRAND_REGISTRATION_OVERRIDE_WRITE_ROLES = {
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


def _has_meaningful_value(doc, fieldname):
	if not _has_value(doc, fieldname):
		return False

	value = str(_value(doc, fieldname)).strip()
	return value not in IMPLICIT_SELECT_EMPTY_VALUES.get(fieldname, set())


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
	apply_warranty_brand_registration_recommendation(doc)
	validate_brand_registration(doc)
	validate_brand_registration_override(doc)
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

	# Internal server-side bypass for trusted quick-action / product-receipt
	# workflows (audit B1). These set the flag only AFTER an explicit,
	# action-specific role check. Never honoured for Guest, so the public QR
	# endpoint can never use it to write protected fields.
	if getattr(getattr(doc, "flags", None), "ignore_lavanya_field_guard", False) and frappe.session.user != "Guest":
		return

	changed_service_fields = sorted(
		fieldname for fieldname in SERVICE_COORDINATION_FIELDS if _field_changed(doc, fieldname)
	)
	changed_closure_fields = sorted(
		fieldname for fieldname in CLOSURE_CONTROL_FIELDS if _field_changed(doc, fieldname)
	)
	changed_override_fields = sorted(
		fieldname for fieldname in BRAND_REGISTRATION_OVERRIDE_FIELDS if _field_changed(doc, fieldname)
	)

	if changed_service_fields and not _has_any_role(SERVICE_COORDINATION_WRITE_ROLES):
		frappe.throw(
			"Only Lavanya Manager, Lavanya Helpdesk Agent, or Lavanya Service Coordinator "
			"can update service coordination fields: "
			+ ", ".join(changed_service_fields)
			+ ".",
			frappe.PermissionError,
		)

	if changed_override_fields and not _has_any_role(BRAND_REGISTRATION_OVERRIDE_WRITE_ROLES):
		frappe.throw(
			"Only Lavanya Manager or Lavanya Service Coordinator can update brand registration "
			"override fields: "
			+ ", ".join(changed_override_fields)
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


def apply_warranty_brand_registration_recommendation(doc):
	recommended = is_brand_registration_recommended(doc)

	if hasattr(doc, "brand_registration_recommended"):
		doc.brand_registration_recommended = 1 if recommended else 0

	if not recommended:
		if (
			hasattr(doc, "pending_reason")
			and _value(doc, "pending_reason") in IMPLICIT_SELECT_EMPTY_VALUES["pending_reason"]
			and _value(doc, "status") not in FOLLOW_UP_REQUIRED_STATUSES
		):
			doc.pending_reason = ""
		return

	if hasattr(doc, "brand_registration_recommended_at") and not _has_value(
		doc, "brand_registration_recommended_at"
	):
		doc.brand_registration_recommended_at = now_datetime()

	if _brand_registration_completed(doc):
		return

	if _value(doc, "status") in FOLLOW_UP_REQUIRED_STATUSES:
		return

	if hasattr(doc, "pending_reason") and not _has_meaningful_value(doc, "pending_reason"):
		doc.pending_reason = BRAND_REGISTRATION_RECOMMENDED_REASON

	if (
		hasattr(doc, "next_follow_up_date")
		and _value(doc, "pending_reason") != INVOICE_PENDING_REASON
		and not _has_value(doc, "next_follow_up_date")
	):
		doc.next_follow_up_date = today()


def is_brand_registration_recommended(doc):
	if _value(doc, "warranty_status") != "In Warranty":
		return False

	ticket_type = _value(doc, "ticket_type")
	if ticket_type in BRAND_REGISTRATION_RECOMMENDED_TICKET_TYPES:
		return True

	if ticket_type in BRAND_REGISTRATION_EXEMPT_TICKET_TYPES:
		return False

	if ticket_type == "Free Service":
		return _matching_free_service_rule_is_brand_backed(doc)

	return False


def _matching_free_service_rule_is_brand_backed(doc):
	if not frappe.db.exists("DocType", "Free Service Rule"):
		return False

	if not frappe.get_meta("Free Service Rule").get_field("brand_backed"):
		return False

	product_type = _value(doc, "product_type")
	if not product_type:
		return False

	filters = [
		["active", "=", 1],
		["brand_backed", "=", 1],
		["product_type", "=", product_type],
	]

	brand = _value(doc, "brand")
	if brand:
		filters.append(["brand", "in", [brand, ""]])

	return bool(frappe.get_all("Free Service Rule", filters=filters, pluck="name", limit=1))


def _brand_registration_completed(doc):
	return (
		_value(doc, "manufacturer_registered") == "Yes"
		and _has_value(doc, "brand_ticket_number")
		and _has_value(doc, "registration_date")
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


def validate_brand_registration_override(doc):
	if not is_brand_registration_recommended(doc):
		return

	if not _brand_registration_marked_skipped(doc):
		return

	if _has_meaningful_value(doc, "brand_registration_override_reason") or _has_meaningful_value(
		doc, "registration_pending_reason"
	):
		return

	frappe.throw(
		"Brand registration is recommended for this in-warranty case. "
		"Enter Brand Registration Override Reason or Registration Pending Reason to continue."
	)


def _brand_registration_marked_skipped(doc):
	for fieldname, skip_values in BRAND_REGISTRATION_SKIP_VALUES.items():
		if _value(doc, fieldname) in skip_values:
			return True
	return False


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


def validate_linked_record_closure(doc):
	"""H1: Linked-record closure checks — prevent closing a ticket before its
	linked service record (Replacement, Return, Stock, Store) is completed."""
	flow = _value(doc, "service_flow_type") or _value(doc, "ticket_type")
	stage = _value(doc, "current_service_stage")

	if flow == "Replacement / Exchange":
		ref = _value(doc, "replacement_reference")
		if ref:
			rec_status = frappe.db.get_value("Replacement Record", ref, "status")
			if rec_status != "Completed":
				frappe.throw(
					"Cannot close: Replacement Record {0} status is '{1}' (must be Completed).".format(ref, rec_status)
				)
		elif _value(doc, "status") == "Closed":
			frappe.throw("Cannot close: Replacement / Exchange ticket requires a completed Replacement Record.")

	if flow == "Refund Case" or stage in ("Return Reason Verified", "Brand Notified for Return", "Customer Refund Processed"):
		ref = _value(doc, "return_reference")
		if ref:
			rec_status = frappe.db.get_value("Return Service Record", ref, "status")
			refund = frappe.db.get_value("Return Service Record", ref, "refund_status")
			if rec_status != "Completed":
				frappe.throw(
					"Cannot close: Return Service Record {0} status is '{1}' (must be Completed).".format(ref, rec_status)
				)
			if refund not in ("Processed", "Not Applicable"):
				frappe.throw(
					"Cannot close: Return Service Record refund status is '{0}' (must be Processed or Not Applicable).".format(refund)
				)

	if flow == "Stock Complaint":
		ref = _value(doc, "stock_complaint_reference")
		if ref:
			rec_status = frappe.db.get_value("Stock Complaint Record", ref, "status")
			if rec_status != "Completed":
				frappe.throw(
					"Cannot close: Stock Complaint Record {0} status is '{1}' (must be Completed).".format(ref, rec_status)
				)

	if flow == "Customer Product at Store":
		receipt = _value(doc, "service_product_receipt")
		if not receipt and _value(doc, "status") == "Closed":
			frappe.throw("Cannot close: Customer Product at Store ticket requires a Service Product Receipt.")
		ref = _value(doc, "store_service_reference")
		if ref:
			rec_status = frappe.db.get_value("Store Service Record", ref, "status")
			if rec_status != "Completed":
				frappe.throw(
					"Cannot close: Store Service Record {0} status is '{1}' (must be Completed).".format(ref, rec_status)
				)


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

	# H1: Linked-record closure checks
	validate_linked_record_closure(doc)
