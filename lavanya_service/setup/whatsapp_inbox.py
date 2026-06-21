"""H6A: WhatsApp Inbox — read-only inbound + draft-only outbound DocTypes.

Safety boundaries:
- No live WhatsApp API send (no Twilio/360dialog/WhatsApp Business API calls).
- No SMS gateway calls.
- No automatic ticket closure.
- No ERP posting, accounting entries, or penalty application.
- No CRM auto-conversion.
"""

import frappe
from lavanya_service.setup.masters import ensure_doctype, field


def create_whatsapp_inbound_message_doctype():
	return ensure_doctype(
		"WhatsApp Inbound Message",
		[
			field("sender_mobile", "Sender Mobile", "Data", reqd=1, in_list_view=1, in_standard_filter=1),
			field("sender_name", "Sender Name", "Data", in_list_view=1),
			field("message_text", "Message", "Text", reqd=1),
			field("received_at", "Received At", "Datetime", reqd=1, in_list_view=1),
			field("linked_ticket", "Linked Ticket", "Link", options="HD Ticket", in_list_view=1),
			field("linked_customer_profile", "Customer Profile", "Link", options="Lavanya Customer Profile"),
			field("linked_customer_product", "Customer Product", "Link", options="Lavanya Customer Product"),
			field("review_status", "Review Status", "Select",
				options="New\nReviewed\nLinked to Ticket\nIgnored\nSpam",
				default="New", in_list_view=1, in_standard_filter=1),
			field("reviewed_by", "Reviewed By", "Link", options="User"),
			field("reviewed_at", "Reviewed At", "Datetime"),
			field("review_notes", "Review Notes", "Small Text"),
			field("sb_source", "Source Info", "Section Break"),
			field("source", "Source", "Select",
				options="WhatsApp\nSMS\nWeb Chat\nEmail",
				default="WhatsApp", in_list_view=1),
			field("raw_payload", "Raw Payload", "Code"),
		],
		autoname="LV-WA-IN-.YYYY.-.#####",
	)


def create_whatsapp_draft_outbound_doctype():
	return ensure_doctype(
		"WhatsApp Draft Outbound",
		[
			field("ticket", "Ticket", "Link", options="HD Ticket", reqd=1, in_list_view=1, in_standard_filter=1),
			field("recipient_mobile", "Recipient Mobile", "Data", reqd=1, in_list_view=1),
			field("recipient_name", "Recipient Name", "Data"),
			field("draft_message", "Draft Message", "Text", reqd=1),
			field("created_by_user", "Created By", "Link", options="User", in_list_view=1),
			field("created_at", "Created At", "Datetime", reqd=1, in_list_view=1),
			field("review_status", "Review Status", "Select",
				options="Draft\nManager Reviewed\nApproved (Ready)\nRejected\nSent (External)",
				default="Draft", in_list_view=1, in_standard_filter=1),
			field("reviewed_by", "Reviewed By", "Link", options="User"),
			field("reviewed_at", "Reviewed At", "Datetime"),
			field("rejection_reason", "Rejection Reason", "Small Text"),
			field("sb_template", "Template Info", "Section Break"),
			field("template_name", "Template", "Data"),
			field("template_language", "Language", "Data", default="ml"),
			field("sb_safety", "Safety Gates", "Section Break"),
			field("live_send_blocked", "Live Send Blocked", "Check", default="1", read_only=1,
				description="Always locked: live WhatsApp sending is not enabled"),
			field("dry_run_note", "Dry-Run Note", "Small Text",
				default="This is a draft-only system. No live WhatsApp message will be sent."),
		],
		autoname="LV-WA-OUT-.YYYY.-.#####",
	)


def create_whatsapp_inbox():
	results = {
		"whatsapp_inbound_message": create_whatsapp_inbound_message_doctype(),
		"whatsapp_draft_outbound": create_whatsapp_draft_outbound_doctype(),
	}
	frappe.clear_cache()
	return results
