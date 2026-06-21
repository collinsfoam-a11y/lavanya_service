import frappe
from frappe.utils import now_datetime, today

"""
H5D: Supplier and Area Performance Log scheduler task.

Advisory/read-only:
- Creates "Supplier Performance Log" and "Area Performance Log" entries.
- Does NOT post ERP entries, accounting entries, penalties, WhatsApp, or SMS.
- Read-only data collection for manager dashboards.
- All log DocTypes must exist (created by setup/supplier_perf_log.py and setup/area_perf_log.py).
"""


def log_supplier_performance():
	"""Daily: compute per-brand SLA compliance from HD Tickets and log to Supplier Performance Log."""
	date_str = today()
	brands = frappe.get_all("Brand Service Master", pluck="name")
	for brand in brands:
		tickets = frappe.get_all(
			"HD Ticket",
			filters={"brand": brand, "status": ("not in", ["Closed", "Cancelled"])},
			fields=["name", "current_service_stage"],
		)
		total = len(tickets)
		if not total:
			continue
		breached = sum(1 for t in tickets if getattr(t, "current_service_stage", "") == "Escalated")
		doc = frappe.get_doc({
			"doctype": "Supplier Performance Log",
			"log_date": date_str,
			"brand": brand,
			"period": "Daily",
			"tickets_total": total,
			"tickets_breached": breached,
			"tickets_on_time": total - breached,
			"sla_compliance_percent": round((total - breached) / total * 100, 1) if total else 0,
		})
		doc.insert(ignore_permissions=True)
	frappe.db.commit()


def log_area_performance():
	"""Daily: compute per-area ticket metrics from HD Tickets and log to Area Performance Log."""
	date_str = today()
	areas = frappe.get_all("HD Ticket", filters={"area": ("is", "set")}, pluck="area", distinct=True)
	for area in areas:
		if not area:
			continue
		tickets = frappe.get_all(
			"HD Ticket",
			filters={"area": area},
			fields=["name", "status", "current_service_stage"],
		)
		total = len(tickets)
		if not total:
			continue
		closed = sum(1 for t in tickets if t.status == "Closed")
		overdue = sum(1 for t in tickets if t.status not in ("Closed", "Cancelled"))
		breached = sum(1 for t in tickets if getattr(t, "current_service_stage", "") == "Escalated")
		doc = frappe.get_doc({
			"doctype": "Area Performance Log",
			"log_date": date_str,
			"area": area,
			"period": "Daily",
			"tickets_total": total,
			"tickets_closed": closed,
			"tickets_overdue": overdue,
			"tickets_breached": breached,
			"closure_rate_percent": round(closed / total * 100, 1) if total else 0,
		})
		doc.insert(ignore_permissions=True)
	frappe.db.commit()
