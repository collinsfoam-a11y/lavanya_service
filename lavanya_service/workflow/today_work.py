import frappe
from frappe.utils import getdate, today


TICKET_DOCTYPE = "HD Ticket"

FINAL_STATUSES = {
	"Closed",
	"Resolved",
	"Cancelled",
}

# Unified status model: every HD Ticket Status maps to a status_category
# (Open / Paused / Resolved), maintained by Helpdesk. Only the "Resolved"
# category is terminal (Closed/Resolved/Cancelled all map to it); Open + Paused
# are active. Driving active/terminal off the category — instead of a hard-coded
# status-string list — keeps Today's Work correct for ANY status, including
# Helpdesk-native ones (Open/Replied) and any future status, without code edits.
TERMINAL_STATUS_CATEGORY = "Resolved"

REGISTRATION_RECOMMENDED_TYPES = {
	"Customer Complaint - Site",
	"Customer Product at Store",
	"Installation / Demo",
	"Replacement / DOA",
}

REGISTRATION_EXEMPT_TYPES = {
	"Stock Complaint",
	"Out of Warranty Local Service",
}

SAFE_TICKET_FIELDS = [
	"name",
	"subject",
	"status",
	"ticket_type",
	"priority",
	"customer_name",
	"phone_1",
	"brand",
	"product_type",
	"product_item",
	"pending_reason",
	"next_follow_up_date",
	"service_product_receipt",
	"modified",
]

CLASSIFICATION_FIELDS = [
	"status_category",
	"warranty_status",
	"manufacturer_registered",
	"brand_ticket_number",
	"brand_registration_override_reason",
	"customer_confirmation_received",
	"closure_type",
	"creation",
]

GROUPS = [
	{
		"key": "overdue_follow_up",
		"label": "Overdue Follow-up",
		"priority": 1,
	},
	{
		"key": "due_today",
		"label": "Due Today",
		"priority": 2,
	},
	{
		"key": "registration_recommended",
		"label": "Registration Recommended",
		"priority": 3,
	},
	{
		"key": "registration_pending",
		"label": "Registration Pending",
		"priority": 4,
	},
	{
		"key": "waiting_on_customer",
		"label": "Waiting on Customer",
		"priority": 5,
	},
	{
		"key": "waiting_on_part",
		"label": "Waiting on Part / Approval",
		"priority": 6,
	},
	{
		"key": "ready_for_pickup",
		"label": "Ready for Pickup",
		"priority": 7,
	},
	{
		"key": "product_receipt_missing",
		"label": "Product Receipt Missing",
		"priority": 8,
	},
	{
		"key": "closure_pending",
		"label": "Closure Pending",
		"priority": 9,
	},
	{
		"key": "new_complaints",
		"label": "New Complaints",
		"priority": 10,
	},
]

HELPDESK_AGENT_GROUPS = {
	"overdue_follow_up",
	"due_today",
	"registration_pending",
	"waiting_on_customer",
	"waiting_on_part",
}

FRONT_DESK_GROUPS = {
	"ready_for_pickup",
	"product_receipt_missing",
	"new_complaints",
}


def get_today_work_data(user=None, owner=None, include_counts=True, limit=50):
	user = user or frappe.session.user
	limit = _coerce_limit(limit)

	if not frappe.has_permission(TICKET_DOCTYPE, "read", user=user):
		frappe.throw("Not permitted to read HD Ticket.", frappe.PermissionError)

	allowed_group_keys = _allowed_group_keys_for_user(user)
	rows = _ticket_rows(owner=owner, limit=limit)
	today_date = getdate(today())

	group_map = {
		group["key"]: {
			"key": group["key"],
			"label": group["label"],
			"priority": group["priority"],
			"tickets": [],
		}
		for group in GROUPS
		if group["key"] in allowed_group_keys
	}

	for row in rows:
		for key in classify_ticket(row, today_date):
			if key not in group_map:
				continue

			if len(group_map[key]["tickets"]) >= limit:
				continue

			group_map[key]["tickets"].append(_safe_ticket_payload(row))

	groups = [group_map[group["key"]] for group in GROUPS if group["key"] in group_map]
	for group in groups:
		if include_counts:
			group["count"] = len(group["tickets"])

	return {
		"date": str(today_date),
		"groups": groups,
		"summary": _summary(groups),
	}


def classify_ticket(row, today_date=None):
	today_date = getdate(today_date or today())
	keys = []

	if is_active_ticket(row):
		follow_up_date = _date_value(row, "next_follow_up_date")
		if follow_up_date and follow_up_date < today_date:
			keys.append("overdue_follow_up")
		if follow_up_date and follow_up_date == today_date:
			keys.append("due_today")

		if is_registration_recommended(row):
			keys.append("registration_recommended")

		status = _value(row, "status")
		if status == "Registration Pending":
			keys.append("registration_pending")
		if status == "Waiting on Customer":
			keys.append("waiting_on_customer")
		if status == "Waiting on Part / Approval":
			keys.append("waiting_on_part")
		if status == "Ready for Pickup":
			keys.append("ready_for_pickup")
		if (
			_value(row, "ticket_type") == "Customer Product at Store"
			and not _has_value(row, "service_product_receipt")
		):
			keys.append("product_receipt_missing")
		if status == "New":
			keys.append("new_complaints")

		# Safety net: an active ticket that matched no bucket above is otherwise
		# invisible on Today's Work. This happens for Helpdesk's native
		# "Open"/"Replied" statuses (still present alongside the Lavanya status
		# set), which the standard new-ticket form assigns on creation — so a
		# freshly created ticket would vanish from Today's Work until its status
		# was changed. Surface any such active ticket as a new complaint to triage.
		if not keys:
			keys.append("new_complaints")

	if _is_closure_pending(row):
		keys.append("closure_pending")

	return keys


def is_active_ticket(row):
	# Prefer the unified status_category (terminal == "Resolved"); fall back to the
	# status-string list only when the category isn't on the row (e.g. a hand-built
	# dict in a unit test).
	category = _value(row, "status_category")
	if category:
		return category != TERMINAL_STATUS_CATEGORY
	return _value(row, "status") not in FINAL_STATUSES


def is_registration_recommended(row):
	if not is_active_ticket(row):
		return False

	if _value(row, "warranty_status") != "In Warranty":
		return False

	if _value(row, "manufacturer_registered") == "Yes":
		return False

	if _has_value(row, "brand_ticket_number"):
		return False

	if _has_value(row, "brand_registration_override_reason"):
		return False

	ticket_type = _value(row, "ticket_type")
	if ticket_type in REGISTRATION_RECOMMENDED_TYPES:
		return True

	if ticket_type in REGISTRATION_EXEMPT_TYPES:
		return False

	if ticket_type == "Free Service":
		return _matching_free_service_rule_is_brand_backed(row)

	return False


def _ticket_rows(owner=None, limit=50):
	fields = _available_ticket_fields()
	filters = [["status", "not in", ["Closed", "Cancelled"]]]
	if owner:
		filters.append(["owner", "=", owner])

	return frappe.get_list(
		TICKET_DOCTYPE,
		filters=filters,
		fields=fields,
		order_by="modified asc",
		limit_page_length=max(limit * len(GROUPS), 200),
	)


def _available_ticket_fields():
	meta = frappe.get_meta(TICKET_DOCTYPE)
	fields = []
	for fieldname in SAFE_TICKET_FIELDS + CLASSIFICATION_FIELDS:
		if fieldname in {"name", "modified", "creation"} or meta.has_field(fieldname):
			if fieldname not in fields:
				fields.append(fieldname)
	return fields


def _matching_free_service_rule_is_brand_backed(row):
	if not frappe.db.exists("DocType", "Free Service Rule"):
		return False

	meta = frappe.get_meta("Free Service Rule")
	if not meta.has_field("brand_backed"):
		return False

	product_type = _value(row, "product_type")
	if not product_type:
		return False

	filters = [
		["active", "=", 1],
		["brand_backed", "=", 1],
		["product_type", "=", product_type],
	]

	brand = _value(row, "brand")
	if brand and meta.has_field("brand"):
		filters.append(["brand", "in", [brand, ""]])

	return bool(frappe.get_all("Free Service Rule", filters=filters, pluck="name", limit=1))


def _allowed_group_keys_for_user(user):
	roles = set(frappe.get_roles(user))
	all_keys = {group["key"] for group in GROUPS}

	if user == "Administrator" or roles.intersection(
		{"System Manager", "Lavanya Manager", "Lavanya Service Coordinator"}
	):
		return all_keys

	if "Lavanya Viewer" in roles:
		return all_keys

	allowed = set()
	if "Lavanya Helpdesk Agent" in roles:
		allowed.update(HELPDESK_AGENT_GROUPS)
	if "Lavanya Front Desk" in roles:
		allowed.update(FRONT_DESK_GROUPS)

	return allowed or all_keys


def _is_closure_pending(row):
	if _value(row, "status") != "Resolved":
		return False

	return _value(row, "customer_confirmation_received") != "Yes" or not _has_value(row, "closure_type")


def _safe_ticket_payload(row):
	return {fieldname: _json_safe(_value(row, fieldname)) for fieldname in SAFE_TICKET_FIELDS}


def _summary(groups):
	counts = {group["key"]: len(group.get("tickets", [])) for group in groups}
	return {
		"total": sum(counts.values()),
		"overdue": counts.get("overdue_follow_up", 0),
		"due_today": counts.get("due_today", 0),
	}


def _coerce_limit(limit):
	try:
		limit = int(limit)
	except (TypeError, ValueError):
		limit = 50
	return max(1, min(limit, 200))


def _value(row, fieldname):
	if hasattr(row, "get"):
		return row.get(fieldname)
	return getattr(row, fieldname, None)


def _has_value(row, fieldname):
	value = _value(row, fieldname)
	return value is not None and str(value).strip() != ""


def _date_value(row, fieldname):
	value = _value(row, fieldname)
	if not value:
		return None
	return getdate(value)


def _json_safe(value):
	if value is None:
		return None

	if hasattr(value, "isoformat"):
		return value.isoformat()

	return value
