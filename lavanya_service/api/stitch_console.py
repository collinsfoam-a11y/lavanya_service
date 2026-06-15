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
        "assigned_to": ticket._assign if ticket._assign else None,
        "creation": ticket.creation
    }
