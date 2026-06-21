import frappe
from frappe.utils import now_datetime

"""
H5D: Supplier Payment Block scheduler task.

Advisory/dry-run only:
- Creates "Supplier Payment Block" records in "Pending Review" status.
- Auto-releases blocks when overdue tickets clear.
- Does NOT post ERP entries, accounting entries, penalties, WhatsApp, or SMS.
- Does NOT block actual supplier payments — it is an operational advisory record.
- All payment-block DocTypes must exist (created by setup/supplier_payment_block.py).
"""

TICKET_DOCTYPE = "HD Ticket"


def check_payment_block_triggers():
	brands_with_overdue = _find_brands_with_overdue_tickets()
	overdue_brands = {b for b, d, c in brands_with_overdue}

	# Create new blocks for brands exceeding trigger threshold
	for brand, delay_days, ticket_count in brands_with_overdue:
		sla = _get_sla_for_brand(brand)
		if not sla or not sla.get("enabled"):
			continue
		trigger_days = sla.get("payment_block_delay_days") or 15
		if delay_days < trigger_days:
			continue
		if _existing_active_block(brand):
			continue
		_create_payment_block(brand, delay_days, ticket_count)

	# Auto-release active blocks for brands with no overdue tickets
	for block in frappe.get_all(
		"Supplier Payment Block",
		filters={"block_status": "Active"},
		fields=["name", "brand"],
	):
		if block.brand not in overdue_brands:
			doc = frappe.get_doc("Supplier Payment Block", block.name)
			doc.block_status = "Released"
			doc.released_at = now_datetime()
			doc.release_reason = "Auto-released: no overdue tickets remain"
			doc.save(ignore_permissions=True)

	frappe.db.commit()


def _find_brands_with_overdue_tickets():
	results = {}
	tickets = frappe.get_all(
		TICKET_DOCTYPE,
		filters={
			"status": ["not in", ["Closed", "Cancelled", "Resolved"]],
			"brand": ["is", "set"],
		},
		fields=["name", "brand", "stage_due_at"],
	)
	for t in tickets:
		if not t.stage_due_at:
			continue
		delay = max(0, int((now_datetime() - t.stage_due_at).total_seconds() // 86400))
		if delay <= 0:
			continue
		if t.brand not in results:
			results[t.brand] = {"max_delay": 0, "count": 0}
		results[t.brand]["max_delay"] = max(results[t.brand]["max_delay"], delay)
		results[t.brand]["count"] += 1
	return [(b, v["max_delay"], v["count"]) for b, v in results.items()]


def _get_sla_for_brand(brand):
	name = frappe.db.get_value(
		"Supplier SLA Definition",
		{"brand": brand, "enabled": 1},
		"name",
	)
	if not name:
		return None
	return frappe.get_doc("Supplier SLA Definition", name)


def _existing_active_block(brand):
	return frappe.db.exists(
		"Supplier Payment Block",
		{"brand": brand, "block_status": ["in", ["Active", "Pending Review"]]},
	)


def _create_payment_block(brand, delay_days, ticket_count):
	doc = frappe.get_doc({
		"doctype": "Supplier Payment Block",
		"brand": brand,
		"block_status": "Pending Review",
		"blocked_at": now_datetime(),
		"block_reason": "Auto-triggered: {0} tickets overdue by {1} days".format(ticket_count, delay_days),
		"overdue_ticket_count": ticket_count,
		"max_delay_days": float(delay_days),
	})
	doc.insert(ignore_permissions=True)
