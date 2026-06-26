import frappe
from frappe.utils import today, now_datetime

# Guard flag — prevents on_update from triggering itself recursively
_IN_QUALITY_UPDATE = False

def after_insert(doc, method):
    """Ticket created — set initial SLA due date."""
    _set_sla_due_date(doc)

def on_update(doc, method):
    """
    Ticket saved — recompute quality badge + next action.
    Uses frappe.db.set_value (not doc.save/db_update) to avoid
    re-triggering on_update → infinite recursion.
    """
    global _IN_QUALITY_UPDATE
    if _IN_QUALITY_UPDATE:
        return
    _IN_QUALITY_UPDATE = True
    try:
        from lavanya_service.utils.quality import compute_badge, get_next_action
        badge  = compute_badge(doc.name)
        action = get_next_action(doc.name)
        frappe.db.set_value("Lavanya Ticket", doc.name, {
            "quality_badge": badge,
            "next_action":   action,
        }, update_modified=False)
    finally:
        _IN_QUALITY_UPDATE = False

def on_cancel(doc, method):
    pass

def _set_sla_due_date(doc):
    from frappe.utils import add_days
    # FIXED: service path values must match the Select field options exactly
    sla_map = {
        "Brand Warranty":         2,
        "Brand Paid Service":     2,
        "Local Paid Service":     1,
        "Lavanya Goodwill Service": 1,   # fixed: was "Goodwill"
        "Demo / Installation":    1,
        "In-Showroom Service":    3,
        "Stock Complaint":        5,
    }
    days = sla_map.get(doc.service_path, 2)
    doc.db_set("sla_due_date", add_days(today(), days), update_modified=False)
