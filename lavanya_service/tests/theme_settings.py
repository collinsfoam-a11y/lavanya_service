"""H2 theme + Lavanya Service Settings tests."""
import frappe

_PASS = []
_FAIL = []


def _check(name, cond, detail=""):
	(_PASS if cond else _FAIL).append(name)
	print("[{}] {}".format("PASS" if cond else "FAIL", name) + (" | " + str(detail) if detail != "" else ""))


def _reset_settings():
	if not frappe.db.exists("Lavanya Service Settings", "Lavanya Service Settings"):
		return
	doc = frappe.get_doc("Lavanya Service Settings", "Lavanya Service Settings")
	doc.default_theme = "Lavanya Light"
	doc.allow_user_theme_override = 1
	doc.compact_mode_enabled = 0
	doc.large_text_mode_enabled = 0
	doc.high_contrast_mode_enabled = 0
	doc.save(ignore_permissions=True)
	frappe.db.commit()


def test_doctype_exists():
	_check("doctype_exists", frappe.db.exists("DocType", "Lavanya Service Settings"))


def test_default_settings_record_exists():
	_check("default_settings_record_exists", frappe.db.exists("Lavanya Service Settings", "Lavanya Service Settings"))


def test_theme_settings_defaults():
	from lavanya_service.api.ui_settings import get_lavanya_service_settings
	_reset_settings()
	s = get_lavanya_service_settings()
	_check("default_theme_light", s.get("default_theme") == "Lavanya Light", s.get("default_theme"))
	_check("allow_user_theme_override_default_1", s.get("allow_user_theme_override") == 1, s.get("allow_user_theme_override"))
	_check("compact_mode_default_0", s.get("compact_mode_enabled") == 0, s.get("compact_mode_enabled"))
	_check("large_text_default_0", s.get("large_text_mode_enabled") == 0, s.get("large_text_mode_enabled"))
	_check("high_contrast_default_0", s.get("high_contrast_mode_enabled") == 0, s.get("high_contrast_mode_enabled"))


def test_user_theme_override_allowed():
	from lavanya_service.api.ui_settings import get_lavanya_service_settings
	_reset_settings()
	doc = frappe.get_doc("Lavanya Service Settings", "Lavanya Service Settings")
	doc.allow_user_theme_override = 0
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	s = get_lavanya_service_settings()
	_check("user_override_can_be_disabled", s.get("allow_user_theme_override") == 0)


def test_high_contrast_setting_available():
	from lavanya_service.api.ui_settings import get_lavanya_service_settings
	_reset_settings()
	doc = frappe.get_doc("Lavanya Service Settings", "Lavanya Service Settings")
	doc.high_contrast_mode_enabled = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	s = get_lavanya_service_settings()
	_check("high_contrast_setting_available", s.get("high_contrast_mode_enabled") == 1)


def test_compact_mode_setting_available():
	from lavanya_service.api.ui_settings import get_lavanya_service_settings
	_reset_settings()
	doc = frappe.get_doc("Lavanya Service Settings", "Lavanya Service Settings")
	doc.compact_mode_enabled = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	s = get_lavanya_service_settings()
	_check("compact_mode_setting_available", s.get("compact_mode_enabled") == 1)


def test_ui_flags_returned():
	from lavanya_service.api.ui_settings import get_lavanya_service_settings
	_reset_settings()
	s = get_lavanya_service_settings()
	expected = [
		"show_next_action_bar", "show_workflow_timeline", "show_customer_journey_summary",
		"show_followup_quality_badge", "show_mobile_field_mode", "show_penalty_tab",
		"show_notification_tab", "show_erp_status_panel",
	]
	missing = [k for k in expected if k not in s]
	_check("ui_flags_returned", not missing, "missing=" + str(missing))


def test_safety_locks_returned():
	from lavanya_service.api.ui_settings import get_lavanya_service_settings
	_reset_settings()
	s = get_lavanya_service_settings()
	expected = ["live_notifications_blocked", "erp_posting_disabled", "penalty_apply_disabled", "dry_run_mode_on"]
	missing = [k for k in expected if k not in s]
	_check("safety_locks_returned", not missing, "missing=" + str(missing))
	_check("safety_locks_default_blocked", all(s.get(k) == 1 for k in expected))


def test_theme_engine_valid_themes():
	from lavanya_service.setup.ui_settings import THEME_OPTIONS
	expected = ["Lavanya Light", "Lavanya Dark", "Lavanya Blue", "Lavanya Green", "High Contrast", "Compact Counter Mode"]
	actual = [x.strip() for x in THEME_OPTIONS.split("\n") if x.strip()]
	_check("all_themes_present", actual == expected, str(actual))


def test_api_safe_when_no_record():
	from lavanya_service.api.ui_settings import get_lavanya_service_settings
	if frappe.db.exists("Lavanya Service Settings", "Lavanya Service Settings"):
		frappe.delete_doc("Lavanya Service Settings", "Default", ignore_permissions=True)
		frappe.db.commit()
	s = get_lavanya_service_settings()
	_check("api_safe_when_no_record", s.get("default_theme") == "Lavanya Light")
	# recreate for subsequent tests
	from lavanya_service.setup.ui_settings import seed_default_lavanya_service_settings
	seed_default_lavanya_service_settings()


def test_save_settings_requires_manager():
	from lavanya_service.api.ui_settings import save_lavanya_service_settings
	_reset_settings()
	frappe.set_user("Guest")
	try:
		save_lavanya_service_settings({"show_penalty_tab": 0})
		_check("save_rejects_guest", False)
	except frappe.PermissionError:
		_check("save_rejects_guest", True)
	finally:
		frappe.set_user("Administrator")


def test_save_settings_updates_editable_field():
	from lavanya_service.api.ui_settings import save_lavanya_service_settings, get_lavanya_service_settings
	_reset_settings()
	frappe.set_user("Administrator")
	updated = save_lavanya_service_settings({"show_penalty_tab": 0, "show_notification_tab": 0})
	_check("save_updates_flag", updated.get("show_penalty_tab") == 0)
	_check("save_persists_flag", get_lavanya_service_settings().get("show_notification_tab") == 0)


def test_save_settings_ignores_safety_locks():
	from lavanya_service.api.ui_settings import save_lavanya_service_settings, get_lavanya_service_settings
	_reset_settings()
	frappe.set_user("Administrator")
	# Try flipping safety locks through the save endpoint — should be ignored.
	save_lavanya_service_settings({"live_notifications_blocked": 0, "erp_posting_disabled": 0})
	s = get_lavanya_service_settings()
	_check("save_ignores_safety_locks", s.get("live_notifications_blocked") == 1 and s.get("erp_posting_disabled") == 1)


def test_save_settings_rejects_invalid_theme():
	from lavanya_service.api.ui_settings import save_lavanya_service_settings
	_reset_settings()
	frappe.set_user("Administrator")
	try:
		save_lavanya_service_settings({"default_theme": "Invalid Theme"})
		_check("save_rejects_invalid_theme", False)
	except frappe.ValidationError:
		_check("save_rejects_invalid_theme", True)


def test_reset_settings_restores_defaults():
	from lavanya_service.api.ui_settings import save_lavanya_service_settings, reset_lavanya_service_settings, get_lavanya_service_settings
	_reset_settings()
	frappe.set_user("Administrator")
	save_lavanya_service_settings({
		"show_penalty_tab": 0,
		"show_notification_tab": 0,
		"allow_user_theme_override": 0,
		"compact_mode_enabled": 1,
	})
	reset_lavanya_service_settings()
	s = get_lavanya_service_settings()
	_check("reset_restores_flags", s.get("show_penalty_tab") == 1 and s.get("show_notification_tab") == 1)
	_check("reset_restores_theme", s.get("allow_user_theme_override") == 1 and s.get("compact_mode_enabled") == 0)


def test_can_manage_settings():
	from lavanya_service.api.ui_settings import can_manage_lavanya_settings
	frappe.set_user("Administrator")
	_check("admin_can_manage", can_manage_lavanya_settings())


def run():
	_PASS.clear(); _FAIL.clear()
	frappe.set_user("Administrator")
	test_doctype_exists()
	test_default_settings_record_exists()
	test_theme_settings_defaults()
	test_user_theme_override_allowed()
	test_high_contrast_setting_available()
	test_compact_mode_setting_available()
	test_ui_flags_returned()
	test_safety_locks_returned()
	test_theme_engine_valid_themes()
	test_api_safe_when_no_record()
	test_save_settings_requires_manager()
	test_save_settings_updates_editable_field()
	test_save_settings_ignores_safety_locks()
	test_save_settings_rejects_invalid_theme()
	test_reset_settings_restores_defaults()
	test_can_manage_settings()
	_reset_settings()
	print("\nRESULT: pass={} fail={}".format(len(_PASS), len(_FAIL)))
	return {"pass": len(_PASS), "fail": len(_FAIL)}
