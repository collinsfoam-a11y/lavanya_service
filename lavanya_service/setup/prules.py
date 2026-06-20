"""Supplier Penalty Rule and Supplier Penalty Computation doctypes."""

from lavanya_service.setup.masters import ensure_doctype, field

BREACH_TYPES = "\n".join([
	"SLA Breach", "Credit Note Delay", "Replacement Delay",
	"Return Pickup Delay", "Refund Delay", "Part Pending Delay",
	"No Update Delay", "Payment Block Triggered",
])

PENALTY_TYPES = "\n".join([
	"Fixed Amount", "Per Day", "Percentage of Claim",
	"Percentage of Invoice", "Manual Review Only",
])

PENALTY_STATUSES = "\n".join([
	"Draft", "Computed", "Manager Review",
	"Approved", "Waived", "Rejected", "Applied", "Cancelled",
])


def create_penalty_rule_doctype():
	return ensure_doctype(
		"Supplier Penalty Rule",
		[
			field("supplier", "Supplier", "Data", in_list_view=1, in_standard_filter=1),
			field("brand", "Brand", "Link", options="Brand Service Master", in_list_view=1, in_standard_filter=1),
			field("service_flow_type", "Service Flow Type", "Select",
				options="\nCustomer Complaint - Site\nCustomer Product at Store\nStock Complaint\nReplacement / Exchange\nRefund Case\nOut of Warranty Local Service\nExtended Warranty Claim\nInstallation / Demo\nPeriodic / Free Service"),
			field("breach_type", "Breach Type", "Select", options=BREACH_TYPES, reqd=1, in_list_view=1, in_standard_filter=1),
			field("grace_days", "Grace Days", "Int", default="0"),
			field("penalty_type", "Penalty Type", "Select", options=PENALTY_TYPES, reqd=1),
			field("fixed_amount", "Fixed Amount", "Currency"),
			field("percentage_rate", "Percentage Rate %", "Percent"),
			field("per_day_amount", "Per Day Amount", "Currency"),
			field("max_penalty_amount", "Max Penalty Amount", "Currency"),
			field("active", "Active", "Check", default="1", in_list_view=1),
			field("valid_from", "Valid From", "Date"),
			field("valid_to", "Valid To", "Date"),
		],
		autoname="format:PEN-RULE-.#####",
	)


def create_penalty_computation_doctype():
	return ensure_doctype(
		"Supplier Penalty Computation",
		[
			field("ticket", "Ticket", "Link", options="HD Ticket", reqd=1, in_list_view=1, in_standard_filter=1),
			field("supplier", "Supplier", "Data", in_list_view=1),
			field("brand", "Brand", "Link", options="Brand Service Master", in_list_view=1),
			field("service_flow_type", "Service Flow Type", "Data"),
			field("linked_record_type", "Linked Record Type", "Data"),
			field("linked_record", "Linked Record", "Data"),
			field("breach_type", "Breach Type", "Select", options=BREACH_TYPES, reqd=1, in_list_view=1, in_standard_filter=1),
			field("sb_dates", "Dates", "Section Break"),
			field("breach_start_date", "Breach Start Date", "Date", in_list_view=1),
			field("breach_days", "Breach Days", "Int"),
			field("grace_days", "Grace Days", "Int"),
			field("chargeable_days", "Chargeable Days", "Int"),
			field("sb_amounts", "Amounts", "Section Break"),
			field("penalty_type", "Penalty Type", "Data"),
			field("base_amount", "Base Amount", "Currency"),
			field("computed_penalty_amount", "Computed Penalty", "Currency"),
			field("max_penalty_amount", "Max Penalty", "Currency"),
			field("final_penalty_amount", "Final Penalty", "Currency", in_list_view=1),
			field("sb_status", "Status", "Section Break"),
			field("status", "Status", "Select", options=PENALTY_STATUSES, default="Draft", in_list_view=1, in_standard_filter=1),
			field("manager_review_required", "Manager Review Required", "Check", default="0"),
			field("calculation_narration", "Calculation Narration", "Small Text"),
			field("created_from_scheduler", "Created from Scheduler", "Check", default="0"),
			field("sb_approval", "Approval", "Section Break", collapsible=1),
			field("approved_by", "Approved By", "Link", options="User"),
			field("approved_at", "Approved At", "Datetime"),
			field("approval_narration", "Approval Narration", "Small Text"),
			field("waived_by", "Waived By", "Link", options="User"),
			field("waived_at", "Waived At", "Datetime"),
			field("waiver_reason", "Waiver Reason", "Small Text"),
			field("rejected_by", "Rejected By", "Link", options="User"),
			field("rejected_at", "Rejected At", "Datetime"),
			field("rejection_reason", "Rejection Reason", "Small Text"),
		],
		autoname="format:PEN-COMP-.YYYY.-.#####",
	)
