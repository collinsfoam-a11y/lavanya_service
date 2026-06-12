"""Rollback-safe test for System Pushed HD Notifications (Phase 1N-6D).

Run with:
    bench --site <site> execute lavanya_service.tests.system_pushed_notifications.run
"""

import frappe
from frappe.utils import today

RESULTS = []

SIDE_EFFECT_DOCTYPES = [
    "Email Queue",
    "Notification Log",
    "Communication",
    "ToDo",
    "Comment",
]

ROLLBACK_DOCTYPES = [
    "HD Ticket",
    "HD Notification",
    "User",
    "Has Role",
] + SIDE_EFFECT_DOCTYPES


def _record(test_id, description, passed, detail=""):
    RESULTS.append((test_id, description, bool(passed), detail))
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {test_id} - {description}" + (f" | {detail}" if detail else ""))


def _assert(test_id, description, condition, detail=""):
    _record(test_id, description, condition, detail)


def _count(doctype):
    return frappe.db.count(doctype) if frappe.db.exists("DocType", doctype) else 0


def _side_effect_counts():
    return {doctype: _count(doctype) for doctype in SIDE_EFFECT_DOCTYPES}


def _make_user(role):
    email = "sys-notify-" + role.lower().replace(" ", "-") + "@example.com"
    user = frappe.new_doc("User")
    user.email = email
    user.first_name = "Sys Notify"
    user.enabled = 1
    user.user_type = "System User"
    user.append("roles", {"role": role})
    user.insert(ignore_permissions=True)
    return email


def _insert_ticket(subject, status="New", ticket_type="Customer Complaint - Site", **overrides):
    doc = frappe.new_doc("HD Ticket")
    doc.subject = subject
    doc.raised_by = "sys-notify-test@example.com"
    doc.status = status
    doc.ticket_type = ticket_type
    doc.priority = overrides.pop("priority", "Medium")
    doc.complaint_source = overrides.pop("complaint_source", "Phone Call")
    doc.customer_name = overrides.pop("customer_name", "Sys Notify Customer")
    doc.phone_1 = overrides.pop("phone_1", "0495-2222222 ext 5")
    doc.product_type = overrides.pop("product_type", "AC")
    doc.brand = overrides.pop("brand", "LG")
    
    if status in {"In Progress", "Waiting on Customer", "Waiting on Part / Approval", "Ready for Pickup"}:
        doc.pending_reason = overrides.pop("pending_reason", "Service Follow-up Required")
        doc.next_follow_up_date = overrides.pop("next_follow_up_date", today())

    doc.update(overrides)
    doc.insert(ignore_permissions=True)
    
    doc = frappe.get_doc("HD Ticket", doc.name)
    if doc.status != status:
        doc.status = status
        doc.save(ignore_permissions=True)
        doc.reload()
    return doc


def run():
    RESULTS.clear()
    baseline = {doctype: _count(doctype) for doctype in ROLLBACK_DOCTYPES}

    try:
        from lavanya_service.reminders.notification_output import run_daily_reminder_notifications_dry_safe

        _run_all(run_daily_reminder_notifications_dry_safe, baseline)
    finally:
        frappe.set_user("Administrator")
        frappe.db.rollback()

        rollback_ok = {doctype: _count(doctype) == baseline[doctype] for doctype in ROLLBACK_DOCTYPES}
        _assert(
            "SN-005",
            "automated test records roll back cleanly",
            all(rollback_ok.values()),
            rollback_ok,
        )
        print("\nTRANSACTION ROLLED BACK - no records persisted")

    failed = [row for row in RESULTS if not row[2]]
    print(f"\nTOTAL: {len(RESULTS)} | PASS: {len(RESULTS) - len(failed)} | FAIL: {len(failed)}")
    if failed:
        print("FAILED TESTS:")
        for test_id, description, _passed, detail in failed:
            print(f"  - {test_id}: {description} | {detail}")
    print("BASELINE:", baseline)
    print("OVERALL:", "PASS" if not failed else "FAIL")
    return {"total": len(RESULTS), "failed": len(failed)}


def _run_all(run_daily_reminder_notifications_dry_safe, baseline):
    front_desk = _make_user("Lavanya Front Desk")
    
    new_ticket = _insert_ticket("SN New Complaint", status="New")
    
    before_api_counts = _side_effect_counts()
    
    # Run once
    res1 = run_daily_reminder_notifications_dry_safe()
    
    created_count = len(res1["results"].get("created", []))
    _assert("SN-001", "first run creates notifications", created_count > 0, {"created": created_count})
    
    # Verify the notification has the right format
    created_notifications = res1["results"].get("created", [])
    has_target = False
    for notif in created_notifications:
        if notif["user"] == front_desk and notif["category"] == "new_complaints":
            has_target = True
            break
            
    _assert("SN-002", "front desk user received new_complaints notification", has_target)
    
    after_api_counts = _side_effect_counts()
    
    _assert(
        "SN-003",
        "API creates no forbidden side effects",
        before_api_counts == after_api_counts,
        {"before": before_api_counts, "after": after_api_counts},
    )
    
    # Run twice
    res2 = run_daily_reminder_notifications_dry_safe()
    created_count_2 = len(res2["results"].get("created", []))
    deduped_count_2 = len(res2["results"].get("deduped", []))
    
    _assert("SN-004", "second run dedupes and creates zero new notifications", created_count_2 == 0 and deduped_count_2 > 0, {"created": created_count_2, "deduped": deduped_count_2})
