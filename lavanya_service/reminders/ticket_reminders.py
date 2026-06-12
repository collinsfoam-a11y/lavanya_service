import frappe
from frappe.utils import now_datetime, today


ACTIVE_STATUS_CATEGORY = "Open"
RESOLVED_STATUS_CATEGORY = "Resolved"
REMINDER_HEARTBEAT_CACHE_KEY = "lavanya_service:last_reminder_scan_heartbeat"


DEFAULT_FIELDS = [
    "name",
    "subject",
    "status",
    "status_category",
    "priority",
    "ticket_type",
    "customer_name",
    "phone_1",
    "brand",
    "product_type",
    "pending_reason",
    "next_follow_up_date",
    "response_by",
    "resolution_by",
    "agreement_status",
    "sla",
    "modified",
]


def _ticket_rows(filters, limit=100):
    return frappe.get_all(
        "HD Ticket",
        filters=filters,
        fields=DEFAULT_FIELDS,
        order_by="modified asc",
        limit=limit,
    )


def get_follow_up_due_today(limit=100):
    return _ticket_rows(
        {
            "next_follow_up_date": today(),
            "status_category": ["!=", RESOLVED_STATUS_CATEGORY],
        },
        limit=limit,
    )


def get_overdue_follow_ups(limit=100):
    return _ticket_rows(
        [
            ["next_follow_up_date", "is", "set"],
            ["next_follow_up_date", "<", today()],
            ["status_category", "!=", RESOLVED_STATUS_CATEGORY],
        ],
        limit=limit,
    )


def get_registration_pending(limit=100):
    return _ticket_rows({"status": "Registration Pending"}, limit=limit)


def get_brand_registered_pending_service(limit=100):
    return _ticket_rows({"status": "Brand Registered"}, limit=limit)


def get_waiting_on_part_or_approval(limit=100):
    return _ticket_rows({"status": "Waiting on Part / Approval"}, limit=limit)


def get_ready_for_pickup(limit=100):
    return _ticket_rows({"status": "Ready for Pickup"}, limit=limit)


def get_sla_response_breach_candidates(limit=100):
    return _ticket_rows(
        [
            ["response_by", "is", "set"],
            ["response_by", "<", now_datetime()],
            ["status_category", "=", ACTIVE_STATUS_CATEGORY],
        ],
        limit=limit,
    )


def get_sla_resolution_breach_candidates(limit=100):
    return _ticket_rows(
        [
            ["resolution_by", "is", "set"],
            ["resolution_by", "<", now_datetime()],
            ["status_category", "=", ACTIVE_STATUS_CATEGORY],
        ],
        limit=limit,
    )


def get_reminder_snapshot(limit=100):
    snapshot = {
        "follow_up_due_today": get_follow_up_due_today(limit=limit),
        "overdue_follow_ups": get_overdue_follow_ups(limit=limit),
        "registration_pending": get_registration_pending(limit=limit),
        "brand_registered_pending_service": get_brand_registered_pending_service(limit=limit),
        "waiting_on_part_or_approval": get_waiting_on_part_or_approval(limit=limit),
        "ready_for_pickup": get_ready_for_pickup(limit=limit),
        "sla_response_breach_candidates": get_sla_response_breach_candidates(limit=limit),
        "sla_resolution_breach_candidates": get_sla_resolution_breach_candidates(limit=limit),
    }

    return {
        "generated_at": str(now_datetime()),
        "counts": {key: len(value) for key, value in snapshot.items()},
        "tickets": snapshot,
    }


def print_reminder_snapshot(limit=100):
    snapshot = get_reminder_snapshot(limit=limit)

    print("generated_at:", snapshot["generated_at"])
    print("counts:", snapshot["counts"])

    for category, rows in snapshot["tickets"].items():
        print("\n===", category, "=== count=", len(rows))
        for row in rows:
            print(dict(row))

    return snapshot


def record_reminder_scan_heartbeat(snapshot, started_at=None, finished_at=None, event=None):
    started_at = started_at or now_datetime()
    finished_at = finished_at or now_datetime()
    duration_seconds = (finished_at - started_at).total_seconds()

    heartbeat = {
        "event": event or "daily_reminder_scan",
        "site": frappe.local.site,
        "started_at": str(started_at),
        "finished_at": str(finished_at),
        "duration_seconds": duration_seconds,
        "counts": snapshot.get("counts", {}),
    }

    frappe.cache().set_value(REMINDER_HEARTBEAT_CACHE_KEY, frappe.as_json(heartbeat))
    frappe.logger("lavanya_service.reminders").info(heartbeat)

    return heartbeat


def get_last_reminder_scan_heartbeat():
    raw_value = frappe.cache().get_value(REMINDER_HEARTBEAT_CACHE_KEY)
    if not raw_value:
        return None

    if isinstance(raw_value, bytes):
        raw_value = raw_value.decode()

    return frappe.parse_json(raw_value)


def run_daily_reminder_scan_dry_run():
    """Daily scheduler entrypoint.

    Safe dry-run only:
    - scans reminder categories
    - logs counts
    - does not create notifications
    - does not enqueue emails
    - does not mutate tickets
    """
    started_at = now_datetime()
    snapshot = get_reminder_snapshot(limit=500)
    record_reminder_scan_heartbeat(
        snapshot=snapshot,
        started_at=started_at,
        finished_at=now_datetime(),
        event="daily_reminder_scan_dry_run",
    )

    return snapshot
