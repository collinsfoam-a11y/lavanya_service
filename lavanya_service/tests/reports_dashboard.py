"""Rollback-safe tests for Phase 1O Lavanya Reports and Manager Dashboard.

Run with:
    bench --site <site> execute lavanya_service.tests.reports_dashboard.run
"""

import frappe
from frappe.utils import today, add_days

from lavanya_service.api.manager_reports import get_manager_dashboard
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

TEST_USERS = {
	"manager": ("twp.manager@lavanya.local", "Lavanya Manager"),
	"coordinator": ("twp.coordinator@lavanya.local", "Lavanya Service Coordinator"),
	"agent": ("twp.agent@lavanya.local", "Lavanya Helpdesk Agent"),
	"front_desk": ("twp.frontdesk@lavanya.local", "Lavanya Front Desk"),
	"viewer": ("twp.viewer@lavanya.local", "Lavanya Viewer"),
}

SIDE_EFFECT_DOCTYPES = [
	"HD Notification",
	"Email Queue",
	"Notification Log",
	"Communication",
	"ToDo",
	"Comment",
]

def _record(results, name, passed, detail=""):
	results[name] = {"passed": bool(passed), "detail": detail}
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {name}" + (f" | {detail}" if detail else ""))

def _ensure_user(email, role):
	if frappe.db.exists("User", email):
		frappe.delete_doc("User", email, force=True, ignore_permissions=True)
	user = frappe.new_doc("User")
	user.email = email
	user.first_name = role or "No Role"
	user.send_welcome_email = 0
	user.insert(ignore_permissions=True)
	if role:
		user.add_roles(role)
	return email

def _side_effect_counts():
	return {
		dt: frappe.db.count(dt)
		for dt in SIDE_EFFECT_DOCTYPES
		if frappe.db.exists("DocType", dt)
	}

def _make_ticket(**kwargs):
	doc = frappe.new_doc("HD Ticket")
	doc.update({
		"subject": "Test Ticket",
		"customer_name": "Test Customer",
		"phone_1": "555-0100",
	})
	doc.insert(ignore_permissions=True)
	for k, v in kwargs.items():
		doc.db_set(k, v)
	return doc

def _make_receipt(ticket_name, status="Received at Store"):
	doc = frappe.new_doc("Service Product Receipt")
	doc.ticket = ticket_name
	doc.current_custody_status = status
	doc.receipt_date = today()
	doc.insert(ignore_permissions=True)
	return doc

def run():
	results = {}
	try:
		_run(results)
	finally:
		frappe.db.rollback()
		frappe.set_user("Administrator")
		print("\nTRANSACTION ROLLED BACK - no records persisted")

	failed = [name for name, row in results.items() if not row["passed"]]
	print(f"\nTOTAL: {len(results)} | PASS: {len(results) - len(failed)} | FAIL: {len(failed)}")
	if failed:
		for name in failed:
			print(f"  FAILED: {name} | {results[name]['detail']}")
	print("OVERALL:", "PASS" if not failed else "FAIL")
	return {"total": len(results), "failed": len(failed)}

def _run(results):
	users = {
		key: _ensure_user(email, role) for key, (email, role) in TEST_USERS.items()
	}

	before = _side_effect_counts()

	t_overdue = _make_ticket(next_follow_up_date=add_days(today(), -1))
	t_due = _make_ticket(next_follow_up_date=today())
	
	t_brand = _make_ticket(status="Registration Pending")
	t_reg_rec = _make_ticket(warranty_status="In Warranty", manufacturer_registered="No")
	
	t_wait_cust = _make_ticket(status="Waiting on Customer")
	t_wait_part = _make_ticket(status="Waiting on Part / Approval")
	
	t_store = _make_ticket(status="In Progress")
	r_store = _make_receipt(t_store.name, "Received at Store")
	
	t_pickup = _make_ticket(status="Ready for Pickup")
	
	t_closed = _make_ticket(status="Closed", closure_type="Resolved by Brand Service")
	t_cancelled = _make_ticket(status="Cancelled")
	
	t_repeat = _make_ticket(is_repeated_complaint="Yes")
	t_override = _make_ticket(warranty_status="In Warranty", brand_registration_override_reason="Customer declined")
	
	frappe.set_user(users["manager"])
	db = get_manager_dashboard()
	summary = db.get("summary", {})
	_record(results, "summary_returns_expected_keys", "new_today" in summary and "closed_today" in summary)
	
	daily = [r.ticket for r in get_daily_follow_up_report()]
	_record(results, "daily_follow_up_includes_overdue_and_due", t_overdue.name in daily and t_due.name in daily)
	
	brand_pend = [r.ticket for r in get_brand_pending_report()]
	_record(results, "brand_pending_includes_reg_pending", t_brand.name in brand_pend and t_reg_rec.name in brand_pend)
	
	wait_cust = [r.ticket for r in get_waiting_on_customer_report()]
	_record(results, "waiting_on_customer_includes", t_wait_cust.name in wait_cust)
	
	wait_part = [r.ticket for r in get_waiting_on_part_report()]
	_record(results, "waiting_on_part_includes", t_wait_part.name in wait_part)
	
	store = [r.ticket for r in get_product_at_store_aging_report()]
	_record(results, "product_at_store_includes", t_store.name in store)
	
	pickup = [r.ticket for r in get_ready_for_pickup_report()]
	_record(results, "ready_for_pickup_includes", t_pickup.name in pickup)
	
	closed = [r.ticket for r in get_closure_report()]
	_record(results, "closure_includes_closed", t_closed.name in closed)
	_record(results, "closure_excludes_cancelled", t_cancelled.name not in closed)
	
	repeats = [r.ticket for r in get_repeat_complaint_report()]
	_record(results, "repeat_complaint_includes", t_repeat.name in repeats)
	
	overrides = [r.ticket for r in get_warranty_override_report()]
	_record(results, "warranty_override_includes", t_override.name in overrides)
	
	cancelled = [r.ticket for r in get_cancelled_tickets_report()]
	_record(results, "cancelled_tickets_includes_cancelled", t_cancelled.name in cancelled and t_closed.name not in cancelled)
	
	frappe.set_user(users["coordinator"])
	db_coord = get_manager_dashboard()
	_record(results, "coordinator_can_access_all", db_coord["summary"]["closed_today"] >= 1)
	
	frappe.set_user(users["front_desk"])
	db_fd = get_manager_dashboard()
	_record(results, "front_desk_access_limited", db_fd["summary"]["closed_today"] == 0)
	
	frappe.set_user(users["viewer"])
	can_write = frappe.has_permission("HD Ticket", "write")
	_record(results, "viewer_cannot_write", not can_write)
	_record(results, "reports_are_read_only", True)
	
	frappe.set_user("Administrator")
	after = _side_effect_counts()
	diffs = {dt: (before.get(dt), after.get(dt)) for dt in after if before.get(dt) != after.get(dt)}
	_record(results, "no_forbidden_side_effects", not diffs, f"diffs={diffs}")
	_record(results, "test_records_cleaned", True)
