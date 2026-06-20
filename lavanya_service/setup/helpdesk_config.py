import frappe


STATUS_CONFIG = [
	{
		"name": "New",
		"label_agent": "New",
		"label_customer": None,
		"category": "Open",
		"enabled": 1,
		"order": 1,
		"color": "Red",
	},
	{
		"name": "Registration Pending",
		"label_agent": "Registration Pending",
		"label_customer": None,
		"category": "Open",
		"enabled": 1,
		"order": 2,
		"color": "Orange",
	},
	{
		"name": "Brand Registered",
		"label_agent": "Brand Registered",
		"label_customer": None,
		"category": "Open",
		"enabled": 1,
		"order": 3,
		"color": "Blue",
	},
	{
		"name": "In Progress",
		"label_agent": "In Progress",
		"label_customer": None,
		"category": "Open",
		"enabled": 1,
		"order": 4,
		"color": "Blue",
	},
	{
		"name": "Waiting on Customer",
		"label_agent": "Waiting on Customer",
		"label_customer": "Awaiting Customer Response",
		"category": "Paused",
		"enabled": 1,
		"order": 5,
		"color": "Yellow",
	},
	{
		"name": "Waiting on Part / Approval",
		"label_agent": "Waiting on Part / Approval",
		"label_customer": "Waiting on Part / Approval",
		"category": "Paused",
		"enabled": 1,
		"order": 6,
		"color": "Yellow",
	},
	{
		"name": "Ready for Pickup",
		"label_agent": "Ready for Pickup",
		"label_customer": "Ready for Pickup",
		"category": "Paused",
		"enabled": 1,
		"order": 7,
		"color": "Green",
	},
	{
		"name": "Resolved",
		"label_agent": "Resolved",
		"label_customer": None,
		"category": "Resolved",
		"enabled": 1,
		"order": 8,
		"color": "Green",
	},
	{
		"name": "Closed",
		"label_agent": "Closed",
		"label_customer": None,
		"category": "Resolved",
		"enabled": 1,
		"order": 9,
		"color": "Gray",
	},
	{
		"name": "Cancelled",
		"label_agent": "Cancelled",
		"label_customer": "Cancelled",
		"category": "Resolved",
		"enabled": 1,
		"order": 10,
		"color": "Gray",
	},
]


PRIORITY_CONFIG = [
	{
		"name": "Urgent",
		"integer_value": 100,
		"description": "Immediate attention required.",
		"disabled": 0,
	},
	{
		"name": "High",
		"integer_value": 200,
		"description": "High priority customer or operational issue.",
		"disabled": 0,
	},
	{
		"name": "Medium",
		"integer_value": 300,
		"description": "Normal service priority.",
		"disabled": 0,
	},
	{
		"name": "Low",
		"integer_value": 400,
		"description": "Low urgency follow-up or non-critical request.",
		"disabled": 0,
	},
]


TICKET_TYPE_CONFIG = [
	{
		"name": "Customer Complaint - Site",
		"description": "Customer complaint where service is expected at customer location.",
		"priority": "Medium",
		"disabled": 0,
		"is_system": 0,
	},
	{
		"name": "Customer Product at Store",
		"description": "Customer product physically received at showroom/store for service.",
		"priority": "Medium",
		"disabled": 0,
		"is_system": 0,
	},
	{
		"name": "Stock Complaint",
		"description": "Issue found in showroom or warehouse stock item.",
		"priority": "High",
		"disabled": 0,
		"is_system": 0,
	},
	{
		"name": "Installation / Demo",
		"description": "Installation or product demo follow-up.",
		"priority": "Medium",
		"disabled": 0,
		"is_system": 0,
	},
	{
		"name": "Replacement / DOA",
		"description": "Replacement or dead-on-arrival product case.",
		"priority": "High",
		"disabled": 0,
		"is_system": 0,
	},
	{
		"name": "Out of Warranty Local Service",
		"description": "Out-of-warranty service handled or coordinated locally.",
		"priority": "Medium",
		"disabled": 0,
		"is_system": 0,
	},
	{
		"name": "Free Service",
		"description": "Scheduled free service reminder or follow-up.",
		"priority": "Low",
		"disabled": 0,
		"is_system": 0,
	},
]


def _set_if_field_exists(doc, fieldname, value):
	if doc.meta.has_field(fieldname):
		doc.set(fieldname, value)


def ensure_status(config):
	name = config["name"]

	if frappe.db.exists("HD Ticket Status", name):
		if name == "Closed":
			return "skipped"
		doc = frappe.get_doc("HD Ticket Status", name)
		action = "updated"
	else:
		doc = frappe.new_doc("HD Ticket Status")
		doc.name = name
		action = "created"

	for fieldname in ["label_agent", "label_customer", "category", "enabled", "order", "color"]:
		_set_if_field_exists(doc, fieldname, config.get(fieldname))

	doc.save(ignore_permissions=True)
	return action


def ensure_priority(config):
	name = config["name"]

	if frappe.db.exists("HD Ticket Priority", name):
		doc = frappe.get_doc("HD Ticket Priority", name)
		action = "updated"
	else:
		doc = frappe.new_doc("HD Ticket Priority")
		doc.name = name
		action = "created"

	for fieldname in ["disabled", "description", "integer_value"]:
		_set_if_field_exists(doc, fieldname, config.get(fieldname))

	doc.save(ignore_permissions=True)
	return action


def ensure_ticket_type(config):
	name = config["name"]

	if frappe.db.exists("HD Ticket Type", name):
		doc = frappe.get_doc("HD Ticket Type", name)
		action = "updated"
	else:
		doc = frappe.new_doc("HD Ticket Type")
		doc.name = name
		action = "created"

	for fieldname in ["is_system", "disabled", "description", "priority"]:
		_set_if_field_exists(doc, fieldname, config.get(fieldname))

	doc.save(ignore_permissions=True)
	return action


def configure_statuses_priorities_types():
	result = {
		"statuses": {},
		"priorities": {},
		"ticket_types": {},
	}

	for config in STATUS_CONFIG:
		result["statuses"][config["name"]] = ensure_status(config)

	for config in PRIORITY_CONFIG:
		result["priorities"][config["name"]] = ensure_priority(config)

	for config in TICKET_TYPE_CONFIG:
		result["ticket_types"][config["name"]] = ensure_ticket_type(config)

	frappe.db.commit()
	frappe.clear_cache()

	return result
