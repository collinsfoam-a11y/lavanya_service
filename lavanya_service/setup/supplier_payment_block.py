import frappe

from lavanya_service.setup.masters import ensure_doctype, field


def create_supplier_payment_block_doctype():
	return ensure_doctype(
		"Supplier Payment Block",
		[
			field("brand", "Brand", "Link", options="Brand Service Master", reqd=1, in_list_view=1, in_standard_filter=1),
			field("service_center", "Service Center", "Link", options="Service Center Master"),
			field("block_status", "Block Status", "Select", options="Active\nReleased\nPending Review", default="Pending Review", in_list_view=1, in_standard_filter=1),
			field("sb_block_details", "Block Details", "Section Break"),
			field("blocked_at", "Blocked At", "Datetime", in_list_view=1),
			field("released_at", "Released At", "Datetime"),
			field("blocked_by", "Blocked By", "Link", options="User"),
			field("block_reason", "Block Reason", "Small Text"),
			field("release_reason", "Release Reason", "Small Text"),
			field("sb_computed", "Computed", "Section Break"),
			field("overdue_ticket_count", "Overdue Ticket Count", "Int", default="0", read_only=1, in_list_view=1),
			field("max_delay_days", "Max Delay Days", "Float", default="0", read_only=1),
		],
		autoname="format:PB-{brand}-.#####",
	)
