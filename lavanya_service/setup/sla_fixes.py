import frappe

SLA_DOCTYPE = "HD Service Level Agreement"
LAVANYA_SLA = "Lavanya Default"
STOCK_SLA = "Default"


def ensure_helpdesk_sla_defaults():
	"""Keep Lavanya Default as the single default SLA and disable the stock Default.

	Idempotent. Uses db.set_value to avoid re-triggering HD SLA validation,
	which blocks transient states during fixture import (see fresh-install
	failure: importing stock Default with default_sla=0 before Lavanya
	Default exists raises "You must set one SLA as Default").
	"""

	if not frappe.db.exists("DocType", SLA_DOCTYPE):
		return {"changed": False, "reason": "doctype missing"}

	if not frappe.db.exists(SLA_DOCTYPE, LAVANYA_SLA):
		return {"changed": False, "reason": "Lavanya Default not installed yet"}

	changed = False

	if not frappe.db.get_value(SLA_DOCTYPE, LAVANYA_SLA, "default_sla"):
		frappe.db.set_value(SLA_DOCTYPE, LAVANYA_SLA, "default_sla", 1)
		changed = True

	if not frappe.db.get_value(SLA_DOCTYPE, LAVANYA_SLA, "enabled"):
		frappe.db.set_value(SLA_DOCTYPE, LAVANYA_SLA, "enabled", 1)
		changed = True

	if frappe.db.exists(SLA_DOCTYPE, STOCK_SLA):
		stock = frappe.db.get_value(
			SLA_DOCTYPE, STOCK_SLA, ["default_sla", "enabled"], as_dict=True
		)
		if stock.default_sla:
			frappe.db.set_value(SLA_DOCTYPE, STOCK_SLA, "default_sla", 0)
			changed = True
		if stock.enabled:
			frappe.db.set_value(SLA_DOCTYPE, STOCK_SLA, "enabled", 0)
			changed = True

	if changed:
		frappe.clear_cache()
		frappe.db.commit()

	return {"changed": changed}
