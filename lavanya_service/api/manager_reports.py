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
	get_cancelled_tickets_report
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
