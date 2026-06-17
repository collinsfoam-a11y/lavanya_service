import frappe


def _stage_overdue_status(ticket):
    from lavanya_service.stage_rules import compute_overdue_status

    return compute_overdue_status(
        ticket.get("stage_due_at"), ticket.get("pre_overdue_alert_at"), ticket.get("next_follow_up_date")
    )


def _stage_escalation_level(ticket):
    from lavanya_service.stage_rules import compute_escalation_level

    return compute_escalation_level(
        ticket.get("stage_due_at"),
        ticket.get("next_follow_up_date"),
        is_repeat=(ticket.get("is_repeated_complaint") == "Yes"),
    )


def _stage_promise_status(ticket):
    from lavanya_service.stage_rules import compute_promise_status

    return compute_promise_status(
        ticket.get("customer_promised_update_at"), ticket.get("customer_promise_status")
    )


def _reminder_intelligence(ticket):
    """Read-only Reminder Engine state for the drawer (Step 5). Blank-safe —
    never raises, so a resolver issue can't break the ticket detail."""
    try:
        from lavanya_service.reminder_engine import refresh_ticket_reminder_state

        state = refresh_ticket_reminder_state(ticket, save=False)
        manual = ticket.get("next_follow_up_date")
        return {
            "reminder_rule_applied": state.get("reminder_rule_applied"),
            "next_follow_up_date": manual,  # manual / staff-facing
            "computed_next_followup_at": state.get("computed_next_followup_at"),
            "computed_due_soon_at": state.get("computed_due_soon_at"),
            "computed_stage_due_at": state.get("computed_stage_due_at"),
            "overdue_status": state.get("overdue_status"),
            "escalation_level": state.get("computed_escalation_level"),
            "customer_promise_status": state.get("customer_promise_status"),
            "customer_promised_update_at": ticket.get("customer_promised_update_at"),
            "promise_breach_reason": ticket.get("promise_breach_reason"),
            "customer_update_due": state.get("customer_update_due"),
            "manual_followup": bool(manual),
        }
    except Exception:
        frappe.log_error(title="lavanya reminder_intelligence (drawer)", message=frappe.get_traceback())
        return {}


@frappe.whitelist(methods=["POST"])
def set_customer_promise(ticket_name, promised_at=None, status=None):
    """Record a customer-promised update time (status -> Pending), or mark it Kept /
    Clear. The reminder engine flips Pending -> Breached once the time passes.
    Write-permission scoped; logs a [Customer Informed] comment (Comment stays the
    canonical activity log)."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    if not frappe.db.exists("HD Ticket", ticket_name):
        frappe.throw("Ticket not found.")
    if not frappe.has_permission("HD Ticket", "write", doc=ticket_name):
        frappe.throw("Not permitted", frappe.PermissionError)

    doc = frappe.get_doc("HD Ticket", ticket_name)
    if status == "Kept":
        doc.customer_promise_status = "Kept"
        note = "[Customer Informed] Promised update kept"
    elif status == "Clear":
        doc.customer_promised_update_at = None
        doc.customer_promise_status = "None"
        note = "[Customer Informed] Promise cleared"
    else:
        dt = (promised_at or "").replace("T", " ").strip()
        if not dt:
            frappe.throw("Promised update date & time is required.")
        doc.customer_promised_update_at = dt
        doc.customer_promise_status = "Pending"
        note = f"[Customer Informed] Promised an update by {dt}"

    doc.flags.ignore_lavanya_field_guard = True
    doc.save(ignore_permissions=True)
    doc.add_comment("Comment", note)
    return {"ok": True, "ticket": ticket_name, "promise_status": doc.customer_promise_status}


# Ticket fields safe to surface in the SPA list view.
_LIST_FIELDS = [
    "name",
    "subject",
    "status",
    "priority",
    "customer_name",
    "phone_1",
    "product_item",
    "brand",
    "next_follow_up_date",
    "pending_reason",
    "modified",
    "creation",
    # SLA (Helpdesk-maintained) — surfaced as due/breach badges in the SPA.
    "agreement_status",
    "response_by",
    "resolution_by",
    "first_responded_on",
]


@frappe.whitelist()
def get_ticket_list(search=None, status=None, start=0, page_length=30):
    """Paginated, permission-scoped HD Ticket list for the SPA Tickets page.

    Honours the user's HD Ticket read permissions (frappe.get_list applies the
    user_permissions / role-based query filters automatically). Supports a free
    -text search across name / subject / customer / phone, and a status filter.
    """
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)

    start = frappe.utils.cint(start)
    page_length = min(frappe.utils.cint(page_length) or 30, 100)

    filters = {}
    if status and status != "All":
        filters["status"] = status

    or_filters = None
    if search:
        like = f"%{search.strip()}%"
        or_filters = [
            ["name", "like", like],
            ["subject", "like", like],
            ["customer_name", "like", like],
            ["phone_1", "like", like],
        ]

    tickets = frappe.get_list(
        "HD Ticket",
        fields=_LIST_FIELDS,
        filters=filters,
        or_filters=or_filters,
        order_by="modified desc",
        start=start,
        page_length=page_length,
    )

    has_more = len(tickets) == page_length
    return {"tickets": tickets, "start": start, "page_length": page_length, "has_more": has_more}


# Comment types Frappe auto-logs as ticket activity (status/field/assignment
# changes) vs. a user-written note ("Comment").
_ACTIVITY_TYPES = ("Info", "Workflow", "Edit", "Label", "Assigned", "Assignment Completed", "Attachment")


@frappe.whitelist()
def get_new_ticket_options():
    """Option lists for the staff New Ticket screen (brands / product types /
    ticket types). Reuses the QR intake's safe lists."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    from lavanya_service.api.qr_intake import get_qr_intake_options

    opts = get_qr_intake_options()
    opts["complaint_sources"] = ["Staff Entered", "Phone Call", "WhatsApp", "Direct Visit", "Email"]
    opts["warranty_statuses"] = ["Unknown", "In Warranty", "Out of Warranty", "Extended Warranty", "Brand Denied"]
    return opts


@frappe.whitelist(methods=["POST"])
def create_ticket(
    customer_name=None,
    mobile=None,
    complaint_details=None,
    product_type=None,
    brand=None,
    ticket_type=None,
    model_no=None,
    serial_no=None,
    warranty_status=None,
    address=None,
    pincode=None,
    complaint_source=None,
):
    """Staff-side ticket creation for the SPA New Ticket screen. Created as the
    real staff user (permission-scoped) with complaint_source 'Staff Entered',
    returning the ticket name so the UI can open it. Reuses the QR intake's
    validation constants + phone normalization."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    if not frappe.has_permission("HD Ticket", "create"):
        frappe.throw("Not permitted to create tickets.", frappe.PermissionError)

    from lavanya_service.api.qr_intake import (
        VALID_PRODUCT_TYPES,
        SAFE_TICKET_TYPES,
        DEFAULT_TICKET_TYPE,
        BRAND_DOCTYPE,
    )
    from lavanya_service.utils.phone import normalize_phone

    def _req(value, label):
        if not value or not str(value).strip():
            frappe.throw(f"{label} is required.")
        return str(value).strip()

    customer_name = _req(customer_name, "Customer Name")
    mobile = _req(mobile, "Mobile Number")
    complaint_details = _req(complaint_details, "Complaint Details")
    product_type = _req(product_type, "Product Type")
    brand = _req(brand, "Brand")

    phone = normalize_phone(mobile)
    if not phone.get("is_valid_mobile"):
        frappe.throw("Please provide a valid 10-digit mobile number.")
    mobile = phone["normalized"]

    if product_type not in VALID_PRODUCT_TYPES:
        frappe.throw("Please select a valid product type from the list.")
    if not frappe.db.exists(BRAND_DOCTYPE, brand):
        frappe.throw("Please select a valid brand from the list.")

    if not ticket_type or ticket_type not in SAFE_TICKET_TYPES:
        ticket_type = DEFAULT_TICKET_TYPE

    valid_sources = {"Staff Entered", "Phone Call", "WhatsApp", "Direct Visit", "Email"}
    if complaint_source not in valid_sources:
        complaint_source = "Staff Entered"

    valid_warranty = {"Unknown", "In Warranty", "Out of Warranty", "Extended Warranty", "Brand Denied"}

    doc = frappe.new_doc("HD Ticket")
    doc.subject = f"{customer_name} / {product_type} {brand}"[:140]
    doc.ticket_type = ticket_type
    doc.priority = "Medium"
    doc.complaint_source = complaint_source
    doc.customer_name = customer_name
    doc.phone_1 = mobile
    doc.description = complaint_details
    doc.product_type = product_type
    doc.brand = brand
    doc.warranty_status = warranty_status if warranty_status in valid_warranty else "Unknown"
    if model_no:
        doc.model_no = str(model_no).strip()
    if serial_no:
        doc.serial_no = str(serial_no).strip()
    if address:
        doc.address = str(address).strip()
    if pincode:
        doc.pincode = str(pincode).strip()
    doc.insert()

    return {"ok": True, "ticket": doc.name, "message": f"Ticket {doc.name} created"}


@frappe.whitelist()
def get_ticket_activity(ticket_id, limit=50):
    """Merged activity timeline for a ticket: user notes + Frappe's auto-logged
    field/status/assignment changes, newest first. Read-permission scoped."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    if not frappe.has_permission("HD Ticket", "read", doc=ticket_id):
        frappe.throw("Not permitted", frappe.PermissionError)

    limit = min(frappe.utils.cint(limit) or 50, 100)
    comments = frappe.get_all(
        "Comment",
        filters={"reference_doctype": "HD Ticket", "reference_name": ticket_id},
        fields=["name", "comment_type", "content", "comment_by", "comment_email", "creation"],
        order_by="creation desc",
        limit_page_length=limit,
    )

    events = []
    for c in comments:
        is_note = c.comment_type == "Comment"
        events.append({
            "id": c.name,
            "kind": "note" if is_note else "activity",
            "text": frappe.utils.strip_html(c.content or "").strip(),
            "by": c.comment_by or c.comment_email or "System",
            "on": c.creation,
        })

    # Always append the ticket creation as the earliest event.
    created = frappe.db.get_value("HD Ticket", ticket_id, ["creation", "owner"], as_dict=True)
    if created:
        events.append({
            "id": "_created",
            "kind": "activity",
            "text": "Ticket created",
            "by": created.owner or "System",
            "on": created.creation,
        })

    return {"events": events}


@frappe.whitelist(methods=["POST"])
def add_ticket_note(ticket_id, note):
    """Add an internal note to a ticket (write-permission scoped). Returns the
    new timeline event so the UI can prepend it without a full reload."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    if not frappe.has_permission("HD Ticket", "write", doc=ticket_id):
        frappe.throw("Not permitted", frappe.PermissionError)

    note = (note or "").strip()
    if not note:
        frappe.throw("Note cannot be empty.")

    doc = frappe.get_doc("HD Ticket", ticket_id)
    comment = doc.add_comment("Comment", note)
    return {
        "id": comment.name,
        "kind": "note",
        "text": frappe.utils.strip_html(comment.content or "").strip(),
        "by": comment.comment_by or comment.comment_email or frappe.session.user,
        "on": comment.creation,
    }


@frappe.whitelist(methods=["POST"])
def schedule_appointment(ticket_name, appointment_datetime, technician=None, notes=None):
    """Schedule a site-visit appointment for a ticket (date+time+technician).
    Stored in the Lavanya Service Appointment doctype — no HD Ticket schema change."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    if not frappe.db.exists("HD Ticket", ticket_name):
        frappe.throw("Ticket not found.")
    if not frappe.has_permission("HD Ticket", "write", doc=ticket_name):
        frappe.throw("Not permitted", frappe.PermissionError)

    dt = (appointment_datetime or "").replace("T", " ").strip()
    if not dt:
        frappe.throw("Appointment date & time is required.")

    appt = frappe.new_doc("Lavanya Service Appointment")
    appt.ticket = ticket_name
    appt.appointment_datetime = dt
    appt.technician = (technician or "").strip() or None
    appt.notes = (notes or "").strip() or None
    appt.status = "Scheduled"
    appt.insert()
    return {"ok": True, "appointment": appt.name, "message": "Appointment scheduled"}


@frappe.whitelist()
def get_ticket_detail(ticket_id):
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)

    # Validate permission to read the ticket
    if not frappe.has_permission("HD Ticket", "read", doc=ticket_id):
        frappe.throw("Not permitted", frappe.PermissionError)

    ticket = frappe.get_doc("HD Ticket", ticket_id)

    # Basic Customer details from the ticket
    customer_name = ticket.get("customer_name")
    phone_1 = ticket.get("phone_1") or ""
    address = ticket.get("address") or ""
    pincode = ticket.get("pincode") or ""
    
    # Get receipt custody info
    receipt_no = None
    custody_status = None
    last_movement = None
    ready_for_pickup = False

    receipts = frappe.get_all("Service Product Receipt", 
        filters={"ticket": ticket_id, "docstatus": 1},
        fields=["name", "current_custody_status", "modified"],
        order_by="creation desc", limit=1
    )
    if receipts:
        receipt_no = receipts[0].name
        custody_status = receipts[0].current_custody_status
        last_movement = receipts[0].modified
        ready_for_pickup = (custody_status == "Ready for Customer Pickup")

    # Safe payload
    return {
        "name": ticket.name,
        "status": ticket.status,
        "priority": ticket.priority,
        "customer": {
            "name": customer_name,
            "mobile": phone_1,
            "address": address,
            "pincode": pincode
        },
        "product": {
            "type": ticket.get("product_type"),
            "item": ticket.get("product_item"),
            "brand": ticket.get("brand"),
            "model_number": ticket.get("model_no"),
            "serial_number": ticket.get("serial_no"),
            "warranty_status": ticket.get("warranty_status"),
            "invoice_number": ticket.get("invoice_no") or ticket.get("invoice_number"),
            "purchase_date": ticket.get("purchase_date")
        },
        "workflow": {
            "status": ticket.status,
            "pending_reason": ticket.get("pending_reason"),
            "next_follow_up_date": ticket.get("next_follow_up_date"),
            "brand_ticket_number": ticket.get("brand_ticket_number"),
            "brand_registration_date": ticket.get("registration_date") or ticket.get("brand_registration_date"),
            "service_center": ticket.get("service_center")
        },
        "receipt": {
            "number": receipt_no,
            "custody_status": custody_status,
            "last_movement": last_movement,
            "ready_for_pickup": ready_for_pickup
        },
        "sla": {
            "name": ticket.get("sla"),
            "agreement_status": ticket.get("agreement_status"),
            "response_by": ticket.get("response_by"),
            "resolution_by": ticket.get("resolution_by"),
            "first_responded_on": ticket.get("first_responded_on"),
            "resolution_date": ticket.get("resolution_date"),
        },
        "repeat": {
            "is_repeat": ticket.get("is_repeated_complaint") == "Yes",
            "previous_ticket": ticket.get("previous_ticket_link"),
        },
        "appointment": (lambda a: a[0] if a else None)(
            frappe.get_all(
                "Lavanya Service Appointment",
                filters={"ticket": ticket_id, "status": "Scheduled"},
                fields=["name", "appointment_datetime", "technician"],
                order_by="appointment_datetime asc",
                limit=1,
            )
        ),
        "stage": {
            "service_flow_type": ticket.get("service_flow_type"),
            "current_service_stage": ticket.get("current_service_stage"),
            "next_action": ticket.get("next_action"),
            "next_action_owner": ticket.get("next_action_owner"),
            "next_action_role": ticket.get("next_action_role"),
            "next_follow_up_date": ticket.get("next_follow_up_date"),
            "stage_due_at": ticket.get("stage_due_at"),
            "pre_overdue_alert_at": ticket.get("pre_overdue_alert_at"),
            "overdue_status": _stage_overdue_status(ticket),
            "escalation_level": _stage_escalation_level(ticket),
            "customer_informed": ticket.get("customer_informed"),
            "customer_promised_update_at": ticket.get("customer_promised_update_at"),
            "customer_promise_status": _stage_promise_status(ticket),
        },
        "reminder": _reminder_intelligence(ticket),
        "assigned_to": ticket._assign if ticket._assign else None,
        "creation": ticket.creation
    }
