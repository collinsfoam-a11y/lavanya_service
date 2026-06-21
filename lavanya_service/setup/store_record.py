from lavanya_service.setup.masters import ensure_doctype, field


def create_store_service_record_doctype():
	return ensure_doctype(
		"Store Service Record",
		[
			field("ticket", "HD Ticket", "Link", options="HD Ticket", reqd=1, in_list_view=1),
			field("product_receipt", "Product Receipt", "Link", options="Service Product Receipt"),
			field("brand", "Brand", "Link", options="Brand Service Master", in_list_view=1),
			field("service_center", "Service Center", "Link", options="Service Center Master"),
			field("sb_store", "Store Service Processing", "Section Break"),
			field("product_received_at", "Product Received At", "Datetime"),
			field("sent_to_sc_at", "Sent to Service Center At", "Datetime"),
			field("diagnosis_received_at", "Diagnosis Received At", "Datetime"),
			field("diagnosis_summary", "Diagnosis Summary", "Small Text"),
			field("returned_to_store_at", "Returned to Store At", "Datetime"),
			field("customer_notified_at", "Customer Notified At", "Datetime"),
			field("product_handed_over_at", "Product Handed Over At", "Datetime"),
			field("sb_notes", "Notes", "Section Break"),
			field("notes", "Notes", "Small Text"),
			field("status", "Status", "Select", options="In Progress\nCompleted\nCancelled", default="In Progress", in_list_view=1),
		],
		autoname="format:STR-.YYYY.-.#####",
	)
