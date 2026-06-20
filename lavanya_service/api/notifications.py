"""P2.2 notification template preview and dry-run queue API."""

import json
import re

import frappe
from frappe.utils import now_datetime

from lavanya_service.notifications.provider import get_provider, live_notifications_enabled
from lavanya_service.utils.phone import normalize_phone


TEMPLATE_DOCTYPE = "Lavanya Notification Template"
QUEUE_DOCTYPE = "Lavanya Notification Queue"
LIVE_NOTIFICATIONS_ENABLED = live_notifications_enabled()

PREVIEW_ROLES = {"System Manager", "Lavanya Manager", "Lavanya Service Coordinator", "Lavanya Helpdesk Agent", "Lavanya Front Desk"}
APPROVAL_ROLES = {"System Manager", "Lavanya Manager", "Lavanya Service Coordinator"}
CUSTOMER_CHANNELS = {"WhatsApp", "SMS"}
VARIABLE_RE = re.compile(r"{{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*}}")


def _has_any_role(roles):
	return bool(set(frappe.get_roles(frappe.session.user)).intersection(roles))


def _check_preview_role():
	if not _has_any_role(PREVIEW_ROLES):
		frappe.throw("Not permitted.", frappe.PermissionError)


def _check_approval_role():
	if not _has_any_role(APPROVAL_ROLES):
		frappe.throw("Not permitted.", frappe.PermissionError)


def _get_template(template_name=None, event_type=None, channel=None):
	if template_name:
		if not frappe.db.exists(TEMPLATE_DOCTYPE, template_name):
			frappe.throw("Notification template not found.")
		return frappe.get_doc(TEMPLATE_DOCTYPE, template_name)
	filters = {"active": 1}
	if event_type:
		filters["event_type"] = event_type
	if channel:
		filters["channel"] = channel
	name = frappe.db.get_value(TEMPLATE_DOCTYPE, filters, "name", order_by="modified desc")
	if not name:
		frappe.throw("Notification template not found.")
	return frappe.get_doc(TEMPLATE_DOCTYPE, name)


def _ticket_context(ticket_name):
	ticket = frappe.get_doc("HD Ticket", ticket_name)
	return {
		"customer_name": ticket.get("customer_name") or ticket.get("raised_by") or "Customer",
		"ticket_id": ticket.name,
		"product_type": ticket.get("product_type") or ticket.get("item_group") or "product",
		"brand": ticket.get("brand") or "",
		"brand_ticket_number": ticket.get("brand_ticket_number") or "",
		"service_center": ticket.get("service_center") or "",
		"next_follow_up_date": str(ticket.get("next_follow_up_date") or ""),
		"last_followup_summary": ticket.get("last_followup_summary") or "",
		"customer_informed_status": ticket.get("customer_informed_status") or ticket.get("customer_informed") or "Pending",
		"part_name": ticket.get("part_name") or "",
		"part_expected_date": str(ticket.get("part_expected_date") or ""),
		"closure_type": ticket.get("closure_type") or "",
		"store_name": ticket.get("store_name") or "Lavanya eMart",
		"store_phone": ticket.get("store_phone") or "",
		"event_type": "",
		"phone": ticket.get("phone_1_normalized") or ticket.get("phone_1") or "",
	}


def _render(body, context):
	missing = []

	def replace(match):
		key = match.group(1)
		value = context.get(key)
		if value in (None, ""):
			missing.append(key)
			return ""
		return str(value)

	rendered = VARIABLE_RE.sub(replace, body or "")
	return rendered, sorted(set(missing))


def _template_variables(template):
	try:
		data = json.loads(template.get("variables_json") or "[]")
		return data if isinstance(data, list) else []
	except Exception:
		return []


def render_template(template, ticket_name):
	context = _ticket_context(ticket_name)
	context["event_type"] = template.event_type
	rendered, missing = _render(template.message_body, context)
	declared_missing = [v for v in _template_variables(template) if context.get(v) in (None, "")]
	missing = sorted(set(missing + declared_missing))
	return {
		"ok": not missing,
		"template": template.name,
		"channel": template.channel,
		"event_type": template.event_type,
		"rendered_message": rendered,
		"missing_variables": missing,
		"context": context,
		"error": "Missing variables: " + ", ".join(missing) if missing else "",
	}


@frappe.whitelist()
def get_notification_templates(channel=None, event_type=None):
	_check_preview_role()
	filters = {"active": 1}
	if channel:
		filters["channel"] = channel
	if event_type:
		filters["event_type"] = event_type
	return {
		"templates": frappe.get_all(TEMPLATE_DOCTYPE, filters=filters, fields=[
			"name", "template_name", "channel", "event_type", "language", "subject", "message_body", "requires_approval",
		], order_by="event_type asc, channel asc")
	}


@frappe.whitelist()
def get_notification_queue(ticket=None, status=None, limit=50, start=0):
	_check_preview_role()
	filters = {}
	if ticket:
		filters["ticket"] = ticket
	if status:
		filters["status"] = status
	return {"queue": frappe.get_all(QUEUE_DOCTYPE, filters=filters, fields=[
		"name", "ticket", "customer_name", "phone", "channel", "event_type", "template", "rendered_message",
		"status", "requires_approval", "approved_by", "approved_at", "send_after", "sent_at", "error_message", "dry_run", "creation",
	], order_by="creation desc", limit=int(limit), limit_start=int(start))}


@frappe.whitelist()
def preview_notification(template_name=None, ticket=None, event_type=None, channel=None):
	_check_preview_role()
	template = _get_template(template_name=template_name, event_type=event_type, channel=channel)
	if not ticket or not frappe.db.exists("HD Ticket", ticket):
		frappe.throw("Valid ticket is required.")
	return render_template(template, ticket)


@frappe.whitelist(methods=["POST"])
def queue_notification(template_name=None, ticket=None, event_type=None, channel=None, send_after=None):
	_check_preview_role()
	template = _get_template(template_name=template_name, event_type=event_type, channel=channel)
	preview = preview_notification(template_name=template.name, ticket=ticket)
	context = preview.get("context") or {}
	phone_result = normalize_phone(context.get("phone"))
	status = "Approval Pending" if int(template.get("requires_approval") or 0) else "Queued"
	error = preview.get("error") or ""
	phone = phone_result.get("normalized") or ""
	if template.channel in CUSTOMER_CHANNELS and not phone:
		status = "Skipped"
		error = "Missing or invalid customer phone."
	elif not preview.get("ok"):
		status = "Skipped"

	doc = frappe.get_doc({
		"doctype": QUEUE_DOCTYPE,
		"ticket": ticket,
		"customer_name": context.get("customer_name"),
		"phone": phone,
		"channel": template.channel,
		"event_type": template.event_type,
		"template": template.name,
		"rendered_message": preview.get("rendered_message") or "",
		"status": status,
		"requires_approval": int(template.get("requires_approval") or 0),
		"send_after": send_after,
		"provider_response": "Dry-run only; live delivery disabled." if not LIVE_NOTIFICATIONS_ENABLED else "",
		"error_message": error,
		"dry_run": 1,
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"ok": status not in {"Failed"}, "queue": doc.name, "status": doc.status, "dry_run": True, "live_enabled": LIVE_NOTIFICATIONS_ENABLED}


@frappe.whitelist(methods=["POST"])
def approve_notification(queue_name):
	_check_approval_role()
	doc = frappe.get_doc(QUEUE_DOCTYPE, queue_name)
	if doc.status not in {"Approval Pending", "Queued"}:
		frappe.throw("Only queued or approval-pending notifications can be approved.")
	doc.status = "Approved"
	doc.approved_by = frappe.session.user
	doc.approved_at = now_datetime()
	doc.dry_run = 1
	doc.save(ignore_permissions=True)
	return {"ok": True, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def cancel_notification(queue_name, reason=None):
	_check_approval_role()
	doc = frappe.get_doc(QUEUE_DOCTYPE, queue_name)
	if doc.status in {"Sent", "Cancelled"}:
		frappe.throw("Notification cannot be cancelled from its current status.")
	doc.status = "Cancelled"
	doc.error_message = reason or "Cancelled by manager."
	doc.save(ignore_permissions=True)
	return {"ok": True, "status": doc.status}


@frappe.whitelist(methods=["POST"])
def mark_notification_skipped(queue_name, reason=None):
	_check_approval_role()
	doc = frappe.get_doc(QUEUE_DOCTYPE, queue_name)
	if doc.status == "Sent":
		frappe.throw("Sent notification cannot be skipped.")
	doc.status = "Skipped"
	doc.error_message = reason or "Skipped by manager."
	doc.save(ignore_permissions=True)
	return {"ok": True, "status": doc.status}


