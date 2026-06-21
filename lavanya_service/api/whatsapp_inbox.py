"""H6A: WhatsApp Inbox API — read-only inbound + draft-only outbound.

Safety boundaries:
- All outbound operations create DRAFT status only.
- No live WhatsApp API calls (Twilio, 360dialog, WhatsApp Business API).
- No SMS gateway calls.
- No automatic ticket closure.
- No ERP posting, accounting entries, or penalty application.
- No CRM auto-conversion.
- Approval moves status to "Approved (Ready)" but does NOT send.
- "Sent (External)" status is blocked: requires live_send_blocked=0 (currently impossible).
"""

import frappe
from frappe import _
from frappe.utils import now_datetime

INBOUND_DOCTYPE = "WhatsApp Inbound Message"
DRAFT_DOCTYPE = "WhatsApp Draft Outbound"
TICKET_DOCTYPE = "HD Ticket"

BLOCKED_SEND_STATUS = "Sent (External)"
BLOCKED_SEND_FIELDS = ("external_message_id", "sent_at")


def _require_not_guest():
	if frappe.session.user == "Guest":
		frappe.throw("Not permitted", frappe.PermissionError)


def _block_live_send(doc):
	"""H6A server-side guard: prevent any draft from being marked as Sent (External)
	while live_send_blocked is active. This guard cannot be bypassed by Desk/API."""
	if doc.get("live_send_blocked") and doc.get("review_status") == BLOCKED_SEND_STATUS:
		frappe.throw(
			_("Live WhatsApp sending is disabled. Drafts cannot be marked as '{0}' while live_send_blocked is active.").format(BLOCKED_SEND_STATUS),
			frappe.ValidationError,
		)
	for field in BLOCKED_SEND_FIELDS:
		if doc.get(field):
			frappe.throw(
				_("Live WhatsApp sending is disabled. Field '{0}' cannot be set while live_send_blocked is active.").format(field),
				frappe.ValidationError,
			)


@frappe.whitelist()
def list_inbound_messages(status=None, search=None, start=0, page_length=30):
	"""List captured WhatsApp inbound messages (read-only)."""
	_require_not_guest()
	filters = {}
	if status and status != "All":
		filters["review_status"] = status
	if search:
		filters["sender_mobile"] = ["like", f"%{search}%"]
	rows = frappe.get_all(
		INBOUND_DOCTYPE,
		filters=filters,
		fields=["name", "sender_mobile", "sender_name", "message_text", "received_at",
				"linked_ticket", "review_status", "reviewed_by", "source"],
		order_by="received_at desc",
		limit_start=start,
		limit_page_length=page_length,
	)
	return {"messages": rows, "has_more": len(rows) == page_length}


@frappe.whitelist()
def list_draft_outbound(status=None, ticket=None, start=0, page_length=30):
	"""List draft outbound messages (read-only)."""
	_require_not_guest()
	filters = {}
	if status and status != "All":
		filters["review_status"] = status
	if ticket:
		filters["ticket"] = ticket
	rows = frappe.get_all(
		DRAFT_DOCTYPE,
		filters=filters,
		fields=["name", "ticket", "recipient_mobile", "recipient_name", "draft_message",
				"created_by_user", "created_at", "review_status", "reviewed_by",
				"template_name", "template_language"],
		order_by="created_at desc",
		limit_start=start,
		limit_page_length=page_length,
	)
	return {"drafts": rows, "has_more": len(rows) == page_length}


@frappe.whitelist(methods=["POST"])
def create_draft(ticket_name, message, recipient_mobile=None, recipient_name=None, template_name=None, template_language=None):
	"""Create a draft outbound WhatsApp message. Does NOT send."""
	_require_not_guest()
	if not frappe.db.exists(TICKET_DOCTYPE, ticket_name):
		frappe.throw("Ticket not found.")
	if not frappe.has_permission(TICKET_DOCTYPE, "read", doc=ticket_name):
		frappe.throw("Not permitted to read this ticket.", frappe.PermissionError)

	ticket = frappe.get_doc(TICKET_DOCTYPE, ticket_name)
	mobile = recipient_mobile or ticket.get("phone_1") or ""
	name = recipient_name or ticket.get("customer_name") or ""

	if not mobile:
		frappe.throw("No recipient mobile available.")

	doc = frappe.get_doc({
		"doctype": DRAFT_DOCTYPE,
		"ticket": ticket_name,
		"recipient_mobile": mobile,
		"recipient_name": name,
		"draft_message": (message or "").strip(),
		"created_by_user": frappe.session.user,
		"created_at": now_datetime(),
		"review_status": "Draft",
		"live_send_blocked": 1,
		"template_name": template_name,
		"template_language": template_language or "ml",
	})
	doc.insert(ignore_permissions=True)

	return {"ok": True, "draft": doc.name, "message": "Draft created. No live message sent."}


@frappe.whitelist(methods=["POST"])
def review_draft(draft_name, action, notes=None):
	"""Review a draft: approve (ready for manager) or reject. Does NOT send."""
	_require_not_guest()
	if not frappe.db.exists(DRAFT_DOCTYPE, draft_name):
		frappe.throw("Draft not found.")

	doc = frappe.get_doc(DRAFT_DOCTYPE, draft_name)
	actor = frappe.session.user

	if action == "approve":
		doc.review_status = "Manager Reviewed"
		doc.reviewed_by = actor
		doc.reviewed_at = now_datetime()
	elif action == "ready":
		doc.review_status = "Approved (Ready)"
		doc.reviewed_by = actor
		doc.reviewed_at = now_datetime()
	elif action == "reject":
		doc.review_status = "Rejected"
		doc.reviewed_by = actor
		doc.reviewed_at = now_datetime()
		doc.rejection_reason = (notes or "").strip()
	else:
		frappe.throw(f"Unknown action: {action}")

	# H6A guard: block transition to Sent (External) while live_send_blocked
	_block_live_send(doc)

	doc.save(ignore_permissions=True)

	return {
		"ok": True,
		"draft": doc.name,
		"status": doc.review_status,
		"message": f"Draft {action}d. No live message sent.",
	}


@frappe.whitelist(methods=["POST"])
def review_inbound(message_name, action=None):
	"""Mark an inbound message as reviewed or ignore/spam."""
	_require_not_guest()
	if not frappe.db.exists(INBOUND_DOCTYPE, message_name):
		frappe.throw("Message not found.")

	doc = frappe.get_doc(INBOUND_DOCTYPE, message_name)
	actor = frappe.session.user

	if action == "review":
		doc.review_status = "Reviewed"
	elif action == "ignore":
		doc.review_status = "Ignored"
	else:
		frappe.throw(f"Unknown action: {action}")

	doc.reviewed_by = actor
	doc.reviewed_at = now_datetime()
	doc.save(ignore_permissions=True)

	return {"ok": True, "status": doc.review_status}


@frappe.whitelist(methods=["POST"])
def link_inbound_to_ticket(message_name, ticket_name):
	"""Link an inbound WhatsApp message to a ticket."""
	_require_not_guest()
	if not frappe.db.exists(INBOUND_DOCTYPE, message_name):
		frappe.throw("Message not found.")
	if not frappe.db.exists(TICKET_DOCTYPE, ticket_name):
		frappe.throw("Ticket not found.")

	doc = frappe.get_doc(INBOUND_DOCTYPE, message_name)
	doc.linked_ticket = ticket_name
	doc.review_status = "Linked to Ticket"
	doc.reviewed_by = frappe.session.user
	doc.reviewed_at = now_datetime()
	doc.save(ignore_permissions=True)

	return {"ok": True, "message": f"Message {message_name} linked to ticket {ticket_name}."}


@frappe.whitelist()
def get_ticket_drafts(ticket_name):
	"""Get all drafts for a specific ticket."""
	_require_not_guest()
	rows = frappe.get_all(
		DRAFT_DOCTYPE,
		filters={"ticket": ticket_name},
		fields=["name", "draft_message", "review_status", "created_by_user", "created_at", "template_name"],
		order_by="created_at desc",
		limit_page_length=20,
	)
	return {"drafts": rows}
