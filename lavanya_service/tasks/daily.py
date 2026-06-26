import frappe
from frappe.utils import today, add_days

def run_daily_tasks():
    """Called every day — compute quality badges, flag overdue"""
    flag_overdue_followups()
    compute_quality_badges()

def send_morning_digest():
    """Send daily digest email to all Service Managers at 8 AM."""
    from frappe.utils import get_url
    # Fetch managers via Has Role child table
    managers = frappe.db.sql("""
        SELECT u.name, u.full_name, u.email
        FROM `tabUser` u
        JOIN `tabHas Role` r ON r.parent = u.name
        WHERE r.role = 'Service Manager'
          AND u.enabled = 1
          AND u.email IS NOT NULL
          AND u.email != ''
    """, as_dict=True)

    if not managers:
        return

    open_f = {"status": ["not in", ["Closed", "Cancelled"]]}
    stats = {
        "open":      frappe.db.count("Lavanya Ticket", open_f),
        "overdue":   frappe.db.count("Lavanya Ticket", {**open_f, "followup_overdue": 1}),
        "escalated": frappe.db.count("Lavanya Ticket", {**open_f, "escalation_level": ["in", ["L3", "L4"]]}),
        "not_informed": frappe.db.count("Lavanya Ticket", {**open_f, "customer_informed": 0}),
        "closed_today": frappe.db.count("Lavanya Ticket", {"status": "Closed", "closed_on": [">=", today()]}),
    }

    subject = f"[Lavanya Service] Daily Digest — {today()}"
    message = f"""
<h3>Good morning</h3>
<p>Here is your Lavanya Service summary for today:</p>
<table style="border-collapse:collapse;font-family:sans-serif;font-size:14px">
  <tr><td style="padding:6px 16px;color:#555">Open Tickets</td><td style="font-weight:bold">{stats['open']}</td></tr>
  <tr style="background:#FFF1F3"><td style="padding:6px 16px;color:#E11D48">Overdue Follow-ups</td><td style="font-weight:bold;color:#E11D48">{stats['overdue']}</td></tr>
  <tr style="background:#FFF7ED"><td style="padding:6px 16px;color:#D97706">Escalated (L3/L4)</td><td style="font-weight:bold;color:#D97706">{stats['escalated']}</td></tr>
  <tr><td style="padding:6px 16px;color:#555">Customer Not Informed</td><td style="font-weight:bold">{stats['not_informed']}</td></tr>
  <tr style="background:#F0FDFA"><td style="padding:6px 16px;color:#0D9488">Closed Today</td><td style="font-weight:bold;color:#0D9488">{stats['closed_today']}</td></tr>
</table>
<p style="margin-top:16px">
  <a href="{get_url('/lavanya-manager')}" style="background:#0D9488;color:#fff;padding:10px 20px;border-radius:8px;text-decoration:none;font-weight:bold">
    Open Manager Dashboard
  </a>
</p>
"""
    for mgr in managers:
        frappe.sendmail(
            recipients=[mgr.email],
            subject=subject,
            message=message,
            now=True,
        )

def flag_overdue_followups():
    """Set followup_overdue=1 for tickets past their due date,
    AND clear it back to 0 for tickets with a future due date.
    This ensures the flag is always accurate after staff reschedule."""
    open_statuses = ["Closed", "Cancelled"]

    # Mark overdue — list-of-lists so both next_followup_date filters apply
    # (a dict would silently drop the first filter due to duplicate key).
    overdue = frappe.get_all(
        "Lavanya Ticket",
        filters=[
            ["status", "not in", open_statuses],
            ["next_followup_date", "<", today()],
            ["next_followup_date", "is", "set"],
        ],
        fields=["name"]
    )
    for t in overdue:
        frappe.db.set_value("Lavanya Ticket", t.name, "followup_overdue", 1,
                            update_modified=False)

    # Clear flag for tickets with a future follow-up date
    not_overdue = frappe.get_all(
        "Lavanya Ticket",
        filters={
            "status": ["not in", open_statuses],
            "next_followup_date": [">=", today()],
            "followup_overdue": 1,
        },
        fields=["name"]
    )
    for t in not_overdue:
        frappe.db.set_value("Lavanya Ticket", t.name, "followup_overdue", 0,
                            update_modified=False)

    frappe.db.commit()

def compute_quality_badges():
    """
    FIXED: uses bulk SQL query (compute_badge_bulk) instead of
    frappe.get_doc() inside a loop, eliminating the N+1 query problem.
    For 500 open tickets: was 500 DB roundtrips → now 1 query.
    """
    from lavanya_service.utils.quality import compute_badge_bulk
    tickets = frappe.get_all(
        "Lavanya Ticket",
        filters={"status": ["not in", ["Closed", "Cancelled"]]},
        fields=["name"],
        limit=2000,
    )
    names = [t.name for t in tickets]
    if not names:
        return

    badges = compute_badge_bulk(names)
    for name, badge in badges.items():
        frappe.db.set_value("Lavanya Ticket", name, "quality_badge", badge,
                            update_modified=False)
    frappe.db.commit()
