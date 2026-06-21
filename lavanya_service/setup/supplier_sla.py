import frappe

from lavanya_service.setup.masters import ensure_doctype, field


def create_supplier_sla_doctype():
	result = ensure_doctype(
		"Supplier SLA Definition",
		[
			field("brand", "Brand", "Link", options="Brand Service Master", reqd=1, in_list_view=1, in_standard_filter=1),
			field("service_center", "Service Center", "Link", options="Service Center Master", in_list_view=1),
			field("response_sla_hours", "Response SLA (Hours)", "Int", default="4", in_list_view=1),
			field("resolution_sla_hours", "Resolution SLA (Hours)", "Int", default="48", in_list_view=1),
			field("sb_payment", "Payment Terms", "Section Break"),
			field("payment_block_delay_days", "Payment Block Trigger (Days)", "Int", default="15", in_list_view=1),
			field("payment_terms", "Payment Terms", "Select", options="Net 30\nNet 45\nNet 60\nAdvance", default="Net 30"),
			field("penalty_percent", "Penalty Percent", "Float", default="0.0"),
			field("applicable_product_types", "Applicable Product Types", "Small Text"),
			field("enabled", "Enabled", "Check", default="1", in_list_view=1, in_standard_filter=1),
		],
		autoname="format:SLA-.{brand}.-.#####",
	)
	if result == "created":
		_seed_default_records()
	return result


BRAND_SLA_SEEDS = [
	{"brand": "LG", "response_sla_hours": 2, "resolution_sla_hours": 24, "payment_block_delay_days": 30, "payment_terms": "Net 45"},
	{"brand": "Samsung", "response_sla_hours": 2, "resolution_sla_hours": 24, "payment_block_delay_days": 30, "payment_terms": "Net 45"},
	{"brand": "Whirlpool", "response_sla_hours": 4, "resolution_sla_hours": 48, "payment_block_delay_days": 45, "payment_terms": "Net 60"},
	{"brand": "Voltas", "response_sla_hours": 4, "resolution_sla_hours": 48, "payment_block_delay_days": 45, "payment_terms": "Net 60"},
	{"brand": "Preethi", "response_sla_hours": 8, "resolution_sla_hours": 72, "payment_block_delay_days": 15, "payment_terms": "Net 30"},
	{"brand": "Bajaj", "response_sla_hours": 4, "resolution_sla_hours": 48, "payment_block_delay_days": 30, "payment_terms": "Net 45"},
	{"brand": "Prestige", "response_sla_hours": 8, "resolution_sla_hours": 72, "payment_block_delay_days": 15, "payment_terms": "Net 30"},
	{"brand": "Crompton", "response_sla_hours": 4, "resolution_sla_hours": 48, "payment_block_delay_days": 45, "payment_terms": "Net 60"},
	{"brand": "Kent", "response_sla_hours": 2, "resolution_sla_hours": 24, "payment_block_delay_days": 30, "payment_terms": "Net 45"},
	{"brand": "Faber", "response_sla_hours": 8, "resolution_sla_hours": 72, "payment_block_delay_days": 15, "payment_terms": "Net 30"},
]


def _seed_default_records():
	for seed in BRAND_SLA_SEEDS:
		if frappe.db.exists("Supplier SLA Definition", {"brand": seed["brand"]}):
			continue
		doc = frappe.get_doc({"doctype": "Supplier SLA Definition", **seed, "enabled": 1})
		doc.insert(ignore_permissions=True)
	frappe.db.commit()
