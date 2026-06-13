"""Fresh-install integrity checks (Phase 1S).

Verifies that a site (fresh or migrated) has the required lavanya_service
DocTypes, seeded master data, statuses/types/SLA, working QR options, a clean
ticket template and enabled form scripts. Read-only: creates no records.

Run with:
    bench --site <site> execute lavanya_service.tests.fresh_install_integrity.run
"""

import os

import frappe


RESULTS = []

REQUIRED_DOCTYPES = [
	"Brand Service Master",
	"Service Center Master",
	"Local Technician Master",
	"Free Service Rule",
	"Custody Log Entry",
	"Service Product Receipt",
	"Lavanya Customer Profile",
	"Lavanya Product Category",
	"Lavanya Product Item",
]

REQUIRED_BRANDS = ["LG", "Samsung", "Whirlpool", "Voltas", "Preethi",
                   "Bajaj", "Prestige", "Crompton", "Kent", "Faber"]

REQUIRED_STATUSES = [
	"New", "Registration Pending", "Brand Registered", "In Progress",
	"Waiting on Customer", "Waiting on Part / Approval", "Ready for Pickup",
	"Resolved", "Closed", "Cancelled",
]

REQUIRED_TICKET_TYPES = [
	"Customer Complaint - Site", "Customer Product at Store", "Stock Complaint",
	"Installation / Demo", "Replacement / DOA", "Out of Warranty Local Service",
	"Free Service",
]

FORBIDDEN_FIXTURES = {
	"user.json", "has_role.json", "user_permission.json", "role_profile.json",
	"hd_agent.json", "hd_ticket.json", "service_product_receipt.json",
	"lavanya_customer_profile.json", "lavanya_product_category.json",
	"lavanya_product_item.json", "communication.json", "email_queue.json",
	"notification_log.json", "todo.json", "comment.json",
	"hd_ticket_template_field.json", "brand_service_master.json",
}


def _record(test_id, description, passed, detail=""):
	RESULTS.append((test_id, description, bool(passed), detail))
	print(f"[{'PASS' if passed else 'FAIL'}] {test_id} - {description}" + (f" | {detail}" if detail else ""))


def run():
	RESULTS.clear()
	try:
		_run_checks()
	finally:
		frappe.db.rollback()

	failed = [r for r in RESULTS if not r[2]]
	print(f"\nTOTAL: {len(RESULTS)} | PASS: {len(RESULTS) - len(failed)} | FAIL: {len(failed)}")
	print("OVERALL:", "PASS" if not failed else "FAIL")
	if failed:
		for tid, desc, _p, detail in failed:
			print(f"  - {tid}: {desc} | {detail}")
	return {"total": len(RESULTS), "failed": len(failed)}


def _run_checks():
	# FI-001: required custom DocTypes exist
	missing_dt = [dt for dt in REQUIRED_DOCTYPES if not frappe.db.exists("DocType", dt)]
	_record("FI-001", "Required custom DocTypes exist", not missing_dt, f"missing={missing_dt}")

	# FI-002: brand master seeded (nonzero)
	brand_count = frappe.db.count("Brand Service Master") if frappe.db.exists("DocType", "Brand Service Master") else 0
	_record("FI-002", "Brand Service Master has records", brand_count > 0, f"count={brand_count}")

	# FI-003: required brands present
	missing_brands = [b for b in REQUIRED_BRANDS if not frappe.db.exists("Brand Service Master", b)]
	_record("FI-003", "Required brands seeded", not missing_brands, f"missing={missing_brands}")

	# FI-004: HD Ticket statuses exist
	missing_status = [s for s in REQUIRED_STATUSES if not frappe.db.exists("HD Ticket Status", s)]
	_record("FI-004", "Required HD Ticket statuses exist", not missing_status, f"missing={missing_status}")

	# FI-005: HD Ticket types exist
	missing_types = [t for t in REQUIRED_TICKET_TYPES if not frappe.db.exists("HD Ticket Type", t)]
	_record("FI-005", "Required HD Ticket types exist", not missing_types, f"missing={missing_types}")

	# FI-006: Lavanya Default SLA enabled + default
	sla = "HD Service Level Agreement"
	sla_ok = False
	sla_detail = "missing"
	if frappe.db.exists(sla, "Lavanya Default"):
		v = frappe.db.get_value(sla, "Lavanya Default", ["enabled", "default_sla"], as_dict=True)
		sla_ok = bool(v.enabled) and bool(v.default_sla)
		sla_detail = f"{v}"
	_record("FI-006", "Lavanya Default SLA enabled & default", sla_ok, sla_detail)

	# FI-007: QR options endpoint returns non-empty brands + product types
	from lavanya_service.api.qr_intake import get_qr_intake_options
	opts = get_qr_intake_options()
	qr_ok = bool(opts.get("brands")) and bool(opts.get("product_types")) and bool(opts.get("ticket_types"))
	_record("FI-007", "QR options endpoint returns non-empty lists", qr_ok,
	        f"brands={len(opts.get('brands', []))}, products={len(opts.get('product_types', []))}")

	# FI-008: HD Ticket Template has no duplicate fields
	dup_ok, dup_detail = _no_duplicate_template_fields()
	_record("FI-008", "No duplicate HD Ticket Template fields", dup_ok, dup_detail)

	# FI-009: HD Form Scripts enabled
	enabled_scripts = frappe.db.count("HD Form Script", {"enabled": 1}) if frappe.db.exists("DocType", "HD Form Script") else 0
	_record("FI-009", "HD Form Scripts enabled", enabled_scripts > 0, f"enabled={enabled_scripts}")

	# FI-010: no forbidden fixtures shipped
	fixtures_dir = frappe.get_app_path("lavanya_service", "fixtures")
	present = set(os.listdir(fixtures_dir)) if os.path.isdir(fixtures_dir) else set()
	forbidden = sorted(present & FORBIDDEN_FIXTURES)
	_record("FI-010", "No forbidden fixtures shipped", not forbidden, f"found={forbidden}")


def _no_duplicate_template_fields():
	if not frappe.db.exists("HD Ticket Template", "Default"):
		return True, "no Default template (skipped)"
	doc = frappe.get_doc("HD Ticket Template", "Default")
	fields = [f.fieldname for f in (doc.get("fields") or []) if getattr(f, "fieldname", None)]
	dupes = sorted({f for f in fields if fields.count(f) > 1})
	return not dupes, f"dupes={dupes}"
