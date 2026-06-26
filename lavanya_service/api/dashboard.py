import frappe
from frappe.utils import today, add_days, date_diff

@frappe.whitelist()
def get_manager_dashboard(period="Today"):
    """Return all data for Manager Dashboard page."""
    if not frappe.has_permission("Lavanya Ticket", "read"):
        frappe.throw("Not permitted")

    date_from = _period_start(period)
    open_f = {"status": ["not in", ["Closed","Cancelled"]]}

    kpis = {
        "open_tickets":         frappe.db.count("Lavanya Ticket", open_f),
        "overdue_followups":    frappe.db.count("Lavanya Ticket", {**open_f, "followup_overdue": 1}),
        "customer_not_informed":frappe.db.count("Lavanya Ticket", {**open_f, "customer_informed": 0}),
        "closed_today":         frappe.db.count("Lavanya Ticket", {"status": "Closed", "closed_on": [">=", today()]}),
        "escalated":            frappe.db.count("Lavanya Ticket", {**open_f, "escalation_level": ["in", ["L3","L4"]]}),
        "satisfaction_rate":    _satisfaction_rate(),
    }

    escalations = frappe.get_all(
        "Lavanya Ticket",
        filters={**open_f, "escalation_level": ["in", ["L3","L4"]]},
        fields=["name","customer_name","product_model","brand","escalation_level","days_open","quality_badge"],
        order_by="days_open desc",
        limit=20
    )

    brand_scores = _brand_delay_scores()
    staff_perf   = _staff_performance(date_from)
    part_pending = frappe.get_all(
        "Lavanya Ticket",
        filters={**open_f, "part_pending": 1},
        fields=["name","customer_name","part_name","part_expected_date","part_received","days_open"],
        order_by="days_open desc",
        limit=15
    )

    safety_locks = _safety_lock_status()

    return {
        "kpis":         kpis,
        "escalations":  escalations,
        "brand_scores": brand_scores,
        "staff_perf":   staff_perf,
        "part_pending": part_pending,
        "safety_locks": safety_locks,
    }


def _period_start(period):
    from frappe.utils import add_days, today
    if period == "Today":      return today()
    if period == "This Week":  return add_days(today(), -7)
    if period == "This Month": return add_days(today(), -30)
    return today()


def _satisfaction_rate():
    total = frappe.db.count("Lavanya Ticket", {"status": "Closed"})
    if not total: return 0
    satisfied = frappe.db.count("Lavanya Ticket", {"status": "Closed", "customer_satisfaction": "Satisfied"})
    return round(satisfied / total * 100, 1)


def _brand_delay_scores():
    brands = frappe.get_all("Lavanya Brand Master", fields=["name"])
    result = []
    for b in brands:
        open_c = frappe.db.count("Lavanya Ticket", {"brand": b.name, "status": ["not in",["Closed","Cancelled"]]})
        overdue = frappe.db.count("Lavanya Ticket", {"brand": b.name, "followup_overdue": 1, "status": ["not in",["Closed","Cancelled"]]})
        result.append({"name": b.name, "open": open_c, "overdue": overdue})
    return sorted(result, key=lambda x: x["open"], reverse=True)


def _staff_performance(date_from):
    # FIXED: User role is in Has Role child table, not a direct User field
    staff = frappe.db.sql("""
        SELECT DISTINCT u.name, u.full_name
        FROM `tabUser` u
        JOIN `tabHas Role` r ON r.parent = u.name
        WHERE r.role IN ('Service Staff', 'Front Desk')
          AND u.enabled = 1
    """, as_dict=True)

    result = []
    for s in staff:
        logs = frappe.db.count("Lavanya Followup Log", {
            "staff":    s.name,
            "creation": [">=", date_from],
        })
        overdue_assigned = frappe.db.count("Lavanya Ticket", {
            "service_staff":    s.name,
            "followup_overdue": 1,
            "status": ["not in", ["Closed", "Cancelled"]],
        })
        compliance = max(0, round((1 - overdue_assigned / max(logs, 1)) * 100))
        result.append({
            "name":       s.full_name or s.name,
            "logs":       logs,
            "overdue":    overdue_assigned,
            "compliance": compliance,
        })
    return sorted(result, key=lambda x: x["compliance"], reverse=True)


def _safety_lock_status():
    s = frappe.get_single("Lavanya Settings")
    return {
        "closure_guard":      bool(s.closure_guard_enabled),
        "customer_confirm":   bool(s.customer_confirmation_required),
        "live_whatsapp":      bool(s.live_whatsapp_enabled),
        "erp_posting":        bool(s.erp_posting_enabled),
        "penalty":            bool(s.penalty_enabled),
        "whatsapp_bot_mode":  s.whatsapp_bot_mode or "dry_run",
    }


@frappe.whitelist()
def export_report():
    """Generate and return a CSV download URL. FIXED: correct file_manager import."""
    import csv, io
    from frappe.utils.file_manager import save_file  # correct import path

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Ticket", "Customer", "Status", "Brand",
                     "Quality Badge", "Days Open", "Escalation"])
    tickets = frappe.get_all(
        "Lavanya Ticket",
        fields=["name", "customer_name", "status", "brand",
                "quality_badge", "days_open", "escalation_level"],
        limit=500,
    )
    for t in tickets:
        writer.writerow([
            t.name, t.customer_name, t.status, t.brand,
            t.quality_badge, t.days_open, t.escalation_level,
        ])

    csv_bytes = output.getvalue().encode("utf-8")
    saved = save_file(
        fname="lavanya_report.csv",
        content=csv_bytes,
        dt="Lavanya Settings",
        dn="Lavanya Settings",
        is_private=0,
    )
    return saved.file_url
