"""Phase 1N-6B quick workflow actions for HD Ticket.

These functions are the secure backend layer behind the HD Form Script
"Lavanya Actions" buttons. The buttons are only a convenience layer; every
function here independently enforces:

  * role permission (action-specific allowed roles)
  * valid status transition (no acting on Closed/Cancelled tickets)
  * required fields
  * protected field rules (via explicit role checks + existing validation path)
  * no forbidden side effects (only the receipt action may create a document)

Ticket writes run through ``_save_ticket`` which performs an explicit
doctype-level write-permission check for the acting user and then saves with
elevated permissions. Elevation is intentional and is wrapped by the explicit,
action-specific role gate above it: the permlevel/protected-field guard in
``lavanya_service.validations.hd_ticket`` was designed for direct form edits and
would otherwise block role-correct quick actions (for example Front Desk running
"Product Ready", which legitimately needs to touch service-coordination fields).
All other business validations (status, required fields, closure rules) still run
during the elevated save.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, today

from lavanya_service.setup.hd_ticket_fields import (
	CLOSURE_TYPE_OPTIONS,
	PENDING_REASON_OPTIONS,
)


TICKET_DOCTYPE = "HD Ticket"
RECEIPT_DOCTYPE = "Service Product Receipt"

ROLE_MANAGER = "Lavanya Manager"
ROLE_COORDINATOR = "Lavanya Service Coordinator"
ROLE_AGENT = "Lavanya Helpdesk Agent"
ROLE_FRONT_DESK = "Lavanya Front Desk"
ROLE_VIEWER = "Lavanya Viewer"

# Users / roles that may always run any action.
BYPASS_ROLES = {"System Manager"}

# Statuses that are terminal: quick actions may not mutate these tickets.
FINAL_STATUSES = {"Closed", "Cancelled"}

PRODUCT_AT_STORE_TYPE = "Customer Product at Store"

_PENDING_REASON_SET = set(PENDING_REASON_OPTIONS.split("\n"))
_CLOSURE_TYPE_SET = set(CLOSURE_TYPE_OPTIONS.split("\n"))

# Mapping of the "Follow Up Service Center" result to backend behaviour.
FOLLOW_UP_RESULTS = {
	"Service center contacted",
	"Technician assigned",
	"Customer not reachable",
	"Service completed",
	"Part pending",
	"Approval pending",
}

# Select option used to record "approval pending" within the existing
# Pending Reason option list (there is no generic "Approval Pending" option).
APPROVAL_PENDING_REASON = "Estimate Approval Pending"
# Select option used to record an outstanding invoice within the limited
# Registration Pending Reason option list.
INVOICE_REGISTRATION_REASON = "Invoice Missing"


# ---------------------------------------------------------------------------
# Role / permission helpers
# ---------------------------------------------------------------------------


def _acting_user():
	return frappe.session.user


def _user_roles():
	if _acting_user() == "Administrator":
		return {"Administrator"}
	return set(frappe.get_roles(_acting_user()))


def _has_any_role(allowed):
	if _acting_user() == "Administrator":
		return True
	roles = _user_roles()
	return bool(roles.intersection(set(allowed) | BYPASS_ROLES))


def _require_roles(action_label, allowed):
	if not _has_any_role(allowed):
		frappe.throw(
			_("You are not permitted to run '{0}'. Allowed roles: {1}.").format(
				action_label, ", ".join(sorted(allowed))
			),
			frappe.PermissionError,
		)


def _require(value, label):
	if value is None or str(value).strip() == "":
		frappe.throw(_("{0} is required.").format(label))
	return str(value).strip()


def _load_ticket(ticket_name):
	ticket_name = _require(ticket_name, "Ticket")
	if not frappe.db.exists(TICKET_DOCTYPE, ticket_name):
		frappe.throw(_("HD Ticket {0} not found.").format(ticket_name))

	if not frappe.has_permission(TICKET_DOCTYPE, "read", user=_acting_user()):
		frappe.throw(_("You are not permitted to read this ticket."), frappe.PermissionError)

	return frappe.get_doc(TICKET_DOCTYPE, ticket_name)


def _block_if_final(doc):
	if doc.status in FINAL_STATUSES:
		frappe.throw(
			_("Ticket {0} is {1}; quick actions are not allowed on closed or cancelled tickets.").format(
				doc.name, doc.status
			)
		)


def _save_ticket(doc):
	"""Persist ticket changes preserving the real actor in the audit trail.

	The quick action has already enforced an explicit, action-specific role
	check, so we bypass the Lavanya protected-field guard via an internal flag
	rather than impersonating Administrator. This keeps ``modified_by`` (and
	any version/comment authorship) pointed at the real staff user (audit B1).
	"""
	acting_user = _acting_user()
	if not frappe.has_permission(TICKET_DOCTYPE, "write", doc=doc, user=acting_user):
		frappe.throw(_("You are not permitted to update this ticket."), frappe.PermissionError)

	doc.flags.ignore_lavanya_field_guard = True
	doc.save(ignore_permissions=True)

	doc.reload()
	return doc


def _result(doc, message):
	return {
		"ok": True,
		"ticket": doc.name,
		"status": doc.status,
		"message": message,
	}


def _validate_pending_reason(value):
	value = _require(value, "Pending Reason")
	if value not in _PENDING_REASON_SET:
		frappe.throw(_("'{0}' is not a valid Pending Reason.").format(value))
	return value


def _validate_closure_type(value):
	value = _require(value, "Closure Type")
	if value not in _CLOSURE_TYPE_SET:
		frappe.throw(_("'{0}' is not a valid Closure Type.").format(value))
	return value


# ---------------------------------------------------------------------------
# Quick actions
# ---------------------------------------------------------------------------


def register_brand_complaint(
	ticket_name,
	brand_ticket_number=None,
	registration_date=None,
	next_follow_up_date=None,
	service_center=None,
):
	_require_roles("Register Brand Complaint", {ROLE_MANAGER, ROLE_COORDINATOR})

	brand_ticket_number = _require(brand_ticket_number, "Brand Ticket Number")
	registration_date = _require(registration_date, "Registration Date")
	next_follow_up_date = _require(next_follow_up_date, "Next Follow-up Date")

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.manufacturer_registration_required = "Yes"
	doc.manufacturer_registered = "Yes"
	doc.brand_ticket_number = brand_ticket_number
	doc.registration_date = registration_date
	doc.next_follow_up_date = next_follow_up_date
	doc.pending_reason = "Service Follow-up Required"
	if service_center:
		doc.service_center = service_center
	doc.status = "Brand Registered"
	doc.followup_stage = "registration_done"

	_save_ticket(doc)
	return _result(doc, _("Brand complaint registered"))


def need_invoice_from_customer(ticket_name, next_follow_up_date=None, note=None):
	_require_roles(
		"Need Invoice from Customer", {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_AGENT}
	)

	next_follow_up_date = _require(next_follow_up_date, "Next Follow-up Date")

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.status = "Waiting on Customer"
	doc.pending_reason = "Invoice Pending"
	doc.next_follow_up_date = next_follow_up_date
	if frappe.get_meta(TICKET_DOCTYPE).has_field("registration_pending_reason"):
		doc.registration_pending_reason = INVOICE_REGISTRATION_REASON

	_save_ticket(doc)
	return _result(doc, _("Invoice requested from customer"))


def follow_up_service_center(ticket_name, follow_up_result=None, next_follow_up_date=None):
	_require_roles(
		"Follow Up Service Center", {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_AGENT}
	)

	follow_up_result = _require(follow_up_result, "Follow-up Result")
	if follow_up_result not in FOLLOW_UP_RESULTS:
		frappe.throw(_("'{0}' is not a valid Follow-up Result.").format(follow_up_result))

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	if follow_up_result == "Service completed":
		doc.status = "Resolved"
		doc.pending_reason = ""
		if next_follow_up_date:
			doc.next_follow_up_date = next_follow_up_date
	elif follow_up_result == "Part pending":
		next_follow_up_date = _require(next_follow_up_date, "Next Follow-up Date")
		doc.status = "Waiting on Part / Approval"
		doc.pending_reason = "Part Pending"
		doc.next_follow_up_date = next_follow_up_date
	elif follow_up_result == "Approval pending":
		next_follow_up_date = _require(next_follow_up_date, "Next Follow-up Date")
		doc.status = "Waiting on Part / Approval"
		doc.pending_reason = APPROVAL_PENDING_REASON
		doc.next_follow_up_date = next_follow_up_date
	else:
		next_follow_up_date = _require(next_follow_up_date, "Next Follow-up Date")
		doc.status = "In Progress"
		doc.pending_reason = "Service Follow-up Required"
		doc.next_follow_up_date = next_follow_up_date

	_save_ticket(doc)

	# Structured follow-up log entry — a tagged comment so each follow-up is a
	# countable history item with its outcome (the SPA reads these back as the
	# follow-up log and an attempts count).
	entry = "[Follow-up] {0}".format(follow_up_result)
	if next_follow_up_date:
		entry += " · next {0}".format(next_follow_up_date)
	doc.add_comment("Comment", entry)

	return _result(doc, _("Service centre follow-up recorded: {0}").format(follow_up_result))


def waiting_for_part(ticket_name, pending_reason=None, next_follow_up_date=None):
	_require_roles("Waiting for Part", {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_AGENT})

	pending_reason = _validate_pending_reason(pending_reason)
	next_follow_up_date = _require(next_follow_up_date, "Next Follow-up Date")

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.status = "Waiting on Part / Approval"
	doc.pending_reason = pending_reason
	doc.next_follow_up_date = next_follow_up_date
	doc.followup_stage = "part_pending"

	_save_ticket(doc)
	return _result(doc, _("Ticket marked waiting on part / approval"))


def mark_product_ready(ticket_name, next_follow_up_date=None):
	_require_roles("Product Ready", {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_FRONT_DESK})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.status = "Ready for Pickup"
	doc.pending_reason = "Customer Pickup Pending"
	doc.next_follow_up_date = next_follow_up_date or today()

	_save_ticket(doc)
	return _result(doc, _("Product marked ready for pickup"))


def customer_confirmed(ticket_name, work_narration=None, closure_type=None):
	_require_roles("Customer Confirmed", {ROLE_MANAGER, ROLE_COORDINATOR})

	work_narration = _require(work_narration, "Work Narration")
	closure_type = _validate_closure_type(closure_type)

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.customer_confirmation_received = "Yes"
	doc.work_narration = work_narration
	doc.closure_type = closure_type
	doc.closed_by = _acting_user()
	doc.closure_date = now_datetime()
	doc.status = "Closed"

	_save_ticket(doc)
	return _result(doc, _("Customer confirmed; ticket closed"))


def close_ticket(
	ticket_name,
	work_narration=None,
	closure_type=None,
	customer_confirmation_received=None,
):
	_require_roles("Close Ticket", {ROLE_MANAGER, ROLE_COORDINATOR})

	work_narration = _require(work_narration, "Work Narration")
	closure_type = _validate_closure_type(closure_type)
	customer_confirmation_received = _require(
		customer_confirmation_received, "Customer Confirmation Received"
	)
	if customer_confirmation_received != "Yes":
		frappe.throw(_("Customer Confirmation Received must be Yes to close the ticket."))

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	# Block closure unless customer satisfaction is documented (Satisfied or Not Required).
	# This prevents closing tickets after brand/service-center says "completed" without
	# customer confirmation — a critical real-world follow-up guarantee.
	satisfaction = doc.customer_satisfaction_status
	if satisfaction not in ("Satisfied", "Not Required"):
		frappe.throw(_(
			"Ticket cannot be closed. Customer satisfaction must be 'Satisfied' "
			"or documented as 'Not Required' (current: {0})."
		).format(satisfaction or "Not Set"))

	doc.status = "Closed"
	doc.work_narration = work_narration
	doc.closure_type = closure_type
	doc.customer_confirmation_received = customer_confirmation_received
	doc.closed_by = _acting_user()
	doc.closure_date = now_datetime()

	_save_ticket(doc)
	return _result(doc, _("Ticket closed"))


def create_product_receipt(
	ticket_name,
	accessories_received=None,
	physical_condition=None,
	product_type=None,
	brand=None,
	model_no=None,
	serial_no=None
):
	_require_roles(
		"Create Product Receipt", {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_FRONT_DESK}
	)

	if not frappe.db.exists("DocType", RECEIPT_DOCTYPE):
		frappe.throw(_("{0} DocType is not installed.").format(RECEIPT_DOCTYPE))

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	if doc.ticket_type != PRODUCT_AT_STORE_TYPE:
		frappe.throw(
			_("Product Receipt can only be created for '{0}' tickets.").format(
				PRODUCT_AT_STORE_TYPE
			)
		)

	if doc.get("service_product_receipt"):
		frappe.throw(
			_("Ticket {0} already has a linked Service Product Receipt ({1}).").format(
				doc.name, doc.service_product_receipt
			)
		)

	receipt = frappe.new_doc(RECEIPT_DOCTYPE)
	receipt.naming_series = "LV-SR-.YYYY.-.####"
	receipt.ticket = doc.name
	receipt.receipt_date = now_datetime()
	receipt.current_custody_status = "Received at Store"
	receipt.received_by = _acting_user()
	receipt.customer_name = doc.get("customer_name")
	receipt.phone = doc.get("phone_1")
	receipt.address = doc.get("address")
	
	# Use provided values, fallback to ticket values
	receipt.product_type = product_type if product_type else doc.get("product_type")
	receipt.brand = brand if brand else doc.get("brand")
	receipt.model_no = model_no if model_no else doc.get("model_no")
	receipt.serial_no = serial_no if serial_no else doc.get("serial_no")
	
	if accessories_received:
		receipt.accessories_received = accessories_received
	if physical_condition:
		receipt.physical_condition = physical_condition

	receipt.append("custody_log", {
		"custody_action": "Received",
		"custody_status": "Received at Store",
		"action_datetime": now_datetime(),
		"from_party": "Customer",
		"to_party": "Store",
		"handled_by": _acting_user(),
	})

	receipt.insert()

	# Link the receipt back to the ticket using a conditional UPDATE so that
	# if a concurrent request already linked a different receipt, we never
	# silently overwrite it (race-condition guard). ``service_product_receipt``
	# is a protected service-coordination field; Front Desk is an allowed role
	# for this action but is not a service-coordination writer, so the link is
	# set directly. This is the documented, narrowly-scoped permission bypass,
	# gated by the explicit action-role check above.
	frappe.db.sql(
		"""UPDATE `tabHD Ticket`
		   SET service_product_receipt = %s
		   WHERE name = %s
		     AND (service_product_receipt IS NULL OR service_product_receipt = '')""",
		(receipt.name, doc.name),
	)

	doc.reload()
	return {
		"ok": True,
		"ticket": doc.name,
		"status": doc.status,
		"receipt": receipt.name,
		"message": _("Service Product Receipt {0} created").format(receipt.name),
	}


# ---------------------------------------------------------------------------
# Follow-up tracking quick actions (Phase 1N-6B)
# ---------------------------------------------------------------------------

ESCALATION_LEVELS = ["None", "L1 - Agent Follow-up", "L2 - Coordinator Escalation", "L3 - Manager Escalation", "L4 - Owner / Brand Manager Escalation"]
_SATISFACTION_VALUES = {"Satisfied", "Not Satisfied", "Customer Not Reachable", "Not Required"}
_CHANNEL_MAP = {
	"Phone": "Informed by Call",
	"WhatsApp": "Informed by WhatsApp",
	"SMS": "Informed by SMS",
	"Direct": "Informed by Call",
	"Email": "Informed by Call",
}


def _increment_escalation(current):
	"""Move up one level in the escalation ladder."""
	if not current or current == "None":
		return "L1 - Agent Follow-up"
	if current == "L1 - Agent Follow-up":
		return "L2 - Coordinator Escalation"
	if current == "L2 - Coordinator Escalation":
		return "L3 - Manager Escalation"
	if current == "L3 - Manager Escalation":
		return "L4 - Owner / Brand Manager Escalation"
	return "L4 - Owner / Brand Manager Escalation"


def _set_last_followup(doc, summary):
	"""Update the last-followup summary and timestamp."""
	doc.last_followup_summary = summary[:280] if summary else summary
	doc.last_followup_at = now_datetime()


def verify_technician_called(ticket_name, technician_name=None, notes=None):
	_require_roles("Verify Technician Called", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.followup_stage = "technician_called"

	entry = "[Follow-up] Verify Technician Called"
	if technician_name:
		entry += " — Technician: {0}".format(technician_name)
	if notes:
		entry += " · Notes: {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Technician called verified"))


def verify_technician_visit(ticket_name, technician_name=None, visit_result=None, notes=None):
	_require_roles("Verify Technician Visit", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.followup_stage = "technician_visited"

	entry = "[Follow-up] Verify Technician Visit"
	if technician_name:
		entry += " — Technician: {0}".format(technician_name)
	if visit_result:
		entry += " · Result: {0}".format(visit_result)
	if notes:
		entry += " · Notes: {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Technician visit verified"))


def record_sc_followup(ticket_name, follow_up_result=None, next_follow_up_date=None, customer_informed_status=None):
	_require_roles("Record SC Follow-up", {ROLE_MANAGER, ROLE_COORDINATOR})

	follow_up_result = _require(follow_up_result, "Follow-up Result")
	if follow_up_result not in FOLLOW_UP_RESULTS:
		frappe.throw(_("'{0}' is not a valid Follow-up Result.").format(follow_up_result))
	customer_informed_status = _require(customer_informed_status, "Customer Informed Status")

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.followup_stage = "sc_followup_done"
	doc.last_service_center_followup = now_datetime()
	doc.customer_informed_status = customer_informed_status
	if next_follow_up_date:
		doc.next_follow_up_date = next_follow_up_date

	entry = "[Follow-up] Service Center Follow-up — Result: {0}".format(follow_up_result)
	if next_follow_up_date:
		entry += " · Next: {0}".format(next_follow_up_date)
	entry += " · Customer: {0}".format(customer_informed_status)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("SC follow-up recorded: {0}").format(follow_up_result))


def inform_customer(ticket_name, message=None, channel=None):
	_require_roles("Inform Customer", {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_AGENT})

	channel = _require(channel, "Channel")

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.followup_stage = "customer_informed"
	doc.customer_informed = "Yes"
	doc.customer_informed_channel = channel
	doc.customer_informed_at = now_datetime()
	doc.customer_informed_by = _acting_user()
	doc.customer_informed_status = _CHANNEL_MAP.get(channel, "Informed by Call")

	entry = "[Follow-up] Inform Customer — Channel: {0}".format(channel)
	if message:
		entry += " · Message: {0}".format(message)
	# Auto-wire AI suggested customer message into narration when available
	ai_msg = doc.get("ai_suggested_customer_message")
	if ai_msg and not message:
		entry += " · AI message: {0}".format(ai_msg[:280])
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Customer informed via {0}").format(channel))


def mark_no_update(ticket_name, notes=None):
	_require_roles("Mark No Update", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.followup_stage = "no_technician_update"
	doc.escalation_level = _increment_escalation(doc.escalation_level)
	doc.no_update_count = (doc.no_update_count or 0) + 1

	entry = "[Follow-up] Mark No Update — Escalation: {0}".format(doc.escalation_level)
	entry += " · Count: {0}".format(doc.no_update_count)
	if notes:
		entry += " · Notes: {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("No update marked; escalated to {0}").format(doc.escalation_level))


def escalate_case(ticket_name, reason=None):
	_require_roles("Escalate Case", {ROLE_MANAGER, ROLE_COORDINATOR})

	reason = _require(reason, "Reason")

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	prev_level = doc.escalation_level or "None"
	doc.escalation_level = _increment_escalation(doc.escalation_level)

	entry = "[Follow-up] Escalate Case — From: {0} → {1}".format(prev_level, doc.escalation_level)
	entry += " · Reason: {0}".format(reason)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Case escalated from {0} to {1}").format(prev_level, doc.escalation_level))


def record_satisfaction(ticket_name, satisfaction_status=None, notes=None):
	_require_roles("Record Satisfaction", {ROLE_MANAGER, ROLE_COORDINATOR})

	satisfaction_status = _require(satisfaction_status, "Satisfaction Status")
	if satisfaction_status not in _SATISFACTION_VALUES:
		frappe.throw(_("'{0}' is not a valid satisfaction status.").format(satisfaction_status))

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.customer_satisfaction_status = satisfaction_status

	if satisfaction_status == "Satisfied":
		doc.followup_stage = "customer_satisfied"
	elif satisfaction_status == "Not Satisfied":
		doc.followup_stage = "customer_not_satisfied"
	else:
		doc.followup_stage = "customer_confirmation_pending"

	entry = "[Follow-up] Record Satisfaction — Status: {0}".format(satisfaction_status)
	if notes:
		entry += " · Notes: {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Customer satisfaction recorded: {0}").format(satisfaction_status))


def record_customer_approval(ticket_name, approved_amount=None, payment_status=None, notes=None):
	_require_roles("Record Customer Approval", {ROLE_MANAGER, ROLE_COORDINATOR})

	approved_amount = _require(approved_amount, "Approved Amount")

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.customer_approved_amount = float(approved_amount) if approved_amount else 0
	if payment_status:
		doc.payment_status = payment_status

	entry = "[Follow-up] Record Approval — Amount: {0}".format(approved_amount)
	if payment_status:
		entry += " · Payment: {0}".format(payment_status)
	if notes:
		entry += " · Notes: {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Customer approval recorded: amount {0}").format(approved_amount))
