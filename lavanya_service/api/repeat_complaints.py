"""Whitelisted endpoints for Phase 1N-5 repeat complaint suggestion.

Thin wrappers only. All role checks, validation and matching logic live in
``lavanya_service.workflow.repeat_complaints`` and run server-side regardless
of the HD Form Script UI. Never trust the browser for authorization.
"""

import frappe

from lavanya_service.workflow import repeat_complaints


@frappe.whitelist()
def find_repeat_candidates(ticket_name=None, data=None, limit=5):
	if isinstance(data, str) and data.strip():
		data = frappe.parse_json(data)

	return repeat_complaints.find_repeat_candidates(
		ticket_name=ticket_name, data=data, limit=limit
	)


@frappe.whitelist(methods=["POST"])
def confirm_repeat_complaint(ticket_name, previous_ticket_link):
	return repeat_complaints.confirm_repeat_complaint(
		ticket_name, previous_ticket_link
	)


@frappe.whitelist(methods=["POST"])
def clear_repeat_complaint(ticket_name):
	return repeat_complaints.clear_repeat_complaint(ticket_name)
