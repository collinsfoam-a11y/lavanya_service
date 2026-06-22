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

# H1 Fix 4: customer_informed_status is the canonical operational field for
# "has the customer been informed?" It is a Select with values like
# "Informed by Call", "Informed by WhatsApp", etc. The older customer_informed
# (Yes/No/Not Required) field is kept for backward compatibility but all new
# writes should set customer_informed_status as the source of truth.
# Metadata fields: customer_informed_channel, customer_informed_at, customer_informed_by.

import frappe
from frappe import _
from frappe.utils import now_datetime, today, add_to_date, getdate

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

# (service_flow_type, linked_doctype, check_field, acceptable_values_or_None)
# None for acceptable_values means the field must be non-null/non-empty.
_CLOSURE_FLOW_RECORDS = {
	"Replacement / Exchange": ("Replacement Record", "status", ["Completed"]),
	"Refund Case": ("Return Service Record", "refund_status", ["Processed", "Not Applicable"]),
	"Stock Complaint": ("Stock Complaint Record", "credit_note_received_at", None),
	"Customer Product at Store": ("Store Service Record", "product_handed_over_at", None),
}

# Bridge: followup_stage values that imply a current_service_stage advance.
_FOLLOWUP_STAGE_SYNC = {
	"technician_called": "Technician Visit Pending",
	"technician_visited": "Technician Visited - Issue Pending",
	"sc_followup_done": None,  # depends on flow — handled by phase 2.1 actions
	"customer_informed": None,  # informational — stage doesn't change
	"no_technician_update": None,  # risk escalation — handled separately
	"customer_satisfied": "Customer Verification Pending",
	"customer_not_satisfied": "Customer Verification Pending",
}

# Canonical field-to-field alignment: customer_informed_status is the canonical
# operational field; customer_informed (Yes/No) is derived. Uses the existing
# _CHANNEL_MAP values so actions and reports agree.
# customer_informed_status values are documented here as the single source-of-truth:
#   Informed by Call  /  Informed by WhatsApp  /  Informed by SMS
#   Informed by Email /  Informed In-Person
# When customer_informed_status is set, customer_informed auto-syncs to "Yes".


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


# Flows whose current_service_stage is driven by the brand-warranty / local
# follow-up loop (i.e. by followup_stage). Other flows (custody, replacement,
# return, installation, stock…) own current_service_stage via their own advancers,
# so we must never derive over them.
_FOLLOWUP_LOOP_FLOWS = {"", "Customer Complaint - Site", "Out of Warranty Local Service"}


def _sync_service_stage_from_followup(doc):
	"""SoT: within the follow-up loop, followup_stage is authoritative — derive
	current_service_stage from it so the two stage fields cannot drift (e.g.
	registration_done → "Brand Registered", part_pending → "Spare Pending"). Guarded
	by service_flow_type so non-follow-up flows keep their own richer stage."""
	fs = doc.get("followup_stage")
	if not fs:
		return
	if (doc.get("service_flow_type") or "") not in _FOLLOWUP_LOOP_FLOWS:
		return
	from lavanya_service import stage_rules as sr

	derived = sr.derive_stage_from_followup(fs)
	if derived and doc.get("current_service_stage") != derived:
		doc.current_service_stage = derived


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

	# SoT: reconcile the canonical stage from followup_stage before persisting.
	_sync_service_stage_from_followup(doc)

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
# H1 Hardening helpers
# ---------------------------------------------------------------------------

def _validate_closure_prerequisites(doc):
	"""Block close_ticket / customer_confirmed unless linked records are complete
	for Replacement, Return, Stock Complaint, and Product-at-Store flows."""
	flow = doc.get("service_flow_type") or ""
	record_info = _CLOSURE_FLOW_RECORDS.get(flow)
	if not record_info:
		return

	record_doctype, check_field, acceptable = record_info
	linked = frappe.db.get_all(
		record_doctype,
		filters={"ticket": doc.name},
		fields=["name", check_field],
		limit=1,
	)
	if not linked:
		frappe.throw(_(
			"Ticket cannot be closed. No {0} exists for this {1} flow ticket. "
			"Complete the linked record process first."
		).format(record_doctype, flow))

	value = linked[0].get(check_field)
	if acceptable is not None:
		if value not in acceptable:
			frappe.throw(_(
				"Ticket cannot be closed. {0} status is '{1}' — must be one of: {2}."
			).format(record_doctype, value or "Not Set", ", ".join(acceptable)))
	else:
		if not value or str(value).strip() == "":
			frappe.throw(_(
				"Ticket cannot be closed. {0} field '{1}' is not recorded."
			).format(record_doctype, check_field))

def _sync_stage_fields(doc, action_key):
	"""Bridge followup_stage and current_service_stage where a mapping exists.
	Call this from actions that set followup_stage to keep both fields aligned."""
	sync_target = _FOLLOWUP_STAGE_SYNC.get(action_key)
	if sync_target and not doc.get("current_service_stage"):
		doc.current_service_stage = sync_target

def _sync_customer_informed(doc, channel):
	"""Set canonical customer_informed_status from _CHANNEL_MAP, and derive
	customer_informed as Yes. Both fields agree: status is canonical, Yes/No is derived."""
	status = _CHANNEL_MAP.get(channel, "Informed by Call")
	doc.customer_informed_status = status
	doc.customer_informed = "Yes"
	doc.customer_informed_at = now_datetime()
	doc.customer_informed_by = _acting_user()
	doc.customer_informed_channel = channel


def _append_followup_log(doc, stage, action_label, notes=None):
	"""Append a Follow-up Log entry for the stage transition.

	Detects re-entry: if the stage already exists in the log, marks as re-entry
	and requires a reason note.
	"""
	existing_stages = [row.stage for row in (doc.followup_log or [])]
	is_re_entry = stage in existing_stages

	if is_re_entry and not notes:
		frappe.throw(_("Reason for re-entry is required when revisiting a stage."))

	doc.append("followup_log", {
		"stage": stage,
		"completed_at": now_datetime(),
		"user": _acting_user(),
		"is_re_entry": int(is_re_entry),
		"action_label": action_label,
		"notes": notes,
	})


# followup_stage values that represent an UNRESOLVED verification loop — a ticket
# in any of these has an open "next action" and may not reach a terminal state.
_CLOSURE_VERIFICATION_STATES = {
	"technician_call_pending", "technician_visit_pending",
	"customer_confirmation_pending", "customer_not_satisfied",
	"no_technician_update", "appointment_missed",
}

# Stages where customer_confirmed is the correct resolution path.  Any other
# verification state must be resolved through its own action first —
# customer_confirmed must not be a side-door around an active service loop.
_CUSTOMER_CONFIRM_RESOLVABLE_STAGES = {
	None, "",
	"customer_confirmation_pending",
	"customer_satisfied",
}


def _default_next_followup(doc, first=False):
	"""Config-derived successor date (§3 determinism): the next follow-up is a
	function of the ticket's Reminder Rule, never an operator coin-flip. Callers
	pass the operator value first and fall back to this when it is blank, so a
	manual override is always honoured.

	first=True uses the rule's first-follow-up offset (e.g. D+2 after brand
	registration); otherwise the repeat cadence (e.g. every 2 days)."""
	from lavanya_service import reminder_engine as rem
	try:
		rule = rem.resolve_reminder_rule(doc)
	except Exception:
		rule = None
	key = "first_followup_after_minutes" if first else "repeat_every_minutes"
	fallback = rem.FALLBACK_FIRST_FOLLOWUP_MIN if first else rem.FALLBACK_REPEAT_MIN
	mins = rem._minutes(rule, key, fallback)
	return getdate(add_to_date(now_datetime(), minutes=mins))


def _assert_closure_gates(doc):
	"""Single source of truth for the closure Control Law: a ticket may not reach
	a terminal state while any physical, verification, or satisfaction gate is open.

	Called by EVERY path that closes a ticket (close_ticket, customer_confirmed)
	so no action can be a side-door around the gate.
	"""
	# Physical gate 1: flow-specific linked records (replacement/return/stock/custody).
	_validate_closure_prerequisites(doc)

	# Physical gate 2: a pending part that is not confirmed fitted.
	if doc.get("part_required") and not doc.get("part_fitted_confirmed"):
		frappe.throw(_(
			"Ticket cannot be closed. Part '{0}' is still pending (ETA: {1}). "
			"Confirm part is fitted and customer confirms issue resolved before closure."
		).format(doc.get("part_name", "Unknown"), doc.get("part_expected_date", "Unknown")))

	# Verification gate: an unresolved verification loop.
	# customer_confirmation_pending is only blocking when the customer has NOT
	# yet confirmed — once customer_confirmation_received=Yes, this stage is
	# the expected final step before closure.
	stage = doc.get("followup_stage")
	if stage in _CLOSURE_VERIFICATION_STATES:
		if stage == "customer_confirmation_pending" and doc.get("customer_confirmation_received") == "Yes":
			pass  # Customer confirmed — verification loop resolved
		else:
			frappe.throw(_(
				"Ticket cannot be closed. Follow-up stage is '{0}' — customer verification is unresolved. "
				"Verify with customer and record satisfaction before closure."
			).format(stage))

	# CVG-05: Supplier Payment Block — active block for brand blocks closure
	if frappe.db.exists("DocType", "Supplier Payment Block"):
		ticket_brand = doc.get("brand")
		if ticket_brand:
			blocks = frappe.db.get_all(
				"Supplier Payment Block",
				filters={"brand": ticket_brand, "block_status": ("in", ["Active", "Pending Review"])},
				fields=["name", "block_status", "block_reason"],
				limit=1,
			)
			if blocks:
				b = blocks[0]
				frappe.throw(_(
					"Ticket cannot be closed. Supplier Payment Block {0} is {1} for brand '{2}'. "
					"Release the block before closure. Reason: {3}"
				).format(b.name, b.block_status, ticket_brand, b.block_reason or "Not specified"))

	# CVG-06: Paid service requires customer approved amount > 0
	if doc.get("service_charge_type") in (
		"Customer Paid Local Service", "Customer Pays Technician Directly",
		"Customer Pays Lavanya",
	):
		amt = float(doc.get("customer_approved_amount") or 0)
		if amt <= 0:
			frappe.throw(_(
				"Ticket cannot be closed. Paid service requires customer approved amount > 0 "
				"(current: {0}). Record customer approval before closure."
			).format(amt))

	# CVG-07: Customer must be informed before close.
	ci = doc.get("customer_informed")
	if ci not in ("Yes", "Not Required"):
		frappe.throw(_(
			"Ticket cannot be closed. Customer must be marked as informed ('Yes' or 'Not Required'). "
			"Current: {0}. Inform customer before closure."
		).format(ci or "Not Set"))

	# CVG-09: No overdue follow-ups before close.
	if doc.get("overdue_status") in ("Overdue", "Breached"):
		frappe.throw(_(
			"Ticket cannot be closed with overdue follow-ups (status: {0}). "
			"Resolve pending follow-ups before closure."
		).format(doc.get("overdue_status")))

	# CVG-10: Repeat complaint — previous ticket must be closed.
	if doc.get("is_repeated_complaint") == "Yes" and doc.get("previous_ticket_link"):
		prev_status = frappe.db.get_value("HD Ticket", doc.previous_ticket_link, "status")
		if prev_status not in ("Closed", "Cancelled"):
			frappe.throw(_(
				"Ticket cannot be closed. Previous ticket {0} is still '{1}'. "
				"Close the linked ticket first."
			).format(doc.previous_ticket_link, prev_status))

	# Satisfaction gate: satisfaction must be documented.
	satisfaction = doc.customer_satisfaction_status
	if satisfaction not in ("Satisfied", "Not Required"):
		frappe.throw(_(
			"Ticket cannot be closed. Customer satisfaction must be 'Satisfied' "
			"or documented as 'Not Required' (current: {0})."
		).format(satisfaction or "Not Set"))

	# Confirmation gate: customer must have confirmed issue resolved.
	if doc.get("customer_confirmation_received") != "Yes":
		frappe.throw(_(
			"Ticket cannot be closed. Customer confirmation is required."
		))


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

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	# §3: auto-derive the D+2 verification date from the Reminder Rule when the
	# operator does not supply one. Never blank — the loop cannot be forgotten.
	next_follow_up_date = next_follow_up_date or _default_next_followup(doc, first=True)

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
	_append_followup_log(doc, "registration_done", "Brand Complaint Registered")

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
		next_follow_up_date = next_follow_up_date or _default_next_followup(doc)
		doc.status = "Waiting on Part / Approval"
		doc.pending_reason = "Part Pending"
		doc.next_follow_up_date = next_follow_up_date
	elif follow_up_result == "Approval pending":
		next_follow_up_date = next_follow_up_date or _default_next_followup(doc)
		doc.status = "Waiting on Part / Approval"
		doc.pending_reason = APPROVAL_PENDING_REASON
		doc.next_follow_up_date = next_follow_up_date
	else:
		next_follow_up_date = next_follow_up_date or _default_next_followup(doc)
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
	_append_followup_log(doc, "part_pending", "Part Pending")

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


def customer_confirmed(ticket_name, work_narration=None, closure_type=None, notes=None):
	_require_roles("Customer Confirmed", {ROLE_MANAGER, ROLE_COORDINATOR})

	work_narration = _require(work_narration, "Work Narration")
	closure_type = _validate_closure_type(closure_type)

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	# Capture the stage BEFORE overwriting.  customer_confirmed is only valid
	# when the remaining verification loop is the customer-confirmation step
	# itself.  Any other active service/technician state must be resolved first.
	previous_stage = doc.get("followup_stage")
	if previous_stage not in _CUSTOMER_CONFIRM_RESOLVABLE_STAGES:
		frappe.throw(_(
			"Ticket cannot be closed by customer confirmation. Follow-up stage is '{0}' — "
			"the active verification loop must be resolved first."
		).format(previous_stage))

	doc.customer_confirmation_received = "Yes"
	if doc.customer_satisfaction_status not in ("Satisfied", "Not Required"):
		doc.customer_satisfaction_status = "Satisfied"
	doc.followup_stage = "customer_satisfied"
	_append_followup_log(doc, "customer_satisfied", "Customer Confirmed", notes=notes)

	_assert_closure_gates(doc)

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

	# Control Law: enforce all physical, verification, and satisfaction gates.
	doc.customer_confirmation_received = customer_confirmation_received
	_assert_closure_gates(doc)

	doc.status = "Closed"
	doc.work_narration = work_narration
	doc.closure_type = closure_type
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

	# H3: Sync followup_stage and current_service_stage for the Product at Store
	# flow so that the receipt creation is captured in both stage trackers.
	doc.current_service_stage = "Product Received at Store"
	doc.followup_stage = "sc_followup_done"
	_append_followup_log(doc, "sc_followup_done", "Product Receipt Created")
	entry = "[Store Service] Product received at store — Receipt: {0}".format(receipt.name)
	_set_last_followup(doc, entry)
	doc.add_comment("Comment", entry)
	_save_ticket(doc)

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


def _create_comm_log(ticket_name, comm_type, direction, summary, notes=None, next_action=None):
	"""H3: Create a Customer Communication Log entry for the ticket.
	Silently skipped if the doctype is not installed."""
	if not frappe.db.exists("DocType", "Customer Communication Log"):
		return
	try:
		entry = frappe.new_doc("Customer Communication Log")
		entry.ticket = ticket_name
		entry.communication_date = now_datetime()
		entry.communication_type = comm_type
		entry.direction = direction
		entry.agent = _acting_user()
		entry.summary = summary[:280] if summary else summary
		if notes:
			entry.notes = notes
		if next_action:
			entry.next_action = next_action[:140] if next_action else next_action
		entry.insert(ignore_permissions=True)
	except Exception:
		frappe.log_error(title="Lavanya Comm Log creation failed", message=frappe.get_traceback())


def verify_technician_called(ticket_name, technician_name=None, notes=None):
	_require_roles("Verify Technician Called", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.followup_stage = "technician_called"
	_append_followup_log(doc, "technician_called", "Technician Called", notes=notes)

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
	_append_followup_log(doc, "technician_visited", "Technician Visited", notes=notes)

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


def record_sc_followup(ticket_name, follow_up_result=None, next_follow_up_date=None, customer_informed_status=None, notes=None):
	_require_roles("Record SC Follow-up", {ROLE_MANAGER, ROLE_COORDINATOR})

	follow_up_result = _require(follow_up_result, "Follow-up Result")
	if follow_up_result not in FOLLOW_UP_RESULTS:
		frappe.throw(_("'{0}' is not a valid Follow-up Result.").format(follow_up_result))
	customer_informed_status = _require(customer_informed_status, "Customer Informed Status")

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.followup_stage = "sc_followup_done"
	_append_followup_log(doc, "sc_followup_done", "SC Follow-up Done", notes=notes)
	doc.last_service_center_followup = now_datetime()
	doc.customer_informed_status = customer_informed_status
	if next_follow_up_date:
		doc.next_follow_up_date = next_follow_up_date

	# H3: Create Customer Communication Log entry
	comm_summary = "SC Follow-up — Result: {0} · Customer: {1}".format(
		follow_up_result, customer_informed_status)
	_create_comm_log(
		ticket_name, "Call",
		"Outbound" if customer_informed_status != "Not Required" else "Inbound",
		comm_summary, notes=notes,
		next_action="Follow-up on {0}".format(next_follow_up_date) if next_follow_up_date else None,
	)

	entry = "[Follow-up] Service Center Follow-up — Result: {0}".format(follow_up_result)
	if next_follow_up_date:
		entry += " · Next: {0}".format(next_follow_up_date)
	entry += " · Customer: {0}".format(customer_informed_status)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("SC follow-up recorded: {0}").format(follow_up_result))


def inform_customer(ticket_name, message=None, channel=None, notes=None):
	_require_roles("Inform Customer", {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_AGENT})

	channel = _require(channel, "Channel")

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.followup_stage = "customer_informed"
	_append_followup_log(doc, "customer_informed", "Customer Informed", notes=notes)
	_sync_customer_informed(doc, channel)

	# H3: Create Customer Communication Log entry
	comm_summary = "Customer informed via {0}".format(channel)
	if message:
		comm_summary += " — {0}".format(message[:200])
	_create_comm_log(
		ticket_name, "Call" if channel == "Phone" else channel,
		"Outbound", comm_summary, notes=notes,
		next_action=doc.get("next_action"),
	)

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
	_append_followup_log(doc, "no_technician_update", "No Technician Update", notes=notes)
	doc.escalation_level = _increment_escalation(doc.escalation_level)
	doc.no_update_count = (doc.no_update_count or 0) + 1

	entry = "[Follow-up] Mark No Update — Escalation: {0}".format(doc.escalation_level)
	entry += " · Count: {0}".format(doc.no_update_count)

	# §5 bounded non-response: once the configured attempt cap is breached, park the
	# ticket as Pending Customer Response so it leaves Today's Work instead of
	# spinning an unbounded reverification loop against a silent customer.
	from lavanya_service import reminder_engine as rem
	max_attempts = rem.resolve_max_followup_attempts(doc)
	parked = False
	if max_attempts and doc.no_update_count >= max_attempts:
		doc.parked_pending_customer = 1
		doc.parked_at = now_datetime()
		doc.parked_reason = (
			"Auto-parked after {0} consecutive no-updates (cap {1}). "
			"Awaiting customer response; resume to re-enter the follow-up loop."
		).format(doc.no_update_count, max_attempts)
		doc.status = "Waiting on Customer"
		doc.pending_reason = "Customer Not Reachable"
		entry += " · PARKED → Pending Customer Response"
		parked = True

	if notes:
		entry += " · Notes: {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	if parked:
		return _result(doc, _("No update marked; ticket parked as Pending Customer Response (cap {0} reached)").format(max_attempts))
	return _result(doc, _("No update marked; escalated to {0}").format(doc.escalation_level))


def resume_followup(ticket_name, next_follow_up_date=None, notes=None):
	"""§5: un-park a Pending Customer Response ticket (customer responded) and
	re-enter the follow-up loop. Resets the no-update counter and sets a fresh,
	config-derived next verification date so the ticket re-appears in Today's Work."""
	_require_roles("Resume Follow-up", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	if not doc.get("parked_pending_customer"):
		frappe.throw(_("Ticket is not parked — nothing to resume."))

	doc.parked_pending_customer = 0
	doc.parked_reason = ""
	doc.no_update_count = 0
	doc.next_follow_up_date = next_follow_up_date or _default_next_followup(doc)
	doc.status = "In Progress"
	doc.pending_reason = "Service Follow-up Required"
	doc.followup_stage = "technician_call_pending"
	_append_followup_log(doc, "technician_call_pending", "Resume Follow-up", notes=notes)

	entry = "[Follow-up] Resumed from Pending Customer Response — next {0}".format(doc.next_follow_up_date)
	if notes:
		entry += " · {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Follow-up resumed; next verification {0}").format(doc.next_follow_up_date))


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
		_append_followup_log(doc, "customer_satisfied", "Satisfaction Recorded", notes=notes)
	elif satisfaction_status == "Not Satisfied":
		doc.followup_stage = "customer_not_satisfied"
		_append_followup_log(doc, "customer_not_satisfied", "Satisfaction Recorded", notes=notes)
	else:
		doc.followup_stage = "customer_confirmation_pending"
		_append_followup_log(doc, "customer_confirmation_pending", "Satisfaction Recorded", notes=notes)

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


# ---------------------------------------------------------------------------
# Expansion quick actions (Phase 2.1)
# ---------------------------------------------------------------------------


def notify_brand_sc_for_pickup(ticket_name, brand_sc=None, notes=None):
	_require_roles("Notify Brand SC for Pickup", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.current_service_stage = "Brand SC Picked Up"
	if brand_sc:
		doc.service_center = brand_sc
	doc.followup_stage = "sc_followup_done"
	_append_followup_log(doc, "sc_followup_done", "Brand SC Notified for Pickup", notes=notes)

	entry = "[Store Service] Brand SC notified for pickup"
	if brand_sc:
		entry += " — SC: {0}".format(brand_sc)
	if notes:
		entry += " · {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Brand SC notified for pickup"))


def record_diagnosis_received(ticket_name, diagnosis=None, notes=None):
	_require_roles("Record Diagnosis Received", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.current_service_stage = "Diagnosis Received"
	doc.followup_stage = "sc_followup_done"
	_append_followup_log(doc, "sc_followup_done", "Diagnosis Received", notes=notes)

	entry = "[Store Service] Diagnosis received"
	if diagnosis:
		entry += " — {0}".format(diagnosis)
	if notes:
		entry += " · {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Diagnosis received recorded"))


def notify_customer_for_collection(ticket_name, notes=None):
	_require_roles("Notify Customer for Collection", {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_FRONT_DESK})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.current_service_stage = "Customer Notified for Collection"
	doc.followup_stage = "customer_informed"
	_append_followup_log(doc, "customer_informed", "Customer Notified for Collection", notes=notes)
	doc.customer_informed = "Yes"
	doc.customer_informed_at = now_datetime()

	entry = "[Store Service] Customer notified for collection"
	if notes:
		entry += " — {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Customer notified for collection"))


def hand_over_product(ticket_name, notes=None):
	_require_roles("Hand Over Product", {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_FRONT_DESK})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.current_service_stage = "Product Handed Over"
	doc.followup_stage = "customer_satisfied"
	_append_followup_log(doc, "customer_satisfied", "Product Handed Over", notes=notes)

	entry = "[Store Service] Product handed over to customer"
	if notes:
		entry += " — {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Product handed over to customer"))


def collect_old_unit(ticket_name, serial_no=None, notes=None):
	_require_roles("Collect Old Unit", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.current_service_stage = "Old Unit Collected"
	if serial_no:
		doc.serial_no = serial_no

	entry = "[Replacement] Old unit collected"
	if serial_no:
		entry += " — S/N: {0}".format(serial_no)
	if notes:
		entry += " · {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Old unit collected"))


def dispatch_new_unit(ticket_name, new_serial_no=None, notes=None):
	_require_roles("Dispatch New Unit", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.current_service_stage = "New Unit Dispatched"
	doc.followup_stage = "sc_followup_done"
	_append_followup_log(doc, "sc_followup_done", "New Unit Dispatched", notes=notes)

	entry = "[Replacement] New unit dispatched"
	if new_serial_no:
		entry += " — New S/N: {0}".format(new_serial_no)
	if notes:
		entry += " · {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("New unit dispatched"))


def return_old_unit_to_brand(ticket_name, notes=None):
	_require_roles("Return Old Unit to Brand", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.current_service_stage = "Brand Reimbursement Pending"

	entry = "[Replacement] Old unit returned to brand"
	if notes:
		entry += " — {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Old unit returned to brand"))


def record_brand_reimbursement(ticket_name, amount=None, notes=None):
	_require_roles("Record Brand Reimbursement", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.current_service_stage = "Reimbursement Received"

	entry = "[Replacement] Brand reimbursement recorded"
	if amount:
		entry += " — Amount: {0}".format(amount)
	if notes:
		entry += " · {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Brand reimbursement recorded"))


def verify_return_reason(ticket_name, reason=None, notes=None):
	_require_roles("Verify Return Reason", {ROLE_MANAGER, ROLE_COORDINATOR})

	reason = _require(reason, "Return Reason")

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.current_service_stage = "Return Reason Verified"

	entry = "[Return] Return reason verified — {0}".format(reason)
	if notes:
		entry += " · {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Return reason verified"))


def notify_brand_for_return(ticket_name, notes=None):
	_require_roles("Notify Brand for Return", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.current_service_stage = "Brand Notified for Return"

	entry = "[Return] Brand notified for return"
	if notes:
		entry += " — {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Brand notified for return"))


# ---------------------------------------------------------------------------
# P0-1: Appointment execution handlers (Confirm / Miss / Visited / Verify)
# ---------------------------------------------------------------------------

def confirm_appointment(ticket_name, appointment_datetime=None, technician=None, notes=None):
	_require_roles("Confirm Appointment", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.followup_stage = "technician_visit_pending"
	_append_followup_log(doc, "technician_visit_pending", "Appointment Confirmed", notes=notes)
	if appointment_datetime:
		doc.next_follow_up_date = appointment_datetime
	if technician:
		doc.technician_name = str(technician).strip()

	entry = "[Follow-up] Appointment Confirmed"
	if technician:
		entry += " — Technician: {0}".format(technician)
	if appointment_datetime:
		entry += " · {0}".format(appointment_datetime)
	if notes:
		entry += " · {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Appointment confirmed"))


def mark_appointment_missed(ticket_name, reason=None, reschedule_date=None, notes=None):
	_require_roles("Mark Appointment Missed", {ROLE_MANAGER, ROLE_COORDINATOR})

	reason = _require(reason, "Reason")
	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.followup_stage = "no_technician_update"
	_append_followup_log(doc, "no_technician_update", "Appointment Missed", notes=notes)
	doc.escalation_level = _increment_escalation(doc.escalation_level)
	if reschedule_date:
		doc.next_follow_up_date = reschedule_date

	entry = "[Follow-up] Appointment Missed — Reason: {0}".format(reason)
	entry += " · Escalation: {0}".format(doc.escalation_level)
	if reschedule_date:
		entry += " · Reschedule: {0}".format(reschedule_date)
	if notes:
		entry += " · {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Appointment marked missed; escalated to {0}").format(doc.escalation_level))


def mark_technician_visited(ticket_name, visit_result=None, notes=None):
	_require_roles("Mark Technician Visited", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.followup_stage = "technician_visited"
	_append_followup_log(doc, "technician_visited", "Technician Visited", notes=notes)
	doc.no_update_count = 0  # reset if update was received

	entry = "[Follow-up] Technician Visited"
	if visit_result:
		entry += " — Result: {0}".format(visit_result)
	if notes:
		entry += " · {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Technician visit recorded"))


def verify_customer_after_appointment(ticket_name, confirmed=None, satisfaction=None, notes=None):
	"""P0-3: Post-visit customer verification — mandatory before closure."""
	_require_roles("Verify Customer After Appointment", {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_AGENT})

	confirmed = _require(confirmed, "Customer Confirmation Status")
	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	# Record customer's statement
	doc.customer_informed_status = "Informed by Call"
	doc.customer_informed = "Yes"
	doc.customer_informed_at = now_datetime()
	doc.customer_informed_by = _acting_user()

	if confirmed in ("Yes", "Cleared", "Satisfied"):
		doc.followup_stage = "customer_satisfied"
		_append_followup_log(doc, "customer_satisfied", "Post-Appointment Verified", notes=notes)
		doc.customer_satisfaction_status = "Satisfied"
	elif confirmed in ("No", "Not Cleared", "Still Issue"):
		doc.followup_stage = "customer_not_satisfied"
		_append_followup_log(doc, "customer_not_satisfied", "Post-Appointment Verified", notes=notes)
		doc.customer_satisfaction_status = "Not Satisfied"
	elif confirmed == "Part Pending":
		doc.followup_stage = "part_pending"
		_append_followup_log(doc, "part_pending", "Post-Appointment Verified", notes=notes)
		doc.status = "Waiting on Part / Approval"
	else:
		doc.followup_stage = "customer_confirmation_pending"
		_append_followup_log(doc, "customer_confirmation_pending", "Post-Appointment Verified", notes=notes)

	if satisfaction:
		doc.customer_satisfaction_status = str(satisfaction).strip()

	entry = "[Follow-up] Customer Verified — Outcome: {0}".format(confirmed)
	if notes:
		entry += " · {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Customer verified: {0}").format(confirmed))


# ---------------------------------------------------------------------------
# P0-2: Part-pending follow-up loop
# ---------------------------------------------------------------------------

def record_part_required(ticket_name, part_name=None, part_expected_date=None, next_follow_up_date=None, notes=None):
	_require_roles("Record Part Required", {ROLE_MANAGER, ROLE_COORDINATOR})

	part_name = _require(part_name, "Part Name")
	part_expected_date = _require(part_expected_date, "Part Expected Date")
	next_follow_up_date = _require(next_follow_up_date, "Next Follow-up Date")

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	doc.part_required = 1
	doc.part_name = part_name
	doc.part_expected_date = part_expected_date
	doc.followup_stage = "part_pending"
	_append_followup_log(doc, "part_pending", "Part Required", notes=notes)
	doc.status = "Waiting on Part / Approval"
	doc.next_follow_up_date = next_follow_up_date

	entry = "[Follow-up] Part Required — Name: {0} · ETA: {1}".format(part_name, part_expected_date)
	entry += " · Next follow-up: {0}".format(next_follow_up_date)
	if notes:
		entry += " · {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Part pending recorded: {0}").format(part_name))


def update_part_eta(ticket_name, new_eta=None, delay_reason=None, notes=None):
	_require_roles("Update Part ETA", {ROLE_MANAGER, ROLE_COORDINATOR})

	new_eta = _require(new_eta, "New ETA Date")
	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	old_eta = doc.part_expected_date or "not set"
	doc.part_expected_date = new_eta
	if delay_reason:
		doc.part_delay_reason = str(delay_reason).strip()

	entry = "[Follow-up] Part ETA Updated — Old: {0} · New: {1}".format(old_eta, new_eta)
	if delay_reason:
		entry += " · Reason: {0}".format(delay_reason)
	if notes:
		entry += " · {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Part ETA updated to {0}").format(new_eta))


def set_reverification_date(ticket_name, reverify_at=None, notes=None):
	"""Set the next customer verification checkpoint. Used after every
	service-center/technician remark to enforce the follow-up loop."""
	_require_roles("Set Reverification Date", {ROLE_MANAGER, ROLE_COORDINATOR})

	doc = _load_ticket(ticket_name)
	_block_if_final(doc)

	# §3: deterministic default from the Reminder Rule when not explicitly set —
	# a verification date is a function, not a coordinator's coin-flip.
	reverify_at = reverify_at or _default_next_followup(doc)
	doc.next_follow_up_date = reverify_at

	entry = "[Follow-up] Reverification set — Date: {0}".format(reverify_at)
	if notes:
		entry += " · {0}".format(notes)
	doc.add_comment("Comment", entry)
	_set_last_followup(doc, entry)

	_save_ticket(doc)
	return _result(doc, _("Reverification set to {0}").format(reverify_at))
