import frappe
from frappe.model.naming import make_autoname

from lavanya_service.utils.phone import is_mobile_number_name, normalize_phone


PROFILE_DOCTYPE = "Lavanya Customer Profile"
PROFILE_SERIES = "LV-CUST-.#####"


def execute():
	if not frappe.db.exists("DocType", PROFILE_DOCTYPE):
		return

	rows = frappe.get_all(
		PROFILE_DOCTYPE,
		fields=[
			"name",
			"primary_mobile",
			"primary_mobile_raw",
			"alternate_mobile",
			"alternate_mobile_raw",
		],
		order_by="creation asc, name asc",
	)

	_normalize_and_check_collisions(rows)

	for row in rows:
		_migrate_profile(row)

	remaining_mobile_names = [
		row.name
		for row in frappe.get_all(PROFILE_DOCTYPE, fields=["name"])
		if is_mobile_number_name(row.name)
	]
	if remaining_mobile_names:
		frappe.throw(
			"Customer profile migration left mobile-named records: "
			+ ", ".join(sorted(remaining_mobile_names))
		)


def _normalize_and_check_collisions(rows):
	seen = {}
	for row in rows:
		phone = normalize_phone(row.primary_mobile or row.name)
		if not phone["is_valid_mobile"]:
			frappe.throw(
				f"Cannot migrate customer profile {row.name}: invalid primary mobile "
				f"{row.primary_mobile or row.name!r} ({phone['reason']})."
			)

		existing = seen.get(phone["normalized"])
		if existing and existing != row.name:
			frappe.throw(
				"Customer profile primary mobile collision during migration: "
				f"{phone['normalized']} is used by {existing} and {row.name}. "
				"Manual merge decision required."
			)
		seen[phone["normalized"]] = row.name


def _migrate_profile(row):
	doc = frappe.get_doc(PROFILE_DOCTYPE, row.name)
	primary = normalize_phone(doc.primary_mobile or doc.name)
	alternate = normalize_phone(doc.alternate_mobile)

	doc.primary_mobile = primary["normalized"]
	if doc.meta.has_field("primary_mobile_raw") and not doc.primary_mobile_raw:
		doc.primary_mobile_raw = primary["raw"] or row.name

	if doc.meta.has_field("alternate_mobile_raw") and alternate["raw"] and not doc.alternate_mobile_raw:
		doc.alternate_mobile_raw = alternate["raw"]

	if alternate["is_valid_mobile"]:
		doc.alternate_mobile = alternate["normalized"]
	elif alternate["raw"]:
		doc.alternate_mobile = None

	doc.save(ignore_permissions=True)

	if is_mobile_number_name(doc.name):
		new_name = make_autoname(PROFILE_SERIES)
		frappe.rename_doc(
			PROFILE_DOCTYPE,
			doc.name,
			new_name,
			force=True,
			merge=False,
		)
