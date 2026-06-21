import frappe

from lavanya_service.setup.masters import ensure_doctype, field


def create_replacement_record_doctype():
	return ensure_doctype(
		"Replacement Record",
		[
			field("ticket", "HD Ticket", "Link", options="HD Ticket", reqd=1, in_list_view=1),
			field("brand", "Brand", "Link", options="Brand Service Master", in_list_view=1),
			field("old_serial_no", "Old Unit Serial No", "Data", in_list_view=1),
			field("new_serial_no", "New Unit Serial No", "Data", in_list_view=1),
			field("sb_replacement_details", "Replacement Details", "Section Break"),
			field("old_unit_collected_at", "Old Unit Collected At", "Datetime"),
			field("new_unit_dispatched_at", "New Unit Dispatched At", "Datetime"),
			field("reimbursement_amount", "Reimbursement Amount", "Currency"),
			field("reimbursement_received_at", "Reimbursement Received At", "Datetime"),
			field("reimbursement_status", "Reimbursement Status", "Select", options="Pending\nReceived\nNot Applicable", default="Pending"),
			field("sb_notes", "Notes", "Section Break"),
			field("notes", "Notes", "Small Text"),
			field("status", "Status", "Select", options="In Progress\nCompleted\nCancelled", default="In Progress", in_list_view=1),
		],
		autoname="format:REP-.YYYY.-.#####",
	)
