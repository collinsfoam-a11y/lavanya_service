import frappe
from frappe.utils import today

@frappe.whitelist()
def get_coordinator_dashboard(include_counts=True):
	"""Returns the aggregated data for the Lavanya Coordinator Dashboard"""
	if not frappe.has_permission("HD Ticket", "read"):
		frappe.throw("Not permitted to read HD Ticket.", frappe.PermissionError)

	date_str = frappe.utils.formatdate(today(), "dd MMM yyyy")

	# Triage Queue (New tickets)
	triage = frappe.db.sql("""
		SELECT name, subject, customer_name, brand, product_type, creation
		FROM `tabHD Ticket`
		WHERE status = 'New'
		ORDER BY creation ASC
		LIMIT 10
	""", as_dict=True)

	triage_count = frappe.db.count("HD Ticket", {"status": "New"})

	# Unassigned Tickets
	unassigned = frappe.db.sql("""
		SELECT name, subject, customer_name, brand, product_type, creation
		FROM `tabHD Ticket`
		WHERE status IN ('In Progress', 'Brand Registered') AND (IFNULL(_assign, '') = '' OR _assign = '[]')
		ORDER BY creation ASC
		LIMIT 10
	""", as_dict=True)

	unassigned_count = frappe.db.count("HD Ticket", {"status": ["in", ["In Progress", "Brand Registered"]], "_assign": ["in", ["", "[]"]]})

	# Pending Parts
	pending_parts = frappe.db.sql("""
		SELECT name, customer_name, brand, product_item, pending_reason
		FROM `tabHD Ticket`
		WHERE status = 'Waiting on Part / Approval'
		ORDER BY modified DESC
		LIMIT 10
	""", as_dict=True)

	pending_parts_count = frappe.db.count("HD Ticket", {"status": "Waiting on Part / Approval"})

	groups = [
		{
			"key": "triage_queue",
			"label": "Triage Queue",
			"count": triage_count,
			"tickets": triage
		},
		{
			"key": "unassigned_tickets",
			"label": "Unassigned Tickets",
			"count": unassigned_count,
			"tickets": unassigned
		},
		{
			"key": "pending_parts",
			"label": "Pending Parts",
			"count": pending_parts_count,
			"tickets": pending_parts
		}
	]

	return {
		"date": date_str,
		"summary": {
			"triage": triage_count,
			"unassigned": unassigned_count,
			"parts": pending_parts_count
		},
		"groups": groups
	}
