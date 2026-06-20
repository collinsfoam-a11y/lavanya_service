"""P2.4 ERPNext mapping preview API — read-only, no document creation."""

import frappe

from lavanya_service.integrations.erpnext.detector import get_erpnext_status

_MANAGER_ROLES = {"System Manager", "Lavanya Manager", "Lavanya Service Coordinator"}


def _check_role():
	if not set(frappe.get_roles(frappe.session.user)).intersection(_MANAGER_ROLES):
		frappe.throw("Not permitted.", frappe.PermissionError)


@frappe.whitelist()
def get_erp_status():
	"""Return ERPNext availability and settings status."""
	_check_role()
	return get_erpnext_status()


@frappe.whitelist()
def preview_ticket_erp_mapping(ticket=None):
	"""Preview what ERPNext documents would be relevant for a ticket."""
	_check_role()
	status = get_erpnext_status()
	result = {
		"mode": status["mode"],
		"erpnext_available": status["available"],
		"ticket": ticket,
		"possible_links": {
			"customer": None,
			"sales_invoice": None,
			"item": None,
			"serial_no": None,
		},
		"would_create": [],
		"blocked_reason": status["message"] if not status["available"] else "",
	}
	if not status["available"] or not status["enabled"]:
		return result

	if ticket and frappe.db.exists("HD Ticket", ticket):
		tk = frappe.get_doc("HD Ticket", ticket)
		phone = tk.get("phone_1") or tk.get("phone_1_normalized") or ""
		customer_name = tk.get("customer_name") or ""
		product_type = tk.get("product_type") or ""

		if phone:
			result["possible_links"]["customer"] = {
				"lookup_field": "mobile_no",
				"lookup_value": phone,
				"doc_type": "Customer",
			}
		if customer_name and status["details"].get("customer_lookup_enabled"):
			result["possible_links"]["customer"] = result["possible_links"]["customer"] or {
				"lookup_field": "customer_name",
				"lookup_value": customer_name,
				"doc_type": "Customer",
			}
		if product_type and status["details"].get("item_lookup_enabled"):
			result["possible_links"]["item"] = {
				"lookup_field": "item_code",
				"lookup_value": product_type,
				"doc_type": "Item",
			}
		if status["details"].get("invoice_lookup_enabled"):
			result["possible_links"]["sales_invoice"] = {
				"lookup_field": "customer",
				"lookup_value": customer_name,
				"doc_type": "Sales Invoice",
			}

	return result


@frappe.whitelist()
def preview_supplier_penalty_erp_mapping(penalty_name=None):
	"""Preview what ERPNext document would be created for a penalty computation."""
	_check_role()
	status = get_erpnext_status()
	result = {
		"mode": status["mode"],
		"erpnext_available": status["available"],
		"penalty_computation": penalty_name,
		"possible_document": None,
		"would_create": [],
		"blocked_reason": status["message"] if not status["available"] else "",
	}
	if not status["available"] or not status["enabled"]:
		return result

	if penalty_name and frappe.db.exists("Supplier Penalty Computation", penalty_name):
		pc = frappe.get_doc("Supplier Penalty Computation", penalty_name)
		if pc.status == "Approved" and pc.final_penalty_amount > 0:
			result["would_create"].append({
				"doc_type": "Purchase Invoice",
				"is_return": True,
				"supplier": pc.brand or "Unknown",
				"amount": pc.final_penalty_amount,
				"narration": pc.calculation_narration or "",
			})
		elif pc.status != "Approved":
			result["blocked_reason"] = f"Computation status is '{pc.status}'; must be 'Approved' to create ERP document."

	return result


@frappe.whitelist()
def preview_stock_complaint_erp_mapping(complaint_name=None):
	"""Preview what ERPNext document would be created for a stock complaint."""
	_check_role()
	status = get_erpnext_status()
	result = {
		"mode": status["mode"],
		"erpnext_available": status["available"],
		"stock_complaint": complaint_name,
		"possible_document": None,
		"would_create": [],
		"blocked_reason": status["message"] if not status["available"] else "",
	}
	if not status["available"] or not status["enabled"]:
		return result

	if complaint_name and frappe.db.exists("Stock Complaint Record", complaint_name):
		scr = frappe.get_doc("Stock Complaint Record", complaint_name)
		if scr.credit_note_received_at and scr.credit_note_amount > 0:
			result["would_create"].append({
				"doc_type": "Purchase Receipt",
				"is_return": True,
				"supplier": scr.supplier or "Unknown",
				"amount": scr.credit_note_amount,
				"reference_ticket": scr.ticket or "",
			})

	return result
