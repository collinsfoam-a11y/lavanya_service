import frappe
from frappe.utils import today, now_datetime

@frappe.whitelist()
def get_todays_work():
    """
    Return bucketed tickets for Today's Work command center.
    Groups: critical, important, normal
    """
    base_filters = {"status": ["not in", ["Closed", "Cancelled"]]}
    fields = [
        "name", "subject", "customer_name", "customer_phone",
        "status", "follow_up_stage", "brand", "product_model",
        "priority", "quality_badge", "next_action", "next_followup_date",
        "escalation_level", "customer_informed", "days_open",
        "sla_breached", "followup_overdue", "technician_called",
        "technician_visited", "part_pending", "whatsapp_pending",
    ]

    all_tickets = frappe.get_all("Lavanya Ticket", filters=base_filters, fields=fields)

    critical  = []
    important = []
    normal    = []

    for t in all_tickets:
        if _is_critical(t):
            t["bucket_label"] = _critical_label(t)
            critical.append(t)
        elif _is_important(t):
            t["bucket_label"] = _important_label(t)
            important.append(t)
        else:
            t["bucket_label"] = "Normal"
            normal.append(t)

    return {
        "critical":  critical,
        "important": important,
        "normal":    normal,
        "counts": {
            "critical":  len(critical),
            "important": len(important),
            "normal":    len(normal),
            "total":     len(all_tickets),
        }
    }


def _is_critical(t):
    return (
        t.followup_overdue
        or t.escalation_level in ("L3", "L4")
        or t.quality_badge == "Critical"
        or (not t.customer_informed and t.days_open and t.days_open > 2)
        or t.whatsapp_pending
    )


def _is_important(t):
    nfd = t.next_followup_date
    return (
        (nfd and str(nfd) == today())
        or t.part_pending
        or not t.technician_called
        or not t.technician_visited
        or t.status == "Customer Confirmation Pending"
    )


def _critical_label(t):
    if t.quality_badge == "Critical": return "Critical Quality"
    if t.followup_overdue: return "Overdue Follow-up"
    if t.escalation_level in ("L3","L4"): return f"Escalated {t.escalation_level}"
    if not t.customer_informed: return "Customer Not Informed"
    return "Critical"


def _important_label(t):
    if t.status == "Customer Confirmation Pending": return "Satisfaction Pending"
    if not t.technician_called: return "Tech Call Pending"
    if not t.technician_visited: return "Tech Visit Pending"
    if t.part_pending: return "Part Pending"
    return "Due Today"


@frappe.whitelist()
def get_sidebar_counts():
    """Return counts for sidebar badges."""
    open_f = {"status": ["not in", ["Closed", "Cancelled"]]}
    return {
        "today":    frappe.db.count("Lavanya Ticket", {**open_f, "next_followup_date": today()}),
        "tickets":  frappe.db.count("Lavanya Ticket", open_f),
        "whatsapp": frappe.db.count("Lavanya Whatsapp Message", {"reviewed": 0}),
        "critical": frappe.db.count("Lavanya Ticket", {**open_f, "quality_badge": "Critical"}),
    }
