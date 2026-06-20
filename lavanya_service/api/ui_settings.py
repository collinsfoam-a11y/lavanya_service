import frappe
from frappe import _

MANAGER_ROLES = {"Lavanya Manager", "System Manager"}

_EDITABLE_FIELDS = [
	"default_theme",
	"allow_user_theme_override",
	"compact_mode_enabled",
	"large_text_mode_enabled",
	"high_contrast_mode_enabled",
	"show_next_action_bar",
	"show_workflow_timeline",
	"show_customer_journey_summary",
	"show_followup_quality_badge",
	"show_mobile_field_mode",
	"show_penalty_tab",
	"show_notification_tab",
	"show_erp_status_panel",
]

_ALL_SETTINGS_FIELDS = _EDITABLE_FIELDS + [
	"live_notifications_blocked",
	"erp_posting_disabled",
	"penalty_apply_disabled",
	"dry_run_mode_on",
]

_THEME_OPTIONS = {
	"Lavanya Light",
	"Lavanya Dark",
	"Lavanya Blue",
	"Lavanya Green",
	"High Contrast",
	"Compact Counter Mode",
}

_DEFAULTS = {
	"default_theme": "Lavanya Light",
	"allow_user_theme_override": 1,
	"compact_mode_enabled": 0,
	"large_text_mode_enabled": 0,
	"high_contrast_mode_enabled": 0,
	"show_next_action_bar": 1,
	"show_workflow_timeline": 1,
	"show_customer_journey_summary": 1,
	"show_followup_quality_badge": 1,
	"show_mobile_field_mode": 1,
	"show_penalty_tab": 1,
	"show_notification_tab": 1,
	"show_erp_status_panel": 0,
	"live_notifications_blocked": 1,
	"erp_posting_disabled": 1,
	"penalty_apply_disabled": 1,
	"dry_run_mode_on": 1,
}


def _user_can_manage_settings():
	if frappe.session.user == "Administrator":
		return True
	return bool(MANAGER_ROLES & set(frappe.get_roles(frappe.session.user)))


@frappe.whitelist()
def can_manage_lavanya_settings():
	return _user_can_manage_settings()


@frappe.whitelist()
def get_lavanya_service_settings():
	"""Return Lavanya Service Settings for the SPA. Safe defaults if missing."""
	defaults = dict(_DEFAULTS)

	if not frappe.db.exists("Lavanya Service Settings", "Lavanya Service Settings"):
		return defaults

	doc = frappe.get_doc("Lavanya Service Settings", "Lavanya Service Settings")
	for key in defaults:
		defaults[key] = getattr(doc, key, defaults[key])
	return defaults


@frappe.whitelist()
def save_lavanya_service_settings(values):
	"""Save editable Lavanya Service Settings. Manager-only.

	values: dict of setting key → value. Only _EDITABLE_FIELDS are written;
	safety-lock fields are ignored. The DocType is created if missing.
	"""
	if not _user_can_manage_settings():
		frappe.throw(_("Only Lavanya Managers can change settings."), frappe.PermissionError)

	if not isinstance(values, dict):
		frappe.throw(_("Invalid settings payload."), frappe.ValidationError)

	theme = values.get("default_theme", _DEFAULTS["default_theme"])
	if theme not in _THEME_OPTIONS:
		frappe.throw(_("Invalid theme: {0}").format(theme), frappe.ValidationError)

	if not frappe.db.exists("Lavanya Service Settings", "Lavanya Service Settings"):
		doc = frappe.get_doc({
			"doctype": "Lavanya Service Settings",
			"name": "Lavanya Service Settings",
		})
		doc.insert(ignore_permissions=True)
	else:
		doc = frappe.get_doc("Lavanya Service Settings", "Lavanya Service Settings")

	for key in _EDITABLE_FIELDS:
		if key in values:
			doc.set(key, 1 if values[key] else 0 if isinstance(values[key], bool) else values[key])

	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return get_lavanya_service_settings()


@frappe.whitelist()
def reset_lavanya_service_settings():
	"""Reset all settings to safe defaults. Manager-only."""
	if not _user_can_manage_settings():
		frappe.throw(_("Only Lavanya Managers can reset settings."), frappe.PermissionError)

	if not frappe.db.exists("Lavanya Service Settings", "Lavanya Service Settings"):
		doc = frappe.get_doc({
			"doctype": "Lavanya Service Settings",
			"name": "Lavanya Service Settings",
		})
		doc.insert(ignore_permissions=True)
	else:
		doc = frappe.get_doc("Lavanya Service Settings", "Lavanya Service Settings")

	for key, value in _DEFAULTS.items():
		doc.set(key, value)

	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return get_lavanya_service_settings()
