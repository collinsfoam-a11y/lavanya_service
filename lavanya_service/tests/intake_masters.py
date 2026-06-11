"""Rollback-safe tests for Phase 1N-2 intake master shortcuts.

Run with:
    bench --site <site> execute lavanya_service.tests.intake_masters.run
"""

import frappe


RESULTS = []


def _record(test_id, description, passed, detail=""):
	RESULTS.append((test_id, description, passed, detail))
	status = "PASS" if passed else "FAIL"
	print(f"[{status}] {test_id} - {description}" + (f" | {detail}" if detail else ""))


def _assert(test_id, description, condition, detail=""):
	_record(test_id, description, bool(condition), detail)


def _make_user(role):
	email = "intake-master-" + role.lower().replace(" ", "-") + "@example.com"
	user = frappe.new_doc("User")
	user.email = email
	user.first_name = "Intake Master"
	user.enabled = 1
	user.user_type = "System User"
	user.append("roles", {"role": role})
	user.insert(ignore_permissions=True)
	return email


def _base_ticket(user, **overrides):
	doc = frappe.new_doc("HD Ticket")
	doc.subject = overrides.pop("subject", "Intake master test ticket")
	doc.raised_by = overrides.pop("raised_by", user)
	doc.ticket_type = overrides.pop("ticket_type", "Customer Complaint - Site")
	doc.priority = overrides.pop("priority", "Medium")
	doc.complaint_source = overrides.pop("complaint_source", "Phone Call")
	doc.customer_name = overrides.pop("customer_name", "Intake Master Tester")
	doc.phone_1 = overrides.pop("phone_1", "9999200001")
	doc.product_type = overrides.pop("product_type", "AC")
	doc.brand = overrides.pop("brand", "LG")
	doc.purchased_from_lavanya = overrides.pop("purchased_from_lavanya", "Unknown")
	doc.warranty_status = overrides.pop("warranty_status", "Unknown")
	doc.update(overrides)
	return doc


def _expect_block(test_id, description, fn, expected_text):
	try:
		fn()
		_record(test_id, description, False, "operation unexpectedly succeeded")
	except Exception as exc:
		message = str(exc)
		_record(test_id, description, expected_text.lower() in message.lower(), message[:220])


def run():
	RESULTS.clear()
	from lavanya_service.api.intake_masters import (
		create_brand,
		create_category,
		create_item,
		get_item_defaults,
		search_similar_brand,
		search_similar_category,
		search_similar_item,
	)

	baseline = {
		"HD Ticket": frappe.db.count("HD Ticket"),
		"Lavanya Product Category": frappe.db.count("Lavanya Product Category"),
		"Lavanya Product Item": frappe.db.count("Lavanya Product Item"),
		"Communication": frappe.db.count("Communication"),
		"Email Queue": frappe.db.count("Email Queue") if frappe.db.exists("DocType", "Email Queue") else 0,
		"Notification Log": frappe.db.count("Notification Log")
		if frappe.db.exists("DocType", "Notification Log")
		else 0,
	}

	try:
		_run_all(
			create_brand,
			create_category,
			create_item,
			get_item_defaults,
			search_similar_brand,
			search_similar_category,
			search_similar_item,
		)
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


def _run_all(
	create_brand,
	create_category,
	create_item,
	get_item_defaults,
	search_similar_brand,
	search_similar_category,
	search_similar_item,
):
	brand_results = search_similar_brand("prestge")
	_assert(
		"IM-001",
		"similar brand search works",
		any(row.get("name") == "Prestige" for row in brand_results),
		brand_results,
	)

	_expect_block(
		"IM-002",
		"exact duplicate brand blocked",
		lambda: create_brand("prestige "),
		"already exists",
	)

	category_name = "N2 Test Category"
	category = create_category(category_name)
	_assert(
		"IM-003",
		"new category can be created",
		category.get("name") == category_name and frappe.db.exists("Lavanya Product Category", category_name),
		category,
	)

	_expect_block(
		"IM-004",
		"duplicate category blocked",
		lambda: create_category(" n2  test category "),
		"already exists",
	)

	category_results = search_similar_category("n2 category")
	_assert(
		"IM-004b",
		"similar category search works",
		any(row.get("name") == category_name for row in category_results),
		category_results,
	)

	item_name = "N2 Test Prestige Mixer"
	item = create_item(
		item_name=item_name,
		brand="Prestige",
		item_type=category_name,
		model_no="N2-MX-01",
	)
	_assert(
		"IM-005",
		"new item can be created",
		item.get("name") == item_name and frappe.db.exists("Lavanya Product Item", item_name),
		item,
	)

	_expect_block(
		"IM-006",
		"duplicate item blocked",
		lambda: create_item(
			item_name=" n2 test prestige mixer ",
			brand="Prestige",
			item_type=category_name,
			model_no="N2-MX-01",
		),
		"already exists",
	)

	item_results = search_similar_item("prestige mixer", brand="Prestige", category=category_name)
	_assert(
		"IM-007",
		"similar item search works",
		any(row.get("name") == item_name for row in item_results),
		item_results,
	)

	defaults = get_item_defaults(item_name)
	_assert(
		"IM-008",
		"selecting item returns default brand/category/model",
		defaults.get("brand") == "Prestige"
		and defaults.get("item_type") == category_name
		and defaults.get("product_category") == category_name
		and defaults.get("model_no") == "N2-MX-01",
		defaults,
	)

	_test_ticket_save_with_product_fields(category_name, item_name)
	_test_front_desk_and_coordinator_can_use_fields(category_name, item_name)
	_test_viewer_still_blocked()
	_test_no_notification_side_effects()


def _test_ticket_save_with_product_fields(category_name, item_name):
	ticket = _base_ticket(
		"Administrator",
		product_category=category_name,
		product_item=item_name,
		brand="Prestige",
		model_no="N2-MX-01",
	)
	ticket.insert(ignore_permissions=True)
	_assert(
		"IM-009",
		"HD Ticket can save product_category and product_item",
		ticket.product_category == category_name and ticket.product_item == item_name,
		{"product_category": ticket.product_category, "product_item": ticket.product_item},
	)


def _test_front_desk_and_coordinator_can_use_fields(category_name, item_name):
	for role in ["Lavanya Front Desk", "Lavanya Service Coordinator"]:
		user = _make_user(role)
		frappe.set_user(user)
		insert_ok = False
		try:
			ticket = _base_ticket(
				user,
				phone_1="9999200002" if role == "Lavanya Front Desk" else "9999200003",
				product_category=category_name,
				product_item=item_name,
				brand="Prestige",
				model_no="N2-MX-01",
			)
			ticket.insert()
			insert_ok = True
		finally:
			frappe.set_user("Administrator")

		_assert(
			"IM-010-" + role.replace(" ", "-"),
			role + " can use intake product fields",
			insert_ok,
		)


def _test_viewer_still_blocked():
	user = _make_user("Lavanya Viewer")
	frappe.set_user(user)
	can_write = bool(frappe.has_permission("HD Ticket", "write"))
	can_create = bool(frappe.has_permission("HD Ticket", "create"))

	insert_blocked = False
	try:
		_base_ticket(user, phone_1="9999200004").insert()
	except Exception:
		insert_blocked = True
	finally:
		frappe.set_user("Administrator")

	_assert(
		"IM-011",
		"viewer still cannot create/write",
		not can_write and not can_create and insert_blocked,
		{"write": can_write, "create": can_create, "insert_blocked": insert_blocked},
	)


def _test_no_notification_side_effects():
	_assert(
		"IM-012",
		"no Communication / Email Queue / Notification Log side effects",
		frappe.db.count("Email Queue") == 0 and frappe.db.count("Notification Log") == 0,
		{
			"Communication": frappe.db.count("Communication"),
			"Email Queue": frappe.db.count("Email Queue"),
			"Notification Log": frappe.db.count("Notification Log"),
		},
	)
