import frappe
from frappe import _
from frappe.utils import today, now_datetime, date_diff, cint
from lavanya_service.utils.quality import compute_badge, get_next_action

# Whitelist of allowed sort columns — prevents SQL injection
_ALLOWED_SORT = {
    "creation desc":  "t.creation DESC",
    "creation asc":   "t.creation ASC",
    "days_open desc": "t.days_open DESC",
    "days_open asc":  "t.days_open ASC",
    "newest":         "t.creation DESC",   # friendly alias from Vue default
    "oldest":         "t.creation ASC",
}

@frappe.whitelist()
def get_list(filters=None, page=1, page_size=20, sort_by="creation desc", search=None, status=None):
    """Return paginated ticket list for the Tickets page."""
    filters = filters or {}
    if status:
        filters["status"] = status

    # SECURITY: whitelist sort column — never interpolate user input directly
    safe_order = _ALLOWED_SORT.get(str(sort_by).lower(), "t.creation DESC")

    conditions = []
    values = {}

    if search:
        conditions.append("""(
            t.name LIKE %(search)s OR
            t.customer_name LIKE %(search)s OR
            t.customer_phone LIKE %(search)s OR
            t.subject LIKE %(search)s
        )""")
        values["search"] = f"%{search}%"

    if filters.get("status"):
        conditions.append("t.status = %(status)s")
        values["status"] = filters["status"]

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
    offset = (cint(page) - 1) * cint(page_size)

    tickets = frappe.db.sql(f"""
        SELECT
            t.name, t.subject, t.customer_name, t.customer_phone,
            t.status, t.follow_up_stage, t.service_path,
            t.brand, t.product_model, t.priority,
            t.quality_badge, t.next_action,
            t.next_followup_date, t.sla_due_date, t.sla_breached,
            t.followup_overdue, t.escalation_level,
            t.customer_informed, t.days_open,
            t.creation
        FROM `tabLavanya Ticket` t
        {where_clause}
        ORDER BY {safe_order}
        LIMIT %(limit)s OFFSET %(offset)s
    """, dict(limit=cint(page_size), offset=offset, **values), as_dict=True)

    total = frappe.db.sql(f"""
        SELECT COUNT(*) FROM `tabLavanya Ticket` t {where_clause}
    """, values)[0][0]

    return {"tickets": tickets, "total": total}


@frappe.whitelist()
def get_ticket(name):
    """Return full ticket detail for TicketDetail page."""
    if not frappe.has_permission("Lavanya Ticket", "read", name):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    doc = frappe.get_doc("Lavanya Ticket", name)
    data = doc.as_dict()

    # Attach follow-up timeline
    data["timeline"] = frappe.get_all(
        "Lavanya Followup Log",
        filters={"ticket": name},
        fields=["*"],
        order_by="creation desc",
        limit=50
    )

    # Attach product/warranty history
    if doc.customer:
        data["product_history"] = frappe.get_all(
            "Lavanya Customer Product",
            filters={"customer": doc.customer},
            fields=["*"]
        )

    # Compute quality + next action fresh
    data["quality_badge"] = compute_badge(name)
    data["next_action"]   = get_next_action(name)

    # CRM link (if Frappe CRM installed)
    if frappe.db.exists("DocType", "CRM Deal"):
        data["crm_deals"] = frappe.get_all(
            "CRM Deal",
            filters={"custom_service_ticket": name},
            fields=["name", "status", "deal_owner", "annual_revenue"]
        )

    return data


@frappe.whitelist()
def create_ticket(data):
    """Create a new Lavanya Ticket from the 4-step wizard."""
    import json
    if isinstance(data, str):
        data = json.loads(data)

    # Duplicate customer check
    existing = frappe.db.get_value(
        "Lavanya Customer",
        {"customer_phone": data.get("phone")},
        "name"
    )

    doc = frappe.new_doc("Lavanya Ticket")
    # FIXED: form sends 'category' not 'product_category'
    category = data.get("category") or data.get("product_category") or ""
    customer_link = existing or _create_customer(data)

    doc.update({
        "subject":          data.get("subject") or f"{data.get('brand', '')} {category} Complaint".strip(),
        "customer":         customer_link,
        "customer_name":    data.get("customer_name"),
        "customer_phone":   data.get("phone"),
        "brand":            data.get("brand"),
        "product_category": category,
        "product_model":    data.get("model"),
        "serial_number":    data.get("serial"),
        "invoice_number":   data.get("invoice"),
        "purchase_date":    data.get("purchase_date"),
        "warranty_status":  data.get("warranty_status"),
        "service_path":     data.get("service_path"),
        "complaint_type":   data.get("complaint_type"),
        "description":      data.get("description"),
        "priority":         data.get("priority") or "Medium",
        "status":           "New",
        "service_center":   data.get("service_center"),
        "next_followup_date": data.get("next_followup"),
        "whatsapp_optin":   data.get("whatsapp_optin"),
    })
    doc.insert()

    # Auto-create / update Customer Product record so Customer 360 is populated
    _upsert_customer_product(customer_link, data)

    frappe.db.commit()
    return doc.name


def _upsert_customer_product(customer, data):
    """Create or update a Lavanya Customer Product record on ticket creation."""
    serial = data.get("serial")
    model  = data.get("model")
    brand  = data.get("brand")
    if not (customer and brand and model):
        return
    # Check if this serial already tracked
    filters = {"customer": customer, "brand": brand, "product_model": model}
    if serial:
        filters["serial_number"] = serial
    existing = frappe.db.get_value("Lavanya Customer Product", filters, "name")
    if existing:
        frappe.db.set_value("Lavanya Customer Product", existing, {
            "warranty_status":  data.get("warranty_status"),
            "warranty_end_date": data.get("warranty_end"),
        }, update_modified=False)
    else:
        cp = frappe.new_doc("Lavanya Customer Product")
        cp.customer       = customer
        cp.brand          = brand
        cp.product_model  = model
        cp.serial_number  = serial
        cp.invoice_number = data.get("invoice")
        cp.purchase_date  = data.get("purchase_date")
        cp.warranty_status = data.get("warranty_status")
        cp.warranty_end_date = data.get("warranty_end")
        cp.insert(ignore_permissions=True)


def _create_customer(data):
    """Create a Lavanya Customer record if not found."""
    c = frappe.new_doc("Lavanya Customer")
    c.customer_name  = data.get("customer_name")
    c.customer_phone = data.get("phone")
    c.address        = data.get("address")
    c.customer_type  = data.get("customer_type") or "Regular"
    c.whatsapp_optin = data.get("whatsapp_optin", 1)
    c.insert(ignore_permissions=True)
    return c.name


@frappe.whitelist()
def save_followup(ticket, action_type, detail, customer_informed,
                  customer_informed_reason=None, next_followup_date=None,
                  channel=None, contacted_person=None, attachment=None):
    """Save a follow-up log entry and update ticket stage."""
    if not frappe.has_permission("Lavanya Ticket", "write", ticket):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    log = frappe.new_doc("Lavanya Followup Log")
    log.ticket              = ticket
    log.action_type         = action_type
    log.detail              = detail
    log.customer_informed   = customer_informed
    log.customer_informed_reason = customer_informed_reason
    log.next_followup_date  = next_followup_date
    log.channel             = channel or "Manual"
    log.contacted_person    = contacted_person
    log.staff               = frappe.session.user
    log.insert()

    # Update ticket fields
    update = {
        "customer_informed":  customer_informed == "Yes",
        "last_followup_date": today(),
    }
    if next_followup_date:
        update["next_followup_date"] = next_followup_date
    if action_type == "Technician Called":
        update["technician_called"] = 1
    if action_type == "Technician Visited":
        update["technician_visited"] = 1
    if action_type == "Customer Satisfied":
        update["customer_satisfied"] = 1
        update["customer_dissatisfied"] = 0
    if action_type == "Customer Not Satisfied":
        update["customer_dissatisfied"] = 1
        update["customer_satisfied"] = 0

    frappe.db.set_value("Lavanya Ticket", ticket, update)
    frappe.db.commit()
    return log.name


@frappe.whitelist()
def close_ticket(ticket, closure_type, remarks, customer_satisfaction,
                 non_response_attempt_count=0, proof=None):
    """Guarded ticket closure — validates all conditions."""
    if not frappe.has_permission("Lavanya Ticket", "write", ticket):
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    settings = frappe.get_single("Lavanya Settings")
    doc = frappe.get_doc("Lavanya Ticket", ticket)

    # Closure guard checks
    if settings.closure_guard_enabled and settings.customer_confirmation_required:
        if not doc.customer_satisfied and closure_type != "No Response After Attempts":
            frappe.throw(_(
                "Cannot close ticket. Customer has not confirmed the issue is resolved. "
                "Use 'No Response After Attempts' closure type if customer is unreachable."
            ))
        if closure_type == "No Response After Attempts" and cint(non_response_attempt_count) < 3:
            frappe.throw(_("Minimum 3 contact attempts required before no-response closure."))

    if doc.part_pending and not doc.part_received:
        frappe.throw(_("Cannot close — spare part is pending and not yet received."))

    if not doc.technician_visited and doc.service_path in ["Brand Warranty", "Local Paid Service"]:
        frappe.throw(_("Cannot close — technician visit not yet verified."))

    doc.status             = "Closed"
    doc.closure_type       = closure_type
    doc.closure_remarks    = remarks
    doc.customer_satisfaction = customer_satisfaction
    doc.closed_on          = now_datetime()
    doc.closed_by          = frappe.session.user
    doc.save()

    # Timeline entry
    save_followup(
        ticket=ticket,
        action_type="Ticket Closed",
        detail=f"Closed as {closure_type}. {remarks}",
        customer_informed="Yes",
        channel="Manual"
    )

    frappe.db.commit()
    return {"status": "closed"}


@frappe.whitelist()
def escalate_ticket(ticket, reason):
    """Escalate ticket one level (L1→L2→L3→L4)."""
    if not frappe.has_permission("Lavanya Ticket", "write", ticket):
        frappe.throw(_("Not permitted"))

    doc = frappe.get_doc("Lavanya Ticket", ticket)
    levels = {"L1": "L2", "L2": "L3", "L3": "L4"}
    new_level = levels.get(doc.escalation_level or "L1", "L4")

    doc.escalation_level = new_level
    doc.save()

    save_followup(
        ticket=ticket,
        action_type="Escalation",
        detail=f"Escalated to {new_level}. Reason: {reason}",
        customer_informed="No",
        channel="Manual"
    )
    frappe.db.commit()
    return {"escalation_level": new_level}


@frappe.whitelist()
def search_customer(phone):
    """Phone-based customer lookup for New Ticket wizard."""
    if not phone:
        return None
    customer = frappe.db.get_value(
        "Lavanya Customer",
        {"customer_phone": phone},
        ["name", "customer_name", "customer_phone", "address", "whatsapp_optin"],
        as_dict=True
    )
    if customer:
        customer["ticket_count"] = frappe.db.count("Lavanya Ticket", {"customer": customer.name})
        customer["open_tickets"] = frappe.db.count(
            "Lavanya Ticket",
            {"customer": customer.name, "status": ["not in", ["Closed", "Cancelled"]]}
        )
    return customer
