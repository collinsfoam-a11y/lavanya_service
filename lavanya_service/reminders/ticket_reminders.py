import frappe
from frappe.utils import now_datetime, today


RESOLVED_STATUS_CATEGORY = "Resolved"


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
            ["status_category", "!=", RESOLVED_STATUS_CATEGORY],
        ],
        limit=limit,
    )


def get_sla_resolution_breach_candidates(limit=100):
    return _ticket_rows(
        [
            ["resolution_by", "is", "set"],
            ["resolution_by", "<", now_datetime()],
            ["status_category", "!=", RESOLVED_STATUS_CATEGORY],
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
