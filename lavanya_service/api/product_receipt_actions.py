import frappe

from lavanya_service.workflow import product_receipt_actions


@frappe.whitelist(methods=["POST"])
def mark_product_sent_to_sc(receipt_name, expected_return_date=None, notes=None):
	return product_receipt_actions.mark_product_sent_to_sc(
		receipt_name, expected_return_date=expected_return_date, notes=notes
	)


@frappe.whitelist(methods=["POST"])
def mark_product_returned_from_sc(receipt_name, actual_return_date=None, notes=None):
	return product_receipt_actions.mark_product_returned_from_sc(
		receipt_name, actual_return_date=actual_return_date, notes=notes
	)


@frappe.whitelist(methods=["POST"])
def mark_delivered_to_customer(receipt_name, notes=None):
	return product_receipt_actions.mark_delivered_to_customer(receipt_name, notes=notes)


@frappe.whitelist(methods=["POST"])
def mark_ready_for_pickup(receipt_name, next_follow_up_date=None, notes=None):
	return product_receipt_actions.mark_ready_for_pickup(
		receipt_name, next_follow_up_date=next_follow_up_date, notes=notes
	)


@frappe.whitelist(methods=["POST"])
def reopen_ticket(ticket_name, reopen_reason=None):
	return product_receipt_actions.reopen_ticket(ticket_name, reopen_reason=reopen_reason)
