"""ERP Integration Settings DocType for Lavanya Service."""
import frappe
from lavanya_service.setup.masters import ensure_doctype, field

ERP_MODE_OPTIONS = "\n".join(["Disabled", "Read Only", "Draft Only", "Posting Locked"])


def create_erp_integration_settings_doctype():
	return ensure_doctype(
		"Lavanya ERP Integration Settings",
		[
			field("erpnext_enabled", "ERPNext Enabled", "Check", default="0", in_list_view=1),
			field("erpnext_installed_detected", "ERPNext Installed Detected", "Check", default="0", read_only=1),
			field("mode", "Mode", "Select", options=ERP_MODE_OPTIONS, default="Disabled", in_list_view=1),
			field("default_company", "Default Company", "Data"),
			field("customer_lookup_enabled", "Customer Lookup Enabled", "Check", default="0"),
			field("supplier_lookup_enabled", "Supplier Lookup Enabled", "Check", default="0"),
			field("item_lookup_enabled", "Item Lookup Enabled", "Check", default="0"),
			field("invoice_lookup_enabled", "Invoice Lookup Enabled", "Check", default="0"),
			field("serial_lookup_enabled", "Serial Lookup Enabled", "Check", default="0"),
			field("allow_draft_creation", "Allow Draft Creation", "Check", default="0"),
			field("allow_accounting_posting", "Allow Accounting Posting", "Check", default="0"),
			field("last_health_check_at", "Last Health Check At", "Datetime", read_only=1),
			field("last_health_check_status", "Last Health Check Status", "Data", read_only=1),
		],
		autoname="field:default_company",
		title_field="default_company",
	)


def seed_default_erp_settings():
	if not frappe.db.exists("DocType", "Lavanya ERP Integration Settings"):
		return
	if frappe.db.exists("Lavanya ERP Integration Settings", "Default"):
		return
	from lavanya_service.integrations.erpnext.detector import is_erpnext_installed
	installed = is_erpnext_installed()
	doc = frappe.get_doc({
		"doctype": "Lavanya ERP Integration Settings",
		"default_company": "Default",
		"erpnext_enabled": 0,
		"erpnext_installed_detected": 1 if installed else 0,
		"mode": "Disabled",
		"customer_lookup_enabled": 0,
		"supplier_lookup_enabled": 0,
		"item_lookup_enabled": 0,
		"invoice_lookup_enabled": 0,
		"serial_lookup_enabled": 0,
		"allow_draft_creation": 0,
		"allow_accounting_posting": 0,
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()


def create_erp_settings():
	create_erp_integration_settings_doctype()
	seed_default_erp_settings()
