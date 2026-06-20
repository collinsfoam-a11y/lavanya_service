"""P2.2 dry-run notification template and queue tests."""

import frappe
from frappe.utils import today

_PASS = []
_FAIL = []
_created = []


def _check(name, condition, detail=""):
	(_PASS if condition else _FAIL).append(name)
	print("[{}] {}".format("PASS" if condition else "FAIL", name) + ((" | " + detail) if detail else ""))


def _ensure_agent_user():
	if not frappe.db.exists("User", "p2-agent@example.test"):
		user = frappe.get_doc({
			"doctype": "User",
			"email": "p2-agent@example.test",
			"first_name": "P2 Agent",
			"enabled": 1,
			"send_welcome_email": 0,
		})
		user.insert(ignore_permissions=True)
		_created.append(("User", user.name))
	else:
		user = frappe.get_doc("User", "p2-agent@example.test")
	if "Lavanya Helpdesk Agent" not in [r.role for r in user.roles]:
		user.add_roles("Lavanya Helpdesk Agent")
	return user.name


def _new_ticket(**overrides):
	doc = frappe.get_doc({
		"doctype": "HD Ticket",
		"subject": "P2.2 Notification Test",
		"description": "Notification dry-run test",
		"ticket_type": "Customer Complaint - Site",
		"customer_name": "P2 Notify Customer",
		"phone_1": "9876543210",
		"status": "Open",
		"brand": "LG",
		"product_type": "AC",
		**overrides,
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	_created.append(("HD Ticket", doc.name))
	return doc.name


def _new_template(**overrides):
	doc = frappe.get_doc({
		"doctype": "Lavanya Notification Template",
		"template_name": "P2 Test Template " + frappe.generate_hash(length=6),
		"channel": "WhatsApp",
		"event_type": "Ticket created",
		"language": "English",
		"subject": "Ticket {{ ticket_id }}",
		"message_body": "Hello {{ customer_name }}, ticket {{ ticket_id }} for {{ product_type }} is created.",
		"variables_json": "[\"customer_name\", \"ticket_id\", \"product_type\"]",
		"active": 1,
		"requires_approval": 0,
		**overrides,
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	_created.append(("Lavanya Notification Template", doc.name))
	return doc.name


def _cleanup():
	frappe.set_user("Administrator")
	for dt, nm in reversed(_created):
		try:
			if frappe.db.exists(dt, nm):
				frappe.delete_doc(dt, nm, ignore_permissions=True, force=True)
		except Exception:
			pass
	_created.clear()
	frappe.db.commit()


def _purge_stale():
	"""Remove leftovers from previous crashed/interrupted test runs."""
	frappe.set_user("Administrator")
	# Stale notification templates created by _new_template
	for tpl in frappe.get_all("Lavanya Notification Template", {"template_name": ["like", "P2 Test Template%"]}, "name"):
		try:
			frappe.delete_doc("Lavanya Notification Template", tpl.name, ignore_permissions=True, force=True)
		except Exception:
			pass
	# Stale test tickets
	for tkt in frappe.get_all("HD Ticket", {"subject": "P2.2 Notification Test"}, "name"):
		try:
			frappe.delete_doc("HD Ticket", tkt.name, ignore_permissions=True, force=True)
		except Exception:
			pass
	# Stale queue rows linked to test templates/tickets (defensive)
	for row in frappe.get_all("Lavanya Notification Queue", {"rendered_message": ["like", "Hello P2 Notify Customer%"]}, "name"):
		try:
			frappe.delete_doc("Lavanya Notification Queue", row.name, ignore_permissions=True, force=True)
		except Exception:
			pass
	# Stale test agent user
	if frappe.db.exists("User", "p2-agent@example.test"):
		try:
			frappe.delete_doc("User", "p2-agent@example.test", ignore_permissions=True, force=True)
		except Exception:
			pass
	frappe.db.commit()


def test_template_render_success():
	from lavanya_service.api.notifications import preview_notification
	ticket = _new_ticket()
	template = _new_template()
	res = preview_notification(template_name=template, ticket=ticket)
	_check("template_render_success", res.get("ok") and ticket in res.get("rendered_message", ""), str(res))


def test_template_render_missing_variable_fails_safely():
	from lavanya_service.api.notifications import preview_notification
	ticket = _new_ticket()
	template = _new_template(message_body="Missing {{ not_available }}", variables_json="[\"not_available\"]")
	res = preview_notification(template_name=template, ticket=ticket)
	_check("template_render_missing_variable_fails_safely", not res.get("ok") and "not_available" in res.get("missing_variables", []), str(res))


def test_queue_dry_run_notification():
	from lavanya_service.api.notifications import queue_notification
	ticket = _new_ticket(phone_1="+91 98765 43210")
	template = _new_template(requires_approval=1)
	res = queue_notification(template_name=template, ticket=ticket)
	queue_name = res.get("queue")
	if queue_name:
		_created.append(("Lavanya Notification Queue", queue_name))
		doc = frappe.get_doc("Lavanya Notification Queue", queue_name)
		_check("queue_dry_run_notification", doc.dry_run == 1 and doc.status == "Approval Pending" and doc.phone == "9876543210", doc.as_json())
	else:
		_check("queue_dry_run_notification", False, str(res))


def test_no_live_send_when_disabled():
	from lavanya_service.api.notifications import LIVE_NOTIFICATIONS_ENABLED
	from lavanya_service.notifications.provider import get_provider
	provider = get_provider("WhatsApp")
	blocked = False
	try:
		provider.send({"phone": "9876543210", "rendered_message": "hello"})
	except Exception:
		blocked = True
	_check("no_live_send_when_disabled", LIVE_NOTIFICATIONS_ENABLED is False and blocked)


def test_missing_phone_skips_queue():
	from lavanya_service.api.notifications import queue_notification
	ticket = _new_ticket(phone_1="", phone_1_normalized="")
	template = _new_template()
	res = queue_notification(template_name=template, ticket=ticket)
	queue_name = res.get("queue")
	if queue_name:
		_created.append(("Lavanya Notification Queue", queue_name))
		doc = frappe.get_doc("Lavanya Notification Queue", queue_name)
		_check("missing_phone_skips_queue", doc.status == "Skipped" and "phone" in (doc.error_message or "").lower(), doc.as_json())
	else:
		_check("missing_phone_skips_queue", False, str(res))


def test_manager_can_approve_notification():
	from lavanya_service.api.notifications import approve_notification, queue_notification
	ticket = _new_ticket()
	template = _new_template(requires_approval=1)
	queue_name = queue_notification(template_name=template, ticket=ticket).get("queue")
	_created.append(("Lavanya Notification Queue", queue_name))
	res = approve_notification(queue_name=queue_name)
	doc = frappe.get_doc("Lavanya Notification Queue", queue_name)
	_check("manager_can_approve_notification", res.get("ok") and doc.status == "Approved" and doc.approved_by == "Administrator", doc.as_json())


def test_agent_cannot_approve_notification():
	from lavanya_service.api.notifications import approve_notification, preview_notification, queue_notification
	agent = _ensure_agent_user()
	ticket = _new_ticket()
	template = _new_template(requires_approval=1)
	frappe.set_user(agent)
	preview = preview_notification(template_name=template, ticket=ticket)
	frappe.set_user("Administrator")
	queue_name = queue_notification(template_name=template, ticket=ticket).get("queue")
	_created.append(("Lavanya Notification Queue", queue_name))
	frappe.set_user(agent)
	blocked = False
	try:
		approve_notification(queue_name=queue_name)
	except Exception:
		blocked = True
	finally:
		frappe.set_user("Administrator")
	_check("agent_cannot_approve_notification", preview.get("ok") and blocked)


def _event_preview(event_type, name):
	from lavanya_service.api.notifications import preview_notification
	ticket = _new_ticket()
	template = _new_template(event_type=event_type, message_body="{{ event_type }} {{ ticket_id }} {{ customer_name }}")
	res = preview_notification(template_name=template, ticket=ticket)
	_check(name, res.get("ok") and event_type in res.get("rendered_message", ""), str(res))


def test_ticket_created_template_preview():
	_event_preview("Ticket created", "ticket_created_template_preview")


def test_part_pending_template_preview():
	_event_preview("Part pending update", "part_pending_template_preview")


def test_customer_satisfaction_template_preview():
	_event_preview("Customer satisfaction request", "customer_satisfaction_template_preview")


def run():
	global _PASS, _FAIL, _created
	_PASS = []
	_FAIL = []
	_created = []
	frappe.set_user("Administrator")
	_purge_stale()
	print("=== P2.2 Notification Tests ===\n")
	for fn in [
		test_template_render_success,
		test_template_render_missing_variable_fails_safely,
		test_queue_dry_run_notification,
		test_no_live_send_when_disabled,
		test_missing_phone_skips_queue,
		test_manager_can_approve_notification,
		test_agent_cannot_approve_notification,
		test_ticket_created_template_preview,
		test_part_pending_template_preview,
		test_customer_satisfaction_template_preview,
	]:
		try:
			fn()
		except Exception:
			_check(fn.__name__, False, frappe.get_traceback()[:300])
		_cleanup()
	print("\nResults: {} pass, {} fail".format(len(_PASS), len(_FAIL)))
	if _FAIL:
		print("Failed: " + ", ".join(_FAIL))
	return {"pass": len(_PASS), "fail": len(_FAIL)}
