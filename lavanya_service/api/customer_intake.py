import frappe

from lavanya_service.utils.phone import normalize_phone, normalized_mobile


PROFILE_DOCTYPE = "Lavanya Customer Profile"
TICKET_DOCTYPE = "HD Ticket"


def normalize_mobile(value):
	"""Backward-compatible wrapper for older callers."""

	return normalized_mobile(value)


def _get_value(doc, fieldname):
	if hasattr(doc, "get"):
		return doc.get(fieldname)
	return getattr(doc, fieldname, None)


def _clean_text(value):
	if value is None:
		return ""
	return str(value).strip()


def _has_field(doctype, fieldname):
	return bool(frappe.get_meta(doctype).get_field(fieldname))


def _set_if_has_field(doc, fieldname, value):
	if doc.meta.has_field(fieldname):
		doc.set(fieldname, value)
		return True
	return False


def _profile_payload(profile, source=PROFILE_DOCTYPE):
	return {
		"found": True,
		"source": source,
		"name": profile.name,
		"customer_name": profile.customer_name,
		"primary_mobile": profile.primary_mobile,
		"alternate_mobile": profile.alternate_mobile,
		"address": profile.address,
		"pincode": profile.pincode,
		"last_ticket": profile.last_ticket,
		"ticket_count": profile.ticket_count,
		"last_product_type": profile.last_product_type,
		"last_brand": profile.last_brand,
	}


def _ticket_payload(ticket):
	phone_1 = ticket.get("phone_1_normalized") or normalize_mobile(ticket.phone_1)
	phone_2 = ticket.get("phone_2_normalized") or normalize_mobile(ticket.phone_2)
	return {
		"found": True,
		"source": TICKET_DOCTYPE,
		"name": ticket.name,
		"customer_name": ticket.customer_name,
		"primary_mobile": phone_1 or ticket.phone_1,
		"alternate_mobile": phone_2 or ticket.phone_2,
		"address": ticket.address,
		"pincode": ticket.pincode,
		"last_ticket": ticket.name,
		"ticket_count": _ticket_count_for_numbers([phone_1, phone_2]),
		"last_product_type": ticket.product_type,
		"last_brand": ticket.brand,
	}


def _profile_rows_by_mobile(mobile, include_disabled=False):
	if not frappe.db.exists("DocType", PROFILE_DOCTYPE):
		return []

	base_filters = {} if include_disabled else {"disabled": 0}
	matches = {}

	for fieldname in ["primary_mobile", "alternate_mobile"]:
		filters = dict(base_filters)
		filters[fieldname] = mobile
		for row in frappe.get_all(PROFILE_DOCTYPE, filters=filters, fields=["name"]):
			matches[row.name] = fieldname

	return [{"name": name, "matched_field": fieldname} for name, fieldname in matches.items()]


def _find_profile_by_mobile(mobile, include_disabled=False):
	rows = _profile_rows_by_mobile(mobile, include_disabled=include_disabled)
	if not rows:
		return None

	if len(rows) > 1:
		frappe.throw(
			"Ambiguous customer profile conflict for mobile "
			+ mobile
			+ ": "
			+ ", ".join(sorted(row["name"] for row in rows))
			+ ".",
			frappe.ValidationError,
		)

	return frappe.get_doc(PROFILE_DOCTYPE, rows[0]["name"])


def _ticket_search_fields():
	fields = []
	meta = frappe.get_meta(TICKET_DOCTYPE)
	for fieldname in ["phone_1_normalized", "phone_2_normalized", "phone_1", "phone_2"]:
		if meta.has_field(fieldname):
			fields.append(fieldname)
	return fields


def _latest_ticket_for_mobile(mobile):
	rows = []
	for fieldname in _ticket_search_fields():
		rows.extend(
			frappe.get_all(
				TICKET_DOCTYPE,
				filters={fieldname: mobile},
				fields=[
					"name",
					"customer_name",
					"phone_1",
					"phone_2",
					"phone_1_normalized",
					"phone_2_normalized",
					"address",
					"pincode",
					"product_type",
					"brand",
					"modified",
				],
				order_by="modified desc",
				limit=5,
			)
		)

	if not rows:
		return None

	by_name = {row.name: row for row in rows}
	return sorted(by_name.values(), key=lambda row: row.modified, reverse=True)[0]


def _ticket_count_for_numbers(numbers):
	clean_numbers = {normalize_mobile(number) for number in numbers if normalize_mobile(number)}
	if not clean_numbers:
		return 0

	ticket_names = set()
	for fieldname in _ticket_search_fields():
		for number in clean_numbers:
			for row in frappe.get_all(TICKET_DOCTYPE, filters={fieldname: number}, fields=["name"]):
				ticket_names.add(row.name)

	return len(ticket_names)


@frappe.whitelist()
def lookup_customer_by_mobile(mobile):
	phone = normalize_phone(mobile)

	if not phone["is_valid_mobile"]:
		return {
			"found": False,
			"invalid_mobile": bool(_clean_text(mobile)),
			"mobile": _clean_text(mobile),
			"reason": phone["reason"],
		}

	normalized = phone["normalized"]
	profile = _find_profile_by_mobile(normalized)
	if profile:
		return _profile_payload(profile)

	ticket = _latest_ticket_for_mobile(normalized)
	if ticket:
		return _ticket_payload(ticket)

	return {
		"found": False,
		"invalid_mobile": False,
		"mobile": normalized,
		"reason": "valid",
	}


def _set_from_ticket_if_safe(profile, profile_field, ticket_value):
	clean_value = _clean_text(ticket_value)
	if not clean_value:
		return False

	current_value = _clean_text(profile.get(profile_field))
	if current_value:
		return False

	profile.set(profile_field, clean_value)
	return True


def _set_last_value(profile, profile_field, ticket_value):
	clean_value = _clean_text(ticket_value)
	if not clean_value:
		return False

	if _clean_text(profile.get(profile_field)) == clean_value:
		return False

	profile.set(profile_field, clean_value)
	return True


def normalize_customer_profile_phone_numbers(doc, method=None):
	primary = normalize_phone(_get_value(doc, "primary_mobile"))
	if doc.meta.has_field("primary_mobile_raw"):
		doc.primary_mobile_raw = primary["raw"]

	if not primary["is_valid_mobile"]:
		frappe.throw(
			"Primary Mobile must be a valid 10 digit Indian mobile number.",
			frappe.ValidationError,
		)

	doc.primary_mobile = primary["normalized"]

	alternate = normalize_phone(_get_value(doc, "alternate_mobile"))
	if doc.meta.has_field("alternate_mobile_raw"):
		doc.alternate_mobile_raw = alternate["raw"]

	if alternate["is_valid_mobile"]:
		doc.alternate_mobile = alternate["normalized"]
	else:
		doc.alternate_mobile = None


def sync_customer_profile_from_ticket(doc, method=None):
	if getattr(frappe.flags, "skip_lavanya_customer_profile_sync", False):
		return None

	if not frappe.db.exists("DocType", PROFILE_DOCTYPE):
		return None

	primary = normalize_phone(_get_value(doc, "phone_1"))
	if not primary["is_valid_mobile"]:
		return None

	alternate = normalize_phone(_get_value(doc, "phone_2"))
	profile = _find_profile_by_mobile(primary["normalized"], include_disabled=True)
	created = False

	if not profile:
		profile = frappe.new_doc(PROFILE_DOCTYPE)
		profile.primary_mobile = primary["normalized"]
		profile.customer_name = _clean_text(_get_value(doc, "customer_name")) or primary["normalized"]
		_set_if_has_field(profile, "primary_mobile_raw", primary["raw"])
		created = True

	changed = created

	if not created:
		incoming_customer_name = _clean_text(_get_value(doc, "customer_name"))
		current_customer_name = _clean_text(profile.customer_name)
		if incoming_customer_name and (
			not current_customer_name or current_customer_name == profile.primary_mobile
		):
			profile.customer_name = incoming_customer_name
			changed = True

		if profile.meta.has_field("primary_mobile_raw") and primary["raw"]:
			if profile.primary_mobile_raw != primary["raw"]:
				profile.primary_mobile_raw = primary["raw"]
				changed = True

	if alternate["raw"] and profile.meta.has_field("alternate_mobile_raw"):
		if profile.alternate_mobile_raw != alternate["raw"]:
			profile.alternate_mobile_raw = alternate["raw"]
			changed = True

	if (
		alternate["is_valid_mobile"]
		and alternate["normalized"] != primary["normalized"]
		and not profile.alternate_mobile
	):
		profile.alternate_mobile = alternate["normalized"]
		changed = True

	for profile_field, ticket_field in [
		("address", "address"),
		("pincode", "pincode"),
	]:
		changed = _set_from_ticket_if_safe(profile, profile_field, _get_value(doc, ticket_field)) or changed

	for profile_field, ticket_field in [
		("last_product_type", "product_type"),
		("last_brand", "brand"),
	]:
		changed = _set_last_value(profile, profile_field, _get_value(doc, ticket_field)) or changed

	ticket_name = _clean_text(_get_value(doc, "name"))
	if ticket_name and profile.last_ticket != ticket_name:
		profile.last_ticket = ticket_name
		changed = True

	ticket_count = _ticket_count_for_numbers([profile.primary_mobile, profile.alternate_mobile])
	if int(profile.ticket_count or 0) != ticket_count:
		profile.ticket_count = ticket_count
		changed = True

	if changed:
		if created:
			profile.insert(ignore_permissions=True)
		else:
			profile.save(ignore_permissions=True)

	return {
		"created": created,
		"changed": changed,
		"profile": profile.name,
	}
