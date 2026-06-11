import frappe


TEMPLATE_NAME = "Default"


TEMPLATE_FIELDS = [
	{
		"fieldname": "complaint_source",
		"required": 1,
		"hide_from_customer": 0,
		"placeholder": "How did the complaint come in?",
	},
	{
		"fieldname": "customer_name",
		"required": 1,
		"hide_from_customer": 0,
		"placeholder": "Customer full name",
	},
	{
		"fieldname": "phone_1",
		"required": 1,
		"hide_from_customer": 0,
		"placeholder": "Primary 10 digit phone number",
	},
	{
		"fieldname": "phone_2",
		"required": 0,
		"hide_from_customer": 0,
		"placeholder": "Alternate phone number",
	},
	{
		"fieldname": "address",
		"required": 0,
		"hide_from_customer": 0,
		"placeholder": "Customer address",
	},
	{
		"fieldname": "pincode",
		"required": 0,
		"hide_from_customer": 0,
		"placeholder": "Area pincode",
	},
	{
		"fieldname": "product_type",
		"required": 1,
		"hide_from_customer": 0,
		"placeholder": "Select product type",
	},
	{
		"fieldname": "product_category",
		"required": 0,
		"hide_from_customer": 0,
		"placeholder": "Product category",
	},
	{
		"fieldname": "product_item",
		"required": 0,
		"hide_from_customer": 0,
		"placeholder": "Product item",
	},
	{
		"fieldname": "product_subtype",
		"required": 0,
		"hide_from_customer": 0,
		"placeholder": "Select subtype if applicable",
	},
	{
		"fieldname": "brand",
		"required": 1,
		"hide_from_customer": 0,
		"placeholder": "Select brand",
	},
	{
		"fieldname": "model_no",
		"required": 0,
		"hide_from_customer": 0,
		"placeholder": "Model number",
	},
	{
		"fieldname": "serial_no",
		"required": 0,
		"hide_from_customer": 0,
		"placeholder": "Serial number",
	},
	{
		"fieldname": "purchased_from_lavanya",
		"required": 0,
		"hide_from_customer": 0,
		"placeholder": "Purchased from Lavanya?",
	},
	{
		"fieldname": "invoice_source",
		"required": 0,
		"hide_from_customer": 0,
		"placeholder": "Invoice source",
	},
	{
		"fieldname": "old_erp_reference",
		"required": 0,
		"hide_from_customer": 0,
		"placeholder": "Old ERP reference / bill number",
	},
	{
		"fieldname": "purchase_date",
		"required": 0,
		"hide_from_customer": 0,
		"placeholder": "Purchase date",
	},
	{
		"fieldname": "warranty_status",
		"required": 0,
		"hide_from_customer": 0,
		"placeholder": "Warranty status",
	},
	{
		"fieldname": "manufacturer_registration_required",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Registration required?",
	},
	{
		"fieldname": "manufacturer_registered",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Registration status",
	},
	{
		"fieldname": "brand_ticket_number",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Brand service ticket number",
	},
	{
		"fieldname": "registration_date",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Registration date",
	},
	{
		"fieldname": "registration_pending_reason",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Registration pending reason",
	},
	{
		"fieldname": "service_center",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Service center",
	},
	{
		"fieldname": "local_technician",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Local technician",
	},
	{
		"fieldname": "is_repeated_complaint",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Repeated complaint?",
	},
	{
		"fieldname": "previous_ticket_link",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Previous ticket",
	},
	{
		"fieldname": "pending_reason",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Pending reason",
	},
	{
		"fieldname": "next_follow_up_date",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Next follow-up date",
	},
	{
		"fieldname": "service_product_receipt",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Service product receipt",
	},
	{
		"fieldname": "work_narration",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Work narration",
	},
	{
		"fieldname": "closure_type",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Closure type",
	},
	{
		"fieldname": "customer_confirmation_received",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Customer confirmation",
	},
	{
		"fieldname": "closed_by",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Closed by",
	},
	{
		"fieldname": "closure_date",
		"required": 0,
		"hide_from_customer": 1,
		"placeholder": "Closure date",
	},
]


EXCLUDED_FIELDS = {
	"manufacturer_registration_required",
	"manufacturer_registered",
	"brand_ticket_number",
	"registration_date",
	"registration_pending_reason",
	"service_center",
	"is_repeated_complaint",
	"previous_ticket_link",
	"pending_reason",
	"next_follow_up_date",
	"service_product_receipt",
	"local_technician",
	"closure_type",
	"work_narration",
	"customer_confirmation_received",
	"closed_by",
	"closure_date",
}


def _require_template():
	if not frappe.db.exists("HD Ticket Template", TEMPLATE_NAME):
		frappe.throw(f"Missing HD Ticket Template: {TEMPLATE_NAME}")


def _require_hd_ticket_field(fieldname):
	meta = frappe.get_meta("HD Ticket")
	if not meta.get_field(fieldname):
		frappe.throw(f"Missing HD Ticket field: {fieldname}")


def configure_default_ticket_template_fields():
	_require_template()

	for row in TEMPLATE_FIELDS:
		_require_hd_ticket_field(row["fieldname"])

	template = frappe.get_doc("HD Ticket Template", TEMPLATE_NAME)

	# Keep this phase controlled: replace only template field rows for Default.
	template.set("fields", [])

	for row in TEMPLATE_FIELDS:
		template.append(
			"fields",
			{
				"fieldname": row["fieldname"],
				"required": row["required"],
				"hide_from_customer": row["hide_from_customer"],
				"placeholder": row["placeholder"],
			},
		)

	template.save(ignore_permissions=True)

	frappe.db.commit()
	frappe.clear_cache()

	return {
		"template": TEMPLATE_NAME,
		"field_count": len(template.fields),
		"fields": [row.fieldname for row in template.fields],
		"required_fields": [row.fieldname for row in template.fields if row.required],
	}
