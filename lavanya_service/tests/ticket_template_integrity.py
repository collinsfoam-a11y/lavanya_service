"""Read-only integrity checks for the Default HD Ticket Template.

Run with:
    bench --site <site> execute lavanya_service.tests.ticket_template_integrity.run

Guards against the PHASE 1N-FIX-TEMPLATE-1 defect: template child fields were
duplicated because the same rows were exported both embedded in
hd_ticket_template.json and standalone in hd_ticket_template_field.json.
This suite asserts UNIQUENESS (not just set membership), the single fixture
source of truth, and creates no records at all.
"""

import json
import os
from collections import Counter

import frappe

RESULTS = []

TEMPLATE_NAME = "Default"

IMPORTANT_FIELDS = {
	"complaint_source",
	"customer_name",
	"phone_1",
	"product_type",
	"brand",
	"warranty_status",
	"pending_reason",
	"next_follow_up_date",
	"brand_ticket_number",
	"registration_date",
	"service_product_receipt",
	"closure_type",
	"customer_confirmation_received",
	"work_narration",
}

SIDE_EFFECT_DOCTYPES = [
	"HD Ticket",
	"HD Ticket Template",
	"HD Ticket Template Field",
	"Email Queue",
	"Notification Log",
	"Communication",
	"ToDo",
	"Comment",
]


def _record(test_id, description, passed, detail=""):
	RESULTS.append((test_id, description, bool(passed), detail))
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {test_id} - {description}" + (f" | {detail}" if detail else ""))


def _count(doctype):
	return frappe.db.count(doctype) if frappe.db.exists("DocType", doctype) else 0


def _app_path(*parts):
	return os.path.join(frappe.get_app_path("lavanya_service"), *parts)


def run():
	RESULTS.clear()
	before = {dt: _count(dt) for dt in SIDE_EFFECT_DOCTYPES}

	# 1. Template exists
	exists = frappe.db.exists("HD Ticket Template", TEMPLATE_NAME)
	_record("TTI-001", "HD Ticket Template Default exists", bool(exists))

	if exists:
		template = frappe.get_doc("HD Ticket Template", TEMPLATE_NAME)
		fieldnames = [row.fieldname for row in template.fields]
		counts = Counter(fieldnames)
		dupes = {k: v for k, v in counts.items() if v > 1}

		# 2. No duplicate child rows
		_record(
			"TTI-002",
			"no duplicate template fields by fieldname",
			not dupes,
			f"dupes={dict(list(dupes.items())[:5])}",
		)

		# 3. Row count equals unique fieldname count
		_record(
			"TTI-003",
			"row count equals unique fieldname count",
			len(fieldnames) == len(counts),
			f"rows={len(fieldnames)}, unique={len(counts)}",
		)

		# 4. Important fields still present
		missing = IMPORTANT_FIELDS - set(fieldnames)
		_record(
			"TTI-004",
			"important template fields present",
			not missing,
			f"missing={sorted(missing)}",
		)

		# 4b. Template field count matches the embedded fixture children
		fixture_path = _app_path("fixtures", "hd_ticket_template.json")
		if os.path.exists(fixture_path):
			with open(fixture_path) as f:
				records = json.load(f)
			embedded = []
			for record in records:
				if record.get("name") == TEMPLATE_NAME:
					embedded = [
						row.get("fieldname")
						for row in record.get("fields") or []
						if row.get("fieldname")
					]
			_record(
				"TTI-004b",
				"DB fields match embedded fixture children (set + count)",
				set(embedded) == set(fieldnames) and len(embedded) == len(fieldnames),
				f"fixture={len(embedded)}, db={len(fieldnames)}",
			)
		else:
			_record("TTI-004b", "hd_ticket_template.json exists", False, "fixture missing")

	# 5. Standalone child fixture file removed
	standalone = _app_path("fixtures", "hd_ticket_template_field.json")
	_record(
		"TTI-005",
		"hd_ticket_template_field.json not present as fixture",
		not os.path.exists(standalone),
	)

	# 6. hooks.py does not export HD Ticket Template Field standalone
	hooks_fixtures = frappe.get_hooks("fixtures", app_name="lavanya_service") or []
	exported_dts = set()
	for entry in hooks_fixtures:
		if isinstance(entry, dict):
			exported_dts.add(entry.get("dt") or entry.get("doctype"))
		else:
			exported_dts.add(entry)
	_record(
		"TTI-006",
		"hooks.py does not export HD Ticket Template Field",
		"HD Ticket Template Field" not in exported_dts,
		f"exported={sorted(d for d in exported_dts if d)}",
	)

	# 7. Read-only: no side effects
	after = {dt: _count(dt) for dt in SIDE_EFFECT_DOCTYPES}
	diffs = {dt: (before[dt], after[dt]) for dt in after if before[dt] != after[dt]}
	_record("TTI-007", "read-only suite created no records", not diffs, f"diffs={diffs}")

	failed = [r for r in RESULTS if not r[2]]
	print(f"\nTOTAL: {len(RESULTS)} | PASS: {len(RESULTS) - len(failed)} | FAIL: {len(failed)}")
	if failed:
		for test_id, description, _passed, detail in failed:
			print(f"  FAILED: {test_id} - {description} | {detail}")
	print("OVERALL:", "PASS" if not failed else "FAIL")
	return {"total": len(RESULTS), "failed": len(failed)}
