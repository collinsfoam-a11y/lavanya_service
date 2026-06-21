"""Create the service-stage custom fields on HD Ticket programmatically (like the
Lavanya Service Appointment doctype). This is intentionally NOT done via the
shared custom_field.json fixture, so it never conflicts with the other agent's
field set. Idempotent (create_custom_fields(update=True)); wired via
hooks.after_install / after_migrate."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from lavanya_service import stage_rules as sr


def _opts(values):
	# H1 Fix 1: This function generates the full stage option list.
	# The options are sourced from stage_rules.CURRENT_SERVICE_STAGES (52 stages)
	# and must always reflect the complete list to prevent field option regression.
	# Leading blank line so the Select does NOT auto-default to its first option —
	# new tickets start empty and let stage_rules.assign_defaults derive the value.
	return "\n" + "\n".join(values)


def create_service_stage_fields():
	fields = {
		"HD Ticket": [
			{"fieldname": "lavanya_stage_section", "label": "Service Stage", "fieldtype": "Section Break", "insert_after": "ticket_type", "collapsible": 1},
			{"fieldname": "service_flow_type", "label": "Service Flow Type", "fieldtype": "Select", "options": _opts(sr.SERVICE_FLOW_TYPES), "insert_after": "lavanya_stage_section"},
			{"fieldname": "current_service_stage", "label": "Current Service Stage", "fieldtype": "Select", "options": _opts(sr.CURRENT_SERVICE_STAGES), "insert_after": "service_flow_type"},
			{"fieldname": "next_action", "label": "Next Action", "fieldtype": "Select", "options": _opts(sr.NEXT_ACTIONS), "insert_after": "current_service_stage"},
			{"fieldname": "next_action_owner", "label": "Next Action Owner", "fieldtype": "Link", "options": "User", "insert_after": "next_action"},
			{"fieldname": "next_action_role", "label": "Next Action Role", "fieldtype": "Data", "insert_after": "next_action_owner"},
			{"fieldname": "lavanya_stage_col", "fieldtype": "Column Break", "insert_after": "next_action_role"},
			{"fieldname": "stage_due_at", "label": "Stage Due At", "fieldtype": "Datetime", "insert_after": "lavanya_stage_col"},
			{"fieldname": "pre_overdue_alert_at", "label": "Pre-overdue Alert At", "fieldtype": "Datetime", "insert_after": "stage_due_at"},
			{"fieldname": "overdue_status", "label": "Overdue Status", "fieldtype": "Select", "options": _opts(sr.OVERDUE_STATUSES), "insert_after": "pre_overdue_alert_at"},
			{"fieldname": "escalation_level", "label": "Escalation Level", "fieldtype": "Select", "options": _opts(sr.ESCALATION_LEVELS), "default": "None", "insert_after": "overdue_status"},
			{"fieldname": "customer_informed", "label": "Customer Informed", "fieldtype": "Select", "options": _opts(sr.CUSTOMER_INFORMED_OPTIONS), "insert_after": "escalation_level"},
			{"fieldname": "customer_informed_channel", "label": "Customer Informed Channel", "fieldtype": "Select", "options": _opts(sr.CUSTOMER_INFORMED_CHANNELS), "insert_after": "customer_informed"},
			{"fieldname": "customer_informed_at", "label": "Customer Informed At", "fieldtype": "Datetime", "insert_after": "customer_informed_channel"},
			{"fieldname": "customer_informed_by", "label": "Customer Informed By", "fieldtype": "Link", "options": "User", "insert_after": "customer_informed_at"},
			# Customer-promise tracking (reminder engine, Step 2).
			{"fieldname": "customer_promised_update_at", "label": "Customer Promised Update At", "fieldtype": "Datetime", "insert_after": "customer_informed_by"},
			{"fieldname": "customer_promise_status", "label": "Customer Promise Status", "fieldtype": "Select", "options": "\nNone\nPending\nKept\nBreached", "default": "None", "insert_after": "customer_promised_update_at"},
			{"fieldname": "promise_breach_reason", "label": "Promise Breach Reason", "fieldtype": "Small Text", "insert_after": "customer_promise_status"},
		]
	}
	create_custom_fields(fields, update=True)
	frappe.clear_cache(doctype="HD Ticket")
	return "ok"
