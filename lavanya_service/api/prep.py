"""P2.1 penalty report API endpoints."""
import frappe
from frappe import _
from frappe.utils import now_datetime

_MANAGER_ROLES = {"System Manager", "Lavanya Manager", "Lavanya Service Coordinator", "Lavanya Viewer"}

def _check_role():
	if not set(frappe.get_roles(frappe.session.user)).intersection(_MANAGER_ROLES):
		frappe.throw("Not permitted.", frappe.PermissionError)

@frappe.whitelist()
def get_penalty_summary():
	_check_role()
	computations = frappe.get_all("Supplier Penalty Computation",
		filters={"status": ("not in", ["Cancelled", "Draft"])},
		fields=["status", "final_penalty_amount", "manager_review_required", "breach_days", "brand"])
	total = 0; review = 0; approved = 0; waived = 0; rejected = 0; oldest = 0
	highest_supplier = None; highest_amount = 0; supplier_totals = {}
	for c in computations:
		amt = float(c.get("final_penalty_amount") or 0); sup = c.get("brand") or "Unknown"
		if c.get("status") in ("Computed", "Manager Review"): total += amt
		if c.get("manager_review_required"): review += 1
		if c.get("status") == "Approved": approved += amt
		if c.get("status") == "Waived": waived += amt
		if c.get("status") == "Rejected": rejected += 1
		supplier_totals[sup] = supplier_totals.get(sup, 0) + amt
		oldest = max(oldest, int(c.get("breach_days") or 0))
	for s, t in supplier_totals.items():
		if t > highest_amount: highest_amount = t; highest_supplier = s
	return {"total_computed": round(total, 2), "manager_review_count": review,
		"approved_amount": round(approved, 2), "waived_amount": round(waived, 2),
		"rejected_count": rejected, "highest_supplier": highest_supplier or "None",
		"highest_supplier_amount": round(highest_amount, 2), "oldest_breach_days": oldest}

@frappe.whitelist()
def get_penalty_list(status_filter=None, brand=None, limit=50, start=0):
	_check_role()
	filters = {"status": ("not in", ["Cancelled", "Draft"])}
	if status_filter: filters["status"] = status_filter
	if brand: filters["brand"] = brand
	rows = frappe.get_all("Supplier Penalty Computation", filters=filters,
		fields=["name", "ticket", "brand", "supplier", "breach_type", "breach_days",
			"grace_days", "chargeable_days", "computed_penalty_amount",
			"final_penalty_amount", "status", "manager_review_required",
			"calculation_narration", "creation"],
		order_by="creation desc", limit=limit, limit_start=start)
	return {"penalties": rows}

@frappe.whitelist()
def get_penalty_detail(penalty_name):
	_check_role()
	if not frappe.db.exists("Supplier Penalty Computation", penalty_name): frappe.throw("Not found.")
	return frappe.get_doc("Supplier Penalty Computation", penalty_name).as_dict()

@frappe.whitelist(methods=["POST"])
def approve_penalty(penalty_name, narration=None):
	_check_role()
	if not (narration or "").strip(): frappe.throw("Approval narration is required.")
	doc = frappe.get_doc("Supplier Penalty Computation", penalty_name)
	if doc.status not in ("Computed", "Manager Review"): frappe.throw("Only Computed/Manager Review penalties can be approved.")
	doc.status = "Approved"; doc.approved_by = frappe.session.user
	doc.approved_at = now_datetime(); doc.approval_narration = narration or ""
	doc.save(ignore_permissions=True)
	return {"ok": True, "status": "Approved"}

@frappe.whitelist(methods=["POST"])
def waive_penalty(penalty_name, reason=None):
	_check_role()
	if not (reason or "").strip(): frappe.throw("Waiver reason is required.")
	doc = frappe.get_doc("Supplier Penalty Computation", penalty_name)
	if doc.status not in ("Computed", "Manager Review"): frappe.throw("Only Computed/Manager Review penalties can be waived.")
	doc.status = "Waived"; doc.waived_by = frappe.session.user
	doc.waived_at = now_datetime(); doc.waiver_reason = reason or ""
	doc.final_penalty_amount = 0; doc.save(ignore_permissions=True)
	return {"ok": True, "status": "Waived"}

@frappe.whitelist(methods=["POST"])
def reject_penalty(penalty_name, reason=None):
	_check_role()
	if not (reason or "").strip(): frappe.throw("Rejection reason is required.")
	doc = frappe.get_doc("Supplier Penalty Computation", penalty_name)
	if doc.status not in ("Computed", "Manager Review"): frappe.throw("Only Computed/Manager Review penalties can be rejected.")
	doc.status = "Rejected"; doc.rejected_by = frappe.session.user
	doc.rejected_at = now_datetime(); doc.rejection_reason = reason or ""
	doc.save(ignore_permissions=True)
	return {"ok": True, "status": "Rejected"}
