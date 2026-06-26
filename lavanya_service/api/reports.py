import frappe
from frappe.utils import today, add_days

REPORT_FIELDS = {
    "overdue_followups": {
        "fields": ["name","subject","customer_name","brand","product_model","days_open","escalation_level","quality_badge","next_action","next_followup_date"],
        "filters": [["followup_overdue","=",1]],
    },
    "open_by_stage": {
        "fields": ["name","subject","customer_name","status","follow_up_stage","brand","days_open","quality_badge"],
        "filters": [["status","not in",["Closed","Cancelled"]]],
    },
    "brand_delay": {
        "fields": ["brand","name","customer_name","days_open","escalation_level","sla_breached"],
        "filters": [["status","not in",["Closed","Cancelled"]]],
    },
    "not_informed": {
        "fields": ["name","subject","customer_name","brand","days_open","follow_up_stage","next_followup_date"],
        "filters": [["customer_informed","=",0],["status","not in",["Closed","Cancelled"]]],
    },
    "part_aging": {
        "fields": ["name","customer_name","brand","part_name","part_expected_date","part_received","days_open"],
        "filters": [["part_pending","=",1],["status","not in",["Closed","Cancelled"]]],
    },
    "satisfaction": {
        "fields": ["name","customer_name","brand","closed_on","customer_satisfaction","days_open","closure_type"],
        "filters": [["status","=","Closed"]],
    },
    "repeat_complaints": {
        "fields": ["name","customer_name","customer_phone","brand","product_model","days_open","quality_badge"],
        "filters": [["status","not in",["Closed","Cancelled"]]],
    },
    "crm_opportunities": {
        "fields": ["name","subject","customer_name","brand","days_open","escalation_level"],
        "filters": [["status","not in",["Closed","Cancelled"]],["warranty_status","=","Out of Warranty"]],
    },
}

PERIOD_MAP = {
    "Today":         0,
    "This Week":     7,
    "This Month":    30,
    "Last 3 Months": 90,
}

@frappe.whitelist()
def get_report_data(report_key, period="This Month"):
    if not frappe.has_permission("Lavanya Ticket", "read"):
        frappe.throw("Not permitted")

    if report_key not in REPORT_FIELDS:
        return {"rows": [], "total": 0}

    cfg = REPORT_FIELDS[report_key]
    filters = list(cfg["filters"])

    days = PERIOD_MAP.get(period, 30)
    if days > 0:
        filters.append(["creation", ">=", add_days(today(), -days)])

    rows = frappe.get_all(
        "Lavanya Ticket",
        fields  = cfg["fields"],
        filters = filters,
        order_by= "creation desc",
        limit   = 500,
    )

    # Aggregate for brand_delay
    if report_key == "brand_delay":
        agg = {}
        for r in rows:
            b = r.brand or "Unknown"
            if b not in agg:
                agg[b] = {"brand": b, "open_tickets": 0, "overdue": 0, "sla_breached": 0}
            agg[b]["open_tickets"] += 1
            if r.get("sla_breached"): agg[b]["sla_breached"] += 1
        rows = list(agg.values())

    return {"rows": rows, "total": len(rows)}
