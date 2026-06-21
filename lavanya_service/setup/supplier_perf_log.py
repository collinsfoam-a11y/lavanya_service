import frappe
from lavanya_service.setup.masters import ensure_doctype, field


def create_supplier_perf_log_doctype():
	return ensure_doctype(
		"Supplier Performance Log",
		[
			field("log_date", "Date", "Date", reqd=1, in_list_view=1, in_standard_filter=1),
			field("brand", "Brand", "Link", options="Brand Service Master", reqd=1, in_list_view=1, in_standard_filter=1),
			field("service_center", "Service Center", "Link", options="Service Center Master", in_list_view=1),
			field("period", "Period", "Select", options="Daily\nWeekly\nMonthly", default="Daily", in_list_view=1),
			field("sb_vol", "Volume", "Section Break"),
			field("tickets_total", "Total Tickets", "Int", default="0", in_list_view=1),
			field("tickets_breached", "Breached Tickets", "Int", default="0", in_list_view=1),
			field("tickets_on_time", "On-Time Tickets", "Int", default="0", in_list_view=1),
			field("sb_time", "Timing", "Section Break"),
			field("avg_response_hours", "Avg Response (Hours)", "Float", default="0.0"),
			field("avg_resolution_hours", "Avg Resolution (Hours)", "Float", default="0.0"),
			field("sla_compliance_percent", "SLA Compliance %", "Percent", default="0.0", in_list_view=1),
		],
		autoname="format:SPL-.{brand}.-.{log_date}.-.#####",
	)
