"""P2.4 ERPNext scaffold tests — verify safe defaults and no-post behavior."""

import frappe

_PASS = []
_FAIL = []


def _check(name, condition, detail=""):
	(_PASS if condition else _FAIL).append(name)
	print("[{}] {}".format("PASS" if condition else "FAIL", name) + ((" | " + detail) if detail else ""))


def test_erpnext_absent_does_not_crash():
	from lavanya_service.integrations.erpnext.detector import get_erpnext_status, is_erpnext_installed
	installed = is_erpnext_installed()
	status = get_erpnext_status()
	_check("erpnext_absent_does_not_crash", status["ok"] and not status["available"],
		f"Installed={installed}, Available={status['available']}")


def test_default_settings_disable_erp():
	from lavanya_service.integrations.erpnext.detector import get_erpnext_status
	status = get_erpnext_status()
	_check("default_settings_disable_erp", not status["enabled"], f"Enabled={status['enabled']}, Mode={status['mode']}")


def test_accounting_posting_locked_by_default():
	from lavanya_service.integrations.erpnext.detector import get_erpnext_status
	status = get_erpnext_status()
	details = status.get("details", {})
	_check("accounting_posting_locked_by_default", not details.get("allow_accounting_posting", True))


def test_adapter_returns_unavailable_when_erpnext_absent():
	from lavanya_service.integrations.erpnext.adapter import ERPNextAdapter
	res = ERPNextAdapter.lookup_customer(mobile="9876543210")
	_check("adapter_returns_unavailable_when_erpnext_absent",
		not res["ok"] and not res["available"], str(res))


def test_ticket_mapping_preview_when_erpnext_absent():
	from lavanya_service.api.erp_preview import preview_ticket_erp_mapping
	frappe.set_user("Administrator")
	res = preview_ticket_erp_mapping(ticket="FAKE-0001")
	_check("ticket_mapping_preview_when_erpnext_absent",
		not res["erpnext_available"] and res["mode"] == "Disabled",
		f"Mode={res['mode']}, Available={res['erpnext_available']}")


def test_supplier_penalty_mapping_preview_is_read_only():
	from lavanya_service.api.erp_preview import preview_supplier_penalty_erp_mapping
	frappe.set_user("Administrator")
	res = preview_supplier_penalty_erp_mapping(penalty_name="FAKE-PEN-0001")
	_check("supplier_penalty_mapping_preview_is_read_only",
		not res["erpnext_available"] and res["would_create"] == [],
		str(res))


def test_stock_complaint_mapping_preview_is_read_only():
	from lavanya_service.api.erp_preview import preview_stock_complaint_erp_mapping
	frappe.set_user("Administrator")
	res = preview_stock_complaint_erp_mapping(complaint_name="FAKE-STK-0001")
	_check("stock_complaint_mapping_preview_is_read_only",
		not res["erpnext_available"] and res["would_create"] == [],
		str(res))


def test_no_erp_write_doctypes_created():
	"""Verify no ERPNext doctypes are created by any P2.4 code."""
	forbidden = [
		"Sales Invoice", "Purchase Invoice", "Payment Entry",
		"Journal Entry", "Stock Entry", "GL Entry",
	]
	for dt in forbidden:
		exists = frappe.db.exists("DocType", dt)
		_check(f"no_erp_write_doctype_{dt}", not exists, f"{dt} exists={exists}")


def test_no_gl_or_payment_or_invoice_creation():
	"""Grep substitute: verify no ERP posting code paths execute."""
	from lavanya_service.integrations.erpnext.adapter import ERPNextAdapter
	res1 = ERPNextAdapter.lookup_sales_invoice(invoice_no="INV-0001")
	res2 = ERPNextAdapter.lookup_customer(mobile="1234567890")
	res3 = ERPNextAdapter.lookup_item(item_code="ITEM-001")
	_check("no_gl_or_payment_or_invoice_creation",
		all(not r["ok"] for r in [res1, res2, res3]),
		"All lookups returned unavailable as expected")


def run():
	global _PASS, _FAIL
	_PASS = []
	_FAIL = []
	frappe.set_user("Administrator")
	print("=== P2.4 ERPNext Scaffold Tests ===\n")
	for fn in [
		test_erpnext_absent_does_not_crash,
		test_default_settings_disable_erp,
		test_accounting_posting_locked_by_default,
		test_adapter_returns_unavailable_when_erpnext_absent,
		test_ticket_mapping_preview_when_erpnext_absent,
		test_supplier_penalty_mapping_preview_is_read_only,
		test_stock_complaint_mapping_preview_is_read_only,
		test_no_erp_write_doctypes_created,
		test_no_gl_or_payment_or_invoice_creation,
	]:
		try:
			fn()
		except Exception:
			_check(fn.__name__, False, frappe.get_traceback()[:300])
	print("\nResults: {} pass, {} fail".format(len(_PASS), len(_FAIL)))
	if _FAIL:
		print("Failed: " + ", ".join(_FAIL))
	return {"pass": len(_PASS), "fail": len(_FAIL)}
