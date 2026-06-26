import frappe
from frappe import _
from frappe.utils import now_datetime

# ── Safety: live sending is always validated against settings ─────────────────
def _assert_live_allowed():
    """Call this ONLY in a real send function — NOT in generate_draft."""
    s = frappe.get_single("Lavanya Settings")
    if not s.live_whatsapp_enabled:
        frappe.throw(_(
            "Live WhatsApp sending is disabled in Lavanya Settings. "
            "Enable it in Settings → Safety Locks (requires Lavanya Owner role)."
        ))
    if s.whatsapp_bot_mode not in ("staff_approved", "controlled_auto"):
        frappe.throw(_("Bot mode must be 'staff_approved' or 'controlled_auto' to send live messages."))

# ── Templates ─────────────────────────────────────────────────────────────────
TEMPLATES = {
    "complaint_registered": "Dear {name}, your complaint has been registered as #{ticket_id}. "
        "We will follow up regularly and keep you informed. — Lavanya Service",

    "brand_ticket_shared":  "Dear {name}, your complaint #{ticket_id} has been registered with "
        "{brand} service center as {brand_ticket}. Their team will contact you within {sla_days} days.",

    "technician_call_check": "Dear {name}, regarding complaint #{ticket_id} — "
        "has the {brand} technician called you? Please reply YES or NO.",

    "technician_visit_check": "Dear {name}, has the {brand} technician visited your home and "
        "completed the repair for complaint #{ticket_id}? Please reply YES or NO.",

    "part_pending_update":  "Dear {name}, we are waiting for a spare part for complaint #{ticket_id}. "
        "Expected delivery: {expected_date}. We apologise for the delay and will update you.",

    "appointment_confirm":  "Dear {name}, your service appointment for complaint #{ticket_id} is "
        "confirmed for {date} between {time_slot}. Our technician will visit your home.",

    "product_ready":        "Dear {name}, your product is ready for collection at Lavanya showroom "
        "for complaint #{ticket_id}. Please bring this message and a valid ID. Open: 9AM–8PM.",

    "satisfaction_check":   "Dear {name}, has your complaint #{ticket_id} been resolved to your "
        "satisfaction? Please reply SATISFIED or NOT SATISFIED.",

    "no_response_reminder": "Dear {name}, we tried reaching you for complaint #{ticket_id}. "
        "Please call us at {staff_phone} or reply to this message at your earliest convenience.",

    "closure_confirmation": "Dear {name}, complaint #{ticket_id} has been closed as resolved. "
        "Thank you for choosing Lavanya. If you face issues again, please contact us.",
}


@frappe.whitelist()
def get_inbox():
    """Return WhatsApp messages bucketed by intent."""
    messages = frappe.get_all(
        "Lavanya Whatsapp Message",
        fields=["*"],
        order_by="creation desc",
        limit=200
    )

    buckets = {
        "new_messages":       [],
        "unmatched":          [],
        "possible_updates":   [],
        "complaint_drafts":   [],
        "satisfaction_replies":[],
        "technician_replies": [],
        "escalation_risk":    [],
        "spam":               [],
    }

    for m in messages:
        bucket = _classify_message(m)
        buckets[bucket].append(m)

    return {"messages": messages, "buckets": buckets}


def _classify_message(m):
    intent = m.get("bot_intent") or ""
    if not m.get("matched_ticket") and not m.get("matched_customer"):
        return "unmatched"
    if intent in ("issue_resolved_yes", "issue_resolved_no"):
        return "satisfaction_replies"
    if intent in ("technician_called_yes","technician_called_no",
                  "technician_visited_yes","technician_visited_no"):
        return "technician_replies"
    if intent == "new_complaint":
        return "complaint_drafts"
    if intent == "escalation_risk":
        return "escalation_risk"
    if m.get("reviewed"):
        return "possible_updates"
    if intent in ("", "unknown"):
        return "spam"
    return "new_messages"


@frappe.whitelist()
def generate_draft(ticket_id, template_key):
    """
    Generate a WhatsApp message draft — always safe, never sends.
    _assert_dry_run_only removed: draft generation is always allowed regardless
    of live mode setting. Only actual sending requires the live mode check.
    """

    if template_key not in TEMPLATES:
        frappe.throw(_(f"Unknown template: {template_key}"))

    ticket = frappe.get_doc("Lavanya Ticket", ticket_id)
    template = TEMPLATES[template_key]

    draft = template.format(
        name        = ticket.customer_name or "Customer",
        ticket_id   = ticket_id,
        brand       = ticket.brand or "",
        brand_ticket= ticket.brand_ticket_number or "pending",
        sla_days    = 2,
        expected_date = str(ticket.part_expected_date or "TBD"),
        date        = str(ticket.appointment_date or "TBD"),
        time_slot   = ticket.appointment_time_slot or "9AM–1PM",
        staff_phone = frappe.db.get_value("User", ticket.service_staff, "mobile_no") or "",
    )

    # Log draft generation in ticket timeline
    frappe.get_doc({
        "doctype":  "Lavanya Followup Log",
        "ticket":   ticket_id,
        "action_type": "WhatsApp Draft Generated",
        "detail":   f"Template: {template_key}\nDraft: {draft}",
        "channel":  "WhatsApp Draft",
        "staff":    frappe.session.user,
        "customer_informed": "No",
    }).insert(ignore_permissions=True)
    frappe.db.commit()

    return {"draft": draft, "template": template_key, "mode": "dry_run"}


@frappe.whitelist()
def mark_reviewed(msg_id):
    """Mark a WhatsApp message as staff-reviewed."""
    frappe.db.set_value("Lavanya Whatsapp Message", msg_id, {
        "reviewed": 1,
        "reviewed_by": frappe.session.user,
        "reviewed_at": now_datetime(),
    })
    frappe.db.commit()
    return {"reviewed": True}


@frappe.whitelist()
def log_customer_reply(phone, message_text, direction="in"):
    """
    Log an incoming customer WhatsApp reply.
    Called by WhatsApp webhook (when live mode is eventually enabled).
    Never auto-posts ERP entries or closes tickets.
    """
    # Match customer
    customer = frappe.db.get_value("Lavanya Customer", {"customer_phone": phone}, "name")
    matched_ticket = None
    if customer:
        # Find most recent open ticket for customer
        tickets = frappe.get_all(
            "Lavanya Ticket",
            filters={"customer": customer, "status": ["not in", ["Closed","Cancelled"]]},
            fields=["name"],
            order_by="creation desc",
            limit=1
        )
        if tickets:
            matched_ticket = tickets[0].name

    # Classify intent (basic keyword match — replace with NLP/LLM in production)
    intent = _classify_intent(message_text)

    msg = frappe.get_doc({
        "doctype":          "Lavanya Whatsapp Message",
        "phone":            phone,
        "message_text":     message_text,
        "direction":        direction,
        "matched_customer": customer,
        "matched_ticket":   matched_ticket,
        "bot_intent":       intent,
        "reviewed":         0,
        "received_at":      now_datetime(),
    })
    msg.insert(ignore_permissions=True)
    frappe.db.commit()

    # If intent is clear, flag ticket
    if matched_ticket and intent in ("technician_visited_no", "escalation_risk", "issue_resolved_no"):
        frappe.db.set_value("Lavanya Ticket", matched_ticket, "whatsapp_pending", 1)

    return {"msg_id": msg.name, "intent": intent, "matched_ticket": matched_ticket}


def _classify_intent(text):
    """Keyword-based intent classification. Replace with LLM in production."""
    t = (text or "").lower()
    if any(w in t for w in ["not working","not fixed","still broken","problem","issue","complaint"]):
        return "new_complaint"
    if any(w in t for w in ["status","update","what happened","any update"]):
        return "ticket_status"
    if any(w in t for w in ["technician called","called me","got a call"]):
        return "technician_called_yes"
    if any(w in t for w in ["no one called","didn't call","no call"]):
        return "technician_called_no"
    if any(w in t for w in ["came","visited","repaired","fixed"]):
        return "technician_visited_yes"
    if any(w in t for w in ["no one came","didn't come","no visit","not visited"]):
        return "technician_visited_no"
    if any(w in t for w in ["satisfied","happy","working fine","resolved","thank"]):
        return "issue_resolved_yes"
    if any(w in t for w in ["not satisfied","still not","unhappy","not resolved"]):
        return "issue_resolved_no"
    if any(w in t for w in ["consumer forum","complaint authority","case","legal"]):
        return "escalation_risk"
    if any(w in t for w in ["exchange","upgrade","new","buy"]):
        return "sales_enquiry"
    return "unknown"
