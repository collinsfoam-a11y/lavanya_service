import frappe

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
        "assigned_to": ticket._assign if ticket._assign else None,
        "creation": ticket.creation
    }
