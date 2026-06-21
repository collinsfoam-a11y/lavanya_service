"""QR Customer Complaint Intake — public-safe API.

Public-facing whitelisted endpoint that allows guest (unauthenticated)
users to submit a complaint via a QR-code scanned form.

Security:
  - Validates and sanitises all input server-side.
  - Brand and Product Type are validated against the same controlled values
    the desk uses (brand = Brand Service Master link, product_type = Select
    options); unknown values are rejected with a friendly message instead of
    a server traceback (PHASE 1Q-FIX-1 / audit A1).
  - Rate-limits by normalised mobile (3 / hour) and by client IP (10 / hour),
    using a proxy-aware client IP (audit A2).
  - Honeypot field silently drops bot submissions without creating a ticket.
  - Returns only a safe acknowledgement — never internal ticket details.
  - Re-uses existing phone normalisation and customer-profile sync logic.
  - Strips HTML/script tags from all text fields.
  - Does NOT call frappe.db.commit(); the request lifecycle commits on a
    clean response and rolls back on error (audit A3).
"""

import re

import frappe
from frappe import _

from lavanya_service.setup.hd_ticket_fields import PRODUCT_TYPE_OPTIONS
from lavanya_service.utils.phone import normalize_phone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SAFE_TICKET_TYPES = [
    "Customer Complaint - Site",
    "Customer Product at Store",
    "Installation / Demo",
    "Replacement / DOA",
]

DEFAULT_TICKET_TYPE = "Customer Complaint - Site"

BRAND_DOCTYPE = "Brand Service Master"

# Valid product_type Select options (single source of truth: hd_ticket_fields).
VALID_PRODUCT_TYPES = [opt for opt in PRODUCT_TYPE_OPTIONS.split("\n") if opt]

# Single, controlled raised_by placeholder. Using one constant (instead of a
# per-mobile synthetic address) avoids creating a fresh junk contact/customer
# for every public submission (audit A4).
QR_RAISED_BY = "qr-intake@lavanya.local"

# Honeypot fields: real users never see/fill these. Any value => bot.
HONEYPOT_FIELDS = ("company_name", "website")

MAX_TEXT_LENGTH = 2000
MAX_SHORT_TEXT = 200
MAX_MOBILE_RATE = 3   # per hour per normalised mobile
MAX_IP_RATE = 10       # per hour per client IP

RATE_LIMIT_WINDOW = 3600  # seconds (1 hour)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_html(value):
    """Remove HTML/script tags, returning plain text only."""
    if not value:
        return ""
    cleaned = re.sub(r"<[^>]+>", "", str(value))
    # Collapse any leftover angle brackets that survived a malformed tag.
    cleaned = cleaned.replace("<", "").replace(">", "")
    return cleaned.strip()


def _clean_text(value, max_length=MAX_TEXT_LENGTH):
    """Sanitise a text value: strip HTML, cap length, strip whitespace."""
    if value is None:
        return ""
    text = _strip_html(str(value).strip())
    if len(text) > max_length:
        text = text[:max_length]
    return text


def _clean_short(value):
    return _clean_text(value, max_length=MAX_SHORT_TEXT)


def _require(value, label):
    """Raise ValidationError if a required field is blank."""
    if not value:
        frappe.throw(_("{0} is required.").format(label), frappe.ValidationError)


def _client_ip():
    """Best-effort client IP that is aware of a trusting reverse proxy.

    Frappe computes ``frappe.local.request_ip`` from the configured trusted
    proxy chain, so prefer it. Fall back to the leftmost X-Forwarded-For hop
    and finally to the raw remote address. Returns "unknown" when no request
    context is available (e.g. unit tests calling the function directly).
    """
    request_ip = getattr(frappe.local, "request_ip", None)
    if request_ip:
        return request_ip

    request = getattr(frappe.local, "request", None)
    if not request:
        return "unknown"

    forwarded = request.headers.get("X-Forwarded-For") if request.headers else None
    if forwarded:
        # leftmost entry is the originating client
        return forwarded.split(",")[0].strip()

    return request.remote_addr or "unknown"


def _rate_limit_key(prefix, identifier):
    return f"lavanya_qr_rate:{prefix}:{identifier}"


def _check_rate_limit(prefix, identifier, max_count):
    """Fixed-window rate-limiter using an atomic Redis counter.

    Uses INCR + EXPIRE so concurrent requests cannot race past the cap (audit
    A2). The counter auto-expires after the window. Raises ValidationError
    (before any ticket is created) when the cap is exceeded. If the cache
    backend is unavailable the limiter fails open rather than blocking intake.
    """
    cache = frappe.cache()
    key = _rate_limit_key(prefix, identifier)

    try:
        count = cache.incrby(key, 1)
        if count == 1:
            cache.expire(key, RATE_LIMIT_WINDOW)
    except Exception:
        # Never block a genuine complaint because the rate-limit store is down.
        return

    if count > max_count:
        frappe.throw(
            _("Too many complaints submitted. Please try again later."),
            frappe.ValidationError,
        )


def _reset_rate_limit(prefix, identifier):
    """Clear a rate-limit bucket (used by tests).

    Deletes the raw key the atomic counter uses; falls back to the prefixed
    ``delete_value`` for safety.
    """
    key = _rate_limit_key(prefix, identifier)
    cache = frappe.cache()
    try:
        cache.delete(key)
    except Exception:
        cache.delete_value(key)


def _is_honeypot_triggered(kwargs):
    return any(str(kwargs.get(field) or "").strip() for field in HONEYPOT_FIELDS)


# ---------------------------------------------------------------------------
# Public metadata endpoint (A1) — safe options for the public form
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def get_qr_intake_options():
    """Return only the safe option lists the public QR form needs.

    Exposes nothing beyond brand names, product-type options and the allowed
    ticket types — no internal fields, ticket data, reports or user data.
    """
    brands = frappe.get_all(
        BRAND_DOCTYPE,
        filters={"disabled": 0} if _brand_has_disabled_field() else None,
        pluck="name",
        order_by="name asc",
    )
    return {
        "brands": brands,
        "product_types": list(VALID_PRODUCT_TYPES),
        "ticket_types": list(SAFE_TICKET_TYPES),
    }


def _brand_has_disabled_field():
    try:
        return bool(frappe.get_meta(BRAND_DOCTYPE).get_field("disabled"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Public submission endpoint
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def submit_qr_complaint(**kwargs):
    """Accept a complaint from the public QR intake form.

    Required: customer_name, mobile, complaint_details, product_type, brand
    Returns a safe acknowledgement dict.
    """
    # ---- Honeypot: silently accept (no ticket) so bots get no signal ----
    if _is_honeypot_triggered(kwargs):
        return {
            "ok": True,
            "message": "Complaint registered successfully. Lavanya team will contact you.",
            "reference": "LV-QR-0000",
        }

    # ---- Sanitise all inputs ----
    customer_name    = _clean_short(kwargs.get("customer_name"))
    mobile_raw       = _clean_short(kwargs.get("mobile"))
    complaint_details = _clean_text(kwargs.get("complaint_details"))
    product_type     = _clean_short(kwargs.get("product_type"))
    brand            = _clean_short(kwargs.get("brand"))
    ticket_type      = _clean_short(kwargs.get("ticket_type"))
    model_no         = _clean_short(kwargs.get("model_no"))
    serial_no        = _clean_short(kwargs.get("serial_no"))
    address          = _clean_short(kwargs.get("address"))
    pincode          = _clean_short(kwargs.get("pincode"))
    preferred_callback_time = _clean_short(kwargs.get("preferred_callback_time"))

    # ---- Required field validation ----
    _require(customer_name, "Customer Name")
    _require(mobile_raw, "Mobile Number")
    _require(complaint_details, "Complaint Details")
    _require(product_type, "Product Type")
    _require(brand, "Brand")

    # ---- Mobile validation ----
    phone_result = normalize_phone(mobile_raw)
    if not phone_result["is_valid_mobile"]:
        frappe.throw(
            _("Please provide a valid 10-digit Indian mobile number."),
            frappe.ValidationError,
        )

    normalized_mobile = phone_result["normalized"]

    # ---- Brand / Product Type validation (audit A1) ----
    # brand is a Link to Brand Service Master and product_type is a Select;
    # reject unknown values cleanly instead of letting doc.insert() raise a
    # raw LinkValidationError / select error to the public.
    if product_type not in VALID_PRODUCT_TYPES:
        frappe.throw(
            _("Please select a valid product type from the list."),
            frappe.ValidationError,
        )

    if not frappe.db.exists(BRAND_DOCTYPE, brand):
        frappe.throw(
            _("Please select a valid brand from the list."),
            frappe.ValidationError,
        )

    # ---- Rate limiting (audit A2) — runs before any write ----
    _check_rate_limit("mobile", normalized_mobile, MAX_MOBILE_RATE)
    client_ip = _client_ip()
    if client_ip and client_ip != "unknown":
        _check_rate_limit("ip", client_ip, MAX_IP_RATE)

    # ---- Ticket type validation ----
    if not ticket_type or ticket_type not in SAFE_TICKET_TYPES:
        ticket_type = DEFAULT_TICKET_TYPE

    # ---- Create HD Ticket ----
    subject = f"QR complaint - {customer_name} / {product_type} {brand}"
    if len(subject) > 140:
        subject = subject[:137] + "..."

    doc = frappe.new_doc("HD Ticket")
    doc.subject = subject
    doc.raised_by = QR_RAISED_BY
    doc.ticket_type = ticket_type
    doc.priority = "Medium"
    doc.complaint_source = "Customer QR Form"
    doc.customer_name = customer_name
    doc.phone_1 = normalized_mobile
    doc.description = complaint_details
    doc.product_type = product_type
    doc.brand = brand

    # optional fields
    if model_no:
        doc.model_no = model_no
    if serial_no:
        doc.serial_no = serial_no
    if address:
        doc.address = address
    if pincode:
        doc.pincode = pincode
    if preferred_callback_time and doc.meta.has_field("preferred_callback_time"):
        doc.preferred_callback_time = preferred_callback_time

    # sensible defaults
    doc.purchased_from_lavanya = "Unknown"
    doc.warranty_status = "Unknown"

    # Guest intake: create under a privileged identity. ignore_permissions on the
    # ticket alone is insufficient because Helpdesk turns the description into a
    # Communication whose on_communication_update calls HD Ticket.save() WITHOUT
    # ignore_permissions, which a Guest cannot pass. There is no staff actor for a
    # public submission; provenance is recorded via complaint_source="Customer QR
    # Form" and raised_by=QR_RAISED_BY. Validation + rate limiting above already
    # ran as the original (guest) request.
    intake_user = frappe.session.user
    frappe.set_user("Administrator")
    try:
        doc.flags.ignore_permissions = True
        doc.insert()
    finally:
        frappe.set_user(intake_user)

    # Build safe reference (not internal ticket name).
    safe_ref = f"LV-QR-{normalized_mobile[-4:]}"

    # No explicit frappe.db.commit() here (audit A3): the request lifecycle
    # commits on a clean response and rolls back automatically on error.

    return {
        "ok": True,
        "message": "Complaint registered successfully. Lavanya team will contact you.",
        "reference": safe_ref,
    }
