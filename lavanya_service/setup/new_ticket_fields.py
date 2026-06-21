import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def create_fields():
	fields = {
		"HD Ticket": [
			{
				"fieldname": "lavanya_expansion_section",
				"label": "Expansion References",
				"fieldtype": "Section Break",
				"insert_after": "payment_status",
				"collapsible": 1,
			},
			{
				"fieldname": "store_service_reference",
				"label": "Store Service Reference",
				"fieldtype": "Link",
				"options": "Store Service Record",
				"insert_after": "lavanya_expansion_section",
				"permlevel": 1,
			},
			{
				"fieldname": "replacement_reference",
				"label": "Replacement Reference",
				"fieldtype": "Link",
				"options": "Replacement Record",
				"insert_after": "store_service_reference",
				"permlevel": 1,
			},
			{
				"fieldname": "return_reference",
				"label": "Return Reference",
				"fieldtype": "Link",
				"options": "Return Service Record",
				"insert_after": "replacement_reference",
				"permlevel": 1,
			},
			{
				"fieldname": "demo_installation_reference",
				"label": "Demo Installation Reference",
				"fieldtype": "Link",
				"options": "Demo Installation Record",
				"insert_after": "return_reference",
				"permlevel": 1,
			},
			{
				"fieldname": "stock_complaint_reference",
				"label": "Stock Complaint Reference",
				"fieldtype": "Link",
				"options": "Stock Complaint Record",
				"insert_after": "demo_installation_reference",
				"permlevel": 1,
			},
			{
				"fieldname": "expansion_col",
				"fieldtype": "Column Break",
				"insert_after": "stock_complaint_reference",
			},
			{
				"fieldname": "store_service_location",
				"label": "Store Service Location",
				"fieldtype": "Data",
				"insert_after": "expansion_col",
			},
			{
				"fieldname": "area",
				"label": "Area",
				"fieldtype": "Data",
				"insert_after": "store_service_location",
				"in_standard_filter": 1,
			},
			{
				"fieldname": "product_received_via",
				"label": "Product Received Via",
				"fieldtype": "Select",
				"options": "Customer Walk-in\nStore Pickup from Home",
				"insert_after": "area",
			},
			{
				"fieldname": "payment_block_eligible",
				"label": "Payment Block Eligible",
				"fieldtype": "Check",
				"insert_after": "product_received_via",
				"permlevel": 1,
			},
		]
	}
	create_custom_fields(fields, update=True)
	frappe.clear_cache(doctype="HD Ticket")
	return "ok"
