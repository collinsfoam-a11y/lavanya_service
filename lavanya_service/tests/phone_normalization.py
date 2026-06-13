"""Rollback-safe tests for Phase 1N-1-FIX-1A phone handling.

Run with:
    bench --site <site> execute lavanya_service.tests.phone_normalization.run
"""

import frappe


RESULTS = []


def _record(test_id, description, passed, detail=""):
	RESULTS.append((test_id, description, bool(passed), detail))
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {test_id} - {description}" + (f" | {detail}" if detail else ""))


def _assert(test_id, description, condition, detail=""):
	_record(test_id, description, bool(condition), detail)


def _base_ticket(phone, **overrides):
	doc = frappe.new_doc("HD Ticket")
	doc.subject = overrides.pop("subject", f"Phone normalization test {phone or 'blank'}")
	doc.raised_by = overrides.pop("raised_by", "phone-normalization@example.com")
	doc.ticket_type = overrides.pop("ticket_type", "Customer Complaint - Site")
	doc.priority = overrides.pop("priority", "Medium")
	doc.complaint_source = overrides.pop("complaint_source", "Phone Call")
	doc.customer_name = overrides.pop("customer_name", "Phone Normalization Tester")
	doc.phone_1 = phone
	doc.phone_2 = overrides.pop("phone_2", "")
	doc.address = overrides.pop("address", "Phone test address")
	doc.pincode = overrides.pop("pincode", "673001")
	doc.product_type = overrides.pop("product_type", "AC")
	doc.brand = overrides.pop("brand", "LG")
	doc.purchased_from_lavanya = overrides.pop("purchased_from_lavanya", "Unknown")
	doc.warranty_status = overrides.pop("warranty_status", "Unknown")
	doc.update(overrides)
	return doc


def run():
	RESULTS.clear()
	from lavanya_service.utils.phone import normalize_phone
	from lavanya_service.api.customer_intake import lookup_customer_by_mobile

	baseline = {
		"HD Ticket": frappe.db.count("HD Ticket"),
		"Lavanya Customer Profile": frappe.db.count("Lavanya Customer Profile"),
		"Communication": frappe.db.count("Communication"),
		"Email Queue": frappe.db.count("Email Queue") if frappe.db.exists("DocType", "Email Queue") else 0,
		"Notification Log": frappe.db.count("Notification Log")
		if frappe.db.exists("DocType", "Notification Log")
		else 0,
	}

	try:
		_test_normalizer_matrix(normalize_phone)
		_test_ticket_raw_only_behavior()
		_test_format_variants_reuse_one_profile(lookup_customer_by_mobile)
	finally:
		frappe.set_user("Administrator")
		frappe.db.rollback()
		print("\nTRANSACTION ROLLED BACK - no records persisted")

	failed = [row for row in RESULTS if not row[2]]
	print(f"\nTOTAL: {len(RESULTS)} | PASS: {len(RESULTS) - len(failed)} | FAIL: {len(failed)}")
	if failed:
		print("FAILED TESTS:")
		for test_id, description, _passed, detail in failed:
			print(f"  - {test_id}: {description} | {detail}")
	print("BASELINE:", baseline)
	print("OVERALL:", "PASS" if not failed else "FAIL")
	return {"total": len(RESULTS), "failed": len(failed)}


def _test_normalizer_matrix(normalize_phone):
	cases = [
		("PN-001", "9876543210", "9876543210", True, "valid"),
		("PN-002", "+91 98765 43210", "9876543210", True, "valid"),
		("PN-003", "91 9876543210", "9876543210", True, "valid"),
		("PN-004", "09876543210", "9876543210", True, "valid"),
		("PN-005", "98765-43210", "9876543210", True, "valid"),
		("PN-006", "9123456789", "9123456789", True, "valid"),
		("PN-007", "9999999977", "9999999977", True, "valid"),
		("PN-008", "1234567890", None, False, "invalid_mobile_range"),
		("PN-009", "5432109876", None, False, "invalid_mobile_range"),
		("PN-010", "9999999999", None, False, "repeated_junk"),
		("PN-011", "0000000000", None, False, "repeated_junk"),
		("PN-012", "0495-2222222", None, False, "not_indian_mobile"),
		("PN-013", "0495-2222222 ext 4", None, False, "not_indian_mobile"),
		("PN-014", "", None, False, "blank"),
	]

	for test_id, raw, expected_normalized, expected_valid, expected_reason in cases:
		result = normalize_phone(raw)
		_assert(
			test_id,
			f"normalize {raw!r}",
			result.get("normalized") == expected_normalized
			and result.get("is_valid_mobile") is expected_valid
			and result.get("reason") == expected_reason,
			result,
		)


def _test_ticket_raw_only_behavior():
	before_profiles = frappe.db.count("Lavanya Customer Profile")
	ticket = _base_ticket("0495-2222222 ext 4", phone_2="9999999999")
	ticket.insert(ignore_permissions=True)
	ticket.reload()

	_assert(
		"PN-015",
		"raw-only phone does not block HD Ticket insert",
		bool(ticket.name) and ticket.phone_1 == "0495-2222222 ext 4",
		ticket.as_dict(),
	)
	_assert(
		"PN-016",
		"raw-only phone is stored with empty normalized value",
		ticket.phone_1_raw == "0495-2222222 ext 4"
		and not ticket.phone_1_normalized
		and ticket.phone_2_raw == "9999999999"
		and not ticket.phone_2_normalized,
		{
			"phone_1": ticket.phone_1,
			"phone_1_raw": ticket.phone_1_raw,
			"phone_1_normalized": ticket.phone_1_normalized,
			"phone_2_raw": ticket.phone_2_raw,
			"phone_2_normalized": ticket.phone_2_normalized,
		},
	)
	_assert(
		"PN-017",
		"raw-only phone does not create customer profile",
		frappe.db.count("Lavanya Customer Profile") == before_profiles,
		frappe.db.count("Lavanya Customer Profile"),
	)


def _test_format_variants_reuse_one_profile(lookup_customer_by_mobile):
	first = _base_ticket("+91 98765 43210", customer_name="Format Variant Customer")
	first.insert(ignore_permissions=True)
	first.reload()

	second = _base_ticket("09876543210", customer_name="Format Variant Customer Updated")
	second.insert(ignore_permissions=True)
	second.reload()

	lookup = lookup_customer_by_mobile("98765-43210")
	profiles = frappe.get_all(
		"Lavanya Customer Profile",
		filters={"primary_mobile": "9876543210"},
		fields=["name", "primary_mobile", "primary_mobile_raw", "last_ticket", "ticket_count"],
	)

	_assert(
		"PN-018",
		"format variants normalize on HD Ticket",
		first.phone_1 == "9876543210"
		and first.phone_1_raw == "+91 98765 43210"
		and first.phone_1_normalized == "9876543210"
		and second.phone_1 == "9876543210"
		and second.phone_1_raw == "09876543210",
		{
			"first": {
				"phone_1": first.phone_1,
				"raw": first.phone_1_raw,
				"normalized": first.phone_1_normalized,
			},
			"second": {
				"phone_1": second.phone_1,
				"raw": second.phone_1_raw,
				"normalized": second.phone_1_normalized,
			},
		},
	)
	# Assert the business invariant (exactly one profile for the mobile, both
	# variant tickets resolving to it) rather than an absolute count delta.
	# The delta form was stateful: a profile committed by a previous run made
	# the second insert UPDATE instead of CREATE, so the count never grew by 1.
	# The invariant form is idempotent and still catches a real duplicate
	# (len(profiles) would be > 1) without weakening any business rule.
	_assert(
		"PN-019",
		"format variants resolve to one profile",
		len(profiles) == 1
		and lookup.get("found")
		and lookup.get("primary_mobile") == "9876543210"
		and profiles[0]["last_ticket"] == second.name,
		{"profiles": profiles, "lookup": lookup, "second": second.name},
	)
