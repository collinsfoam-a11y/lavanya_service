import re

import frappe


PROFILE_DOCTYPE = "Lavanya Customer Profile"
TICKET_DOCTYPE = "HD Ticket"


def normalize_mobile(value):
	if not value:
		return ""

	digits = re.sub(r"\D+", "", str(value))

	if digits.startswith("91") and len(digits) == 12:
		digits = digits[2:]

	if digits.startswith("0") and len(digits) == 11:
		digits = digits[1:]

	if not re.fullmatch(r"\d{10}", digits):
		return ""

	return digits


def _get_value(doc, fieldname):
	if hasattr(doc, "get"):
		return doc.get(fieldname)
	return getattr(doc, fieldname, None)


def _clean_text(value):
	if value is None:
		return ""
	return str(value).strip()


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
	return {
		"found": True,
		"source": TICKET_DOCTYPE,
		"name": ticket.name,
		"customer_name": ticket.customer_name,
		"primary_mobile": ticket.phone_1,
		"alternate_mobile": ticket.phone_2,
		"address": ticket.address,
		"pincode": ticket.pincode,
		"last_ticket": ticket.name,
		"ticket_count": _ticket_count_for_numbers([ticket.phone_1, ticket.phone_2]),
		"last_product_type": ticket.product_type,
		"last_brand": ticket.brand,
	}


def _find_profile_by_mobile(mobile, include_disabled=False):
	if not frappe.db.exists("DocType", PROFILE_DOCTYPE):
		return None

	base_filters = {} if include_disabled else {"disabled": 0}

	for fieldname in ["primary_mobile", "alternate_mobile"]:
		filters = dict(base_filters)
		filters[fieldname] = mobile
		name = frappe.db.exists(PROFILE_DOCTYPE, filters)
		if name:
			return frappe.get_doc(PROFILE_DOCTYPE, name)

	return None


def _latest_ticket_for_mobile(mobile):
	rows = []
	for fieldname in ["phone_1", "phone_2"]:
		rows.extend(
			frappe.get_all(
				TICKET_DOCTYPE,
				filters={fieldname: mobile},
				fields=[
					"name",
					"customer_name",
					"phone_1",
					"phone_2",
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

	return sorted(rows, key=lambda row: row.modified, reverse=True)[0]


def _ticket_count_for_numbers(numbers):
	clean_numbers = {normalize_mobile(number) for number in numbers if normalize_mobile(number)}
	if not clean_numbers:
		return 0

	ticket_names = set()
	for fieldname in ["phone_1", "phone_2"]:
		for number in clean_numbers:
			for row in frappe.get_all(TICKET_DOCTYPE, filters={fieldname: number}, fields=["name"]):
				ticket_names.add(row.name)

	return len(ticket_names)


@frappe.whitelist()
def lookup_customer_by_mobile(mobile):
	normalized = normalize_mobile(mobile)

	if not normalized:
		return {
			"found": False,
			"invalid_mobile": bool(_clean_text(mobile)),
			"mobile": _clean_text(mobile),
		}

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


def sync_customer_profile_from_ticket(doc, method=None):
	if getattr(frappe.flags, "skip_lavanya_customer_profile_sync", False):
		return None

	if not frappe.db.exists("DocType", PROFILE_DOCTYPE):
		return None

	primary_mobile = normalize_mobile(_get_value(doc, "phone_1"))
	if not primary_mobile:
		return None

	alternate_mobile = normalize_mobile(_get_value(doc, "phone_2"))
	profile = _find_profile_by_mobile(primary_mobile, include_disabled=True)
	created = False

	if not profile:
		profile = frappe.new_doc(PROFILE_DOCTYPE)
		profile.primary_mobile = primary_mobile
		profile.customer_name = _clean_text(_get_value(doc, "customer_name")) or primary_mobile
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

	if alternate_mobile and alternate_mobile != primary_mobile and not profile.alternate_mobile:
		profile.alternate_mobile = alternate_mobile
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
