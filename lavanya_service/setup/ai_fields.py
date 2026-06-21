"""Create the AI-advisory custom fields on HD Ticket programmatically (reminder
engine, Step 6). Advisory-only: these `ai_*` fields hold suggestions a human must
review and act on — nothing here changes operational state. Created the same safe
way as the stage fields (not via the shared fixture). Idempotent
(create_custom_fields(update=True)); wired via hooks.after_install / after_migrate."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

AI_REVIEW_STATUSES = ["Not Required", "Review Needed", "Suggested", "Accepted", "Ignored", "Error"]


def create_ai_advisory_fields():
	fields = {
		"HD Ticket": [
			{"fieldname": "ai_advisory_section", "label": "AI Advisory", "fieldtype": "Section Break",
			 "insert_after": "promise_breach_reason", "collapsible": 1},
			{"fieldname": "ai_review_status", "label": "AI Review Status", "fieldtype": "Select",
			 "options": "\n" + "\n".join(AI_REVIEW_STATUSES), "default": "Not Required",
			 "insert_after": "ai_advisory_section", "read_only": 1, "in_standard_filter": 1},
			{"fieldname": "ai_suggested_next_action", "label": "AI Suggested Next Action", "fieldtype": "Small Text",
			 "insert_after": "ai_review_status", "read_only": 1},
			{"fieldname": "ai_risk_reason", "label": "AI Risk Reason", "fieldtype": "Small Text",
			 "insert_after": "ai_suggested_next_action", "read_only": 1},
			{"fieldname": "ai_manager_summary", "label": "AI Manager Summary", "fieldtype": "Small Text",
			 "insert_after": "ai_risk_reason", "read_only": 1},
			{"fieldname": "ai_suggested_customer_message", "label": "AI Suggested Customer Message", "fieldtype": "Text",
			 "insert_after": "ai_manager_summary", "read_only": 1},
			{"fieldname": "ai_advisory_source", "label": "AI Advisory Source", "fieldtype": "Data",
			 "insert_after": "ai_suggested_customer_message", "read_only": 1},
			{"fieldname": "ai_last_reviewed_at", "label": "AI Last Reviewed At", "fieldtype": "Datetime",
			 "insert_after": "ai_advisory_source", "read_only": 1},
			{"fieldname": "ai_reviewed_by", "label": "AI Reviewed By", "fieldtype": "Link", "options": "User",
			 "insert_after": "ai_last_reviewed_at", "read_only": 1},
		]
	}
	create_custom_fields(fields, update=True)
	return "ok"
