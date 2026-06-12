"""Idempotent dedupe for HD Ticket Template "Default" child fields.

Root cause (PHASE 1N-FIX-TEMPLATE-1): the app exported the template children
twice — embedded in hd_ticket_template.json AND standalone in
hd_ticket_template_field.json — so a migrate imported both sets and every
fieldname appeared twice. The standalone fixture has been removed from
hooks.py; this utility repairs sites that already imported the duplicates.

Run with:
    bench --site <site> execute \
        lavanya_service.setup.ticket_template_dedupe.dedupe_default_hd_ticket_template_fields
"""

import json
import os

import frappe

TEMPLATE_DOCTYPE = "HD Ticket Template"
TEMPLATE_NAME = "Default"


def _canonical_field_order():
	"""Fieldname order from the embedded children in hd_ticket_template.json."""

	path = os.path.join(
		frappe.get_app_path("lavanya_service"), "fixtures", "hd_ticket_template.json"
	)
	if not os.path.exists(path):
		return []

	with open(path) as f:
		records = json.load(f)

	for record in records:
		if record.get("name") == TEMPLATE_NAME:
			return [
				row.get("fieldname")
				for row in record.get("fields") or []
				if row.get("fieldname")
			]

	return []


def dedupe_default_hd_ticket_template_fields():
	"""Keep one row per fieldname and restore the canonical field order.

	Order matters: the portal new-ticket form renders template fields by idx.
	The canonical order comes from the embedded children in
	hd_ticket_template.json; fields missing from the fixture keep their
	relative order at the end. Idempotent: a second run changes nothing.
	"""

	if not frappe.db.exists(TEMPLATE_DOCTYPE, TEMPLATE_NAME):
		return {"template": TEMPLATE_NAME, "skipped": "template missing"}

	doc = frappe.get_doc(TEMPLATE_DOCTYPE, TEMPLATE_NAME)

	before = len(doc.fields)
	seen = set()
	deduped = []

	for row in doc.fields:
		key = row.fieldname
		if key in seen:
			continue
		seen.add(key)
		deduped.append(row)

	removed = before - len(deduped)

	canonical = _canonical_field_order()
	rank = {fieldname: index for index, fieldname in enumerate(canonical)}
	ordered = sorted(
		deduped, key=lambda row: rank.get(row.fieldname, len(rank) + row.idx)
	)
	order_changed = [row.fieldname for row in ordered] != [
		row.fieldname for row in deduped
	]
	idx_dirty = [row.idx for row in ordered] != list(range(1, len(ordered) + 1))

	changed = bool(removed) or order_changed or idx_dirty

	if changed:
		doc.set("fields", ordered)
		for idx, row in enumerate(doc.fields, start=1):
			row.idx = idx
		doc.save(ignore_permissions=True)
		frappe.db.commit()

	return {
		"template": TEMPLATE_NAME,
		"before": before,
		"after": len(ordered),
		"removed": removed,
		"order_restored": order_changed,
		"unique_fieldnames": len(seen),
	}
