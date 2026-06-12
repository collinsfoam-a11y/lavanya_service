"""Whitelisted endpoints for Phase 1N-6B quick workflow actions.

These are thin wrappers. All role checks, status-transition guards, required
field validation and protected-field handling live in
``lavanya_service.workflow.quick_actions`` and run server-side regardless of the
HD Form Script UI. Never trust the browser for authorization.
"""

import frappe

from lavanya_service.workflow import quick_actions


@frappe.whitelist(methods=["POST"])
def register_brand_complaint(
	ticket_name,
	brand_ticket_number=None,
	registration_date=None,
	next_follow_up_date=None,
	service_center=None,
):
	return quick_actions.register_brand_complaint(
		ticket_name,
		brand_ticket_number=brand_ticket_number,
		registration_date=registration_date,
		next_follow_up_date=next_follow_up_date,
		service_center=service_center,
	)


@frappe.whitelist(methods=["POST"])
def need_invoice_from_customer(ticket_name, next_follow_up_date=None, note=None):
	return quick_actions.need_invoice_from_customer(
		ticket_name, next_follow_up_date=next_follow_up_date, note=note
	)


@frappe.whitelist(methods=["POST"])
def follow_up_service_center(ticket_name, follow_up_result=None, next_follow_up_date=None):
	return quick_actions.follow_up_service_center(
		ticket_name,
		follow_up_result=follow_up_result,
		next_follow_up_date=next_follow_up_date,
	)


@frappe.whitelist(methods=["POST"])
def waiting_for_part(ticket_name, pending_reason=None, next_follow_up_date=None):
	return quick_actions.waiting_for_part(
		ticket_name,
		pending_reason=pending_reason,
		next_follow_up_date=next_follow_up_date,
	)


@frappe.whitelist(methods=["POST"])
def mark_product_ready(ticket_name, next_follow_up_date=None):
	return quick_actions.mark_product_ready(
		ticket_name, next_follow_up_date=next_follow_up_date
	)


@frappe.whitelist(methods=["POST"])
def customer_confirmed(ticket_name, work_narration=None, closure_type=None):
	return quick_actions.customer_confirmed(
		ticket_name, work_narration=work_narration, closure_type=closure_type
	)


@frappe.whitelist(methods=["POST"])
def close_ticket(
	ticket_name,
	work_narration=None,
	closure_type=None,
	customer_confirmation_received=None,
):
	return quick_actions.close_ticket(
		ticket_name,
		work_narration=work_narration,
		closure_type=closure_type,
		customer_confirmation_received=customer_confirmation_received,
	)


@frappe.whitelist(methods=["POST"])
def create_product_receipt(ticket_name, accessories_received=None, physical_condition=None):
	return quick_actions.create_product_receipt(
		ticket_name,
		accessories_received=accessories_received,
		physical_condition=physical_condition,
	)
