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
	get_stage_missing_report,
	get_customer_promise_breach_report,
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

	roles = set(frappe.get_roles(user))
	is_manager_or_coordinator = bool(roles.intersection({"System Manager", "Lavanya Manager", "Lavanya Service Coordinator", "Lavanya Viewer"}))
	
	if is_manager_or_coordinator:
		summary["products_in_store"] = len(get_product_at_store_aging_report())
		summary["closed_today"] = len(get_closure_report(from_date, to_date))
		summary["repeat_complaints"] = len(get_repeat_complaint_report())
		summary["warranty_overrides"] = len(get_warranty_override_report())
	else:
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
	"promise_breach": {
		"title": "Customer Promise Breach",
		"description": "Promised-update time passed and not marked kept — handle first",
		"icon": "running_with_errors",
		"fn": get_customer_promise_breach_report,
		"manager_only": True,
		"columns": [
			("ticket", "Ticket"), ("customer_name", "Customer"), ("brand", "Brand"),
			("current_service_stage", "Stage"), ("customer_promised_update_at", "Promised"),
			("hours_late", "Late (h)"),
		],
	},
	"stage_missing": {
		"title": "Stage Missing",
		"description": "Active tickets without a service stage — assign so they follow the flow",
		"icon": "rule",
		"fn": get_stage_missing_report,
		"manager_only": True,
		"columns": [
			("ticket", "Ticket"), ("customer_name", "Customer"), ("ticket_type", "Ticket Type"),
			("service_flow_type", "Flow"), ("status", "Status"), ("creation", "Created"),
		],
	},
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


def _check_manager(user=None):
	"""Raise if user is not a manager-level role."""
	roles = set(frappe.get_roles(user or frappe.session.user))
	if not roles.intersection(_MANAGER_ROLES):
		frappe.throw("Not permitted.", frappe.PermissionError)


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


# ═══════════════════════════════════════════════════════════════════════════
# NEW: Executive Summary — one call for all manager-level counts
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_executive_summary():
	"""Return all executive-level counts for the dashboard summary cards."""
	_check_manager()

	from frappe.utils import today

	cards = []

	# 1. Open tickets
	total = frappe.db.count("HD Ticket", {"status": ("not in", ["Closed", "Cancelled"])})
	cards.append({"key": "open_tickets", "label": "Open Tickets", "count": total, "color": "primary", "icon": "confirmation_number"})

	# 2. Overdue follow-ups
	overdue = frappe.db.count("HD Ticket", {
		"status": ("not in", ["Closed", "Cancelled"]),
		"next_follow_up_date": ("<", today()),
	})
	cards.append({"key": "overdue_followup", "label": "Overdue Follow-up", "count": overdue, "color": "error", "icon": "warning"})

	# 3. No technician update
	no_tech = frappe.db.sql("""
		SELECT COUNT(*) FROM `tabHD Ticket`
		WHERE status NOT IN ('Closed', 'Cancelled')
		AND IFNULL(next_action, '') IN ('Verify Technician Called', 'Verify Technician Visit', 'Schedule Technician Visit')
		AND IFNULL(last_followup_at, '') = ''
	""")[0][0] if frappe.get_meta("HD Ticket").has_field("next_action") else 0
	cards.append({"key": "no_technician_update", "label": "No Tech Update", "count": no_tech, "color": "error", "icon": "cell_tower"})

	# 4. Customer not informed
	not_informed = frappe.db.count("HD Ticket", {
		"status": ("not in", ["Closed", "Cancelled"]),
		"customer_informed": ("!=", "Yes"),
	})
	cards.append({"key": "customer_not_informed", "label": "Customer Not Informed", "count": not_informed, "color": "warning", "icon": "campaign"})

	# 5. Escalated cases
	escalated = len(get_escalation_report())
	cards.append({"key": "escalated_cases", "label": "Escalated Cases", "count": escalated, "color": "error", "icon": "escalator_warning"})

	# 6. Waiting on part
	part = len(get_waiting_on_part_report())
	cards.append({"key": "waiting_on_part", "label": "Waiting on Part", "count": part, "color": "warning", "icon": "build"})

	# 7. Customer satisfaction pending
	sat_pending = frappe.db.sql("""
		SELECT COUNT(*) FROM `tabHD Ticket`
		WHERE status = 'Resolved'
		AND IFNULL(customer_satisfaction_status, '') NOT IN ('Satisfied', '')
	""")[0][0] if frappe.get_meta("HD Ticket").has_field("customer_satisfaction_status") else 0
	cards.append({"key": "satisfaction_pending", "label": "Satisfaction Pending", "count": sat_pending, "color": "secondary", "icon": "feedback"})

	# 8. Supplier payment blocked
	blocked = 0
	if frappe.db.exists("DocType", "Supplier Payment Block"):
		try:
			blocked = frappe.db.sql("SELECT COUNT(*) FROM `tabSupplier Payment Block` WHERE payment_block_status = 'Blocked'")[0][0]
		except Exception:
			blocked = 0
	cards.append({"key": "supplier_payment_blocked", "label": "Payment Blocked", "count": blocked, "color": "error", "icon": "block"})

	# 9. Replacement pending
	repl = frappe.db.count("HD Ticket", {
		"status": ("not in", ["Closed", "Cancelled"]),
		"service_flow_type": "Replacement / Exchange",
	})
	cards.append({"key": "replacement_pending", "label": "Replacement Pending", "count": repl, "color": "warning", "icon": "swap_horiz"})

	# 10. Return pending
	ret = frappe.db.count("HD Ticket", {
		"status": ("not in", ["Closed", "Cancelled"]),
		"service_flow_type": "Refund Case",
	})
	cards.append({"key": "return_pending", "label": "Return Pending", "count": ret, "color": "warning", "icon": "undo"})

	# 11. Stock complaint pending
	stock = frappe.db.count("HD Ticket", {
		"status": ("not in", ["Closed", "Cancelled"]),
		"service_flow_type": "Stock Complaint",
	})
	cards.append({"key": "stock_complaint_pending", "label": "Stock Complaint Pending", "count": stock, "color": "secondary", "icon": "inventory"})

	return {"cards": cards, "total_open": total}


# ═══════════════════════════════════════════════════════════════════════════
# NEW: Brand / Service Center Delay — aggregated per brand
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_brand_delay_aggregated():
	"""Per-brand: open, overdue, no-update, avg days, escalated, part pending."""
	_check_manager()

	from frappe.utils import today

	brands = frappe.db.sql("""
		SELECT
			IFNULL(brand, '(no brand)') as brand,
			COUNT(*) as open_cases,
			SUM(CASE WHEN next_follow_up_date < %s THEN 1 ELSE 0 END) as overdue,
			SUM(CASE WHEN IFNULL(customer_informed, '') != 'Yes' THEN 1 ELSE 0 END) as no_tech_update,
			ROUND(AVG(DATEDIFF(%s, creation)), 0) as avg_days,
			SUM(CASE WHEN agreement_status = 'Failed' OR escalation_level != 'None' THEN 1 ELSE 0 END) as escalated,
			SUM(CASE WHEN status = 'Waiting on Part / Approval' THEN 1 ELSE 0 END) as part_pending
		FROM `tabHD Ticket`
		WHERE status NOT IN ('Closed', 'Cancelled')
		GROUP BY brand
		ORDER BY overdue DESC
	""", (today(), today()), as_dict=True)

	return {"brands": brands}


# ═══════════════════════════════════════════════════════════════════════════
# NEW: Supplier Control — payment block + active stock complaints
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_supplier_control():
	"""Supplier control view: active stock complaints, payment block status."""
	_check_manager()

	from frappe.utils import today

	# Active stock complaints per supplier (brand)
	stock_rows = frappe.db.sql("""
		SELECT
			IFNULL(brand, '(no brand)') as brand,
			COUNT(*) as active_stock_complaints,
			SUM(CASE WHEN next_follow_up_date < %s THEN 1 ELSE 0 END) as overdue_complaints,
			SUM(CASE WHEN escalation_level != 'None' THEN 1 ELSE 0 END) as escalated
		FROM `tabHD Ticket`
		WHERE status NOT IN ('Closed', 'Cancelled')
		AND service_flow_type = 'Stock Complaint'
		GROUP BY brand
		ORDER BY active_stock_complaints DESC
	""", (today(),), as_dict=True)

	# Payment blocks
	payment_blocks = frappe.db.get_all("Supplier Payment Block",
		fields=["name", "brand", "status", "blocked_at", "block_reason", "ticket"],
		order_by="creation desc") if frappe.db.exists("DocType", "Supplier Payment Block") else []

	# SLA breach count per brand
	sla_breaches = frappe.db.sql("""
		SELECT brand, SUM(tickets_breached) as breaches
		FROM `tabSupplier Performance Log`
		GROUP BY brand
	""", as_dict=True) if frappe.db.exists("DocType", "Supplier Performance Log") else []

	# Merge into unified view
	brands = set()
	brand_data = {}

	for r in stock_rows:
		b = r["brand"]
		brands.add(b)
		brand_data[b] = {"brand": b, "active_stock_complaints": r["active_stock_complaints"],
			"overdue_complaints": r["overdue_complaints"], "escalated": r["escalated"],
			"payment_blocked": False, "block_reason": "", "blocked_at": "",
			"sla_breaches": 0, "has_block_record": False}

	for b in payment_blocks:
		bname = b.get("brand") or "(no brand)"
		bd = brand_data.get(bname)
		if not bd:
			bd = {"brand": bname, "active_stock_complaints": 0, "overdue_complaints": 0,
				"escalated": 0, "sla_breaches": 0}
			brand_data[bname] = bd
		if b.get("status") == "Blocked":
			bd["payment_blocked"] = True
			bd["block_reason"] = b.get("block_reason", "")
			bd["blocked_at"] = str(b.get("blocked_at", ""))
		bd["has_block_record"] = True

	for b in sla_breaches:
		bname = b.get("brand") or "(no brand)"
		bd = brand_data.get(bname)
		if not bd:
			bd = {"brand": bname, "active_stock_complaints": 0, "overdue_complaints": 0,
				"escalated": 0, "payment_blocked": False, "block_reason": "", "blocked_at": ""}
			brand_data[bname] = bd
		bd["sla_breaches"] = b.get("breaches", 0)

	return {"suppliers": list(brand_data.values())}


# ═══════════════════════════════════════════════════════════════════════════
# NEW: Follow-up Quality — measure whether Lavanya proves follow-up properly
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_followup_quality():
	"""Follow-up quality metrics for manager review."""
	_check_manager()

	from frappe.utils import today

	active = "status NOT IN ('Closed', 'Cancelled')"

	# Tickets without any follow-up logged
	no_followup = frappe.db.sql(f"""
		SELECT COUNT(*) FROM `tabHD Ticket`
		WHERE {active}
		AND IFNULL(last_followup_summary, '') = ''
		AND IFNULL(last_followup_at, '') = ''
	""")[0][0] if frappe.get_meta("HD Ticket").has_field("last_followup_summary") else 0

	# Customer not informed
	not_informed = frappe.db.count("HD Ticket", {
		"status": ("not in", ["Closed", "Cancelled"]),
		"customer_informed": ("!=", "Yes"),
	})

	# Promise breached
	promise_breach = frappe.db.count("HD Ticket", {
		"status": ("not in", ["Closed", "Cancelled"]),
		"customer_promise_status": "Breached",
	}) if frappe.get_meta("HD Ticket").has_field("customer_promise_status") else 0

	# No technician update (tickets where tech action is expected but no update)
	no_tech = frappe.db.sql(f"""
		SELECT COUNT(*) FROM `tabHD Ticket`
		WHERE {active}
		AND IFNULL(next_action, '') IN ('Verify Technician Called', 'Verify Technician Visit', 'Schedule Technician Visit')
		AND IFNULL(last_followup_at, '') = ''
	""")[0][0] if frappe.get_meta("HD Ticket").has_field("next_action") else 0

	# Closed with satisfaction
	closed_sat = frappe.db.sql("""
		SELECT COUNT(*) FROM `tabHD Ticket`
		WHERE status = 'Closed'
		AND IFNULL(customer_satisfaction_status, '') = 'Satisfied'
	""")[0][0] if frappe.get_meta("HD Ticket").has_field("customer_satisfaction_status") else 0

	# Closed total (for ratio)
	closed_total = frappe.db.count("HD Ticket", {"status": "Closed"})

	satisfaction_pct = round((closed_sat / closed_total * 100), 1) if closed_total else 0

	return {
		"no_followup": no_followup,
		"customer_not_informed": not_informed,
		"promise_breach": promise_breach,
		"no_technician_update": no_tech,
		"closed_with_satisfaction": closed_sat,
		"closed_total": closed_total,
		"satisfaction_pct": satisfaction_pct,
	}


# ═══════════════════════════════════════════════════════════════════════════
# NEW: Aging buckets — breakdown by service flow type and age
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_aging_data():
	"""Aging buckets for active tickets: 0-1d, 2-3d, 4-7d, 8-15d, 15+d."""
	_check_manager()

	from frappe.utils import today

	buckets = [
		("0-1 days", 0, 1),
		("2-3 days", 2, 3),
		("4-7 days", 4, 7),
		("8-15 days", 8, 15),
		("15+ days", 16, 9999),
	]

	# H4: Use stage-relative date for aging — COALESCE(last_followup_at,
	# stage_due_at, creation) gives the most meaningful "time since last action"
	# rather than always measuring from ticket creation.
	flow_types = frappe.db.sql("""
		SELECT service_flow_type,
			DATEDIFF(%s, COALESCE(DATE(last_followup_at), DATE(stage_due_at), DATE(creation))) as age_days
		FROM `tabHD Ticket`
		WHERE status NOT IN ('Closed', 'Cancelled')
	""", (today(),), as_dict=True)

	categories = ["open_complaints", "part_pending", "supplier_complaint", "replacement", "return_in_progress", "product_at_store", "payment_block"]
	aging = {}

	for cat in categories:
		aging[cat] = []
		for (label, low, high) in buckets:
			aging[cat].append({"label": label, "count": 0})

	# Aggregate from flow_types
	for t in flow_types:
		ft = t.get("service_flow_type") or ""
		age = int(t.get("age_days") or 0)

		category = "open_complaints"
		if ft == "Stock Complaint":
			category = "supplier_complaint"
		elif ft == "Replacement / Exchange":
			category = "replacement"
		elif ft == "Refund Case":
			category = "return_in_progress"
		elif ft in ("Customer Product at Store",):
			category = "product_at_store"

		if category not in aging:
			aging[category] = []
			for (label, low, high) in buckets:
				aging[category].append({"label": label, "count": 0})

		for i, (label, low, high) in enumerate(buckets):
			if low <= age <= high:
				aging[category][i]["count"] += 1
				break

	# Also count waiting on part
	part_aging = frappe.db.sql(f"""
		SELECT DATEDIFF(%s, COALESCE(DATE(last_followup_at), DATE(stage_due_at), DATE(creation))) as age_days
		FROM `tabHD Ticket`
		WHERE status NOT IN ('Closed', 'Cancelled')
		AND status = 'Waiting on Part / Approval'
	""", (today(),), as_dict=True)

	aging["part_pending"] = []
	for (label, low, high) in buckets:
		aging["part_pending"].append({"label": label, "count": 0})

	for t in part_aging:
		age = int(t.get("age_days") or 0)
		for i, (label, low, high) in enumerate(buckets):
			if low <= age <= high:
				aging["part_pending"][i]["count"] += 1
				break

	return {"categories": categories, "buckets": buckets, "aging": aging}


# ═══════════════════════════════════════════════════════════════════════════
# Existing: supplier_performance, area_performance, payment_block_status,
# brand_delay_summary, get_report
# ═══════════════════════════════════════════════════════════════════════════

@frappe.whitelist()
def supplier_performance(brand=None, from_date=None, to_date=None):
	from frappe.utils import add_days, getdate, today
	to_date = getdate(to_date or today())
	from_date = getdate(from_date or add_days(to_date, -89))

	roles = set(frappe.get_roles(frappe.session.user))
	if not roles.intersection(_MANAGER_ROLES):
		frappe.throw("Not permitted.", frappe.PermissionError)

	filters = {"creation": ["between", (from_date, to_date)]}
	if brand:
		filters["brand"] = brand

	rows = frappe.db.get_all("Supplier Performance Log", filters=filters,
		fields=["brand", "log_date", "tickets_total", "tickets_breached", "tickets_on_time", "sla_compliance_percent"],
		order_by="log_date desc")

	penalties = {}
	if brand:
		sla = frappe.db.get_value("Supplier SLA Definition", {"brand": brand, "enabled": 1}, "penalty_percent")
		if sla:
			breached_count = sum(r.tickets_breached for r in rows)
			penalties[brand] = {"penalty_percent": float(sla), "breached_tickets": breached_count, "estimated_penalty": round(float(sla) * breached_count, 2)}

	return {"rows": rows, "from_date": str(from_date), "to_date": str(to_date), "penalties": penalties}


@frappe.whitelist()
def area_performance(area=None, from_date=None, to_date=None):
	from frappe.utils import add_days, getdate, today
	to_date = getdate(to_date or today())
	from_date = getdate(from_date or add_days(to_date, -89))

	roles = set(frappe.get_roles(frappe.session.user))
	if not roles.intersection(_MANAGER_ROLES):
		frappe.throw("Not permitted.", frappe.PermissionError)

	filters = {"creation": ["between", (from_date, to_date)]}
	if area:
		filters["area"] = area

	rows = frappe.db.get_all("Area Performance Log", filters=filters,
		fields=["area", "log_date", "tickets_total", "tickets_closed", "tickets_overdue", "closure_rate_percent"],
		order_by="log_date desc")
	return {"rows": rows, "from_date": str(from_date), "to_date": str(to_date)}


@frappe.whitelist()
def payment_block_status():
	roles = set(frappe.get_roles(frappe.session.user))
	if not roles.intersection(_MANAGER_ROLES):
		frappe.throw("Not permitted.", frappe.PermissionError)

	rows = frappe.db.get_all("Supplier Payment Block",
		fields=["name", "brand", "status", "blocked_at", "block_reason", "ticket"],
		order_by="creation desc")
	return {"rows": rows}


@frappe.whitelist()
def brand_delay_summary(brand=None):
	roles = set(frappe.get_roles(frappe.session.user))
	if not roles.intersection(_MANAGER_ROLES):
		frappe.throw("Not permitted.", frappe.PermissionError)

	filters = {"status": ("!=", "Closed"), "docstatus": 0}
	if brand:
		filters["brand"] = brand

	rows = frappe.db.get_all("HD Ticket", filters=filters,
		fields=["brand", "name", "current_service_stage", "creation", "modified",
			"TIMESTAMPDIFF(DAY, creation, NOW()) as age_days"],
		order_by="creation desc")
	return {"rows": rows}


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
