import frappe
from frappe.client import get as frappe_client_get
from helpdesk.consts import DEFAULT_TICKET_TEMPLATE
from helpdesk.helpdesk.doctype.hd_ticket.api import get_one as helpdesk_get_ticket
from helpdesk.helpdesk.doctype.hd_ticket.api import (
	get_ticket_customizations as helpdesk_get_ticket_customizations,
)
from helpdesk.helpdesk.doctype.hd_ticket_template.api import get_fields_meta


DEFAULT_TICKET_FIELDS = ["ticket_type", "agent_group", "priority"]

INTAKE_FIELDS = {
	"complaint_source",
	"customer_name",
	"phone_1",
	"phone_2",
	"address",
	"pincode",
	"product_type",
	"product_category",
	"product_item",
	"product_subtype",
	"brand",
	"model_no",
	"serial_no",
	"purchased_from_lavanya",
	"invoice_source",
	"old_erp_reference",
	"purchase_date",
	"warranty_status",
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

AI_ADVISORY_FIELDS = {
	"ai_review_status",
	"ai_suggested_next_action",
	"ai_risk_reason",
	"ai_manager_summary",
	"ai_suggested_customer_message",
	"ai_advisory_source",
	"ai_last_reviewed_at",
	"ai_reviewed_by",
}

SERVICE_WRITE_ROLES = {
	"Lavanya Manager",
	"Lavanya Helpdesk Agent",
	"Lavanya Service Coordinator",
}

CLOSURE_WRITE_ROLES = {
	"Lavanya Manager",
	"Lavanya Service Coordinator",
}

FULL_FIELD_ROLES = {
	"Lavanya Manager",
	"Lavanya Service Coordinator",
}

READ_ONLY_FIELD_ROLES = {
	"Lavanya Viewer",
}


def _ticket_name(response):
	if isinstance(response, dict):
		return response.get("name")

	return getattr(response, "name", None)


def _ticket_template(response):
	template = None

	if isinstance(response, dict):
		template = response.get("template")
	else:
		template = getattr(response, "template", None)

	if isinstance(template, str) and template.strip():
		return template

	return DEFAULT_TICKET_TEMPLATE


def _current_roles():
	if frappe.session.user == "Administrator":
		return {"Administrator", "System Manager"}

	return set(frappe.get_roles(frappe.session.user))


def _field_allowed(fieldname, roles):
	if roles.intersection({"Administrator", "System Manager"}):
		return True

	if fieldname in AI_ADVISORY_FIELDS:
		return True  # read-only advisory fields visible to all roles

	if roles.intersection(FULL_FIELD_ROLES):
		return fieldname in INTAKE_FIELDS | SERVICE_COORDINATION_FIELDS | CLOSURE_CONTROL_FIELDS

	if "Lavanya Helpdesk Agent" in roles:
		return fieldname in INTAKE_FIELDS | SERVICE_COORDINATION_FIELDS

	if "Lavanya Front Desk" in roles:
		return fieldname in INTAKE_FIELDS

	if roles.intersection(READ_ONLY_FIELD_ROLES):
		return fieldname in INTAKE_FIELDS

	return fieldname in INTAKE_FIELDS


def _field_writable(fieldname, roles, ticket_name):
	if roles.intersection({"Administrator", "System Manager"}):
		return True

	if not frappe.has_permission("HD Ticket", "write", ticket_name):
		return False

	if fieldname in DEFAULT_TICKET_FIELDS or fieldname in INTAKE_FIELDS:
		return "Lavanya Viewer" not in roles

	if fieldname in SERVICE_COORDINATION_FIELDS:
		return bool(roles.intersection(SERVICE_WRITE_ROLES))

	if fieldname in CLOSURE_CONTROL_FIELDS:
		return bool(roles.intersection(CLOSURE_WRITE_ROLES))

	return False


def _base_fields():
	meta = frappe.get_meta("HD Ticket")
	fields = []

	for fieldname in DEFAULT_TICKET_FIELDS:
		df = meta.get_field(fieldname)
		if df:
			fields.append(df.as_dict())

	return fields


def _sanitise_link_fields(field):
	# Avoid permission-noise lookups for read-only display fields.
	if field.get("fieldname") == "closed_by":
		field["fieldtype"] = "Data"
		field["options"] = None


def _ticket_fields_for_current_user(response):
	roles = _current_roles()
	ticket_name = _ticket_name(response)
	template = _ticket_template(response)
	fields = []

	for field in _base_fields() + get_fields_meta(template):
		field = dict(field)
		fieldname = field.get("fieldname")

		if not fieldname or field.get("hidden"):
			continue

		if not _field_allowed(fieldname, roles):
			continue

		if not _field_writable(fieldname, roles, ticket_name):
			field["readonly"] = 1
			field["disabled"] = 1

		_sanitise_link_fields(field)
		fields.append(field)

	return fields


def _with_lavanya_ticket_fields(response):
	if _ticket_name(response):
		fields = _ticket_fields_for_current_user(response)

		if isinstance(response, dict):
			response["fields"] = fields
		else:
			response.fields = fields

	return response


def _filter_customization_fields(response):
	roles = _current_roles()
	custom_fields = response.get("custom_fields") or []
	response["custom_fields"] = [
		field
		for field in custom_fields
		if _field_allowed(field.get("fieldname"), roles)
	]
	return response


@frappe.whitelist()
def get(doctype, name=None, filters=None, parent=None):
	response = frappe_client_get(doctype, name=name, filters=filters, parent=parent)

	if doctype == "HD Ticket":
		response = _with_lavanya_ticket_fields(response)

	return response


@frappe.whitelist()
def get_ticket(name, is_customer_portal=False):
	response = helpdesk_get_ticket(name=name, is_customer_portal=is_customer_portal)
	return _with_lavanya_ticket_fields(response)


@frappe.whitelist()
def get_ticket_customizations():
	response = helpdesk_get_ticket_customizations()
	return _filter_customization_fields(response)
