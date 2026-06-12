"""Rollback-safe tests for Phase 1N-6C product receipt and closure actions.

Run with:
    bench --site <site> execute lavanya_service.tests.product_receipt_ux.run
"""

import frappe
from frappe.utils import today

from lavanya_service.tests.workflow_quick_actions import (
	_record,
	_count,
	_ensure_users,
	_insert_ticket,
	_call_as,
	_blocks,
	_forbidden_counts,
	RESULTS,
	ROLLBACK_DOCTYPES,
	USERS,
)


def run():
	RESULTS.clear()
	baseline = {dt: _count(dt) for dt in ROLLBACK_DOCTYPES}
	try:
		_run_all()
	finally:
		frappe.set_user("Administrator")
		frappe.db.rollback()
		rollback_ok = {dt: _count(dt) == baseline[dt] for dt in ROLLBACK_DOCTYPES}
		_record(
			"PR-014",
			"automated test records roll back cleanly",
			all(rollback_ok.values()),
			rollback_ok,
		)
		print("\nTRANSACTION ROLLED BACK - no records persisted")

	failed = [row for row in RESULTS if not row[2]]
	print(f"\nTOTAL: {len(RESULTS)} | PASS: {len(RESULTS) - len(failed)} | FAIL: {len(failed)}")
	if failed:
		print("FAILED TESTS:")
		for test_id, description, _passed, detail in failed:
			print(f"  - {test_id}: {description} | {detail}")
	print("OVERALL:", "PASS" if not failed else "FAIL")
	return {"total": len(RESULTS), "failed": len(failed)}


def _run_all():
	from lavanya_service.api import workflow_actions as wa
	from lavanya_service.api import product_receipt_actions as pra

	_ensure_users()

	# Helper to create ticket and receipt
	def _create_receipt(serial_no="PR-001"):
		t = _insert_ticket(f"PR Test {serial_no}", ticket_type="Customer Product at Store", serial_no=serial_no)
		res = _call_as(USERS["front_desk"], wa.create_product_receipt, ticket_name=t)
		return t, res.get("receipt")

	# PR-001 Create receipt from Customer Product at Store ticket
	# PR-004 Front Desk can create receipt
	t1, r1 = _create_receipt("PR-001")
	doc1 = frappe.get_doc("Service Product Receipt", r1)
	_record(
		"PR-001",
		"Front Desk can create receipt from Customer Product at Store ticket",
		r1 is not None and doc1.current_custody_status == "Received at Store",
		f"receipt={r1}",
	)

	# PR-009 Custody log records movement (initial creation)
	log1 = doc1.get("custody_log")
	_record(
		"PR-009a",
		"Custody log records initial Received movement",
		len(log1) == 1 and log1[0].custody_action == "Received",
		f"log_len={len(log1)}",
	)

	# PR-002 Block duplicate receipt
	blocked, err = _blocks(USERS["coordinator"], wa.create_product_receipt, ticket_name=t1)
	_record("PR-002", "Block duplicate receipt", blocked, err)

	# PR-003 Block receipt creation for wrong ticket type
	wrong_t = _insert_ticket("PR Wrong Type")
	blocked, err = _blocks(USERS["coordinator"], wa.create_product_receipt, ticket_name=wrong_t)
	_record("PR-003", "Block receipt creation for wrong ticket type", blocked, err)

	# PR-005 Helpdesk Agent cannot create receipt
	store_t2 = _insert_ticket("PR Agent", ticket_type="Customer Product at Store", serial_no="PR-002")
	blocked, err = _blocks(USERS["agent"], wa.create_product_receipt, ticket_name=store_t2)
	_record("PR-005", "Helpdesk Agent cannot create receipt", blocked, err)

	# PR-006 Viewer cannot create receipt
	store_t3 = _insert_ticket("PR Viewer", ticket_type="Customer Product at Store", serial_no="PR-003")
	blocked, err = _blocks(USERS["viewer"], wa.create_product_receipt, ticket_name=store_t3)
	_record("PR-006", "Viewer cannot create receipt", blocked, err)

	# Additional movements for testing Mark Ready / Mark Delivered / log updates
	t2, r2 = _create_receipt("PR-MOV")
	
	# Move to SC
	_call_as(USERS["coordinator"], pra.mark_product_sent_to_sc, receipt_name=r2)
	doc2 = frappe.get_doc("Service Product Receipt", r2)
	_record(
		"PR-009b",
		"Custody log records Handed Over movement",
		len(doc2.get("custody_log")) == 2 and doc2.current_custody_status == "Handed to Service Center",
		f"status={doc2.current_custody_status}",
	)

	# Move back from SC
	_call_as(USERS["coordinator"], pra.mark_product_returned_from_sc, receipt_name=r2)
	doc2.reload()
	_record(
		"PR-009c",
		"Custody log records Returned movement",
		len(doc2.get("custody_log")) == 3 and doc2.current_custody_status == "Returned to Store",
		f"status={doc2.current_custody_status}",
	)

	# PR-007 Mark Ready for Pickup updates ticket
	_call_as(USERS["front_desk"], pra.mark_ready_for_pickup, receipt_name=r2)
	doc2.reload()
	ticket2 = frappe.get_doc("HD Ticket", t2)
	_record(
		"PR-007",
		"Mark Ready for Pickup updates ticket status",
		doc2.current_custody_status == "Ready for Customer Pickup" and ticket2.status == "Ready for Pickup",
		f"receipt_status={doc2.current_custody_status}, ticket_status={ticket2.status}",
	)

	# PR-008 Mark Delivered updates receipt
	_call_as(USERS["coordinator"], pra.mark_delivered_to_customer, receipt_name=r2)
	doc2.reload()
	_record(
		"PR-008",
		"Mark Delivered updates receipt and adds log",
		doc2.current_custody_status == "Delivered to Customer" and len(doc2.get("custody_log")) == 5,
		f"status={doc2.current_custody_status}",
	)

	# PR-010 Token slip print format exists
	pf_exists = frappe.db.exists("Print Format", "Lavanya Service Product Receipt Token")
	_record("PR-010", "Token slip print format exists", bool(pf_exists), f"format={pf_exists}")

	# PR-011 Close requires customer confirmation
	t3 = _insert_ticket("PR Close Conf")
	blocked, err = _blocks(
		USERS["manager"],
		wa.close_ticket,
		ticket_name=t3,
		work_narration="Done",
		closure_type="Customer Collected Product",
		customer_confirmation_received="No"
	)
	_record("PR-011", "Close requires customer confirmation", blocked, err)

	_call_as(
		USERS["manager"],
		wa.close_ticket,
		ticket_name=t3,
		work_narration="Done",
		closure_type="Customer Collected Product",
		customer_confirmation_received="Yes"
	)

	# PR-012 Reopen moves ticket to In Progress with reason
	_call_as(USERS["manager"], pra.reopen_ticket, ticket_name=t3, reopen_reason="Not working")
	ticket3 = frappe.get_doc("HD Ticket", t3)
	_record(
		"PR-012",
		"Reopen moves ticket to In Progress with reason",
		ticket3.status == "In Progress" and "Not working" in ticket3.work_narration and not ticket3.closure_date,
		f"status={ticket3.status}",
	)

	# PR-013 No forbidden side effects
	before = _forbidden_counts()
	_call_as(USERS["coordinator"], pra.mark_product_sent_to_sc, receipt_name=r1)
	
	# Attempt to reopen an unclosed ticket should fail but not cause side effects
	_blocks(USERS["manager"], pra.reopen_ticket, ticket_name=t1, reopen_reason="Test") 

	after = _forbidden_counts()
	_record(
		"PR-013",
		"No forbidden side effects during actions",
		before == after,
		f"delta={ {k: after[k]-before[k] for k in before} }",
	)
