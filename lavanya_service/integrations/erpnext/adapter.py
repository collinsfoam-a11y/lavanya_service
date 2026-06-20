"""Read-only ERPNext adapter for Lavanya Service.

Provides lookup methods that fail safely when ERPNext is absent.
All methods return structured responses. No ERPNext modules are imported directly.
"""

import frappe

from lavanya_service.integrations.erpnext.detector import is_erpnext_installed, _get_settings


def _safe_result(ok=False, message="", data=None):
	return {
		"ok": ok,
		"available": is_erpnext_installed(),
		"message": message,
		"data": data,
	}


def _check_availability():
	if not is_erpnext_installed():
		return _safe_result(ok=False, message="ERPNext is not installed.")
	settings = _get_settings()
	if not settings or not int(settings.erpnext_enabled or 0):
		return _safe_result(ok=False, message="ERP integration is disabled in settings.")
	return None


def _read_only_lookup(doctype, filters, fields, enabled_check=True):
	"""Perform a read-only lookup against an ERPNext doctype.

	If ERPNext is not installed, returns unavailable response.
	If the doctype does not exist, returns not-found response.
	"""
	unavailable = _check_availability()
	if unavailable:
		return unavailable
	if enabled_check:
		settings = _get_settings()
		mapping = {
			"Customer": int(settings.customer_lookup_enabled or 0) if settings else 0,
			"Supplier": int(settings.supplier_lookup_enabled or 0) if settings else 0,
			"Item": int(settings.item_lookup_enabled or 0) if settings else 0,
			"Sales Invoice": int(settings.invoice_lookup_enabled or 0) if settings else 0,
			"Serial No": int(settings.serial_lookup_enabled or 0) if settings else 0,
		}
		if doctype in mapping and not mapping[doctype]:
			return _safe_result(ok=False, message=f"{doctype} lookup is disabled in ERP Integration Settings.")

	if not frappe.db.exists("DocType", doctype):
		return _safe_result(ok=False, message=f"{doctype} doctype is not installed.", data=[])
	try:
		results = frappe.get_all(doctype, filters=filters, fields=fields, limit=20)
		return _safe_result(ok=True, message=f"Found {len(results)} {doctype}(s).", data=results)
	except Exception as e:
		return _safe_result(ok=False, message=str(e))


class ERPNextAdapter:
	"""Read-only ERPNext adapter. All methods are safe to call even when ERPNext is not installed."""

	@staticmethod
	def is_available():
		return is_erpnext_installed()

	@staticmethod
	def lookup_customer(mobile=None, name=None):
		if not mobile and not name:
			return _safe_result(ok=False, message="mobile or name filter required.")
		filters = {}
		if mobile:
			filters["mobile_no"] = mobile
		if name:
			filters["customer_name"] = ("like", f"%{name}%")
		return _read_only_lookup("Customer", filters, ["name", "customer_name", "mobile_no", "customer_group"])

	@staticmethod
	def lookup_supplier(supplier_name=None, gstin=None):
		if not supplier_name and not gstin:
			return _safe_result(ok=False, message="supplier_name or gstin filter required.")
		filters = {}
		if supplier_name:
			filters["supplier_name"] = ("like", f"%{supplier_name}%")
		if gstin:
			filters["gstin"] = gstin
		return _read_only_lookup("Supplier", filters, ["name", "supplier_name", "gstin", "supplier_group"])

	@staticmethod
	def lookup_item(item_code=None, barcode=None, serial_no=None):
		if not item_code and not barcode and not serial_no:
			return _safe_result(ok=False, message="item_code, barcode, or serial_no filter required.")
		filters = {}
		if item_code:
			filters["item_code"] = ("like", f"%{item_code}%")
		if barcode:
			filters["barcodes"] = ("like", f"%{barcode}%")
		return _read_only_lookup("Item", filters,
			["name", "item_code", "item_name", "item_group", "standard_rate"])

	@staticmethod
	def lookup_sales_invoice(invoice_no=None, customer=None):
		if not invoice_no and not customer:
			return _safe_result(ok=False, message="invoice_no or customer filter required.")
		filters = {}
		if invoice_no:
			filters["name"] = invoice_no
		if customer:
			filters["customer"] = customer
		return _read_only_lookup("Sales Invoice", filters,
			["name", "customer", "posting_date", "grand_total", "status", "due_date"])

	@staticmethod
	def lookup_serial_no(serial_no):
		if not serial_no:
			return _safe_result(ok=False, message="serial_no filter required.")
		return _read_only_lookup("Serial No", {"name": serial_no},
			["name", "item_code", "item_name", "status", "warranty_expiry_date"])
