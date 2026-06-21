from lavanya_service.setup.masters import ensure_doctype, field


def create_stock_complaint_record_doctype():
	return ensure_doctype(
		"Stock Complaint Record",
		[
			field("ticket", "HD Ticket", "Link", options="HD Ticket", reqd=1, in_list_view=1),
			field("supplier", "Supplier", "Data", in_list_view=1),
			field("product_type", "Product Type", "Data"),
			field("sb_stock", "Stock Complaint Processing", "Section Break"),
			field("issue_identified_at", "Issue Identified At", "Datetime"),
			field("supplier_notified_at", "Supplier Notified At", "Datetime"),
			field("supplier_acknowledged_at", "Supplier Acknowledged At", "Datetime"),
			field("replacement_received_at", "Replacement Received At", "Datetime"),
			field("defective_returned_at", "Defective Returned At", "Datetime"),
			field("credit_note_received_at", "Credit Note Received At", "Datetime"),
			field("credit_note_amount", "Credit Note Amount", "Currency"),
			field("sb_notes", "Notes", "Section Break"),
			field("notes", "Notes", "Small Text"),
			field("status", "Status", "Select", options="In Progress\nCompleted\nCancelled", default="In Progress", in_list_view=1),
		],
		autoname="format:STK-.YYYY.-.#####",
	)
