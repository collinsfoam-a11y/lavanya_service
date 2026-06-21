import frappe
from lavanya_service.setup.masters import ensure_doctype, field


def create_area_perf_log_doctype():
	return ensure_doctype(
		"Area Performance Log",
		[
			field("log_date", "Date", "Date", reqd=1, in_list_view=1, in_standard_filter=1),
			field("area", "Area", "Data", reqd=1, in_list_view=1, in_standard_filter=1),
			field("period", "Period", "Select", options="Daily\nWeekly\nMonthly", default="Daily", in_list_view=1),
			field("sb_vol", "Volume", "Section Break"),
			field("tickets_total", "Total Tickets", "Int", default="0", in_list_view=1),
			field("tickets_closed", "Closed Tickets", "Int", default="0", in_list_view=1),
			field("tickets_overdue", "Overdue Tickets", "Int", default="0", in_list_view=1),
			field("tickets_breached", "Breached Tickets", "Int", default="0", in_list_view=1),
			field("closure_rate_percent", "Closure Rate %", "Percent", default="0.0", in_list_view=1),
		],
		autoname="format:APL-.{area}.-.{log_date}.-.#####",
	)
