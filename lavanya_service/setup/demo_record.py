from lavanya_service.setup.masters import ensure_doctype, field


def create_demo_installation_record_doctype():
	return ensure_doctype(
		"Demo Installation Record",
		[
			field("ticket", "HD Ticket", "Link", options="HD Ticket", reqd=1, in_list_view=1),
			field("technician", "Technician", "Link", options="Local Technician Master"),
			field("product_type", "Product Type", "Data", in_list_view=1),
			field("sb_demo", "Demo / Installation", "Section Break"),
			field("scheduled_at", "Scheduled At", "Datetime"),
			field("demo_conducted_at", "Demo Conducted At", "Datetime"),
			field("installation_completed_at", "Installation Completed At", "Datetime"),
			field("customer_feedback", "Customer Feedback", "Small Text"),
			field("customer_satisfied", "Customer Satisfied", "Select", options="Yes\nNo\nNot Recorded", default="Not Recorded"),
			field("sb_notes", "Notes", "Section Break"),
			field("notes", "Notes", "Small Text"),
			field("status", "Status", "Select", options="Scheduled\nIn Progress\nCompleted\nCancelled", default="Scheduled", in_list_view=1),
		],
		autoname="format:DEM-.YYYY.-.#####",
	)
