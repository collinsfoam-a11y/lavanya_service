import frappe
from lavanya_service.setup.masters import ensure_doctype, field


def create_comm_log_doctype():
	return ensure_doctype(
		"Customer Communication Log",
		[
			field("ticket", "Ticket", "Link", options="HD Ticket", reqd=1, in_list_view=1, in_standard_filter=1),
			field("communication_date", "Communication Date", "Datetime", reqd=1, in_list_view=1),
			field("communication_type", "Type", "Select", options="Call\nSMS\nEmail\nIn-Person\nWhatsApp", reqd=1, in_list_view=1, in_standard_filter=1),
			field("direction", "Direction", "Select", options="Outbound\nInbound", default="Outbound", in_list_view=1),
			field("agent", "Agent", "Link", options="User", in_list_view=1),
			field("summary", "Summary", "Small Text"),
			field("notes", "Notes", "Text"),
			field("next_action", "Next Action", "Small Text"),
		],
		autoname="format:COMM-.{ticket}.-.#####",
	)
