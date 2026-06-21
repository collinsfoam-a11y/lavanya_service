from lavanya_service.setup.masters import ensure_doctype, field


def create_return_service_record_doctype():
	return ensure_doctype(
		"Return Service Record",
		[
			field("ticket", "HD Ticket", "Link", options="HD Ticket", reqd=1, in_list_view=1),
			field("brand", "Brand", "Link", options="Brand Service Master", in_list_view=1),
			field("return_reason", "Return Reason", "Small Text", in_list_view=1),
			field("return_reason_verified_at", "Return Reason Verified At", "Datetime"),
			field("return_reason_verified_by", "Verified By", "Link", options="User"),
			field("sb_return", "Return Processing", "Section Break"),
			field("brand_notified_at", "Brand Notified At", "Datetime"),
			field("brand_decision", "Brand Decision", "Select", options="Accepted\nRejected\nPending", default="Pending"),
			field("customer_refund_amount", "Customer Refund Amount", "Currency"),
			field("customer_refund_processed_at", "Refund Processed At", "Datetime"),
			field("refund_status", "Refund Status", "Select", options="Pending\nProcessed\nNot Applicable", default="Pending"),
			field("sb_notes", "Notes", "Section Break"),
			field("notes", "Notes", "Small Text"),
			field("status", "Status", "Select", options="In Progress\nCompleted\nCancelled", default="In Progress", in_list_view=1),
		],
		autoname="format:RET-.YYYY.-.#####",
	)
