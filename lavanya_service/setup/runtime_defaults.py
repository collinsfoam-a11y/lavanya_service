import frappe


def _set_if_field_exists(doc, fieldname, value):
	if doc.meta.has_field(fieldname):
		doc.set(fieldname, value)
		return True
	return False


def configure_runtime_defaults():
	result = {
		"sla": {},
		"hd_settings": {},
	}

	if not frappe.db.exists("HD Service Level Agreement", "Lavanya Default"):
		frappe.throw("Missing required SLA: Lavanya Default")

	lavanya_sla = frappe.get_doc("HD Service Level Agreement", "Lavanya Default")
	lavanya_sla.enabled = 1
	lavanya_sla.default_sla = 1
	_set_if_field_exists(lavanya_sla, "default_priority", "Medium")
	_set_if_field_exists(lavanya_sla, "default_ticket_status", "New")
	_set_if_field_exists(lavanya_sla, "ticket_reopen_status", "In Progress")
	lavanya_sla.save(ignore_permissions=True)

	result["sla"]["Lavanya Default"] = {
		"enabled": lavanya_sla.enabled,
		"default_sla": lavanya_sla.default_sla,
		"default_priority": getattr(lavanya_sla, "default_priority", None),
		"default_ticket_status": getattr(lavanya_sla, "default_ticket_status", None),
		"ticket_reopen_status": getattr(lavanya_sla, "ticket_reopen_status", None),
	}

	if frappe.db.exists("HD Service Level Agreement", "Default"):
		default_sla = frappe.get_doc("HD Service Level Agreement", "Default")
		default_sla.enabled = 0
		default_sla.default_sla = 0
		default_sla.save(ignore_permissions=True)

		result["sla"]["Default"] = {
			"enabled": default_sla.enabled,
			"default_sla": default_sla.default_sla,
		}

	settings = frappe.get_doc("HD Settings")

	result["hd_settings"]["default_ticket_status_set"] = _set_if_field_exists(
		settings,
		"default_ticket_status",
		"New",
	)

	result["hd_settings"]["ticket_reopen_status_set"] = _set_if_field_exists(
		settings,
		"ticket_reopen_status",
		"In Progress",
	)

	result["hd_settings"]["default_priority_set"] = _set_if_field_exists(
		settings,
		"default_priority",
		"Medium",
	)

	settings.save(ignore_permissions=True)

	for fieldname in [
		"default_ticket_status",
		"ticket_reopen_status",
		"default_priority",
	]:
		if settings.meta.has_field(fieldname):
			result["hd_settings"][fieldname] = getattr(settings, fieldname, None)

	frappe.db.commit()
	frappe.clear_cache()

	return result
