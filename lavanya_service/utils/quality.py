import frappe
from frappe.utils import today, date_diff


def compute_badge(ticket_name):
    """
    Compute follow-up quality badge for a ticket.
    FIXED: uses frappe.db.get_value (single query) instead of frappe.get_doc
    to avoid unnecessary full-document loads when called from loops.
    Returns: 'Good' | 'Needs Update' | 'At Risk' | 'Critical'
    """
    t = frappe.db.get_value("Lavanya Ticket", ticket_name, [
        "customer_dissatisfied", "promise_breach_count",
        "part_pending", "part_expected_date",
        "followup_overdue", "sla_breached", "escalation_level",
        "customer_informed", "next_followup_date",
    ], as_dict=True)

    if not t:
        return "Needs Update"

    # Critical conditions
    part_overdue = (
        t.part_pending
        and t.part_expected_date
        and date_diff(today(), str(t.part_expected_date)) > 0
    )
    if t.customer_dissatisfied or (t.promise_breach_count or 0) > 2 or part_overdue:
        return "Critical"

    # At Risk
    if t.followup_overdue or t.sla_breached or t.escalation_level in ["L3", "L4"]:
        return "At Risk"

    # Needs Update
    if not t.customer_informed or not t.next_followup_date:
        return "Needs Update"

    return "Good"


def compute_badge_bulk(ticket_names):
    """
    Bulk-compute quality badges for a list of ticket names.
    Returns a dict {ticket_name: badge}.
    Uses a single SQL query to avoid N+1 problem.
    """
    if not ticket_names:
        return {}

    placeholders = ", ".join(["%s"] * len(ticket_names))
    rows = frappe.db.sql(f"""
        SELECT
            name, customer_dissatisfied, promise_breach_count,
            part_pending, part_expected_date,
            followup_overdue, sla_breached, escalation_level,
            customer_informed, next_followup_date
        FROM `tabLavanya Ticket`
        WHERE name IN ({placeholders})
    """, tuple(ticket_names), as_dict=True)

    result = {}
    for t in rows:
        part_overdue = (
            t.part_pending
            and t.part_expected_date
            and date_diff(today(), str(t.part_expected_date)) > 0
        )
        if t.customer_dissatisfied or (t.promise_breach_count or 0) > 2 or part_overdue:
            badge = "Critical"
        elif t.followup_overdue or t.sla_breached or t.escalation_level in ["L3", "L4"]:
            badge = "At Risk"
        elif not t.customer_informed or not t.next_followup_date:
            badge = "Needs Update"
        else:
            badge = "Good"
        result[t.name] = badge

    return result


def get_next_action(ticket_name):
    """
    AI-style next action recommendation based on ticket state.
    Returns a string describing what staff should do next.
    """
    t = frappe.db.get_value("Lavanya Ticket", ticket_name, [
        "service_path", "brand_ticket_number", "technician_called",
        "technician_visited", "customer_informed", "followup_overdue",
        "brand_says_completed", "customer_satisfied", "status",
        "technician", "part_pending", "part_received",
    ], as_dict=True)

    if not t:
        return "Review ticket"

    if not t.brand_ticket_number and t.service_path in ["Brand Warranty", "Brand Paid Service"]:
        return "Register brand complaint — brand ticket number missing"

    if t.service_path in ["Brand Warranty", "Brand Paid Service"]:
        if not t.technician_called:
            return "Verify whether technician called the customer"
        if not t.technician_visited:
            return "Verify whether technician visited the customer"
        if not t.customer_informed:
            return "Inform customer about current status"
        if t.followup_overdue:
            return "Record service center follow-up — overdue"
        if t.brand_says_completed and not t.customer_satisfied:
            return "Verify customer satisfaction — brand marked resolved"

    if t.service_path == "Local Paid Service":
        if not t.technician:
            return "Assign a local technician"
        if not t.technician_visited:
            return "Verify technician visit"

    if t.status == "Customer Confirmation Pending":
        return "Call customer and confirm issue is resolved"

    if t.part_pending and not t.part_received:
        return "Follow up spare part delivery status"

    if t.customer_satisfied:
        return "Close ticket — customer confirmed resolution"

    return "Review ticket and take appropriate follow-up action"
