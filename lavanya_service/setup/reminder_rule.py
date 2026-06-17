"""Lavanya Reminder Rule — config/master DocType for the rule-first reminder
engine (see docs/reminder_engine_implementation_plan.md). Created programmatically
(like Lavanya Service Appointment) so it never touches the shared fixture. This is
the Sprint-3 skeleton: fields only — resolution/refresh logic comes next."""

import frappe

from lavanya_service import stage_rules as sr

REMINDER_RULE = "Lavanya Reminder Rule"


def _f(fieldname, label, fieldtype, **kwargs):
	return {"fieldname": fieldname, "label": label, "fieldtype": fieldtype, **kwargs}


def _perm(role, write=1):
	return {
		"role": role, "read": 1, "write": write, "create": write, "delete": write,
		"report": 1, "export": 1, "share": 1, "print": 1, "email": 1,
	}


def create_reminder_rule_doctype():
	if frappe.db.exists("DocType", REMINDER_RULE):
		return "exists"

	doc = frappe.get_doc(
		{
			"doctype": "DocType",
			"name": REMINDER_RULE,
			"module": "Lavanya Service",
			"custom": 1,
			"autoname": "field:rule_name",
			"sort_field": "priority",
			"sort_order": "ASC",
			"track_changes": 1,
			"fields": [
				_f("rule_name", "Rule Name", "Data", reqd=1, unique=1, in_list_view=1),
				_f("enabled", "Enabled", "Check", default="1", in_list_view=1),
				_f("priority", "Priority", "Int", default="100", in_list_view=1, description="Lower wins on ties"),
				_f("match_section", "Match Conditions", "Section Break"),
				_f("brand", "Brand", "Link", options="Brand Service Master"),
				_f("product_type", "Product Type", "Data"),
				_f("ticket_type", "Ticket Type", "Data"),
				_f("service_flow_type", "Service Flow Type", "Select", options="\n" + "\n".join(sr.SERVICE_FLOW_TYPES)),
				_f("current_service_stage", "Current Service Stage", "Select", options="\n" + "\n".join(sr.CURRENT_SERVICE_STAGES)),
				_f("warranty_route", "Warranty Route", "Data"),
				_f("pending_reason", "Pending Reason", "Data"),
				_f("customer_priority", "Customer Priority", "Select", options="\nLow\nNormal\nHigh\nVIP"),
				_f("timing_section", "Reminder Timing (minutes)", "Section Break"),
				_f("first_followup_after_minutes", "First Follow-up After (min)", "Int"),
				_f("repeat_every_minutes", "Repeat Every (min)", "Int"),
				_f("due_soon_before_minutes", "Due Soon Before (min)", "Int"),
				_f("overdue_after_minutes", "Overdue After (min)", "Int"),
				_f("timing_col", "", "Column Break"),
				_f("manager_escalate_after_minutes", "Manager Escalate After (min)", "Int"),
				_f("owner_escalate_after_minutes", "Owner Escalate After (min)", "Int"),
				_f("customer_update_required", "Customer Update Required", "Check"),
				_f("customer_update_every_minutes", "Customer Update Every (min)", "Int"),
				_f("flags_section", "Flags", "Section Break"),
				_f("pause_when_sla_paused", "Pause When SLA Paused", "Check", default="1"),
				_f("business_hours_only", "Business Hours Only", "Check"),
				_f("notes", "Notes", "Small Text"),
			],
			"permissions": [
				_perm("System Manager"),
				_perm("Lavanya Manager"),
				_perm("Lavanya Service Coordinator", write=0),
			],
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache(doctype=REMINDER_RULE)
	return "created"
