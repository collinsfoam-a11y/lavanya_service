"""H6C: Customer 360 — read-only customer intelligence API.

Safety boundaries:
- Read-only: no CRM lead/deal creation, no WhatsApp send, no ERP posting.
- No customer merge automation.
- No automatic ticket closure.
- No penalty application.
"""

import frappe
from frappe.utils import getdate, today

TICKET_DOCTYPE = "HD Ticket"
PRODUCT_DOCTYPE = "Lavanya Customer Product"
PROFILE_DOCTYPE = "Lavanya Customer Profile"


def _clean_mobile(mobile):
	return str(mobile or "").strip().replace(" ", "")


@frappe.whitelist()
def get_customer_360(mobile):
	"""Read-only Customer 360 view for a single mobile number.

	Returns a safe dict with sections: identity, products, tickets, crm, whatsapp.
	Never creates or modifies any record.
	"""
	if frappe.session.user == "Guest":
		frappe.throw("Not permitted", frappe.PermissionError)

	mobile = _clean_mobile(mobile)
	if not mobile or len(mobile) < 10:
		return {"mobile": mobile, "found": False, "reason": "Invalid mobile"}

	payload = {
		"mobile": mobile,
		"found": False,
		"identity": _identity(mobile),
		"products": _products(mobile),
		"tickets": _ticket_summary(mobile),
		"crm": _crm_summary(mobile),
		"whatsapp": _whatsapp_summary(mobile),
	}

	if payload["identity"]["has_customer"] or payload["tickets"]["total"] > 0:
		payload["found"] = True

	return payload


def _identity(mobile):
	"""Customer identity: profile, name, address, duplicate warnings."""
	identity = {
		"has_customer": False,
		"customer_name": "",
		"primary_mobile": mobile,
		"alternate_mobile": "",
		"address": "",
		"pincode": "",
		"profile_exists": False,
		"last_ticket": None,
		"last_product_type": None,
		"last_brand": None,
		"duplicate_warning": None,
	}
	try:
		profile = frappe.db.get_value(
			PROFILE_DOCTYPE,
			{"primary_mobile": mobile},
			["name", "customer_name", "alternate_mobile", "address", "pincode", "last_ticket", "last_product_type", "last_brand"],
			as_dict=True,
		)
		if not profile:
			profile = frappe.db.get_value(
				PROFILE_DOCTYPE,
				{"alternate_mobile": mobile},
				["name", "customer_name", "alternate_mobile", "address", "pincode", "last_ticket", "last_product_type", "last_brand"],
				as_dict=True,
			)
			if profile:
				identity["duplicate_warning"] = f"Found via alternate mobile: {profile.primary_mobile}"
		if profile:
			identity["has_customer"] = True
			identity["customer_name"] = profile.customer_name or ""
			identity["alternate_mobile"] = profile.alternate_mobile or ""
			identity["address"] = profile.address or ""
			identity["pincode"] = profile.pincode or ""
			identity["profile_exists"] = True
			identity["last_ticket"] = profile.last_ticket
			identity["last_product_type"] = profile.last_product_type
			identity["last_brand"] = profile.last_brand
	except Exception:
		pass

	# Fallback: derive customer name from ticket records
	if not identity["has_customer"]:
		names = frappe.get_all(
			TICKET_DOCTYPE,
			filters={"phone_1": mobile},
			pluck="customer_name",
			order_by="modified desc",
			limit=1,
		)
		if names:
			identity["has_customer"] = True
			identity["customer_name"] = names[0] or mobile

	return identity


def _products(mobile):
	"""Customer product and warranty history."""
	try:
		from lavanya_service.api.operational_masters import get_customer_product_history
		result = get_customer_product_history(mobile)
		return {
			"products": result.get("products", []),
			"count": len(result.get("products", [])),
			"has_history": len(result.get("products", [])) > 0,
		}
	except Exception:
		return {"products": [], "count": 0, "has_history": False}


def _ticket_summary(mobile):
	"""Ticket summary: active, overdue, escalated, recently closed."""
	active = frappe.get_all(
		TICKET_DOCTYPE,
		filters={"phone_1": mobile, "status": ["not in", ["Closed", "Cancelled", "Resolved"]]},
		fields=["name", "status", "subject", "brand", "product_type",
				"next_action", "next_follow_up_date", "overdue_status",
				"escalation_level", "customer_informed_status",
				"customer_satisfaction_status", "creation"],
		order_by="modified desc",
		limit_page_length=50,
	)
	closed = frappe.get_all(
		TICKET_DOCTYPE,
		filters={"phone_1": mobile, "status": ["in", ["Closed", "Resolved"]]},
		fields=["name", "status", "subject", "brand", "product_type", "closure_date"],
		order_by="modified desc",
		limit_page_length=20,
	)

	total = len(active) + len(closed)
	overdue = sum(1 for t in active if t.overdue_status == "Overdue")
	escalated = sum(1 for t in active if t.escalation_level and t.escalation_level != "None")
	not_informed = sum(1 for t in active if not t.customer_informed_status or t.customer_informed_status == "Pending")
	sat_pending = sum(1 for t in active if t.customer_satisfaction_status == "Pending")
	repeat_count = sum(1 for t in active)  # active tickets = potential repeats if > 1

	return {
		"total": total,
		"active": len(active),
		"active_tickets": active,
		"closed": len(closed),
		"closed_tickets": closed,
		"overdue": overdue,
		"escalated": escalated,
		"not_informed": not_informed,
		"satisfaction_pending": sat_pending,
		"repeat_candidate": len(active) > 1,
	}


def _crm_summary(mobile):
	"""CRM relationship summary from H6B adapter (read-only)."""
	try:
		from lavanya_service.integrations.crm.adapter import get_crm_relationship
		return get_crm_relationship(customer_mobile=mobile)
	except Exception:
		return {"available": False, "enabled": False, "mode": "Disabled", "warnings": ["CRM lookup failed safely."]}


def _whatsapp_summary(mobile):
	"""WhatsApp summary from H6A inbox (read-only)."""
	summary = {
		"inbound_count": 0,
		"pending_review": 0,
		"draft_count": 0,
		"approved_drafts": 0,
		"last_message_at": None,
		"last_message_text": None,
	}
	try:
		if not frappe.db.exists("DocType", "WhatsApp Inbound Message"):
			return summary
		inbound = frappe.get_all(
			"WhatsApp Inbound Message",
			filters={"sender_mobile": mobile},
			fields=["name", "message_text", "received_at", "review_status"],
			order_by="received_at desc",
			limit_page_length=20,
		)
		summary["inbound_count"] = len(inbound)
		summary["pending_review"] = sum(1 for m in inbound if m.review_status == "New")
		if inbound:
			summary["last_message_at"] = str(inbound[0].received_at)[:16] if inbound[0].received_at else None
			summary["last_message_text"] = (inbound[0].message_text or "")[:200]
	except Exception:
		pass

	try:
		if not frappe.db.exists("DocType", "WhatsApp Draft Outbound"):
			return summary
		drafts = frappe.get_all(
			"WhatsApp Draft Outbound",
			filters={"recipient_mobile": mobile},
			fields=["name", "review_status"],
			limit_page_length=20,
		)
		summary["draft_count"] = len(drafts)
		summary["approved_drafts"] = sum(1 for d in drafts if d.review_status in ("Approved (Ready)", "Manager Reviewed"))
	except Exception:
		pass

	return summary
