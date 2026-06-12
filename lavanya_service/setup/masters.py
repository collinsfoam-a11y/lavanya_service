import frappe


BRAND_SEEDS = [
	"LG",
	"Samsung",
	"Whirlpool",
	"Voltas",
	"Preethi",
	"Bajaj",
	"Prestige",
	"Crompton",
	"Kent",
	"Faber",
]


PRODUCT_TYPE_OPTIONS = "\n".join(
	[
		"AC",
		"Refrigerator",
		"Washing Machine",
		"Mixer",
		"Induction Cooker",
		"Chimney",
		"Hob",
		"Gas Stove",
		"TV",
		"Water Purifier",
		"Other",
	]
)


def field(fieldname, label, fieldtype, **kwargs):
	row = {
		"fieldname": fieldname,
		"label": label,
		"fieldtype": fieldtype,
	}
	row.update(kwargs)
	return row


def permission(role="System Manager"):
	return {
		"role": role,
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"submit": 0,
		"cancel": 0,
		"amend": 0,
		"export": 1,
		"report": 1,
		"share": 1,
		"print": 1,
		"email": 1,
	}


def ensure_doctype(name, fields, autoname=None, title_field=None, sort_field="modified"):
	if frappe.db.exists("DocType", name):
		return "exists"

	doc = frappe.get_doc(
		{
			"doctype": "DocType",
			"name": name,
			"module": "Lavanya Service",
			"custom": 1,
			"istable": 0,
			"editable_grid": 1,
			"track_changes": 1,
			"allow_rename": 1,
			"autoname": autoname or "",
			"title_field": title_field or "",
			"sort_field": sort_field,
			"sort_order": "DESC",
			"fields": fields,
			"permissions": [permission()],
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return "created"


def create_brand_service_master():
	return ensure_doctype(
		"Brand Service Master",
		[
			field(
				"brand_name",
				"Brand Name",
				"Data",
				reqd=1,
				unique=1,
				in_list_view=1,
				in_standard_filter=1,
			),
			field("toll_free_number", "Toll Free Number", "Data", in_list_view=1),
			field(
				"registration_channel",
				"Registration Channel",
				"Select",
				options="Toll Free\nWhatsApp\nWeb Portal\nDealer Portal\nEmail",
				in_list_view=1,
			),
			field("portal_url", "Portal URL", "Data"),
			field("dealer_code", "Dealer Code", "Data"),
			field("default_registration_sla_hours", "Default Registration SLA Hours", "Int", default="4"),
			field("free_service_supported", "Free Service Supported", "Check"),
			field("notes", "Notes", "Small Text"),
		],
		autoname="field:brand_name",
		title_field="brand_name",
	)


def create_service_center_master():
	return ensure_doctype(
		"Service Center Master",
		[
			field(
				"service_center_name",
				"Service Center Name",
				"Data",
				reqd=1,
				unique=1,
				in_list_view=1,
				in_standard_filter=1,
			),
			field(
				"brand",
				"Brand",
				"Link",
				options="Brand Service Master",
				reqd=1,
				in_list_view=1,
				in_standard_filter=1,
			),
			field("phone", "Phone", "Data", in_list_view=1),
			field("contact_person", "Contact Person", "Data"),
			field("coverage_pincodes", "Coverage Pincodes", "Small Text"),
			field(
				"status",
				"Status",
				"Select",
				options="Active\nDelayed-Prone\nOut of Area\nBlacklisted",
				default="Active",
				in_list_view=1,
				in_standard_filter=1,
			),
		],
		autoname="field:service_center_name",
		title_field="service_center_name",
	)


def create_local_technician_master():
	return ensure_doctype(
		"Local Technician Master",
		[
			field(
				"technician_name",
				"Technician Name",
				"Data",
				reqd=1,
				unique=1,
				in_list_view=1,
				in_standard_filter=1,
			),
			field("phone", "Phone", "Data", in_list_view=1),
			field("skills", "Skills", "Small Text"),
			field(
				"default_commission_type",
				"Default Commission Type",
				"Select",
				options="Fixed Amount\nPercentage\nNo Commission\nIncluded in Service Cost",
				default="No Commission",
				in_list_view=1,
			),
			field("default_commission_value", "Default Commission Value", "Currency"),
			field("active", "Active", "Check", default="1", in_list_view=1, in_standard_filter=1),
		],
		autoname="field:technician_name",
		title_field="technician_name",
	)


def create_free_service_rule():
	return ensure_doctype(
		"Free Service Rule",
		[
			field("brand", "Brand", "Link", options="Brand Service Master", in_list_view=1, in_standard_filter=1),
			field(
				"product_type",
				"Product Type",
				"Select",
				options=PRODUCT_TYPE_OPTIONS,
				reqd=1,
				in_list_view=1,
				in_standard_filter=1,
			),
			field(
				"service_type",
				"Service Type",
				"Select",
				options="AC Free Service\nChimney Service\nWater Purifier Service\nDemo Follow-up",
				reqd=1,
				in_list_view=1,
			),
			field("brand_backed", "Brand Backed", "Check", default="0", in_list_view=1, in_standard_filter=1),
			field("due_after_days", "Due After Days", "Int", reqd=1),
			field("reminder_before_days", "Reminder Before Days", "Int", default="7"),
			field("active", "Active", "Check", default="1", in_list_view=1, in_standard_filter=1),
		],
		autoname="format:FSR-.#####",
		title_field="service_type",
	)


def ensure_free_service_rule_brand_backed_field():
	doctype = "Free Service Rule"
	fieldname = "brand_backed"

	if not frappe.db.exists("DocType", doctype):
		frappe.throw(f"Missing required DocType: {doctype}")

	meta = frappe.get_meta(doctype)
	if meta.get_field(fieldname):
		return "exists"

	doc = frappe.get_doc("DocType", doctype)
	doc.append(
		"fields",
		field(
			fieldname,
			"Brand Backed",
			"Check",
			default="0",
			in_list_view=1,
			in_standard_filter=1,
		),
	)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache(doctype=doctype)
	return "created"


def seed_brand_service_master():
	created = []
	existing = []

	for brand in BRAND_SEEDS:
		if frappe.db.exists("Brand Service Master", brand):
			existing.append(brand)
			continue

		doc = frappe.get_doc(
			{
				"doctype": "Brand Service Master",
				"brand_name": brand,
				"registration_channel": "Toll Free",
				"default_registration_sla_hours": 4,
				"free_service_supported": 0,
			}
		)
		doc.insert(ignore_permissions=True)
		created.append(brand)

	frappe.db.commit()
	return {"created": created, "existing": existing}


def create_supporting_masters():
	results = {
		"Brand Service Master": create_brand_service_master(),
		"Service Center Master": create_service_center_master(),
		"Local Technician Master": create_local_technician_master(),
		"Free Service Rule": create_free_service_rule(),
	}
	results["Free Service Rule brand_backed field"] = ensure_free_service_rule_brand_backed_field()

	frappe.clear_cache()

	brand_seed_result = seed_brand_service_master()

	return {
		"doctypes": results,
		"brand_seeds": brand_seed_result,
	}
