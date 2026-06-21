"""H6B: CRM read-only adapter — fetches lightweight CRM relationship context.

Safety boundaries:
- Never creates CRM records (no insert/save on CRM DocTypes).
- Never calls CRM write APIs.
- Never triggers WhatsApp/SMS/ERP/accounting.
- Never auto-links records.
- Returns safe empty payload if CRM is missing, disabled, or mode is not Read Only.
"""

import frappe
from lavanya_service.integrations.crm.detector import (
	can_read_crm,
	is_crm_installed,
	is_crm_organization_available,
	get_crm_settings,
	CRM_CONTACT_DOCTYPE,
	CRM_DEAL_DOCTYPE,
	CRM_ORGANIZATION_DOCTYPE,
)


def get_crm_relationship(customer_mobile=None, customer_name=None):
	"""Fetch read-only CRM relationship summary for a service customer.

	Returns a safe dict with keys:
	- available: bool
	- enabled: bool
	- mode: str
	- contact_linked: bool
	- contact_name: str
	- organization: str
	- open_deals: int
	- recent_communications: int
	- last_sales_followup: str or None
	- next_sales_followup: str or None
	- service_to_sales_opportunity: bool (set by caller)
	- service_risk: bool (set by caller)
	- warnings: list[str]
	"""
	settings = get_crm_settings()
	base = {
		"available": is_crm_installed(),
		"enabled": settings.get("crm_enabled", 0) == 1,
		"mode": settings.get("crm_mode", "Disabled"),
		"contact_linked": False,
		"contact_name": None,
		"organization": None,
		"open_deals": 0,
		"recent_communications": 0,
		"last_sales_followup": None,
		"next_sales_followup": None,
		"service_to_sales_opportunity": False,
		"service_risk": False,
		"warnings": [],
	}

	if not can_read_crm():
		if not base["available"]:
			base["warnings"].append("Frappe CRM is not installed.")
		elif not base["enabled"]:
			base["warnings"].append("CRM integration is disabled in Lavanya Service Settings.")
		else:
			base["warnings"].append("CRM is not in Read Only mode.")
		return base

	mobile = str(customer_mobile or "").strip()

	# Lookup CRM Contact by mobile
	if mobile:
		try:
			contact = frappe.db.get_value(
				CRM_CONTACT_DOCTYPE,
				{"mobile_no": mobile},
				["name", "first_name", "last_name", "company_name"],
				as_dict=True,
			)
			if contact:
				base["contact_linked"] = True
				base["contact_name"] = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
				base["organization"] = contact.company_name or None
		except Exception:
			pass

	# Lookup CRM Organization by name
	if not base["organization"] and customer_name and is_crm_organization_available():
		try:
			org = frappe.db.get_value(
				CRM_ORGANIZATION_DOCTYPE,
				{"organization_name": customer_name},
				"organization_name",
			)
			if org:
				base["organization"] = org
		except Exception:
			pass

	# Count open deals for linked contact
	if base["contact_linked"]:
		try:
			contact_name = f"{contact.first_name or ''} {contact.last_name or ''}".strip()
			base["open_deals"] = frappe.db.count(
				CRM_DEAL_DOCTYPE,
				{"contact": contact.name, "status": ["not in", ["Won", "Lost", "Closed"]]},
			)
		except Exception:
			pass

	return base
