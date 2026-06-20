"""Lavanya Service Settings DocType (UI, theme, and safety locks)."""
import frappe
from lavanya_service.setup.masters import ensure_doctype, field

THEME_OPTIONS = "\n".join([
	"Lavanya Light",
	"Lavanya Dark",
	"Lavanya Blue",
	"Lavanya Green",
	"High Contrast",
	"Compact Counter Mode",
])


def create_lavanya_service_settings_doctype():
	if frappe.db.exists("DocType", "Lavanya Service Settings"):
		return "exists"

	doc = frappe.get_doc(
		{
			"doctype": "DocType",
			"name": "Lavanya Service Settings",
			"module": "Lavanya Service",
			"custom": 1,
			"issingle": 1,
			"track_changes": 1,
			"fields": [
				# Section: Theme Preferences
				field("theme_section", "Theme & Accessibility", "Section Break"),
				field("default_theme", "Default Theme", "Select", options=THEME_OPTIONS, default="Lavanya Light"),
				field("allow_user_theme_override", "Allow User Theme Override", "Check", default="1"),
				field("compact_mode_enabled", "Compact Mode Enabled", "Check", default="0"),
				field("large_text_mode_enabled", "Large Text Mode Enabled", "Check", default="0"),
				field("high_contrast_mode_enabled", "High Contrast Mode Enabled", "Check", default="0"),

				# Section: UI Feature Flags
				field("ui_feature_section", "UI Feature Flags", "Section Break"),
				field("show_next_action_bar", "Show Next Action Bar", "Check", default="1"),
				field("show_workflow_timeline", "Show Workflow Timeline", "Check", default="1"),
				field("show_customer_journey_summary", "Show Customer Journey Summary", "Check", default="1"),
				field("show_followup_quality_badge", "Show Follow-up Quality Badge", "Check", default="1"),
				field("show_mobile_field_mode", "Show Mobile Field Mode", "Check", default="1"),
				field("show_penalty_tab", "Show Penalty Tab", "Check", default="1"),
				field("show_notification_tab", "Show Notification Tab", "Check", default="1"),
				field("show_erp_status_panel", "Show ERP Status Panel", "Check", default="0"),

				# Section: Safety Locks (read-only mirrors of actual gates)
				field("safety_lock_section", "Safety Locks", "Section Break"),
				field("live_notifications_blocked", "Live Notifications Blocked", "Check", default="1", read_only=1),
				field("erp_posting_disabled", "ERP Posting Disabled", "Check", default="1", read_only=1),
				field("penalty_apply_disabled", "Penalty Apply Disabled", "Check", default="1", read_only=1),
				field("dry_run_mode_on", "Dry-run Mode On", "Check", default="1", read_only=1),
			],
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return "created"


def seed_default_lavanya_service_settings():
	if not frappe.db.exists("DocType", "Lavanya Service Settings"):
		return
	if frappe.db.exists("Lavanya Service Settings", "Lavanya Service Settings"):
		return

	doc = frappe.get_doc({
		"doctype": "Lavanya Service Settings",
		"name": "Lavanya Service Settings",
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
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()


def create_lavanya_settings():
	create_lavanya_service_settings_doctype()
	seed_default_lavanya_service_settings()
