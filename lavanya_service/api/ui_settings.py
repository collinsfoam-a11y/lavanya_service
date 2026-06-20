import frappe


@frappe.whitelist()
def get_lavanya_service_settings():
	"""Return Lavanya Service Settings for the SPA. Safe defaults if missing."""
	defaults = {
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

	if not frappe.db.exists("Lavanya Service Settings", "Lavanya Service Settings"):
		return defaults

	doc = frappe.get_doc("Lavanya Service Settings", "Lavanya Service Settings")
	for key in defaults:
		defaults[key] = getattr(doc, key, defaults[key])
	return defaults
