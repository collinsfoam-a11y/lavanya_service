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

	existing = frappe.db.get_value(RECEIPT_DOCTYPE, {"ticket": doc.name}, "name")
	if existing:
		frappe.throw(
			_("A Service Product Receipt ({0}) already exists for ticket {1}.").format(
				existing, doc.name
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

	# Link the receipt back to the ticket. ``service_product_receipt`` is a
	# protected service-coordination field; Front Desk is an allowed role for
	# this action but is not a service-coordination writer, so the link is set
	# directly. This is the documented, narrowly-scoped permission bypass,
	# gated by the explicit action-role check above.
	frappe.db.set_value(TICKET_DOCTYPE, doc.name, "service_product_receipt", receipt.name)

	doc.reload()
	return {
		"ok": True,
		"ticket": doc.name,
		"status": doc.status,
		"receipt": receipt.name,
		"message": _("Service Product Receipt {0} created").format(receipt.name),
	}
