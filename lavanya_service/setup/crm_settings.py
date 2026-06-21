"""H6B: CRM settings — read-only safety flags for Lavanya Service Settings.

Safety boundaries:
- All CRM flags default to disabled (0) or read-only mode.
- No automatic CRM lead/deal creation.
- No CRM-to-ERP posting.
- No CRM-triggered WhatsApp sending.
- No CRM-triggered service ticket closure.
"""

import frappe

SETTINGS_DOCTYPE = "Lavanya Service Settings"

CRM_FIELDS = {
	"crm_enabled": {
		"label": "CRM Enabled",
		"fieldtype": "Check",
		"default": "0",
		"description": "Enable CRM relationship visibility in service tickets.",
	},
	"crm_mode": {
		"label": "CRM Mode",
		"fieldtype": "Select",
		"options": "Disabled\nRead Only",
		"default": "Disabled",
		"description": "Read Only shows CRM context without creating records.",
	},
	"crm_readonly_lookup_enabled": {
		"label": "CRM Read-only Lookup",
		"fieldtype": "Check",
		"default": "1",
		"description": "Show CRM contact/organization/open-deal counts in service tickets.",
	},
	"crm_create_lead_enabled": {
		"label": "CRM Lead Creation",
		"fieldtype": "Check",
		"default": "0",
		"description": "Allow creating CRM leads from service tickets. DISABLED for safety.",
	},
	"crm_create_deal_enabled": {
		"label": "CRM Deal Creation",
		"fieldtype": "Check",
		"default": "0",
		"description": "Allow creating CRM deals from service tickets. DISABLED for safety.",
	},
	"crm_auto_link_customer_enabled": {
		"label": "CRM Auto-link Customer",
		"fieldtype": "Check",
		"default": "0",
		"description": "Automatically link CRM contacts to service customers. DISABLED for safety.",
	},
	"crm_service_to_sales_enabled": {
		"label": "Service-to-Sales",
		"fieldtype": "Check",
		"default": "0",
		"description": "Allow suggesting CRM opportunities from service tickets. DISABLED for safety.",
	},
	"crm_manager_approval_required": {
		"label": "Manager Approval Required",
		"fieldtype": "Check",
		"default": "1",
		"description": "Require manager approval before any CRM action from service.",
	},
}


def _ensure_field(dt, fieldname, meta):
	"""Idempotently add a field to a DocType if it does not already exist."""
	if frappe.get_meta(dt).has_field(fieldname):
		return "exists"
	frappe.get_doc({
		"doctype": "Custom Field",
		"dt": dt,
		"fieldname": fieldname,
		"label": meta["label"],
		"fieldtype": meta["fieldtype"],
		"options": meta.get("options"),
		"default": meta.get("default"),
		"description": meta.get("description"),
		"insert_after": meta.get("insert_after", "dry_run_mode_on"),
		"allow_on_submit": 0,
		"read_only": 0,
		"translatable": 0,
	}).insert(ignore_permissions=True)
	frappe.db.commit()
	return "created"


def ensure_crm_settings_fields():
	"""Idempotently add CRM safety fields to Lavanya Service Settings."""
	if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		return {"skipped": f"{SETTINGS_DOCTYPE} DocType not found"}

	results = {}
	prev = "dry_run_mode_on"
	order = list(CRM_FIELDS.keys())
	for fieldname in order:
		meta = dict(CRM_FIELDS[fieldname])
		meta["insert_after"] = prev
		results[fieldname] = _ensure_field(SETTINGS_DOCTYPE, fieldname, meta)
		prev = fieldname

	frappe.clear_cache(doctype=SETTINGS_DOCTYPE)
	return results
