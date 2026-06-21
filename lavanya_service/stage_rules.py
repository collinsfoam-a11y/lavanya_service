"""Service-stage rules — the single source of truth for the stage layer added on
top of the existing SPA (per docs/spa_alignment_delta_implementation_plan.md).

This adds service_flow_type / current_service_stage / next_action as a layer
ABOVE Helpdesk status; it does NOT replace status or Today's Work. Option lists
are deliberately controlled (the plan says "start controlled, not hundreds").
"""

# ── Option lists (newline-joined for Select fields) ────────────────────────────
SERVICE_FLOW_TYPES = [
	"Customer Complaint - Site",
	"Customer Product at Store",
	"Installation / Demo",
	"Periodic / Free Service",
	"Stock Complaint",
	"Out of Warranty Local Service",
	"Extended Warranty Claim",
	"Replacement / Exchange",
	"Refund Case",
	"Finance Sale Service Issue",
	"Reopened / Repeat Complaint",
]

# Controlled stage set (delta plan §4.3), grouped here for readability.
CURRENT_SERVICE_STAGES = [
	# Intake
	"Complaint Received", "Details Pending", "Warranty Check Pending",
	# Brand warranty
	"Brand Registration Pending", "Brand Registered", "Service Center Follow-up",
	# Extended warranty
	"Extended Warranty Check Pending", "Claim Registration Pending", "Provider Follow-up", "Provider Denied",
	# Technician
	"Technician Visit Pending", "Technician Visited - Issue Pending",
	# Waiting
	"Spare Pending", "Estimate Approval Pending", "Customer Not Reachable", "Waiting on Customer",
	# Product at store (store service)
	"Product Received at Store", "Brand SC Notified", "Brand SC Picked Up", "Brand SC Diagnosis Pending", "Diagnosis Received", "Product Returned to Store", "Customer Notified for Collection", "Product Handed Over",
	# Installation / Demo
	"Installation Registration Pending", "Installation Technician Visit Pending", "Demo Scheduled", "Installation Completed",
	# Replacement / Exchange
	"Old Unit Collected", "New Unit Dispatched", "Brand Reimbursement Pending", "Reimbursement Received",
	# Return / Refund
	"Return Requested", "Return Reason Verified", "Brand Notified for Return", "Customer Refund Processed",
	# Periodic service
	"Periodic Service Due", "Customer Contact Pending", "Service Scheduled", "Feedback Pending",
	# Stock
	"Stock Proof Pending", "Supplier Follow-up Pending", "Credit Note Pending", "Supplier Notified", "Credit Note Received", "Replacement Pending", "Stock Decision Pending",
	# Closure
	"Customer Verification Pending", "Closure Confirmation Pending", "Closed", "Cancelled",
]

# Controlled next-action set (the plan lists actions per flow; this is the common
# union used as Select options — the per-stage default lives in STAGE_DEFAULT_ACTION).
NEXT_ACTIONS = [
	"Check Warranty", "Request Missing Details", "Register with Brand", "Follow up Service Center",
	"Schedule Technician Visit", "Await Technician Visit", "Order Spare / Part", "Await Approval",
	"Inform Customer", "Call Customer", "Await Customer Response", "Verify with Customer",
	"Confirm Closure", "Collect Payment", "Register Extended Warranty Claim", "Follow up Provider",
	"Request Documents", "Capture Proof", "Follow up Supplier", "Hand to Service Center",
	"Mark Returned to Store", "Mark Ready for Pickup", "Deliver to Customer", "Schedule Service",
	"Record Feedback", "Reschedule Follow-up", "Manager Override",
	# Expansion: store service
	"Notify Brand SC for Pickup", "Await Brand SC Diagnosis", "Record Diagnosis Received",
	"Notify Customer for Collection", "Hand Over Product",
	# Expansion: replacement
	"Arrange Old Unit Collection", "Dispatch New Unit", "Follow Up Brand Reimbursement", "Record Reimbursement Received",
	# Expansion: return
	"Verify Return Reason", "Notify Brand for Return", "Process Customer Refund",
]

OVERDUE_STATUSES = ["Not Due", "Due Soon", "Overdue", "Breached"]
ESCALATION_LEVELS = ["None", "L1 - Agent Follow-up", "L2 - Coordinator Escalation", "L3 - Manager Escalation", "L4 - Owner / Brand Manager Escalation"]
CUSTOMER_INFORMED_OPTIONS = ["Yes", "No", "Not Required"]
CUSTOMER_INFORMED_CHANNELS = ["Phone", "WhatsApp", "Direct", "SMS", "Email"]

# Statuses (status_category 'Resolved') that mean the ticket is no longer active.
TERMINAL_STAGES = {"Closed", "Cancelled"}

# ── Defaults / mappings ────────────────────────────────────────────────────────
DEFAULT_STAGE = "Complaint Received"
DEFAULT_NEXT_ACTION = "Check Warranty"

# Existing ticket_type -> new service_flow_type (so existing data maps cleanly).
TICKET_TYPE_TO_FLOW = {
	"Customer Complaint - Site": "Customer Complaint - Site",
	"Customer Product at Store": "Customer Product at Store",
	"Stock Complaint": "Stock Complaint",
	"Installation / Demo": "Installation / Demo",
	"Replacement / DOA": "Replacement / Exchange",
	"Out of Warranty Local Service": "Out of Warranty Local Service",
	"Free Service": "Periodic / Free Service",
}

# service_path -> service_flow_type (for the new sub-flows).
SERVICE_PATH_TO_FLOW = {
	"store_service": "Customer Product at Store",
	"replacement_brand": "Replacement / Exchange",
	"return_service": "Customer Complaint - Site",
}

# Ordered stages per flow for stage advancement.
FLOW_STAGES_ORDERED = {
	"Customer Complaint - Site": [
		"Complaint Received", "Details Pending", "Warranty Check Pending",
		"Brand Registration Pending", "Brand Registered", "Service Center Follow-up",
		"Technician Visit Pending", "Technician Visited - Issue Pending",
		"Spare Pending", "Estimate Approval Pending",
		"Customer Not Reachable", "Waiting on Customer",
		"Return Requested", "Return Reason Verified", "Brand Notified for Return", "Customer Refund Processed",
		"Customer Verification Pending", "Closure Confirmation Pending",
	],
	"Customer Product at Store": [
		"Product Received at Store", "Brand SC Notified", "Brand SC Picked Up",
		"Brand SC Diagnosis Pending", "Diagnosis Received",
		"Product Returned to Store", "Customer Notified for Collection", "Product Handed Over",
		"Customer Verification Pending", "Closure Confirmation Pending",
	],
	"Installation / Demo": [
		"Installation Registration Pending", "Installation Technician Visit Pending",
		"Demo Scheduled", "Installation Completed",
		"Customer Verification Pending", "Closure Confirmation Pending",
	],
	"Periodic / Free Service": [
		"Periodic Service Due", "Customer Contact Pending", "Service Scheduled", "Feedback Pending",
		"Customer Verification Pending", "Closure Confirmation Pending",
	],
	"Stock Complaint": [
		"Stock Proof Pending", "Supplier Follow-up Pending", "Credit Note Pending",
		"Supplier Notified", "Credit Note Received", "Replacement Pending", "Stock Decision Pending",
		"Customer Verification Pending", "Closure Confirmation Pending",
	],
	"Out of Warranty Local Service": [
		"Complaint Received", "Details Pending", "Warranty Check Pending",
		"Technician Visit Pending", "Technician Visited - Issue Pending",
		"Spare Pending", "Estimate Approval Pending",
		"Customer Not Reachable", "Waiting on Customer",
		"Customer Verification Pending", "Closure Confirmation Pending",
	],
	"Extended Warranty Claim": [
		"Extended Warranty Check Pending", "Claim Registration Pending", "Provider Follow-up", "Provider Denied",
		"Customer Verification Pending", "Closure Confirmation Pending",
	],
	"Replacement / Exchange": [
		"Complaint Received", "Warranty Check Pending",
		"Old Unit Collected", "New Unit Dispatched",
		"Brand Reimbursement Pending", "Reimbursement Received",
		"Customer Verification Pending", "Closure Confirmation Pending",
	],
	"Refund Case": [
		"Complaint Received", "Details Pending",
		"Return Requested", "Return Reason Verified", "Brand Notified for Return", "Customer Refund Processed",
		"Customer Verification Pending", "Closure Confirmation Pending",
	],
	"Finance Sale Service Issue": [
		"Complaint Received", "Details Pending",
		"Customer Verification Pending", "Closure Confirmation Pending",
	],
	"Reopened / Repeat Complaint": [
		"Complaint Received",
		"Customer Verification Pending", "Closure Confirmation Pending",
	],
}


def derive_flow_from_path(path):
	return SERVICE_PATH_TO_FLOW.get(path)




# ── H1 Fix 5: Bridge between current_service_stage and followup_stage ──────────
# current_service_stage = canonical workflow stage (the "where am I" field)
# followup_stage = post-brand follow-up sub-stage (the "what follow-up step am I on" field)
# This mapping allows code to derive a current_service_stage from a followup_stage
# when a quick action only sets followup_stage.
FOLLOWUP_STAGE_TO_SERVICE_STAGE = {
	"registration_done": "Brand Registered",
	"part_pending": "Spare Pending",
	"technician_called": "Service Center Follow-up",
	"technician_visited": "Service Center Follow-up",
	"sc_followup_done": "Service Center Follow-up",
	"customer_informed": "Waiting on Customer",
	"no_technician_update": "Customer Not Reachable",
	"customer_satisfied": "Customer Verification Pending",
	"customer_not_satisfied": "Customer Verification Pending",
	"customer_confirmation_pending": "Customer Verification Pending",
}


def derive_stage_from_followup(followup_stage):
	"""Map a followup_stage value to its corresponding current_service_stage."""
	return FOLLOWUP_STAGE_TO_SERVICE_STAGE.get(followup_stage)

def get_next_stage(stage, flow):
	ordered = FLOW_STAGES_ORDERED.get(flow, [])
	if not ordered:
		return None
	try:
		idx = ordered.index(stage)
		if idx + 1 < len(ordered):
			return ordered[idx + 1]
	except ValueError:
		pass
	return None


# Per-stage default next action (used when assigning defaults / advancing).
STAGE_DEFAULT_ACTION = {
	"Complaint Received": "Check Warranty",
	"Details Pending": "Request Missing Details",
	"Warranty Check Pending": "Check Warranty",
	"Brand Registration Pending": "Register with Brand",
	"Brand Registered": "Follow up Service Center",
	"Service Center Follow-up": "Follow up Service Center",
	"Extended Warranty Check Pending": "Register Extended Warranty Claim",
	"Claim Registration Pending": "Register Extended Warranty Claim",
	"Provider Follow-up": "Follow up Provider",
	"Technician Visit Pending": "Await Technician Visit",
	"Spare Pending": "Order Spare / Part",
	"Estimate Approval Pending": "Await Approval",
	"Customer Not Reachable": "Call Customer",
	"Waiting on Customer": "Await Customer Response",
	"Product Received at Store": "Hand to Service Center",
	"Brand SC Notified": "Await Brand SC Diagnosis",
	"Brand SC Picked Up": "Follow up Service Center",
	"Brand SC Diagnosis Pending": "Follow up Service Center",
	"Diagnosis Received": "Inform Customer",
	"Product Returned to Store": "Notify Customer for Collection",
	"Customer Notified for Collection": "Hand Over Product",
	"Product Handed Over": "Confirm Closure",
	"Old Unit Collected": "Dispatch New Unit",
	"New Unit Dispatched": "Follow Up Brand Reimbursement",
	"Brand Reimbursement Pending": "Follow Up Brand Reimbursement",
	"Reimbursement Received": "Confirm Closure",
	"Return Requested": "Verify Return Reason",
	"Return Reason Verified": "Notify Brand for Return",
	"Brand Notified for Return": "Process Customer Refund",
	"Customer Refund Processed": "Confirm Closure",
	"Demo Scheduled": "Await Technician Visit",
	"Supplier Notified": "Follow up Supplier",
	"Credit Note Received": "Confirm Closure",
	"Periodic Service Due": "Call Customer",
	"Stock Proof Pending": "Capture Proof",
	"Customer Verification Pending": "Verify with Customer",
	"Closure Confirmation Pending": "Confirm Closure",
}

# Per-stage SLA: minutes until stage_due_at (delta plan §6 / detailed §6). Used by
# Delta Sprint 2's Due Soon / overdue calculation; safe to keep here now.
_H = 60
STAGE_SLA_MINUTES = {
	"Complaint Received": 30,
	"Details Pending": 2 * _H,
	"Warranty Check Pending": 4 * _H,
	"Brand Registration Pending": 4 * _H,
	"Extended Warranty Check Pending": 4 * _H,
	"Claim Registration Pending": 4 * _H,
	"Brand Registered": 24 * _H,
	"Service Center Follow-up": 24 * _H,
	"Provider Follow-up": 24 * _H,
	"Technician Visit Pending": 24 * _H,
	"Spare Pending": 24 * _H,
	"Estimate Approval Pending": 24 * _H,
	"Brand SC Diagnosis Pending": 48 * _H,
	"Brand Reimbursement Pending": 72 * _H,
	"Return Reason Verified": 24 * _H,
	"Brand Notified for Return": 72 * _H,
	"Customer Contact Pending": 24 * _H,
	"Stock Proof Pending": 2 * _H,
	"Supplier Follow-up Pending": 24 * _H,
	"Customer Verification Pending": 24 * _H,
	"Closure Confirmation Pending": 24 * _H,
}
DEFAULT_SLA_MINUTES = 24 * _H

# Pre-overdue lead time by SLA bucket (delta plan §7).
def pre_overdue_lead_minutes(sla_minutes):
	if sla_minutes <= 30:
		return 10
	if sla_minutes <= 2 * _H:
		return 30
	if sla_minutes <= 8 * _H:
		return _H
	return 4 * _H


def flow_for_ticket_type(ticket_type):
	return TICKET_TYPE_TO_FLOW.get(ticket_type, "Customer Complaint - Site")


# ── Due-Soon / overdue / escalation (delta plan §7, Sprint 2) ──────────────────
# Stage-SLA first (stage_due_at / pre_overdue_alert_at); fall back to the existing
# date-based next_follow_up_date so old tickets without stage fields keep working.
def compute_overdue_status(stage_due_at=None, pre_overdue_alert_at=None, next_follow_up_date=None, now=None):
	from frappe.utils import getdate, get_datetime, now_datetime, today as _today

	now = now or now_datetime()
	if stage_due_at:
		due = get_datetime(stage_due_at)
		if now >= due:
			return "Overdue"
		if pre_overdue_alert_at and get_datetime(pre_overdue_alert_at) <= now < due:
			return "Due Soon"
		return "Not Due"
	# Fallback: existing date-based due-today / overdue.
	if next_follow_up_date:
		d, t = getdate(next_follow_up_date), getdate(_today())
		if d < t:
			return "Overdue"
		if d == t:
			return "Due Soon"
	return "Not Due"


def overdue_days(stage_due_at=None, next_follow_up_date=None, now=None):
	from frappe.utils import getdate, get_datetime, now_datetime, today as _today, date_diff

	now = now or now_datetime()
	if stage_due_at:
		return max(0, int((now - get_datetime(stage_due_at)).total_seconds() // 86400))
	if next_follow_up_date:
		return max(0, date_diff(getdate(_today()), getdate(next_follow_up_date)))
	return 0


def compute_promise_status(promised_at=None, stored_status=None, now=None):
	"""Live customer-promise status: a Pending promise whose time has passed is
	Breached (unless staff already marked it Kept). None/Pending/Kept/Breached."""
	if stored_status == "Kept":
		return "Kept"
	if not promised_at:
		return stored_status or "None"
	from frappe.utils import get_datetime, now_datetime

	now = now or now_datetime()
	if now > get_datetime(promised_at):
		return "Breached"
	return "Pending"


def assign_defaults(doc):
	"""Populate stage fields for a new/unstaged ticket without overriding anything
	staff already set. Safe to call on validate — never touches terminal tickets."""
	if doc.get("status") in TERMINAL_STAGES:
		return
	if not doc.get("service_flow_type"):
		doc.service_flow_type = flow_for_ticket_type(doc.get("ticket_type"))
	if not doc.get("current_service_stage"):
		doc.current_service_stage = DEFAULT_STAGE
	if not doc.get("next_action"):
		doc.next_action = STAGE_DEFAULT_ACTION.get(doc.get("current_service_stage"), DEFAULT_NEXT_ACTION)
