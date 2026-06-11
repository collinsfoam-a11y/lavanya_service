import frappe
from frappe.utils import today

from lavanya_service.reminders.ticket_reminders import get_reminder_snapshot


REMINDER_CATEGORIES = {
    "follow_up_due_today": "Follow-up Due Today",
    "overdue_follow_ups": "Overdue Follow-up",
    "registration_pending": "Registration Pending",
    "brand_registered_pending_service": "Brand Registered Follow-up",
    "waiting_on_part_or_approval": "Waiting on Part / Approval",
    "ready_for_pickup": "Ready for Pickup",
    "sla_response_breach_candidates": "SLA Response Breach Candidate",
    "sla_resolution_breach_candidates": "SLA Resolution Breach Candidate",
}

REMINDER_NOTIFICATION_TYPE = "Reaction"
DEFAULT_SENDER = "Administrator"


def get_staff_recipients():
    """Return enabled staff users for reminder notifications."""

    recipients = set()

    if frappe.db.exists("DocType", "HD Agent"):
        agent_meta = frappe.get_meta("HD Agent")
        agent_user_field = None

        for candidate in ["user", "agent", "email"]:
            if agent_meta.has_field(candidate):
                agent_user_field = candidate
                break

        if agent_user_field:
            for row in frappe.get_all("HD Agent", fields=[agent_user_field], limit=500):
                user = row.get(agent_user_field)
                if _is_enabled_user(user):
                    recipients.add(user)

    for role in ["Agent", "Agent Manager"]:
        holders = frappe.get_all(
            "Has Role",
            filters={"role": role, "parenttype": "User"},
            fields=["parent"],
            limit=500,
        )

        for holder in holders:
            if _is_enabled_user(holder.parent):
                recipients.add(holder.parent)

    if not recipients and _is_enabled_user(DEFAULT_SENDER):
        recipients.add(DEFAULT_SENDER)

    return sorted(recipients)


def build_reminder_message(category, row):
    label = REMINDER_CATEGORIES.get(category, category)
    ticket_name = _ticket_name(row)
    subject = _row_value(row, "subject")
    customer_name = _row_value(row, "customer_name")

    parts = [f"[{category}] {label}"]

    if ticket_name:
        parts.append(f"Ticket: {ticket_name}")
    if subject:
        parts.append(f"Subject: {subject}")
    if customer_name:
        parts.append(f"Customer: {customer_name}")

    return " | ".join(parts)


def create_hd_notification(user, ticket_name, category, message):
    existing = _existing_unread_same_day_notification(
        user=user,
        ticket_name=ticket_name,
        message=message,
    )
    if existing:
        return {
            "created": False,
            "existing": existing,
            "user": user,
            "ticket": ticket_name,
            "category": category,
        }

    doc = frappe.new_doc("HD Notification")
    doc.user_from = _sender_user()
    doc.user_to = user
    doc.notification_type = REMINDER_NOTIFICATION_TYPE
    doc.reference_ticket = ticket_name
    doc.message = message
    doc.read = 0
    doc.insert(ignore_permissions=True)

    return {
        "created": True,
        "name": doc.name,
        "user": user,
        "ticket": ticket_name,
        "category": category,
    }


def create_reminder_notifications(snapshot=None, recipients=None, limit=100):
    """Create HD Notification reminders from scanner output."""

    snapshot = snapshot or get_reminder_snapshot(limit=limit)
    recipients = recipients or get_staff_recipients()

    results = {
        "recipients": recipients,
        "created": [],
        "deduped": [],
        "skipped": [],
    }

    if not recipients:
        results["skipped"].append({"reason": "no_recipients"})
        return results

    for category, rows in snapshot.get("tickets", {}).items():
        if category not in REMINDER_CATEGORIES:
            continue

        for row in rows:
            ticket_name = _ticket_name(row)
            if not ticket_name:
                results["skipped"].append(
                    {"category": category, "reason": "missing_ticket_name"}
                )
                continue

            message = build_reminder_message(category, row)

            for user in recipients:
                result = create_hd_notification(user, ticket_name, category, message)
                if result.get("created"):
                    results["created"].append(result)
                else:
                    results["deduped"].append(result)

    return results


def run_daily_reminder_notifications_dry_safe():
    """Create in-app HD Notification reminders without email or task side effects."""

    snapshot = get_reminder_snapshot(limit=500)
    results = create_reminder_notifications(snapshot=snapshot)

    frappe.logger("lavanya_service.reminders").info(
        {
            "event": "daily_reminder_notifications_hd_notification",
            "counts": snapshot.get("counts"),
            "recipients": results.get("recipients"),
            "created_count": len(results.get("created", [])),
            "deduped_count": len(results.get("deduped", [])),
            "skipped_count": len(results.get("skipped", [])),
        }
    )

    return {
        "snapshot_counts": snapshot.get("counts"),
        "results": results,
    }


def _existing_unread_same_day_notification(user, ticket_name, message):
    if not user or not ticket_name:
        return None

    filters = {
        "user_to": user,
        "reference_ticket": ticket_name,
        "notification_type": REMINDER_NOTIFICATION_TYPE,
        "message": message,
        "read": 0,
        "creation": ["between", [today() + " 00:00:00", today() + " 23:59:59"]],
    }

    existing = frappe.get_all("HD Notification", filters=filters, fields=["name"], limit=1)
    return existing[0].name if existing else None


def _is_enabled_user(user):
    return bool(user and frappe.db.exists("User", user) and frappe.db.get_value("User", user, "enabled"))


def _row_value(row, fieldname):
    if hasattr(row, "get"):
        return row.get(fieldname)

    return getattr(row, fieldname, None)


def _sender_user():
    if _is_enabled_user(frappe.session.user):
        return frappe.session.user

    return DEFAULT_SENDER


def _ticket_name(row):
    return _row_value(row, "name")
