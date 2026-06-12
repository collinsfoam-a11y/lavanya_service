"""Phase 1N-5 repeat complaint suggestion for HD Ticket.

The system SUGGESTS possible previous complaints from customer/product
signals; staff must explicitly confirm before any link is recorded. Nothing
here auto-links.

Identity anchors: candidates are only pulled when the normalized mobile or
the serial number matches a previous ticket — brand/product/model alone never
suggest a candidate (they only add score), so two different customers owning
the same product model are never cross-matched.

Role policy:
  * find:    any user with HD Ticket read access (read-only, safe fields only)
  * confirm: Lavanya Manager, Lavanya Service Coordinator, Lavanya Helpdesk Agent
             (Front Desk is BLOCKED: intake-correction policy is not confirmed,
             so the spec's "if uncertain, block Front Desk" rule applies)
  * clear:   Lavanya Manager, Lavanya Service Coordinator
"""

import frappe
from frappe import _

from lavanya_service.utils.phone import normalized_mobile
from lavanya_service.workflow.quick_actions import _save_ticket

TICKET_DOCTYPE = "HD Ticket"

ROLE_MANAGER = "Lavanya Manager"
ROLE_COORDINATOR = "Lavanya Service Coordinator"
ROLE_AGENT = "Lavanya Helpdesk Agent"

CONFIRM_ROLES = {ROLE_MANAGER, ROLE_COORDINATOR, ROLE_AGENT}
CLEAR_ROLES = {ROLE_MANAGER, ROLE_COORDINATOR}
BYPASS_ROLES = {"System Manager"}

SIGNAL_FIELDS = [
	"phone_1",
	"brand",
	"product_item",
	"product_type",
	"model_no",
	"serial_no",
]

SAFE_CANDIDATE_FIELDS = [
	"name",
	"subject",
	"status",
	"customer_name",
	"brand",
	"product_type",
	"product_item",
	"model_no",
	"serial_no",
	"creation",
]

SCORE_SERIAL = 60
SCORE_MOBILE = 30
SCORE_BRAND = 15
SCORE_PRODUCT_ITEM = 20
SCORE_PRODUCT_TYPE = 10
SCORE_MODEL = 20

SCORE_THRESHOLD = 40
DEFAULT_LIMIT = 5
MAX_LIMIT = 20
CANDIDATE_POOL = 100


def _acting_user():
	return frappe.session.user


def _user_roles():
	if _acting_user() == "Administrator":
		return {"Administrator"}
	return set(frappe.get_roles(_acting_user()))


def _has_any_role(allowed):
	if _acting_user() == "Administrator":
		return True
	return bool(_user_roles().intersection(set(allowed) | BYPASS_ROLES))


def _require_roles(action_label, allowed):
	if not _has_any_role(allowed):
		frappe.throw(
			_("You are not permitted to run '{0}'. Allowed roles: {1}.").format(
				action_label, ", ".join(sorted(allowed))
			),
			frappe.PermissionError,
		)


def _require_read_access():
	if not frappe.has_permission(TICKET_DOCTYPE, "read", user=_acting_user()):
		frappe.throw(
			_("You are not permitted to read HD Ticket."), frappe.PermissionError
		)


def _clean(value):
	if value is None:
		return ""
	return str(value).strip()


def _norm(value):
	return _clean(value).lower()


def _coerce_limit(limit):
	try:
		limit = int(limit)
	except (TypeError, ValueError):
		limit = DEFAULT_LIMIT
	return max(1, min(limit, MAX_LIMIT))


def _signals_from_ticket(ticket_name):
	row = frappe.db.get_value(
		TICKET_DOCTYPE, ticket_name, SIGNAL_FIELDS, as_dict=True
	)
	if not row:
		frappe.throw(_("HD Ticket {0} not found.").format(ticket_name))
	return dict(row)


def _signals_from_data(data):
	data = data or {}
	return {fieldname: data.get(fieldname) for fieldname in SIGNAL_FIELDS}


def extract_signals(ticket_name=None, data=None):
	"""Resolve matching signals from a saved ticket or unsaved form data."""

	if ticket_name:
		raw = _signals_from_ticket(ticket_name)
	else:
		raw = _signals_from_data(data)

	return {
		"mobile": normalized_mobile(raw.get("phone_1")),
		"brand": _clean(raw.get("brand")),
		"product_item": _clean(raw.get("product_item")),
		"product_type": _clean(raw.get("product_type")),
		"model_no": _clean(raw.get("model_no")),
		"serial_no": _clean(raw.get("serial_no")),
	}


def score_candidate(signals, row):
	"""Return (score, match_reasons) for a candidate ticket row."""

	score = 0
	reasons = []

	serial = _norm(signals.get("serial_no"))
	if serial and _norm(row.get("serial_no")) == serial:
		score += SCORE_SERIAL
		reasons.append("same serial")

	mobile = signals.get("mobile") or ""
	if mobile and normalized_mobile(row.get("phone_1")) == mobile:
		score += SCORE_MOBILE
		reasons.append("same mobile")

	brand = signals.get("brand")
	if brand and _clean(row.get("brand")) == brand:
		score += SCORE_BRAND
		reasons.append("same brand")

	product_item = signals.get("product_item")
	if product_item and _clean(row.get("product_item")) == product_item:
		score += SCORE_PRODUCT_ITEM
		reasons.append("same product item")

	product_type = signals.get("product_type")
	if product_type and _clean(row.get("product_type")) == product_type:
		score += SCORE_PRODUCT_TYPE
		reasons.append("same product type")

	model = _norm(signals.get("model_no"))
	if model and _norm(row.get("model_no")) == model:
		score += SCORE_MODEL
		reasons.append("same model")

	return score, reasons


def find_repeat_candidates(ticket_name=None, data=None, limit=DEFAULT_LIMIT):
	"""Suggest previous tickets that look like the same complaint.

	Read-only. Candidates require an identity anchor match (normalized mobile
	or serial number); other signals only contribute to the score.
	"""

	_require_read_access()
	limit = _coerce_limit(limit)
	signals = extract_signals(ticket_name=ticket_name, data=data)

	or_filters = []
	if signals["mobile"]:
		or_filters.append(["phone_1", "=", signals["mobile"]])
	if signals["serial_no"]:
		or_filters.append(["serial_no", "=", signals["serial_no"]])

	if not or_filters:
		return {"ok": True, "candidates": []}

	filters = []
	if ticket_name:
		filters.append(["name", "!=", ticket_name])

	rows = frappe.get_all(
		TICKET_DOCTYPE,
		filters=filters,
		or_filters=or_filters,
		fields=SAFE_CANDIDATE_FIELDS + ["phone_1"],
		order_by="creation desc",
		limit_page_length=CANDIDATE_POOL,
	)

	candidates = []
	serial = _norm(signals.get("serial_no"))
	for row in rows:
		score, reasons = score_candidate(signals, row)

		if score < SCORE_THRESHOLD:
			continue

		serial_exact = bool(serial) and _norm(row.get("serial_no")) == serial
		if row.get("status") == "Cancelled" and not serial_exact:
			continue

		candidates.append(
			{
				"ticket": row.get("name"),
				"score": score,
				"match_reasons": reasons,
				"subject": row.get("subject"),
				"status": row.get("status"),
				"customer_name": row.get("customer_name"),
				"brand": row.get("brand"),
				"product_type": row.get("product_type"),
				"product_item": row.get("product_item"),
				"model_no": row.get("model_no"),
				"serial_no": row.get("serial_no"),
				"creation": _json_safe(row.get("creation")),
			}
		)

	# Stable two-pass sort: highest score first, latest ticket first on ties.
	candidates.sort(key=lambda c: str(c["creation"] or ""), reverse=True)
	candidates.sort(key=lambda c: c["score"], reverse=True)

	return {"ok": True, "candidates": candidates[:limit]}


def confirm_repeat_complaint(ticket_name, previous_ticket_link):
	"""Record a staff-confirmed repeat complaint link."""

	_require_roles("Confirm Repeat Complaint", CONFIRM_ROLES)

	ticket_name = _clean(ticket_name)
	previous_ticket_link = _clean(previous_ticket_link)

	if not ticket_name:
		frappe.throw(_("Ticket is required."))
	if not previous_ticket_link:
		frappe.throw(_("Previous Ticket is required."))
	if ticket_name == previous_ticket_link:
		frappe.throw(_("A ticket cannot be linked to itself as a repeat complaint."))
	if not frappe.db.exists(TICKET_DOCTYPE, ticket_name):
		frappe.throw(_("HD Ticket {0} not found.").format(ticket_name))
	if not frappe.db.exists(TICKET_DOCTYPE, previous_ticket_link):
		frappe.throw(_("Previous HD Ticket {0} not found.").format(previous_ticket_link))

	doc = frappe.get_doc(TICKET_DOCTYPE, ticket_name)
	doc.is_repeated_complaint = "Yes"
	doc.previous_ticket_link = previous_ticket_link

	_save_ticket(doc)

	return {
		"ok": True,
		"ticket": doc.name,
		"is_repeated_complaint": doc.is_repeated_complaint,
		"previous_ticket_link": doc.previous_ticket_link,
		"message": _("Repeat complaint linked to {0}").format(previous_ticket_link),
	}


def clear_repeat_complaint(ticket_name):
	"""Clear the repeat flag and the previous ticket link."""

	_require_roles("Clear Repeat Complaint", CLEAR_ROLES)

	ticket_name = _clean(ticket_name)
	if not ticket_name:
		frappe.throw(_("Ticket is required."))
	if not frappe.db.exists(TICKET_DOCTYPE, ticket_name):
		frappe.throw(_("HD Ticket {0} not found.").format(ticket_name))

	doc = frappe.get_doc(TICKET_DOCTYPE, ticket_name)
	doc.is_repeated_complaint = "No"
	doc.previous_ticket_link = ""

	_save_ticket(doc)

	return {
		"ok": True,
		"ticket": doc.name,
		"is_repeated_complaint": doc.is_repeated_complaint,
		"previous_ticket_link": doc.previous_ticket_link or "",
		"message": _("Repeat complaint link cleared"),
	}


def _json_safe(value):
	if value is None:
		return None
	if hasattr(value, "isoformat"):
		return value.isoformat()
	return value
