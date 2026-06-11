import frappe


def _has_value(row, fieldname):
	value = getattr(row, fieldname, None)
	return value is not None and str(value).strip() != ""


def validate_service_product_receipt(doc, method=None):
	validate_custody_log_rows(doc)
	validate_current_status_matches_latest_log(doc)


def validate_custody_log_rows(doc):
	for index, row in enumerate(getattr(doc, "custody_log", []) or [], start=1):
		missing = []

		if not _has_value(row, "custody_action"):
			missing.append("Custody Action")
		if not _has_value(row, "custody_status"):
			missing.append("Custody Status")
		if not _has_value(row, "action_datetime"):
			missing.append("Action Datetime")

		if missing:
			frappe.throw(f"Custody Log row {index} requires: " + ", ".join(missing) + ".")


def validate_current_status_matches_latest_log(doc):
	rows = list(getattr(doc, "custody_log", []) or [])
	if not rows:
		return

	latest = rows[-1]
	latest_status = getattr(latest, "custody_status", None)

	if latest_status and getattr(doc, "current_custody_status", None) != latest_status:
		frappe.throw(
			"Current Custody Status must match the latest Custody Log status: "
			+ str(latest_status)
			+ "."
		)
