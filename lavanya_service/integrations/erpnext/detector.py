"""ERPNext availability detection for Lavanya Service.

This module detects whether ERPNext is installed without importing ERPNext
modules. It uses Frappe's app registry for detection and never crashes if
ERPNext is absent.
"""

import frappe
from frappe.utils import now_datetime

SETTINGS_DOCTYPE = "Lavanya ERP Integration Settings"


def is_erpnext_installed():
	"""Return True if the erpnext app is installed in this bench."""
	apps = frappe.get_installed_apps()
	return "erpnext" in apps


def _get_settings():
	if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		return None
	name = frappe.db.get_value(SETTINGS_DOCTYPE, {}, "name", order_by="creation desc")
	if name:
		return frappe.get_doc(SETTINGS_DOCTYPE, name)
	return None


def _update_settings(installed):
	name = frappe.db.get_value(SETTINGS_DOCTYPE, {}, "name")
	if not name:
		return
	frappe.db.set_value(SETTINGS_DOCTYPE, name, {
		"erpnext_installed_detected": 1 if installed else 0,
		"last_health_check_at": now_datetime(),
		"last_health_check_status": "Installed" if installed else "Not Installed",
	})


def get_erpnext_status():
	"""Return a structured status dict for ERPNext availability."""
	installed = is_erpnext_installed()
	settings = _get_settings()
	enabled = int(settings.erpnext_enabled or 0) if settings else 0
	mode = settings.mode if settings else "Disabled"

	status = {
		"ok": True,
		"available": installed,
		"enabled": bool(enabled),
		"mode": mode,
		"message": "ERPNext is available and enabled." if (installed and enabled) else
			   "ERPNext is installed but ERP integration is disabled in settings." if installed else
			   "ERPNext is not installed in this bench.",
		"details": {
			"customer_lookup_enabled": bool(int(settings.customer_lookup_enabled or 0)) if settings else False,
			"supplier_lookup_enabled": bool(int(settings.supplier_lookup_enabled or 0)) if settings else False,
			"item_lookup_enabled": bool(int(settings.item_lookup_enabled or 0)) if settings else False,
			"invoice_lookup_enabled": bool(int(settings.invoice_lookup_enabled or 0)) if settings else False,
			"serial_lookup_enabled": bool(int(settings.serial_lookup_enabled or 0)) if settings else False,
			"allow_draft_creation": bool(int(settings.allow_draft_creation or 0)) if settings else False,
			"allow_accounting_posting": bool(int(settings.allow_accounting_posting or 0)) if settings else False,
		} if settings else {},
	}

	_update_settings(installed)
	return status


def assert_erpnext_available():
	"""Raise if ERPNext is not installed or not enabled.

	Safe to call anywhere; does not import ERPNext code.
	"""
	status = get_erpnext_status()
	if not status["available"]:
		frappe.throw("ERPNext is not installed in this bench.", frappe.ValidationError)
	if not status["enabled"]:
		frappe.throw("ERP integration is disabled in ERP Integration Settings.", frappe.ValidationError)
