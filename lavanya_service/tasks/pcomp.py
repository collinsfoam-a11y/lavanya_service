"""Supplier Penalty Computation - advisory/operational only (P2.1)."""

import frappe
from frappe.utils import today, date_diff, getdate, now_datetime

COMPUTATION_DOCTYPE = "Supplier Penalty Computation"
RULE_DOCTYPE = "Supplier Penalty Rule"


def get_applicable_penalty_rule(ticket):
	if not frappe.db.exists("DocType", RULE_DOCTYPE):
		return None
	tk = frappe.get_doc("HD Ticket", ticket) if isinstance(ticket, str) else ticket
	now = getdate(today())
	filters = {"active": 1}
	candidates = frappe.get_all(RULE_DOCTYPE, filters=filters,
		fields=["name", "brand", "supplier", "service_flow_type", "breach_type",
			"grace_days", "penalty_type", "fixed_amount", "percentage_rate",
			"per_day_amount", "max_penalty_amount", "valid_from", "valid_to"])
	best = None; best_score = -1
	for rule in candidates:
		score = 0
		if rule.get("brand") and rule["brand"] != tk.get("brand"): continue
		if rule.get("brand"): score += 20
		if rule.get("supplier") and rule.get("supplier", "").lower() != (tk.get("brand") or "").lower(): continue
		if rule.get("supplier"): score += 10
		if rule.get("service_flow_type") and rule["service_flow_type"] != tk.get("service_flow_type"): continue
		if rule.get("service_flow_type"): score += 15
		if rule.get("valid_from") and getdate(rule["valid_from"]) > now: continue
		if rule.get("valid_to") and getdate(rule["valid_to"]) < now: continue
		score += 5
		if score > best_score: best_score = score; best = rule
	return best


def _existing_computation(ticket_name, breach_type):
	return frappe.db.exists(COMPUTATION_DOCTYPE, {
		"ticket": ticket_name, "breach_type": breach_type,
		"status": ("not in", ["Approved", "Waived", "Rejected", "Cancelled", "Applied"]),
	})


def calculate_penalty(rule, ticket_name, breach_type, breach_start_date, breach_days, base_amount=0):
	if not rule:
		return {"penalty_type": "Manual Review Only", "computed_penalty_amount": 0,
			"final_penalty_amount": 0, "grace_days": 0, "chargeable_days": breach_days,
			"max_penalty_amount": 0,
			"manager_review_required": True,
			"calculation_narration": "No applicable rule found - requires manager review."}
	grace = int(rule.get("grace_days") or 0)
	chargeable = max(0, breach_days - grace)
	penalty_type = rule.get("penalty_type")
	computed = 0; narration = ""
	if penalty_type == "Fixed Amount":
		computed = float(rule.get("fixed_amount") or 0)
		narration = f"Fixed: {computed} (breach: {breach_days}d, grace: {grace}d)"
	elif penalty_type == "Per Day":
		per_day = float(rule.get("per_day_amount") or 0)
		computed = per_day * chargeable
		narration = f"Per-day: {per_day} x {chargeable}d = {computed}"
	elif penalty_type == "Percentage of Claim":
		pct = float(rule.get("percentage_rate") or 0) / 100.0
		computed = base_amount * pct
		narration = f"{rule.get('percentage_rate')}% of {base_amount} = {computed}"
	elif penalty_type == "Percentage of Invoice":
		pct = float(rule.get("percentage_rate") or 0) / 100.0
		computed = base_amount * pct
		narration = f"{rule.get('percentage_rate')}% of {base_amount} = {computed}"
	else:
		narration = f"Type '{penalty_type}' - manual review required."
	max_p = float(rule.get("max_penalty_amount") or 0)
	final = min(computed, max_p) if max_p > 0 else computed
	if chargeable <= 0: final = 0; narration += " (within grace)"
	return {"penalty_type": penalty_type, "computed_penalty_amount": round(computed, 2),
		"final_penalty_amount": round(final, 2), "grace_days": grace,
		"chargeable_days": chargeable, "max_penalty_amount": max_p,
		"manager_review_required": penalty_type == "Manual Review Only",
		"calculation_narration": narration}


def compute_penalty_for_ticket(ticket_name, breach_type, breach_start_date, breach_days=None, base_amount=0):
	if not frappe.db.exists("HD Ticket", ticket_name): return None
	if _existing_computation(ticket_name, breach_type): return None
	tk = frappe.get_doc("HD Ticket", ticket_name)
	rule = get_applicable_penalty_rule(tk)
	if breach_days is None:
		breach_days = max(0, date_diff(today(), breach_start_date)) if breach_start_date else 0
	calc = calculate_penalty(rule, ticket_name, breach_type, str(breach_start_date) if breach_start_date else None, breach_days, base_amount)
	if breach_days <= 0: return None
	if calc["chargeable_days"] <= 0: return None
	doc = frappe.get_doc({"doctype": COMPUTATION_DOCTYPE, "ticket": ticket_name,
		"brand": tk.get("brand"), "supplier": tk.get("brand"),
		"service_flow_type": tk.get("service_flow_type"), "breach_type": breach_type,
		"breach_start_date": breach_start_date, "breach_days": breach_days,
		"grace_days": calc["grace_days"], "chargeable_days": calc["chargeable_days"],
		"penalty_type": calc["penalty_type"], "base_amount": base_amount,
		"computed_penalty_amount": calc["computed_penalty_amount"],
		"max_penalty_amount": calc["max_penalty_amount"],
		"final_penalty_amount": calc["final_penalty_amount"],
		"status": "Manager Review" if calc["manager_review_required"] else "Computed", "manager_review_required": calc["manager_review_required"],
		"calculation_narration": calc["calculation_narration"], "created_from_scheduler": True})
	doc.insert(ignore_permissions=True)
	return doc.name


def _find_sla_breaches():
	rows = frappe.get_all("HD Ticket", filters={"agreement_status": "Failed",
		"status": ("not in", ["Closed", "Cancelled", "Resolved"])},
		fields=["name", "resolution_date", "response_by"])
	for r in rows:
		start = r.get("response_by") or r.get("resolution_date")
		if start: compute_penalty_for_ticket(r.name, "SLA Breach", start)

def _find_stock_complaint_delays():
	if not frappe.db.exists("DocType", "Stock Complaint Record"): return
	for r in frappe.get_all("Stock Complaint Record", filters={
		"supplier_notified_at": ("is", "set"), "credit_note_received_at": ("is", "not set"),
		"status": ("!=", "Completed")}, fields=["ticket", "supplier_notified_at"]):
		if r.ticket: compute_penalty_for_ticket(r.ticket, "Credit Note Delay", r.supplier_notified_at)

def _find_replacement_delays():
	if not frappe.db.exists("DocType", "Replacement Record"): return
	for r in frappe.get_all("Replacement Record", filters={
		"new_unit_dispatched_at": ("is", "not set"), "reimbursement_status": ("!=", "Received"),
		"status": ("!=", "Completed")}, fields=["ticket", "old_unit_collected_at"]):
		if r.ticket and r.old_unit_collected_at: compute_penalty_for_ticket(r.ticket, "Replacement Delay", r.old_unit_collected_at)

def _find_return_delays():
	if not frappe.db.exists("DocType", "Return Service Record"): return
	for r in frappe.get_all("Return Service Record", filters={
		"brand_notified_at": ("is", "set"), "customer_refund_processed_at": ("is", "not set"),
		"refund_status": "Pending", "status": ("!=", "Completed")}, fields=["ticket", "brand_notified_at"]):
		if r.ticket: compute_penalty_for_ticket(r.ticket, "Refund Delay", r.brand_notified_at)

def _find_part_pending_delays():
	for t in frappe.get_all("HD Ticket", filters={"status": "Waiting on Part / Approval"}, fields=["name", "modified"]):
		compute_penalty_for_ticket(t.name, "Part Pending Delay", t.modified)

def _find_no_update_delays():
	for t in frappe.get_all("HD Ticket", filters={"followup_stage": "no_technician_update",
		"status": ("not in", ["Closed", "Cancelled", "Resolved"])}, fields=["name", "modified"]):
		compute_penalty_for_ticket(t.name, "No Update Delay", t.modified)

def _find_payment_block_breaches():
	if not frappe.db.exists("DocType", "Supplier Payment Block"): return
	for b in frappe.get_all("Supplier Payment Block", filters={
		"block_status": ("in", ["Active", "Pending Review"])}, fields=["ticket", "blocked_at"]):
		if b.ticket: compute_penalty_for_ticket(b.ticket, "Payment Block Triggered", b.blocked_at)

def compute_penalties_for_open_cases():
	for fn in [_find_sla_breaches, _find_stock_complaint_delays, _find_replacement_delays,
			   _find_return_delays, _find_part_pending_delays, _find_no_update_delays, _find_payment_block_breaches]:
		try: fn()
		except Exception: frappe.log_error(title="lavanya p2 scan: " + fn.__name__, message=frappe.get_traceback())
	frappe.db.commit()

def run_daily_penalty_computation_dry_safe():
	compute_penalties_for_open_cases()
