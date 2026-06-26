import frappe

def after_install():
    """Run once after bench install-app lavanya_service"""
    create_roles()
    create_default_settings()
    frappe.db.commit()

def create_roles():
    for role in ["Service Staff", "Service Manager", "Front Desk", "CRM Manager", "Lavanya Owner"]:
        if not frappe.db.exists("Role", role):
            r = frappe.new_doc("Role")
            r.role_name = role
            r.insert(ignore_permissions=True)

def create_default_settings():
    if not frappe.db.exists("Lavanya Settings", "Lavanya Settings"):
        s = frappe.new_doc("Lavanya Settings")
        # Safety defaults — all dangerous features OFF
        s.closure_guard_enabled = 1
        s.customer_confirmation_required = 1
        s.live_whatsapp_enabled = 0
        s.erp_posting_enabled = 0
        s.penalty_enabled = 0
        s.whatsapp_bot_mode = "dry_run"
        s.insert(ignore_permissions=True)
