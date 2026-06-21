"""Phase 1N-6C workflow actions for Service Product Receipt and Closure UX.

These functions manage custody log movements for product-at-store tickets
and handle the ticket reopening flow.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, today

# We import helpers from quick_actions to reuse role checking and save logic where possible.
from lavanya_service.workflow.quick_actions import (
	TICKET_DOCTYPE,
	RECEIPT_DOCTYPE,
	ROLE_MANAGER,
	ROLE_COORDINATOR,
	ROLE_FRONT_DESK,
	_acting_user,
	_require_roles,
	_require,
	_load_ticket,
	_save_ticket,
)


def _load_receipt(receipt_name):
	receipt_name = _require(receipt_name, "Receipt")
	if not frappe.db.exists(RECEIPT_DOCTYPE, receipt_name):
		frappe.throw(_("Service Product Receipt {0} not found.").format(receipt_name))

	if not frappe.has_permission(RECEIPT_DOCTYPE, "read", user=_acting_user()):
		frappe.throw(_("You are not permitted to read this receipt."), frappe.PermissionError)

	return frappe.get_doc(RECEIPT_DOCTYPE, receipt_name)


def _save_receipt(doc):
	"""Persist receipt changes."""
	acting_user = _acting_user()
	if not frappe.has_permission(RECEIPT_DOCTYPE, "write", doc=doc, user=acting_user):
		frappe.throw(_("You are not permitted to update this receipt."), frappe.PermissionError)

	# The action already enforced an explicit role check above; save with
	# ignore_permissions WITHOUT impersonating Administrator so modified_by
	# keeps the real acting user for the audit trail (audit B1).
	doc.flags.ignore_lavanya_field_guard = True
	doc.save(ignore_permissions=True)

	doc.reload()
	return doc


def _append_custody_log(doc, action, status, from_party, to_party, notes=None):
	doc.append(
		"custody_log",
		{
			"custody_action": action,
			"custody_status": status,
			"action_datetime": now_datetime(),
			"from_party": from_party,
			"to_party": to_party,
			"handled_by": _acting_user(),
			"notes": notes,
		},
	)


def _result(doc, message):
	return {
		"ok": True,
		"receipt": doc.name,
		"status": doc.current_custody_status,
		"message": message,
	}


def mark_product_sent_to_sc(receipt_name, expected_return_date=None, notes=None):
	_require_roles("Mark Product Sent to Service Center", {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_FRONT_DESK})

	doc = _load_receipt(receipt_name)
	
	if doc.current_custody_status != "Received at Store":
		frappe.throw(_("Cannot send to Service Center from current status: {0}").format(doc.current_custody_status))

	doc.current_custody_status = "Handed to Service Center"
	if expected_return_date:
		doc.expected_return_date = expected_return_date

	_append_custody_log(
		doc,
		action="Handed Over",
		status="Handed to Service Center",
		from_party="Store",
		to_party="Service Center",
		notes=notes,
	)

	_save_receipt(doc)
	return _result(doc, _("Product sent to Service Center"))


def mark_product_returned_from_sc(receipt_name, actual_return_date=None, notes=None):
	_require_roles("Mark Product Returned from Service Center", {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_FRONT_DESK})

	doc = _load_receipt(receipt_name)

	if doc.current_custody_status != "Handed to Service Center":
		frappe.throw(_("Cannot mark as returned from current status: {0}").format(doc.current_custody_status))

	doc.current_custody_status = "Returned to Store"
	if actual_return_date:
		doc.actual_return_date = actual_return_date
	else:
		doc.actual_return_date = today()

	_append_custody_log(
		doc,
		action="Returned",
		status="Returned to Store",
		from_party="Service Center",
		to_party="Store",
		notes=notes,
	)

	_save_receipt(doc)
	return _result(doc, _("Product returned from Service Center"))


def mark_delivered_to_customer(receipt_name, notes=None):
	_require_roles("Mark Delivered to Customer", {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_FRONT_DESK})

	doc = _load_receipt(receipt_name)

	valid_previous_statuses = {"Received at Store", "Returned to Store", "Ready for Customer Pickup"}
	if doc.current_custody_status not in valid_previous_statuses:
		frappe.throw(_("Cannot deliver to customer from current status: {0}").format(doc.current_custody_status))

	doc.current_custody_status = "Delivered to Customer"
	if not doc.customer_pickup_date:
		doc.customer_pickup_date = now_datetime()

	_append_custody_log(
		doc,
		action="Delivered",
		status="Delivered to Customer",
		from_party="Store",
		to_party="Customer",
		notes=notes,
	)

	_save_receipt(doc)
	return _result(doc, _("Product delivered to customer"))


def reopen_ticket(ticket_name, reopen_reason=None):
	_require_roles("Reopen Ticket", {ROLE_MANAGER, ROLE_COORDINATOR})

	reopen_reason = _require(reopen_reason, "Reopen Reason")

	doc = _load_ticket(ticket_name)
	
	if doc.status != "Closed":
		frappe.throw(_("Only closed tickets can be reopened. Ticket {0} is {1}.").format(doc.name, doc.status))

	doc.status = "In Progress"
	doc.pending_reason = "Other"
	doc.next_follow_up_date = today()
	
	# Clear closure fields
	doc.closure_type = ""
	doc.closed_by = ""
	doc.closure_date = None
	doc.customer_confirmation_received = ""
	
	# Append reason to narration
	timestamp = frappe.utils.format_datetime(now_datetime(), "medium")
	reopen_text = f"\n\n--- Reopened on {timestamp} ---\nReason: {reopen_reason}"
	doc.work_narration = (doc.work_narration or "") + reopen_text

	_save_ticket(doc)
	
	return {
		"ok": True,
		"ticket": doc.name,
		"status": doc.status,
		"message": _("Ticket reopened"),
	}

def mark_ready_for_pickup(receipt_name, next_follow_up_date=None, notes=None):
	_require_roles("Mark Ready for Pickup", {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_FRONT_DESK})

	doc = _load_receipt(receipt_name)

	valid_previous_statuses = {"Received at Store", "Returned to Store"}
	if doc.current_custody_status not in valid_previous_statuses:
		frappe.throw(_("Cannot mark ready for pickup from current status: {0}").format(doc.current_custody_status))

	doc.current_custody_status = "Ready for Customer Pickup"

	_append_custody_log(
		doc,
		action="Ready for Pickup",
		status="Ready for Customer Pickup",
		from_party="Store",
		to_party="Store",
		notes=notes,
	)

	_save_receipt(doc)

	# Also update the HD Ticket status
	ticket = _load_ticket(doc.ticket)
	if ticket.status not in ("Closed", "Cancelled"):
		ticket.status = "Ready for Pickup"
		ticket.pending_reason = "Customer Pickup Pending"
		ticket.next_follow_up_date = next_follow_up_date or today()
		_save_ticket(ticket)

	return _result(doc, _("Product marked ready for pickup"))
