import frappe
from lavanya_service.workflow.today_work import get_today_work_data
from lavanya_service.reports.manager_dashboard import (
	get_daily_follow_up_report,
	get_brand_pending_report,
	get_waiting_on_customer_report,
	get_waiting_on_part_report,
	get_product_at_store_aging_report,
	get_ready_for_pickup_report,
	get_closure_report,
	get_repeat_complaint_report,
	get_warranty_override_report,
	get_cancelled_tickets_report,
	get_escalation_report,
)

@frappe.whitelist()
def get_manager_dashboard(from_date=None, to_date=None):
	user = frappe.session.user
	
	if not frappe.has_permission("HD Ticket", "read", user=user):
		frappe.throw("Not permitted to read HD Ticket.", frappe.PermissionError)

	# Fetch base data
	work_data = get_today_work_data(user=user, include_counts=True, limit=200)
	counts = {g["key"]: g.get("count", 0) for g in work_data.get("groups", [])}

	summary = {
		"new_today": counts.get("new_complaints", 0),
		"overdue_followups": counts.get("overdue_follow_up", 0),
		"due_today": counts.get("due_today", 0),
		"registration_recommended": counts.get("registration_recommended", 0),
		"registration_pending": counts.get("registration_pending", 0),
		"waiting_on_customer": counts.get("waiting_on_customer", 0),
		"waiting_on_part": counts.get("waiting_on_part", 0),
		"ready_for_pickup": counts.get("ready_for_pickup", 0),
		"product_receipt_missing": counts.get("product_receipt_missing", 0),
		"closure_pending": counts.get("closure_pending", 0),
	}

	# Some reports might bypass normal group limits but must respect read permission implicitly
	# Since these use raw SQL, we must consider permission. 
	# The raw SQL in manager_dashboard.py does not do doc-level permission checks right now,
	# but `HD Ticket` read permission is required above.
	# For strict role checks, we will return full counts if they can access these reports.
	
	roles = set(frappe.get_roles(user))
	is_manager_or_coordinator = bool(roles.intersection({"System Manager", "Lavanya Manager", "Lavanya Service Coordinator", "Lavanya Viewer"}))
	
	if is_manager_or_coordinator:
		summary["products_in_store"] = len(get_product_at_store_aging_report())
		summary["closed_today"] = len(get_closure_report(from_date, to_date))
		summary["repeat_complaints"] = len(get_repeat_complaint_report())
		summary["warranty_overrides"] = len(get_warranty_override_report())
	else:
		# Front Desk / Agent etc should not see full organizational stats for these if not permitted.
		# For this phase, we default to 0 for non-managers to be safe.
		summary["products_in_store"] = 0
		summary["closed_today"] = 0
		summary["repeat_complaints"] = 0
		summary["warranty_overrides"] = 0

	return {
		"summary": summary,
		"sections": []
	}


# ──────────────────────────────────────────────────────────────────────────
# Report catalog — drill-down "Reports Center". Each entry reuses an existing
# reports.manager_dashboard function so a card's count always matches the list
# it opens. `columns` drives a generic table on the frontend; `manager_only`
# gates the org-wide reports the same way get_manager_dashboard does.
# ──────────────────────────────────────────────────────────────────────────
_MANAGER_ROLES = {"System Manager", "Lavanya Manager", "Lavanya Service Coordinator", "Lavanya Viewer"}

REPORTS = {
	"escalations": {
		"title": "Escalations",
		"description": "SLA failed, or follow-up overdue 3+ days — needs management action",
		"icon": "priority_high",
		"fn": get_escalation_report,
		"manager_only": True,
		"columns": [
			("ticket", "Ticket"), ("customer_name", "Customer"), ("brand", "Brand"),
			("status", "Status"), ("agreement_status", "SLA"),
			("overdue_days", "Overdue (d)"), ("next_follow_up_date", "Follow-up"),
		],
	},
	"daily_follow_up": {
		"title": "Daily Follow-Up",
		"description": "Active tickets needing follow-up today or overdue",
		"icon": "event_available",
		"fn": get_daily_follow_up_report,
		"manager_only": False,
		"columns": [
			("ticket", "Ticket"), ("customer_name", "Customer"), ("phone_1", "Phone"),
			("brand", "Brand"), ("status", "Status"),
			("next_follow_up_date", "Follow-up"), ("age_days", "Age (d)"),
		],
	},
	"brand_pending": {
		"title": "Brand Pending",
		"description": "Awaiting brand registration, parts or authorization",
		"icon": "verified",
		"fn": get_brand_pending_report,
		"manager_only": False,
		"columns": [
			("ticket", "Ticket"), ("customer_name", "Customer"), ("brand", "Brand"),
			("warranty_status", "Warranty"), ("brand_ticket_number", "Brand Ref"),
			("registration_date", "Registered"), ("next_follow_up_date", "Follow-up"),
		],
	},
	"waiting_on_customer": {
		"title": "Waiting on Customer",
		"description": "Paused pending customer feedback, approval or pickup",
		"icon": "hourglass_top",
		"fn": get_waiting_on_customer_report,
		"manager_only": False,
		"columns": [
			("ticket", "Ticket"), ("customer_name", "Customer"), ("phone_1", "Phone"),
			("pending_reason", "Reason"), ("next_follow_up_date", "Follow-up"),
			("age_days", "Age (d)"),
		],
	},
	"waiting_on_part": {
		"title": "Waiting on Part",
		"description": "Held for spare parts or service-center approval",
		"icon": "build",
		"fn": get_waiting_on_part_report,
		"manager_only": False,
		"columns": [
			("ticket", "Ticket"), ("customer_name", "Customer"), ("brand", "Brand"),
			("product_item", "Product"), ("pending_reason", "Reason"),
			("next_follow_up_date", "Follow-up"), ("age_days", "Age (d)"),
		],
	},
	"ready_for_pickup": {
		"title": "Ready for Pickup",
		"description": "Repaired products awaiting customer collection",
		"icon": "inventory_2",
		"fn": get_ready_for_pickup_report,
		"manager_only": False,
		"columns": [
			("ticket", "Ticket"), ("customer_name", "Customer"), ("phone_1", "Phone"),
			("brand", "Brand"), ("product_type", "Product"),
			("service_product_receipt", "Receipt"), ("modified", "Updated"),
		],
	},
	"product_at_store_aging": {
		"title": "Product-at-Store Aging",
		"description": "Products in custody beyond standard processing time",
		"icon": "warehouse",
		"fn": get_product_at_store_aging_report,
		"manager_only": True,
		"columns": [
			("ticket", "Ticket"), ("customer_name", "Customer"), ("brand", "Brand"),
			("product_item", "Product"), ("current_custody_status", "Custody"),
			("receipt_date", "Received"), ("age_days", "Age (d)"),
		],
	},
	"closure": {
		"title": "Closure Report",
		"description": "Tickets resolved or closed today",
		"icon": "task_alt",
		"fn": get_closure_report,
		"manager_only": True,
		"columns": [
			("ticket", "Ticket"), ("customer_name", "Customer"), ("brand", "Brand"),
			("status", "Status"), ("closure_type", "Closure"),
			("closed_by", "Closed By"), ("closure_date", "Closed On"),
		],
	},
	"repeat_complaint": {
		"title": "Repeat Complaints",
		"description": "Items returned for service more than once",
		"icon": "repeat",
		"fn": get_repeat_complaint_report,
		"manager_only": True,
		"columns": [
			("ticket", "Ticket"), ("previous_ticket_link", "Previous"),
			("customer_name", "Customer"), ("brand", "Brand"),
			("model_no", "Model"), ("status", "Status"), ("closure_type", "Closure"),
		],
	},
	"warranty_override": {
		"title": "Warranty Overrides",
		"description": "In-warranty tickets bypassing brand registration",
		"icon": "gavel",
		"fn": get_warranty_override_report,
		"manager_only": True,
		"columns": [
			("ticket", "Ticket"), ("customer_name", "Customer"), ("brand", "Brand"),
			("warranty_status", "Warranty"), ("brand_ticket_number", "Brand Ref"),
			("brand_registration_override_reason", "Override Reason"), ("status", "Status"),
		],
	},
}


def _can_view(meta, roles):
	"""A report is visible if it isn't manager-only, or the user has a manager role."""
	return (not meta["manager_only"]) or bool(roles.intersection(_MANAGER_ROLES))


@frappe.whitelist()
def get_report_catalog():
	"""List the reports the current user may open, each with a live row count."""
	user = frappe.session.user
	if not frappe.has_permission("HD Ticket", "read", user=user):
		frappe.throw("Not permitted to read HD Ticket.", frappe.PermissionError)

	roles = set(frappe.get_roles(user))
	catalog = []
	for key, meta in REPORTS.items():
		if not _can_view(meta, roles):
			continue
		try:
			count = len(meta["fn"]())
		except Exception:
			count = None
		catalog.append({
			"key": key,
			"title": meta["title"],
			"description": meta["description"],
			"icon": meta["icon"],
			"count": count,
		})
	return {"reports": catalog}


@frappe.whitelist()
def get_report_trends(days=30):
	"""30-day (configurable) created-vs-resolved daily series + window totals.
	Org-wide analytics — manager-gated; returns allowed:False for others."""
	user = frappe.session.user
	if not frappe.has_permission("HD Ticket", "read", user=user):
		frappe.throw("Not permitted to read HD Ticket.", frappe.PermissionError)

	if not set(frappe.get_roles(user)).intersection(_MANAGER_ROLES):
		return {"allowed": False, "series": [], "totals": {}}

	days = min(max(frappe.utils.cint(days) or 30, 7), 90)
	start = frappe.utils.getdate(frappe.utils.add_days(frappe.utils.today(), -(days - 1)))

	created = {
		str(d): int(c)
		for d, c in frappe.db.sql(
			"SELECT DATE(creation), COUNT(*) FROM `tabHD Ticket` WHERE DATE(creation) >= %s GROUP BY DATE(creation)",
			(start,),
		)
	}
	resolved = {
		str(d): int(c)
		for d, c in frappe.db.sql(
			"SELECT DATE(resolution_date), COUNT(*) FROM `tabHD Ticket` "
			"WHERE resolution_date IS NOT NULL AND DATE(resolution_date) >= %s GROUP BY DATE(resolution_date)",
			(start,),
		)
	}

	series = []
	for i in range(days):
		ds = str(frappe.utils.getdate(frappe.utils.add_days(start, i)))
		series.append({"date": ds, "created": created.get(ds, 0), "resolved": resolved.get(ds, 0)})

	return {
		"allowed": True,
		"days": days,
		"series": series,
		"totals": {
			"created": sum(p["created"] for p in series),
			"resolved": sum(p["resolved"] for p in series),
		},
	}


@frappe.whitelist()
def get_report_breakdowns():
	"""Counts by status and by closure type (closed/resolved tickets).
	Org-wide analytics — manager-gated."""
	user = frappe.session.user
	if not frappe.has_permission("HD Ticket", "read", user=user):
		frappe.throw("Not permitted to read HD Ticket.", frappe.PermissionError)

	if not set(frappe.get_roles(user)).intersection(_MANAGER_ROLES):
		return {"allowed": False, "by_status": [], "by_closure_type": []}

	by_status = frappe.db.sql(
		"SELECT status, COUNT(*) FROM `tabHD Ticket` GROUP BY status ORDER BY COUNT(*) DESC",
	)
	by_closure = frappe.db.sql(
		"SELECT IFNULL(NULLIF(closure_type, ''), '(unset)'), COUNT(*) FROM `tabHD Ticket` "
		"WHERE status IN ('Closed', 'Resolved') GROUP BY closure_type ORDER BY COUNT(*) DESC",
	)
	return {
		"allowed": True,
		"by_status": [{"label": k, "count": int(v)} for k, v in by_status],
		"by_closure_type": [{"label": k, "count": int(v)} for k, v in by_closure],
	}


@frappe.whitelist()
def get_report(report):
	"""Return the column spec + rows for a single report (the drill-down list)."""
	user = frappe.session.user
	if not frappe.has_permission("HD Ticket", "read", user=user):
		frappe.throw("Not permitted to read HD Ticket.", frappe.PermissionError)

	meta = REPORTS.get(report)
	if not meta:
		frappe.throw("Unknown report.", frappe.DoesNotExistError)

	roles = set(frappe.get_roles(user))
	if not _can_view(meta, roles):
		frappe.throw("Not permitted to view this report.", frappe.PermissionError)

	rows = meta["fn"]()
	columns = [{"key": k, "label": label} for (k, label) in meta["columns"]]
	return {
		"key": report,
		"title": meta["title"],
		"description": meta["description"],
		"icon": meta["icon"],
		"columns": columns,
		"rows": rows,
		"count": len(rows),
	}
