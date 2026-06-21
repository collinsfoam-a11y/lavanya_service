import frappe


CUSTOMER_PRODUCT_DOCTYPE = "Lavanya Customer Product"
WARRANTY_HISTORY_DOCTYPE = "Lavanya Warranty History Entry"
PROOF_CATEGORY_DOCTYPE = "Lavanya Proof Category"

WARRANTY_STATUS_OPTIONS = "\n".join(
	["In Warranty", "Out of Warranty", "Unknown", "Extended Warranty", "Brand Denied"]
)

PROOF_CONTEXT_OPTIONS = "\n".join(
	[
		"All",
		"Customer Product at Store",
		"Warranty Claim",
		"Stock Complaint",
		"Replacement / DOA",
		"Return",
	]
)

DEFAULT_PROOF_CATEGORIES = [
	("Invoice Copy", "All"),
	("Warranty Card", "Warranty Claim"),
	("Product Photo", "All"),
	("Service Center Job Sheet", "Customer Product at Store"),
	("Customer Handover Acknowledgement", "Customer Product at Store"),
]


def _field(fieldname, label, fieldtype, **kwargs):
	row = {"fieldname": fieldname, "label": label, "fieldtype": fieldtype}
	row.update(kwargs)
	return row


def _permission(role="System Manager", *, read=1, write=1, create=1, delete=1):
	return {
		"role": role,
		"read": read,
		"write": write,
		"create": create,
		"delete": delete,
		"submit": 0,
		"cancel": 0,
		"amend": 0,
		"export": read,
		"report": read,
		"share": write,
		"print": read,
		"email": read,
	}


def _role_permissions():
	return [
		_permission(),
		_permission("Lavanya Manager"),
		_permission("Lavanya Service Coordinator"),
		_permission("Lavanya Helpdesk Agent", delete=0),
		_permission("Lavanya Front Desk", delete=0),
		_permission("Lavanya Viewer", write=0, create=0, delete=0),
	]


def _ensure_doctype(name, fields, *, istable=0, autoname="", title_field="", search_fields=""):
	if frappe.db.exists("DocType", name):
		doc = frappe.get_doc("DocType", name)
		action = "updated"
	else:
		doc = frappe.new_doc("DocType")
		doc.name = name
		action = "created"

	doc.module = "Lavanya Service"
	doc.custom = 1
	doc.istable = istable
	doc.editable_grid = 1
	doc.track_changes = 0 if istable else 1
	doc.allow_rename = 0
	doc.autoname = autoname
	doc.title_field = title_field
	doc.search_fields = search_fields
	doc.sort_field = "modified"
	doc.sort_order = "DESC"
	doc.set("fields", [])
	for row in fields:
		doc.append("fields", row)
	doc.set("permissions", [])
	if not istable:
		for perm in _role_permissions():
			doc.append("permissions", perm)

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache(doctype=name)
	return action


def _ensure_field(doctype, field_config):
	if not frappe.db.exists("DocType", doctype):
		frappe.throw(f"Missing required DocType: {doctype}")

	meta = frappe.get_meta(doctype)
	fieldname = field_config["fieldname"]
	if meta.get_field(fieldname):
		return "exists"

	doc = frappe.get_doc("DocType", doctype)
	doc.append("fields", field_config)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache(doctype=doctype)
	return "created"


def create_warranty_history_entry():
	return _ensure_doctype(
		WARRANTY_HISTORY_DOCTYPE,
		[
			_field("ticket", "Ticket", "Link", options="HD Ticket", in_list_view=1),
			_field("warranty_status", "Warranty Status", "Select", options=WARRANTY_STATUS_OPTIONS, in_list_view=1),
			_field("purchase_date", "Purchase Date", "Date"),
			_field("warranty_start_date", "Warranty Start Date", "Date"),
			_field("warranty_end_date", "Warranty End Date", "Date"),
			_field("recorded_at", "Recorded At", "Datetime", in_list_view=1),
			_field("notes", "Notes", "Small Text"),
		],
		istable=1,
	)


def create_customer_product_doctype():
	if not frappe.db.exists("DocType", WARRANTY_HISTORY_DOCTYPE):
		frappe.throw(f"Missing required DocType: {WARRANTY_HISTORY_DOCTYPE}")

	return _ensure_doctype(
		CUSTOMER_PRODUCT_DOCTYPE,
		[
			_field("customer_profile", "Customer Profile", "Link", options="Lavanya Customer Profile", in_list_view=1),
			_field("primary_mobile", "Primary Mobile", "Data", reqd=1, search_index=1, in_list_view=1, in_standard_filter=1),
			_field("customer_name", "Customer Name", "Data", in_list_view=1),
			_field("brand", "Brand", "Link", options="Brand Service Master", in_list_view=1, in_standard_filter=1),
			_field("product_category", "Product Category", "Link", options="Lavanya Product Category", in_standard_filter=1),
			_field("product_item", "Product Item", "Link", options="Lavanya Product Item", in_list_view=1, in_standard_filter=1),
			_field("product_type", "Product Type", "Data", in_list_view=1, in_standard_filter=1),
			_field("model_no", "Model No", "Data", in_list_view=1),
			_field("serial_no", "Serial No", "Data", search_index=1, in_list_view=1, in_standard_filter=1),
			_field("purchase_date", "Purchase Date", "Date"),
			_field("warranty_status", "Warranty Status", "Select", options=WARRANTY_STATUS_OPTIONS, default="Unknown", in_list_view=1),
			_field("warranty_start_date", "Warranty Start Date", "Date"),
			_field("warranty_end_date", "Warranty End Date", "Date"),
			_field("source_ticket", "Source Ticket", "Link", options="HD Ticket"),
			_field("last_ticket", "Last Ticket", "Link", options="HD Ticket", in_list_view=1),
			_field("ticket_count", "Ticket Count", "Int", default="0", in_list_view=1),
			_field("warranty_history", "Warranty History", "Table", options=WARRANTY_HISTORY_DOCTYPE),
			_field("disabled", "Disabled", "Check", default="0", in_standard_filter=1),
		],
		autoname="LV-CP-.#####",
		title_field="serial_no",
		search_fields="primary_mobile,customer_name,serial_no,brand,model_no,product_item",
	)


def create_proof_category_doctype():
	return _ensure_doctype(
		PROOF_CATEGORY_DOCTYPE,
		[
			_field("category_name", "Category Name", "Data", reqd=1, unique=1, in_list_view=1, in_standard_filter=1),
			_field("context", "Context", "Select", options=PROOF_CONTEXT_OPTIONS, default="All", in_list_view=1, in_standard_filter=1),
			_field("requires_notes", "Requires Notes", "Check", default="0"),
			_field("active", "Active", "Check", default="1", in_list_view=1, in_standard_filter=1),
			_field("description", "Description", "Small Text"),
		],
		autoname="field:category_name",
		title_field="category_name",
		search_fields="category_name,context",
	)


def extend_brand_service_master():
	return {
		"escalation_phone": _ensure_field("Brand Service Master", _field("escalation_phone", "Escalation Phone", "Data", insert_after="toll_free_number")),
		"escalation_email": _ensure_field("Brand Service Master", _field("escalation_email", "Escalation Email", "Data", insert_after="escalation_phone")),
		"service_notes": _ensure_field("Brand Service Master", _field("service_notes", "Service Notes", "Small Text", insert_after="notes")),
	}


def extend_service_center_master():
	return {
		"area": _ensure_field("Service Center Master", _field("area", "Area", "Data", insert_after="brand", in_list_view=1, in_standard_filter=1)),
		"city": _ensure_field("Service Center Master", _field("city", "City", "Data", insert_after="area", in_list_view=1, in_standard_filter=1)),
		"email": _ensure_field("Service Center Master", _field("email", "Email", "Data", insert_after="phone")),
		"rating": _ensure_field("Service Center Master", _field("rating", "Rating", "Float", insert_after="status")),
	}


def extend_local_technician_master():
	return {
		"area": _ensure_field("Local Technician Master", _field("area", "Area", "Data", insert_after="phone", in_list_view=1, in_standard_filter=1)),
		"specialization": _ensure_field("Local Technician Master", _field("specialization", "Specialization", "Data", insert_after="area", in_list_view=1)),
		"rating": _ensure_field("Local Technician Master", _field("rating", "Rating", "Float", insert_after="active")),
	}


def extend_service_appointment():
	return {
		"technician_link": _ensure_field("Lavanya Service Appointment", _field("technician_link", "Technician", "Link", options="Local Technician Master", insert_after="appointment_datetime", in_list_view=1)),
		"service_center": _ensure_field("Lavanya Service Appointment", _field("service_center", "Service Center", "Link", options="Service Center Master", insert_after="technician_link", in_list_view=1)),
		"scheduled_by": _ensure_field("Lavanya Service Appointment", _field("scheduled_by", "Scheduled By", "Link", options="User", insert_after="service_center")),
		"completed_at": _ensure_field("Lavanya Service Appointment", _field("completed_at", "Completed At", "Datetime", insert_after="status")),
		"visit_outcome": _ensure_field("Lavanya Service Appointment", _field("visit_outcome", "Visit Outcome", "Small Text", insert_after="completed_at")),
		"cancel_reason": _ensure_field("Lavanya Service Appointment", _field("cancel_reason", "Cancel Reason", "Small Text", insert_after="visit_outcome")),
	}


def extend_service_product_receipt():
	return {
		"proof_category": _ensure_field("Service Product Receipt", _field("proof_category", "Proof Category", "Link", options=PROOF_CATEGORY_DOCTYPE, insert_after="physical_condition", in_list_view=1, in_standard_filter=1)),
		"receipt_proof_notes": _ensure_field("Service Product Receipt", _field("receipt_proof_notes", "Receipt Proof Notes", "Small Text", insert_after="proof_category")),
		"storage_location": _ensure_field("Service Product Receipt", _field("storage_location", "Storage Location", "Data", insert_after="current_custody_status", in_list_view=1)),
	}


def seed_proof_categories():
	created = []
	existing = []
	for category_name, context in DEFAULT_PROOF_CATEGORIES:
		if frappe.db.exists(PROOF_CATEGORY_DOCTYPE, category_name):
			doc = frappe.get_doc(PROOF_CATEGORY_DOCTYPE, category_name)
			existing.append(category_name)
		else:
			doc = frappe.new_doc(PROOF_CATEGORY_DOCTYPE)
			doc.category_name = category_name
			created.append(category_name)
		doc.context = context
		doc.active = 1
		doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"created": created, "existing": existing}


def ensure_h5_operational_data_foundation():
	results = {}
	results[WARRANTY_HISTORY_DOCTYPE] = create_warranty_history_entry()
	results[CUSTOMER_PRODUCT_DOCTYPE] = create_customer_product_doctype()
	results[PROOF_CATEGORY_DOCTYPE] = create_proof_category_doctype()
	results["proof_categories"] = seed_proof_categories()
	results["brand_extensions"] = extend_brand_service_master()
	results["service_center_extensions"] = extend_service_center_master()
	results["technician_extensions"] = extend_local_technician_master()
	results["appointment_extensions"] = extend_service_appointment()
	results["receipt_extensions"] = extend_service_product_receipt()
	frappe.clear_cache()
	frappe.db.commit()
	return results
