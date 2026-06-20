"""P2.2 notification template and dry-run queue DocTypes."""

import frappe

from lavanya_service.setup.masters import ensure_doctype, field


CHANNELS = "\n".join(["WhatsApp", "SMS", "Email", "Internal"])
LANGUAGES = "\n".join(["English", "Malayalam", "Mixed"])
EVENT_TYPES = "\n".join([
	"Ticket created",
	"Brand complaint registered",
	"Technician call pending",
	"Technician visit scheduled",
	"Service center follow-up update",
	"Customer not informed reminder",
	"Part pending update",
	"Product ready for pickup",
	"Customer satisfaction request",
	"Ticket closed",
	"Replacement update",
	"Return/refund update",
	"Stock complaint update",
	"Demo/installation appointment",
	"Payment block / supplier internal alert",
])
STATUSES = "\n".join(["Draft", "Queued", "Approval Pending", "Approved", "Skipped", "Sent", "Failed", "Cancelled"])


DEFAULT_TEMPLATES = [
	("Ticket created", "WhatsApp", "Hello {{ customer_name }}, your service ticket {{ ticket_id }} for {{ product_type }} has been created. Lavanya Service will update you soon."),
	("Brand complaint registered", "WhatsApp", "Hello {{ customer_name }}, your brand complaint for ticket {{ ticket_id }} is registered. Brand ref: {{ brand_ticket_number }}."),
	("Technician call pending", "SMS", "Lavanya Service: Technician call is pending for ticket {{ ticket_id }}. We are following up."),
	("Technician visit scheduled", "WhatsApp", "Hello {{ customer_name }}, technician visit for ticket {{ ticket_id }} is scheduled. Next follow-up: {{ next_follow_up_date }}."),
	("Service center follow-up update", "WhatsApp", "Update for ticket {{ ticket_id }}: {{ last_followup_summary }}"),
	("Customer not informed reminder", "Internal", "Customer update pending for ticket {{ ticket_id }}. Current status: {{ customer_informed_status }}."),
	("Part pending update", "WhatsApp", "Hello {{ customer_name }}, part {{ part_name }} is pending for ticket {{ ticket_id }}. Expected date: {{ part_expected_date }}."),
	("Product ready for pickup", "SMS", "Lavanya Service: Your product for ticket {{ ticket_id }} is ready for pickup. Store: {{ store_name }} {{ store_phone }}."),
	("Customer satisfaction request", "WhatsApp", "Hello {{ customer_name }}, was your service for ticket {{ ticket_id }} completed satisfactorily? Reply to Lavanya Service staff."),
	("Ticket closed", "WhatsApp", "Hello {{ customer_name }}, ticket {{ ticket_id }} is closed as {{ closure_type }}. Thank you."),
	("Replacement update", "WhatsApp", "Hello {{ customer_name }}, replacement update for ticket {{ ticket_id }}: {{ last_followup_summary }}"),
	("Return/refund update", "WhatsApp", "Hello {{ customer_name }}, return/refund update for ticket {{ ticket_id }}: {{ last_followup_summary }}"),
	("Stock complaint update", "Internal", "Stock complaint update for ticket {{ ticket_id }}: {{ last_followup_summary }}"),
	("Demo/installation appointment", "WhatsApp", "Hello {{ customer_name }}, demo/installation appointment for ticket {{ ticket_id }} is planned on {{ next_follow_up_date }}."),
	("Payment block / supplier internal alert", "Internal", "Supplier payment block/internal alert for ticket {{ ticket_id }}: {{ last_followup_summary }}"),
]


def create_notification_template_doctype():
	return ensure_doctype(
		"Lavanya Notification Template",
		[
			field("template_name", "Template Name", "Data", reqd=1, unique=1, in_list_view=1, in_standard_filter=1),
			field("channel", "Channel", "Select", options=CHANNELS, reqd=1, in_list_view=1, in_standard_filter=1),
			field("event_type", "Event Type", "Select", options=EVENT_TYPES, reqd=1, in_list_view=1, in_standard_filter=1),
			field("language", "Language", "Select", options=LANGUAGES, default="English", in_standard_filter=1),
			field("subject", "Subject", "Data"),
			field("message_body", "Message Body", "Text", reqd=1),
			field("variables_json", "Variables JSON", "Code", options="JSON"),
			field("active", "Active", "Check", default="1", in_list_view=1),
			field("requires_approval", "Requires Approval", "Check", default="0", in_list_view=1),
		],
		autoname="field:template_name",
		title_field="template_name",
	)


def create_notification_queue_doctype():
	return ensure_doctype(
		"Lavanya Notification Queue",
		[
			field("ticket", "Ticket", "Link", options="HD Ticket", in_list_view=1, in_standard_filter=1),
			field("customer_name", "Customer Name", "Data", in_list_view=1),
			field("phone", "Phone", "Data", in_list_view=1),
			field("channel", "Channel", "Select", options=CHANNELS, reqd=1, in_list_view=1, in_standard_filter=1),
			field("event_type", "Event Type", "Select", options=EVENT_TYPES, reqd=1, in_list_view=1, in_standard_filter=1),
			field("template", "Template", "Link", options="Lavanya Notification Template", in_list_view=1),
			field("rendered_message", "Rendered Message", "Text"),
			field("status", "Status", "Select", options=STATUSES, default="Draft", in_list_view=1, in_standard_filter=1),
			field("requires_approval", "Requires Approval", "Check", default="0"),
			field("approved_by", "Approved By", "Link", options="User"),
			field("approved_at", "Approved At", "Datetime"),
			field("send_after", "Send After", "Datetime"),
			field("sent_at", "Sent At", "Datetime"),
			field("provider_response", "Provider Response", "Text"),
			field("error_message", "Error Message", "Small Text"),
			field("dry_run", "Dry Run", "Check", default="1", in_list_view=1),
		],
		autoname="format:LNOT-Q-{YYYY}-{#####}",
	)


def seed_default_notification_templates():
	if not frappe.db.exists("DocType", "Lavanya Notification Template"):
		return
	for event_type, channel, body in DEFAULT_TEMPLATES:
		name = f"{event_type} - {channel} - English"
		if frappe.db.exists("Lavanya Notification Template", name):
			continue
		doc = frappe.get_doc({
			"doctype": "Lavanya Notification Template",
			"template_name": name,
			"channel": channel,
			"event_type": event_type,
			"language": "English",
			"subject": event_type,
			"message_body": body,
			"variables_json": "[]",
			"active": 1,
			"requires_approval": 1 if channel in {"WhatsApp", "SMS"} else 0,
		})
		doc.insert(ignore_permissions=True)
	frappe.db.commit()


def create_notification_doctypes():
	create_notification_template_doctype()
	create_notification_queue_doctype()
	seed_default_notification_templates()
