"""Read-only production readiness checks (Phase 1R).

Run with:
    bench --site <site> execute lavanya_service.tests.production_readiness.run

Verifies install/runtime invariants that must hold before a production deploy.
Creates no records; the only writes attempted are none. A rollback guard is
kept for safety.
"""

import importlib
import json
import os

import frappe


RESULTS = []

FORBIDDEN_FIXTURES = {
	"user.json",
	"has_role.json",
	"user_permission.json",
	"role_profile.json",
	"hd_agent.json",
	"hd_ticket.json",
	"service_product_receipt.json",
	"lavanya_customer_profile.json",
	"lavanya_product_category.json",
	"lavanya_product_item.json",
	"communication.json",
	"email_queue.json",
	"notification_log.json",
	"todo.json",
	"comment.json",
	"hd_ticket_template_field.json",
}

REQUIRED_APPS = ("frappe", "helpdesk", "lavanya_service")


def _record(test_id, description, passed, detail=""):
	RESULTS.append((test_id, description, bool(passed), detail))
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {test_id} - {description}" + (f" | {detail}" if detail else ""))


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
		print("FAILED:")
		for tid, desc, _p, detail in failed:
			print(f"  - {tid}: {desc} | {detail}")
	return {"total": len(RESULTS), "failed": len(failed)}


def _run_checks():
	# PRD-001: required apps installed
	installed = set(frappe.get_installed_apps())
	missing = [a for a in REQUIRED_APPS if a not in installed]
	_record("PRD-001", "Required apps installed", not missing, f"missing={missing}")

	# PRD-002: no forbidden fixtures present
	fixtures_dir = frappe.get_app_path("lavanya_service", "fixtures")
	present = set(os.listdir(fixtures_dir)) if os.path.isdir(fixtures_dir) else set()
	forbidden_present = sorted(present & FORBIDDEN_FIXTURES)
	_record("PRD-002", "No forbidden fixtures", not forbidden_present, f"found={forbidden_present}")

	# PRD-003: custom_field fixture scoped to HD Ticket only
	cf_path = os.path.join(fixtures_dir, "custom_field.json")
	cf_scoped = False
	cf_detail = "missing"
	if os.path.isfile(cf_path):
		with open(cf_path, encoding="utf-8") as fh:
			cf = json.load(fh)
		dts = sorted({row.get("dt") for row in cf})
		cf_scoped = dts == ["HD Ticket"]
		cf_detail = f"count={len(cf)}, dt={dts}"
	_record("PRD-003", "custom_field fixture scoped to HD Ticket", cf_scoped, cf_detail)

	# PRD-004: hd_ticket_template_field fixture absent (double-import guard)
	_record(
		"PRD-004",
		"hd_ticket_template_field.json absent",
		"hd_ticket_template_field.json" not in present,
		"",
	)

	# PRD-005: no duplicate fields in HD Ticket Template "Default"
	dup_ok, dup_detail = _no_duplicate_template_fields()
	_record("PRD-005", "No duplicate HD Ticket Template fields", dup_ok, dup_detail)

	# PRD-006..009: runtime callables import
	for tid, dotted in [
		("PRD-006", "lavanya_service.api.qr_intake.submit_qr_complaint"),
		("PRD-006b", "lavanya_service.api.qr_intake.get_qr_intake_options"),
		("PRD-007", "lavanya_service.reports.manager_dashboard.get_brand_pending_report"),
		("PRD-008", "lavanya_service.reminders.notification_output.run_daily_reminder_notifications_dry_safe"),
		("PRD-009", "lavanya_service.validations.hd_ticket.validate_ticket"),
		("PRD-009b", "lavanya_service.overrides.hd_ticket.LavanyaHDTicket"),
	]:
		ok, detail = _importable(dotted)
		_record(tid, f"Importable: {dotted}", ok, detail)

	# PRD-010: hooks wiring points at importable targets
	import lavanya_service.hooks as hooks

	def _as_list(value):
		# Frappe hooks may be a single dotted-string or a list of them.
		if not value:
			return []
		return [value] if isinstance(value, str) else list(value)

	wiring = []
	for evt in (hooks.doc_events.get("HD Ticket") or {}).values():
		wiring.extend(_as_list(evt))
	for jobs in (hooks.scheduler_events or {}).values():
		wiring.extend(_as_list(jobs))
	wiring.extend(_as_list(getattr(hooks, "override_doctype_class", {}) and list(hooks.override_doctype_class.values())))
	wiring.extend(_as_list(getattr(hooks, "after_install", None)))
	wiring.extend(_as_list(getattr(hooks, "after_migrate", None)))
	bad = [w for w in wiring if not _importable(w)[0]]
	_record("PRD-010", "All hooks wiring imports cleanly", not bad, f"bad={bad}")

	# PRD-011: D1 — manager brand-pending report runs without a dead status
	try:
		from lavanya_service.reports.manager_dashboard import get_brand_pending_report
		get_brand_pending_report()
		report_ok, report_detail = True, ""
	except Exception as e:
		report_ok, report_detail = False, f"{type(e).__name__}: {e}"
	_record("PRD-011", "Brand pending report executes", report_ok, report_detail)

	# PRD-012: exactly one restricted HD Ticket All DocPerm (read+print only)
	all_ok, all_detail = _hd_ticket_all_restricted()
	_record("PRD-012", "HD Ticket All permission restricted (single row)", all_ok, all_detail)

	# PRD-013: single default, enabled Lavanya SLA; stock Default disabled
	sla_ok, sla_detail = _sla_invariant()
	_record("PRD-013", "SLA defaults correct", sla_ok, sla_detail)


def _importable(dotted):
	module_path, _, attr = dotted.rpartition(".")
	try:
		mod = importlib.import_module(module_path)
		if not hasattr(mod, attr):
			return False, f"missing attr {attr}"
		return True, ""
	except Exception as e:
		return False, f"{type(e).__name__}: {e}"


def _no_duplicate_template_fields():
	if not frappe.db.exists("HD Ticket Template", "Default"):
		return True, "no Default template (skipped)"
	doc = frappe.get_doc("HD Ticket Template", "Default")
	fields = [f.fieldname for f in (doc.get("fields") or []) if getattr(f, "fieldname", None)]
	dupes = sorted({f for f in fields if fields.count(f) > 1})
	return not dupes, f"dupes={dupes}"


def _hd_ticket_all_restricted():
	rows = frappe.get_all(
		"Custom DocPerm",
		filters={"parent": "HD Ticket", "role": "All", "permlevel": 0},
		fields=["name", "read", "write", "create", "delete", "print"],
	)
	if len(rows) != 1:
		return False, f"row_count={len(rows)}"
	r = rows[0]
	ok = r.read == 1 and r.print == 1 and r.write == 0 and r.create == 0 and r.delete == 0
	return ok, f"{r}"


def _sla_invariant():
	sla = "HD Service Level Agreement"
	if not frappe.db.exists("DocType", sla):
		return True, "SLA doctype missing (skipped)"
	if not frappe.db.exists(sla, "Lavanya Default"):
		return False, "Lavanya Default missing"
	lav = frappe.db.get_value(sla, "Lavanya Default", ["default_sla", "enabled"], as_dict=True)
	ok = bool(lav.default_sla) and bool(lav.enabled)
	detail = f"lavanya={lav}"
	if frappe.db.exists(sla, "Default"):
		stock = frappe.db.get_value(sla, "Default", ["default_sla", "enabled"], as_dict=True)
		ok = ok and not stock.default_sla and not stock.enabled
		detail += f", stock={stock}"
	return ok, detail
