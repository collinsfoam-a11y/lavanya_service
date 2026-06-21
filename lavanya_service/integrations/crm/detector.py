"""H6B: CRM detector — checks whether Frappe CRM is installed and available.

Safety boundaries:
- Never imports CRM modules unless detection confirms availability.
- Returns safe empty state if CRM is missing, disabled, or mode is not Read Only.
- No CRM API calls are made from this module.
"""

import frappe


CRM_LEAD_DOCTYPE = "CRM Lead"
CRM_DEAL_DOCTYPE = "CRM Deal"
CRM_CONTACT_DOCTYPE = "Contact"
CRM_ORGANIZATION_DOCTYPE = "CRM Organization"
SETTINGS_DOCTYPE = "Lavanya Service Settings"


def is_crm_installed():
	"""Check if Frappe CRM DocTypes exist."""
	try:
		return frappe.db.exists("DocType", CRM_LEAD_DOCTYPE)
	except Exception:
		return False


def is_crm_organization_available():
	"""Check if CRM Organization DocType exists."""
	try:
		return frappe.db.exists("DocType", CRM_ORGANIZATION_DOCTYPE)
	except Exception:
		return False


def get_crm_settings():
	"""Read CRM safety flags from Lavanya Service Settings. Returns safe defaults if unavailable."""
	defaults = {
		"crm_enabled": 0,
		"crm_mode": "Disabled",
		"crm_readonly_lookup_enabled": 1,
		"crm_create_lead_enabled": 0,
		"crm_create_deal_enabled": 0,
		"crm_auto_link_customer_enabled": 0,
		"crm_service_to_sales_enabled": 0,
		"crm_manager_approval_required": 1,
	}
	try:
		if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
			return defaults
		doc = frappe.get_single(SETTINGS_DOCTYPE)
		settings = {}
		for key in defaults:
			val = doc.get(key)
			settings[key] = val if val is not None else defaults[key]
		return settings
	except Exception:
		return defaults


def can_read_crm():
	"""Returns True only if CRM is installed, enabled, and in Read Only mode."""
	if not is_crm_installed():
		return False
	settings = get_crm_settings()
	return (
		settings["crm_enabled"] == 1
		and settings["crm_mode"] == "Read Only"
		and settings["crm_readonly_lookup_enabled"] == 1
	)
