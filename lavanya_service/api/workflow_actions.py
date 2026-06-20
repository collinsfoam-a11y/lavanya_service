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
def create_product_receipt(
	ticket_name,
	accessories_received=None,
	physical_condition=None,
	product_type=None,
	brand=None,
	model_no=None,
	serial_no=None
):
	return quick_actions.create_product_receipt(
		ticket_name,
		accessories_received=accessories_received,
		physical_condition=physical_condition,
		product_type=product_type,
		brand=brand,
		model_no=model_no,
		serial_no=serial_no
	)

@frappe.whitelist(methods=["POST"])
def verify_technician_called(ticket_name, technician_name=None, notes=None):
	return quick_actions.verify_technician_called(
		ticket_name, technician_name=technician_name, notes=notes
	)


@frappe.whitelist(methods=["POST"])
def verify_technician_visit(ticket_name, technician_name=None, visit_result=None, notes=None):
	return quick_actions.verify_technician_visit(
		ticket_name, technician_name=technician_name, visit_result=visit_result, notes=notes
	)


@frappe.whitelist(methods=["POST"])
def record_sc_followup(ticket_name, follow_up_result=None, next_follow_up_date=None, customer_informed_status=None):
	return quick_actions.record_sc_followup(
		ticket_name, follow_up_result=follow_up_result, next_follow_up_date=next_follow_up_date,
		customer_informed_status=customer_informed_status
	)


@frappe.whitelist(methods=["POST"])
def inform_customer(ticket_name, message=None, channel=None):
	return quick_actions.inform_customer(
		ticket_name, message=message, channel=channel
	)


@frappe.whitelist(methods=["POST"])
def mark_no_update(ticket_name, notes=None):
	return quick_actions.mark_no_update(ticket_name, notes=notes)


@frappe.whitelist(methods=["POST"])
def escalate_case(ticket_name, reason=None):
	return quick_actions.escalate_case(ticket_name, reason=reason)


@frappe.whitelist(methods=["POST"])
def record_satisfaction(ticket_name, satisfaction_status=None, notes=None):
	return quick_actions.record_satisfaction(
		ticket_name, satisfaction_status=satisfaction_status, notes=notes
    )


@frappe.whitelist(methods=["POST"])
def record_customer_approval(ticket_name, approved_amount=None, payment_status=None, notes=None):
    return quick_actions.record_customer_approval(
        ticket_name, approved_amount=approved_amount, payment_status=payment_status, notes=notes
    )


@frappe.whitelist()
def get_current_user_roles():
    roles = frappe.get_roles(frappe.session.user)
    return {
        'is_manager': 'Lavanya Manager' in roles,
        'is_coordinator': 'Lavanya Service Coordinator' in roles,
        'is_agent': 'Lavanya Helpdesk Agent' in roles,
        'is_front_desk': 'Lavanya Front Desk' in roles
    }
