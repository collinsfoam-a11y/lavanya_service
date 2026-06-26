import frappe
from frappe.utils import now_datetime, add_days, today

def check_sla_breaches():
    """Flag tickets whose SLA due date has passed"""
    tickets = frappe.get_all(
        "Lavanya Ticket",
        filters={
            "status": ["not in", ["Closed", "Cancelled"]],
            "sla_due_date": ["<", now_datetime()],
            "sla_breached": 0
        },
        fields=["name", "customer", "service_staff"]
    )
    for t in tickets:
        frappe.db.set_value("Lavanya Ticket", t.name, "sla_breached", 1)
    if tickets:
        frappe.db.commit()

def auto_escalate_overdue():
    """Escalate tickets overdue by configured days"""
    settings = frappe.get_single("Lavanya Settings")
    escalate_after = settings.get("auto_escalate_after_days") or 3

    tickets = frappe.get_all(
        "Lavanya Ticket",
        filters={
            "status": ["not in", ["Closed", "Cancelled"]],
            "followup_overdue": 1,
            "escalation_level": ["<", "L4"],
        },
        fields=["name", "escalation_level", "days_open"]
    )
    for t in tickets:
        if (t.days_open or 0) >= escalate_after:
            levels = {"L1": "L2", "L2": "L3", "L3": "L4"}
            new_level = levels.get(t.escalation_level, t.escalation_level)
            frappe.db.set_value("Lavanya Ticket", t.name, "escalation_level", new_level)
    if tickets:
        frappe.db.commit()
