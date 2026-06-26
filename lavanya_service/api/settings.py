import frappe
from frappe import _

@frappe.whitelist()
def get_settings():
    """Return current Lavanya Settings (safe fields only)."""
    s = frappe.get_single("Lavanya Settings")
    return {
        "closure_guard":          bool(s.closure_guard_enabled),
        "customer_confirmation":  bool(s.customer_confirmation_required),
        "live_whatsapp":          bool(s.live_whatsapp_enabled),
        "erp_posting":            bool(s.erp_posting_enabled),
        "auto_closure":           bool(s.auto_closure_enabled),
        "penalty":                bool(s.penalty_enabled),
        "brand_sla_days":         s.brand_sla_days or 2,
        "part_sla_days":          s.part_pending_sla_days or 2,
        "confirmation_sla_days":  s.confirmation_sla_days or 1,
        "auto_escalate_days":     s.auto_escalate_after_days or 3,
        "non_response_attempts":  s.non_response_min_attempts or 3,
        "biz_start":              str(s.business_hours_start or "09:00:00")[:5],
        "biz_end":                str(s.business_hours_end or "21:00:00")[:5],
        "bot_mode":               s.whatsapp_bot_mode or "dry_run",
        "wa_webhook_url":         s.wa_webhook_url or "",
        "frappe_crm":             bool(s.frappe_crm_enabled),
        "erpnext":                bool(s.erpnext_enabled),
    }


@frappe.whitelist()
def save_settings(data):
    """Save Lavanya Settings — manager/owner only."""
    import json
    if isinstance(data, str):
        data = json.loads(data)

    if not frappe.has_role(["Service Manager", "Lavanya Owner"]):
        frappe.throw(_("Settings can only be changed by Service Manager or Lavanya Owner."))

    # Dangerous settings — owner only
    dangerous = ["live_whatsapp", "erp_posting", "auto_closure", "penalty"]
    if any(data.get(k) for k in dangerous):
        if not frappe.has_role("Lavanya Owner"):
            frappe.throw(_("Enabling dangerous settings requires Lavanya Owner role."))

    s = frappe.get_single("Lavanya Settings")
    s.closure_guard_enabled         = data.get("closure_guard", True)
    s.customer_confirmation_required = data.get("customer_confirmation", True)
    s.live_whatsapp_enabled          = data.get("live_whatsapp", False)
    s.erp_posting_enabled            = data.get("erp_posting", False)
    s.auto_closure_enabled           = data.get("auto_closure", False)
    s.penalty_enabled                = data.get("penalty", False)
    s.brand_sla_days                 = data.get("brand_sla_days", 2)
    s.part_pending_sla_days          = data.get("part_sla_days", 2)
    s.confirmation_sla_days          = data.get("confirmation_sla_days", 1)
    s.auto_escalate_after_days       = data.get("auto_escalate_days", 3)
    s.non_response_min_attempts      = data.get("non_response_attempts", 3)
    s.whatsapp_bot_mode              = data.get("bot_mode", "dry_run")
    s.wa_webhook_url                 = data.get("wa_webhook_url", "")
    s.frappe_crm_enabled             = data.get("frappe_crm", True)
    s.erpnext_enabled                = data.get("erpnext", False)
    s.save()

    frappe.db.commit()
    return {"status": "saved"}


@frappe.whitelist()
def reset_defaults():
    """Reset all settings to safe defaults — owner only."""
    if not frappe.has_role("Lavanya Owner"):
        frappe.throw(_("Only Lavanya Owner can reset settings to defaults."))

    s = frappe.get_single("Lavanya Settings")
    s.closure_guard_enabled          = 1
    s.customer_confirmation_required = 1
    s.live_whatsapp_enabled          = 0
    s.erp_posting_enabled            = 0
    s.auto_closure_enabled           = 0
    s.penalty_enabled                = 0
    s.whatsapp_bot_mode              = "dry_run"
    s.brand_sla_days                 = 2
    s.save()
    frappe.db.commit()
    return {"status": "reset"}
