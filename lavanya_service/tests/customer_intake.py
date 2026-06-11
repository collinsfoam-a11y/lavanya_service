"""Rollback-safe tests for Lavanya customer intake by mobile.

Run with:
    bench --site <site> execute lavanya_service.tests.customer_intake.run
"""

import frappe


RESULTS = []


def _record(test_id, description, passed, detail=""):
	RESULTS.append((test_id, description, passed, detail))
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {test_id} - {description}" + (f" | {detail}" if detail else ""))


def _assert(test_id, description, condition, detail=""):
	_record(test_id, description, bool(condition), detail)


def _base_ticket(phone, **overrides):
	doc = frappe.new_doc("HD Ticket")
	doc.subject = overrides.pop("subject", f"Customer intake test {phone or 'blank'}")
	doc.raised_by = overrides.pop("raised_by", f"intake-{phone or 'blank'}@example.com")
	doc.ticket_type = overrides.pop("ticket_type", "Customer Complaint - Site")
	doc.priority = overrides.pop("priority", "Medium")
	doc.complaint_source = overrides.pop("complaint_source", "Phone Call")
	doc.customer_name = overrides.pop("customer_name", "Customer Intake Tester")
	doc.phone_1 = phone
	doc.phone_2 = overrides.pop("phone_2", "")
	doc.address = overrides.pop("address", "Test address")
	doc.pincode = overrides.pop("pincode", "673001")
	doc.product_type = overrides.pop("product_type", "AC")
	doc.brand = overrides.pop("brand", "LG")
	doc.purchased_from_lavanya = overrides.pop("purchased_from_lavanya", "Unknown")
	doc.warranty_status = overrides.pop("warranty_status", "Unknown")
	doc.update(overrides)
	return doc


def _profile_count(mobile):
	return frappe.db.count("Lavanya Customer Profile", {"primary_mobile": mobile})


def _make_user(role):
	email = "customer-intake-" + role.lower().replace(" ", "-") + "@example.com"
	user = frappe.new_doc("User")
	user.email = email
	user.first_name = "Customer Intake"
	user.enabled = 1
	user.user_type = "System User"
	user.append("roles", {"role": role})
	user.insert(ignore_permissions=True)
	return email


def run():
	RESULTS.clear()
	from lavanya_service.api.customer_intake import (
		lookup_customer_by_mobile,
		sync_customer_profile_from_ticket,
	)

	baseline = {
		"HD Ticket": frappe.db.count("HD Ticket"),
		"Lavanya Customer Profile": frappe.db.count("Lavanya Customer Profile"),
		"Communication": frappe.db.count("Communication"),
		"Email Queue": frappe.db.count("Email Queue") if frappe.db.exists("DocType", "Email Queue") else 0,
		"Notification Log": frappe.db.count("Notification Log")
		if frappe.db.exists("DocType", "Notification Log")
		else 0,
		"User": frappe.db.count("User"),
	}

	try:
		_run_all(lookup_customer_by_mobile, sync_customer_profile_from_ticket, baseline)
	finally:
		frappe.set_user("Administrator")
		frappe.flags.skip_lavanya_customer_profile_sync = False
		frappe.db.rollback()
		print("\nTRANSACTION ROLLED BACK - no records persisted")

	failed = [row for row in RESULTS if not row[2]]
	print(f"\nTOTAL: {len(RESULTS)} | PASS: {len(RESULTS) - len(failed)} | FAIL: {len(failed)}")
	if failed:
		print("FAILED TESTS:")
		for test_id, description, _passed, detail in failed:
			print(f"  - {test_id}: {description} | {detail}")
	print("OVERALL:", "PASS" if not failed else "FAIL")
	return {"total": len(RESULTS), "failed": len(failed)}


def _run_all(lookup_customer_by_mobile, sync_customer_profile_from_ticket, baseline):
	print("Baseline:", baseline)

	phone = "9999100001"
	ticket = _base_ticket(phone, customer_name="Primary Customer", phone_2="9999100002")
	ticket.insert(ignore_permissions=True)
	profile = frappe.get_doc("Lavanya Customer Profile", phone)
	_assert("CI-001", "new phone creates profile", profile.primary_mobile == phone, profile.as_dict())
	_assert("CI-001b", "new profile stores ticket link", profile.last_ticket == ticket.name, profile.last_ticket)

	second = _base_ticket(phone, customer_name="Primary Customer Updated")
	second.insert(ignore_permissions=True)
	_assert("CI-002", "same phone does not create duplicate profile", _profile_count(phone) == 1, _profile_count(phone))

	primary_lookup = lookup_customer_by_mobile("+91 99991 00001")
	_assert(
		"CI-003",
		"existing primary mobile lookup returns details",
		primary_lookup.get("found") and primary_lookup.get("primary_mobile") == phone,
		primary_lookup,
	)

	alternate_lookup = lookup_customer_by_mobile("9999100002")
	_assert(
		"CI-004",
		"alternate mobile lookup returns profile",
		alternate_lookup.get("found") and alternate_lookup.get("primary_mobile") == phone,
		alternate_lookup,
	)

	before_blank = frappe.db.count("Lavanya Customer Profile")
	sync_customer_profile_from_ticket(frappe._dict({"doctype": "HD Ticket", "phone_1": "", "name": "BLANK"}))
	_assert(
		"CI-005",
		"blank phone does not create profile",
		frappe.db.count("Lavanya Customer Profile") == before_blank,
		frappe.db.count("Lavanya Customer Profile"),
	)

	before_invalid = frappe.db.count("Lavanya Customer Profile")
	sync_customer_profile_from_ticket(
		frappe._dict({"doctype": "HD Ticket", "phone_1": "12345", "name": "INVALID"})
	)
	_assert(
		"CI-006",
		"invalid phone does not create profile",
		frappe.db.count("Lavanya Customer Profile") == before_invalid,
		frappe.db.count("Lavanya Customer Profile"),
	)

	profile.reload()
	profile.address = "Existing nonblank address"
	profile.pincode = "600001"
	profile.save(ignore_permissions=True)
	blank_update = _base_ticket(phone, customer_name="", address="", pincode="")
	blank_update.insert(ignore_permissions=True)
	profile.reload()
	_assert(
		"CI-007",
		"ticket save does not overwrite nonblank profile data with blank",
		profile.address == "Existing nonblank address" and profile.pincode == "600001",
		{"address": profile.address, "pincode": profile.pincode},
	)

	fallback_phone = "9999100003"
	frappe.flags.skip_lavanya_customer_profile_sync = True
	fallback_ticket = _base_ticket(
		fallback_phone,
		customer_name="Fallback Customer",
		address="Fallback address",
		pincode="682001",
		product_type="TV",
		brand="Samsung",
	)
	fallback_ticket.insert(ignore_permissions=True)
	frappe.flags.skip_lavanya_customer_profile_sync = False
	fallback_lookup = lookup_customer_by_mobile(fallback_phone)
	_assert(
		"CI-008",
		"existing HD Ticket fallback lookup works",
		fallback_lookup.get("found")
		and fallback_lookup.get("source") == "HD Ticket"
		and fallback_lookup.get("last_ticket") == fallback_ticket.name,
		fallback_lookup,
	)

	notification_unchanged = (
		frappe.db.count("Communication") == baseline["Communication"]
		and frappe.db.count("Email Queue") == baseline["Email Queue"]
		and frappe.db.count("Notification Log") == baseline["Notification Log"]
	)
	_assert("CI-009", "no Communication / Email Queue / Notification Log created", notification_unchanged)

	_test_viewer_still_blocked()
	_test_front_desk_create_and_autosave()


def _test_viewer_still_blocked():
	baseline_users = frappe.db.count("User")
	user = _make_user("Lavanya Viewer")
	frappe.set_user(user)
	can_write = bool(frappe.has_permission("HD Ticket", "write"))
	can_create = bool(frappe.has_permission("HD Ticket", "create"))

	insert_blocked = False
	try:
		_base_ticket("9999100004", raised_by=user).insert()
	except Exception:
		insert_blocked = True
	finally:
		frappe.set_user("Administrator")

	_assert(
		"CI-010",
		"viewer still cannot create/write ticket",
		not can_write and not can_create and insert_blocked and frappe.db.count("User") == baseline_users + 1,
		{"write": can_write, "create": can_create, "insert_blocked": insert_blocked},
	)


def _test_front_desk_create_and_autosave():
	user = _make_user("Lavanya Front Desk")
	phone = "9999100005"
	frappe.set_user(user)
	insert_ok = False
	try:
		ticket = _base_ticket(phone, raised_by=user, customer_name="Front Desk Customer")
		ticket.insert()
		insert_ok = True
	finally:
		frappe.set_user("Administrator")

	profile_exists = bool(frappe.db.exists("Lavanya Customer Profile", phone))
	_assert(
		"CI-011",
		"front desk can create ticket and auto-save customer",
		insert_ok and profile_exists,
		{"insert_ok": insert_ok, "profile_exists": profile_exists},
	)
