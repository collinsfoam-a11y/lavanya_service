import frappe
from frappe.utils import now_datetime

from lavanya_service.setup.operational_masters import (
	CUSTOMER_PRODUCT_DOCTYPE,
	PROOF_CATEGORY_DOCTYPE,
)
from lavanya_service.utils.phone import normalize_phone


TICKET_DOCTYPE = "HD Ticket"
PROFILE_DOCTYPE = "Lavanya Customer Profile"
APPOINTMENT_DOCTYPE = "Lavanya Service Appointment"


def _clean(value):
	return str(value or "").strip()


def _contains_token(value, token):
	value_key = _clean(value).lower()
	token_key = _clean(token).lower()
	return bool(token_key and token_key in value_key)


def _require_not_guest():
	if frappe.session.user == "Guest":
		frappe.throw("Not permitted", frappe.PermissionError)


def _require_ticket_write(ticket_name):
	_require_not_guest()
	if not frappe.db.exists(TICKET_DOCTYPE, ticket_name):
		frappe.throw("Ticket not found.")
	if not frappe.has_permission(TICKET_DOCTYPE, "write", doc=ticket_name):
		frappe.throw("Not permitted", frappe.PermissionError)


def _valid_mobile_or_throw(mobile):
	phone = normalize_phone(mobile)
	if not phone.get("is_valid_mobile"):
		frappe.throw("Please provide a valid 10-digit mobile number.")
	return phone["normalized"]


def _profile_for_mobile(mobile, ticket=None):
	profile_name = frappe.db.get_value(PROFILE_DOCTYPE, {"primary_mobile": mobile}, "name")
	if not profile_name:
		profile_name = frappe.db.get_value(PROFILE_DOCTYPE, {"alternate_mobile": mobile}, "name")
	if profile_name:
		return frappe.get_doc(PROFILE_DOCTYPE, profile_name)

	profile = frappe.new_doc(PROFILE_DOCTYPE)
	profile.primary_mobile = mobile
	profile.customer_name = _clean(ticket.get("customer_name") if ticket else "") or mobile
	if ticket:
		profile.address = ticket.get("address")
		profile.pincode = ticket.get("pincode")
		profile.last_ticket = ticket.name
		profile.last_product_type = ticket.get("product_type")
		profile.last_brand = ticket.get("brand")
	profile.insert(ignore_permissions=True)
	return profile


def _find_customer_product(mobile, ticket):
	serial_no = _clean(ticket.get("serial_no"))
	if serial_no:
		name = frappe.db.get_value(
			CUSTOMER_PRODUCT_DOCTYPE,
			{"primary_mobile": mobile, "serial_no": serial_no, "disabled": 0},
			"name",
		)
		if name:
			return frappe.get_doc(CUSTOMER_PRODUCT_DOCTYPE, name)

	filters = {
		"primary_mobile": mobile,
		"brand": _clean(ticket.get("brand")),
		"model_no": _clean(ticket.get("model_no")),
		"disabled": 0,
	}
	if _clean(ticket.get("product_item")):
		filters["product_item"] = _clean(ticket.get("product_item"))
	else:
		filters["product_type"] = _clean(ticket.get("product_type"))

	if filters.get("brand") and filters.get("model_no"):
		name = frappe.db.get_value(CUSTOMER_PRODUCT_DOCTYPE, filters, "name")
		if name:
			return frappe.get_doc(CUSTOMER_PRODUCT_DOCTYPE, name)

	doc = frappe.new_doc(CUSTOMER_PRODUCT_DOCTYPE)
	doc.primary_mobile = mobile
	return doc


def _set_if_changed(doc, fieldname, value):
	if not doc.meta.has_field(fieldname):
		return False
	value = value if value is not None else None
	if doc.get(fieldname) == value:
		return False
	doc.set(fieldname, value)
	return True


def _append_warranty_history_if_needed(product, ticket):
	ticket_name = ticket.name
	warranty_status = ticket.get("warranty_status") or "Unknown"
	for row in product.get("warranty_history") or []:
		if row.ticket == ticket_name and row.warranty_status == warranty_status:
			return False

	product.append(
		"warranty_history",
		{
			"ticket": ticket_name,
			"warranty_status": warranty_status,
			"purchase_date": ticket.get("purchase_date"),
			"warranty_start_date": ticket.get("warranty_start_date"),
			"warranty_end_date": ticket.get("warranty_end_date"),
			"recorded_at": now_datetime(),
			"notes": "Synced from HD Ticket",
		},
	)
	return True


@frappe.whitelist(methods=["POST"])
def sync_customer_product_from_ticket(ticket_name):
	"""Create/update the customer-owned product record for one ticket.

	Operational only: no ERP documents, stock entries, accounting entries, messages,
	or automatic repeat links are created.
	"""

	if not frappe.db.exists(TICKET_DOCTYPE, ticket_name):
		frappe.throw("Ticket not found.")
	ticket = frappe.get_doc(TICKET_DOCTYPE, ticket_name)
	mobile = _valid_mobile_or_throw(ticket.get("phone_1"))
	profile = _profile_for_mobile(mobile, ticket=ticket)
	product = _find_customer_product(mobile, ticket)
	created = product.is_new()

	changed = created
	for fieldname, value in [
		("customer_profile", profile.name),
		("primary_mobile", mobile),
		("customer_name", ticket.get("customer_name")),
		("brand", ticket.get("brand")),
		("product_category", ticket.get("product_category")),
		("product_item", ticket.get("product_item")),
		("product_type", ticket.get("product_type")),
		("model_no", ticket.get("model_no")),
		("serial_no", ticket.get("serial_no")),
		("purchase_date", ticket.get("purchase_date")),
		("warranty_status", ticket.get("warranty_status") or "Unknown"),
		("warranty_start_date", ticket.get("warranty_start_date")),
		("warranty_end_date", ticket.get("warranty_end_date")),
		("last_ticket", ticket.name),
	]:
		changed = _set_if_changed(product, fieldname, value) or changed

	if created and not product.source_ticket:
		product.source_ticket = ticket.name
		changed = True

	changed = _append_warranty_history_if_needed(product, ticket) or changed
	product.ticket_count = len({row.ticket for row in product.get("warranty_history") or [] if row.ticket})

	if created:
		product.insert(ignore_permissions=True)
	elif changed:
		product.save(ignore_permissions=True)

	return {"ok": True, "created": created, "product": product.name, "profile": profile.name}


@frappe.whitelist()
def get_customer_product_history(mobile):
	mobile = _valid_mobile_or_throw(mobile)
	products = []
	for row in frappe.get_all(
		CUSTOMER_PRODUCT_DOCTYPE,
		filters={"primary_mobile": mobile, "disabled": 0},
		fields=[
			"name",
			"customer_profile",
			"customer_name",
			"brand",
			"product_category",
			"product_item",
			"product_type",
			"model_no",
			"serial_no",
			"purchase_date",
			"warranty_status",
			"warranty_start_date",
			"warranty_end_date",
			"source_ticket",
			"last_ticket",
			"ticket_count",
		],
		order_by="modified desc",
		limit_page_length=50,
	):
		doc = frappe.get_doc(CUSTOMER_PRODUCT_DOCTYPE, row.name)
		payload = dict(row)
		payload["warranty_history"] = [
			{
				"ticket": history.ticket,
				"warranty_status": history.warranty_status,
				"purchase_date": history.purchase_date,
				"warranty_start_date": history.warranty_start_date,
				"warranty_end_date": history.warranty_end_date,
				"recorded_at": history.recorded_at,
				"notes": history.notes,
			}
			for history in (doc.get("warranty_history") or [])
		]
		products.append(payload)
	return {"ok": True, "mobile": mobile, "products": products}


@frappe.whitelist()
def list_service_centers(brand=None, pincode=None, include_inactive=False):
	filters = {}
	if brand:
		filters["brand"] = _clean(brand)
	rows = frappe.get_all(
		"Service Center Master",
		filters=filters,
		fields=["name", "service_center_name", "brand", "phone", "email", "area", "city", "coverage_pincodes", "status", "rating"],
		order_by="service_center_name asc",
		limit_page_length=200,
	)
	result = []
	for row in rows:
		if not include_inactive and row.status in {"Blacklisted", "Out of Area"}:
			continue
		if pincode and row.coverage_pincodes and _clean(pincode) not in row.coverage_pincodes:
			continue
		result.append(dict(row))
	return result


@frappe.whitelist()
def list_local_technicians(product_type=None, area=None, include_inactive=False):
	filters = {} if include_inactive else {"active": 1}
	if area:
		filters["area"] = _clean(area)
	rows = frappe.get_all(
		"Local Technician Master",
		filters=filters,
		fields=["name", "technician_name", "phone", "skills", "area", "specialization", "rating", "active"],
		order_by="technician_name asc",
		limit_page_length=200,
	)
	result = []
	for row in rows:
		if product_type and not (_contains_token(row.skills, product_type) or _contains_token(row.specialization, product_type)):
			continue
		result.append(dict(row))
	return result


@frappe.whitelist()
def validate_proof_category(category, context=None):
	category = _clean(category)
	if not category:
		frappe.throw("Proof category is required.")
	name = frappe.db.get_value(PROOF_CATEGORY_DOCTYPE, {"category_name": category}, "name") or frappe.db.get_value(
		PROOF_CATEGORY_DOCTYPE, category, "name"
	)
	if not name:
		frappe.throw(f"Proof category is not allowed: {category}")
	doc = frappe.get_doc(PROOF_CATEGORY_DOCTYPE, name)
	if not doc.active:
		frappe.throw(f"Proof category is inactive: {category}")
	if context and doc.context not in {"All", context}:
		frappe.throw(f"Proof category {category} is not allowed for {context}.")
	return {"ok": True, "name": doc.name, "category_name": doc.category_name, "context": doc.context}


@frappe.whitelist()
def get_master_suggestions(query=None, product_type=None, area=None, brand=None):
	query = _clean(query)
	from lavanya_service.api.intake_masters import search_similar_brand

	brands = search_similar_brand(query) if query else []
	brand_filter = brand or (brands[0]["name"] if brands else None)
	proof_filters = {"active": 1}
	proofs = frappe.get_all(
		PROOF_CATEGORY_DOCTYPE,
		filters=proof_filters,
		fields=["name", "category_name", "context", "requires_notes"],
		order_by="category_name asc",
		limit_page_length=50,
	)
	return {
		"brands": brands,
		"service_centers": list_service_centers(brand=brand_filter),
		"technicians": list_local_technicians(product_type=product_type, area=area),
		"proof_categories": [dict(row) for row in proofs],
	}


@frappe.whitelist(methods=["POST"])
def create_service_appointment(ticket_name, appointment_datetime, technician=None, service_center=None, notes=None):
	_require_ticket_write(ticket_name)
	dt = _clean(appointment_datetime).replace("T", " ")
	if not dt:
		frappe.throw("Appointment date & time is required.")
	if service_center and not frappe.db.exists("Service Center Master", service_center):
		frappe.throw(f"Service center does not exist: {service_center}")
	technician_name = _clean(technician) or None
	technician_link = technician_name if technician_name and frappe.db.exists("Local Technician Master", technician_name) else None

	doc = frappe.new_doc(APPOINTMENT_DOCTYPE)
	doc.ticket = ticket_name
	doc.appointment_datetime = dt
	doc.technician = technician_name
	doc.technician_link = technician_link
	doc.service_center = _clean(service_center) or None
	doc.scheduled_by = frappe.session.user
	doc.notes = _clean(notes) or None
	doc.status = "Scheduled"
	doc.insert(ignore_permissions=True)
	return {"ok": True, "appointment": doc.name, "message": "Appointment scheduled"}


@frappe.whitelist(methods=["POST"])
def update_service_appointment_status(appointment_name, status, outcome=None, cancel_reason=None):
	_require_not_guest()
	if not frappe.db.exists(APPOINTMENT_DOCTYPE, appointment_name):
		frappe.throw("Appointment not found.")
	status = _clean(status)
	if status not in {"Scheduled", "Completed", "Cancelled", "No Show"}:
		frappe.throw("Invalid appointment status.")
	doc = frappe.get_doc(APPOINTMENT_DOCTYPE, appointment_name)
	if doc.status in {"Completed", "Cancelled", "No Show"} and doc.status != status:
		frappe.throw("Final appointment status cannot be changed.")
	doc.status = status
	if status == "Completed":
		doc.completed_at = now_datetime()
		doc.visit_outcome = _clean(outcome) or doc.visit_outcome
	if status in {"Cancelled", "No Show"}:
		doc.cancel_reason = _clean(cancel_reason) or doc.cancel_reason
	doc.save(ignore_permissions=True)
	return {"ok": True, "appointment": doc.name, "status": doc.status}
