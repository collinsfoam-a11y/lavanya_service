import json

import frappe


REFERENCE_DOCTYPE = "HD Ticket"
ROUTE_NAME = "TicketsAgent"
VIEW_TYPE = "list"


COLUMNS = [
	{
		"label": "ID",
		"type": "Data",
		"key": "name",
		"width": "5rem",
	},
	{
		"label": "Subject",
		"type": "Data",
		"key": "subject",
		"width": "18rem",
	},
	{
		"label": "Status",
		"type": "Link",
		"key": "status",
		"options": "HD Ticket Status",
		"width": "11rem",
	},
	{
		"label": "Priority",
		"type": "Link",
		"key": "priority",
		"options": "HD Ticket Priority",
		"width": "8rem",
	},
	{
		"label": "Type",
		"type": "Link",
		"key": "ticket_type",
		"options": "HD Ticket Type",
		"width": "14rem",
	},
	{
		"label": "Customer",
		"type": "Data",
		"key": "customer_name",
		"width": "12rem",
	},
	{
		"label": "Phone",
		"type": "Data",
		"key": "phone_1",
		"width": "10rem",
	},
	{
		"label": "Brand",
		"type": "Link",
		"key": "brand",
		"options": "Brand Service Master",
		"width": "10rem",
	},
	{
		"label": "Product",
		"type": "Select",
		"key": "product_type",
		"width": "10rem",
	},
	{
		"label": "Next Follow-up",
		"type": "Date",
		"key": "next_follow_up_date",
		"width": "10rem",
	},
	{
		"label": "Created",
		"type": "Datetime",
		"key": "creation",
		"width": "10rem",
	},
]


ROWS = [
	"name",
	"subject",
	"status",
	"priority",
	"ticket_type",
	"customer_name",
	"phone_1",
	"brand",
	"product_type",
	"next_follow_up_date",
	"creation",
	"service_product_receipt",
	"sla",
	"agreement_status",
	"is_repeated_complaint",
]


QUEUE_DEFINITIONS = [
	{
		"label": "Lavanya - New Complaints",
		"filters": {"status": "New"},
	},
	{
		"label": "Lavanya - Registration Pending",
		"filters": {"status": "Registration Pending"},
	},
	{
		"label": "Lavanya - Brand Registered",
		"filters": {"status": "Brand Registered"},
	},
	{
		"label": "Lavanya - In Progress",
		"filters": {"status": "In Progress"},
	},
	{
		"label": "Lavanya - Waiting on Customer",
		"filters": {"status": "Waiting on Customer"},
	},
	{
		"label": "Lavanya - Waiting on Part / Approval",
		"filters": {"status": "Waiting on Part / Approval"},
	},
	{
		"label": "Lavanya - Ready for Pickup",
		"filters": {"status": "Ready for Pickup"},
	},
	{
		"label": "Lavanya - Customer Product at Store",
		"filters": {"ticket_type": "Customer Product at Store"},
	},
	{
		"label": "Lavanya - Stock Complaint",
		"filters": {"ticket_type": "Stock Complaint"},
	},
	{
		"label": "Lavanya - Installation / Demo",
		"filters": {"ticket_type": "Installation / Demo"},
	},
	{
		"label": "Lavanya - Repeated Complaints",
		"filters": {"is_repeated_complaint": "Yes"},
	},
	{
		"label": "Lavanya - Closed / Resolved",
		"filters": {"status_category": "Resolved"},
	},
]


DEFERRED_DYNAMIC_QUEUES = [
	"Lavanya - Follow-up Due Today",
	"Lavanya - Overdue Follow-ups",
]


def _json(value):
	return json.dumps(value, ensure_ascii=True)


def _get_existing_view(label):
	name = frappe.db.exists("HD View", {"label": label, "dt": REFERENCE_DOCTYPE})
	if name:
		return frappe.get_doc("HD View", name), "updated"

	return frappe.new_doc("HD View"), "created"


def configure_staff_queues():
	if not frappe.db.exists("DocType", "HD View"):
		frappe.throw("HD View DocType is missing.")

	results = {}

	for queue in QUEUE_DEFINITIONS:
		view, action = _get_existing_view(queue["label"])

		view.label = queue["label"]
		view.icon = "list"
		view.dt = REFERENCE_DOCTYPE
		view.route_name = ROUTE_NAME
		view.type = VIEW_TYPE
		view.public = 1
		view.pinned = 0
		view.is_default = 0
		view.is_customer_portal = 0
		view.is_standard = 0
		view.filters = _json(queue["filters"])
		view.order_by = "modified desc"
		view.columns = _json(COLUMNS)
		view.rows = _json(ROWS)
		view.load_default_columns = 0

		if view.is_new():
			view.insert(ignore_permissions=True)
		else:
			view.save(ignore_permissions=True)

		results[queue["label"]] = {
			"name": view.name,
			"action": action,
		}

	frappe.db.commit()
	frappe.clear_cache(doctype="HD View")

	return {
		"created_or_updated": results,
		"count": len(results),
		"deferred_dynamic_queues": DEFERRED_DYNAMIC_QUEUES,
	}
