"""P2.1 supplier computation tests."""
import frappe
from frappe.utils import today, add_days, getdate

_PASS = []; _FAIL = []; _created = []

def _check(name, cond, detail=""):
	(_PASS if cond else _FAIL).append(name)
	print("[{}] {}".format("PASS" if cond else "FAIL", name) + (" | " + detail if detail else ""))

def _new_rule(**ovr):
	doc = frappe.get_doc({"doctype": "Supplier Penalty Rule", "breach_type": "SLA Breach",
		"penalty_type": "Fixed Amount", "active": 1, "grace_days": 2, "fixed_amount": 500,
		"max_penalty_amount": 5000, **ovr})
	doc.insert(ignore_permissions=True); frappe.db.commit(); _created.append(("Supplier Penalty Rule", doc.name)); return doc.name

def _new_ticket(**ovr):
	doc = frappe.get_doc({"doctype": "HD Ticket", "subject": "P2 Test", "description": "Test",
		"ticket_type": "Customer Complaint - Site", "customer_name": "P2 Customer",
		"status": "Open", "agreement_status": "Failed", **ovr})
	doc.insert(ignore_permissions=True); frappe.db.commit(); _created.append(("HD Ticket", doc.name)); return doc.name

def _cleanup():
	for dt, nm in reversed(_created):
		try:
			if frappe.db.exists(dt, nm): frappe.delete_doc(dt, nm, ignore_permissions=True)
		except: pass
	_created.clear(); frappe.db.commit()

def test_no_penalty_before_grace():
	_new_rule(breach_type="SLA Breach", grace_days=5)
	tk = _new_ticket(agreement_status="Failed", response_by=str(today()))
	from lavanya_service.tasks.pcomp import compute_penalty_for_ticket
	r = compute_penalty_for_ticket(tk, "SLA Breach", str(today()), breach_days=3)
	_check("no_penalty_before_grace", r is None, "No comp within grace")

def test_fixed_after_grace():
	_new_rule(breach_type="SLA Breach", penalty_type="Fixed Amount", fixed_amount=500, grace_days=2)
	tk = _new_ticket(agreement_status="Failed", response_by=str(add_days(today(), -10)))
	from lavanya_service.tasks.pcomp import compute_penalty_for_ticket
	r = compute_penalty_for_ticket(tk, "SLA Breach", str(add_days(today(), -10)), breach_days=10)
	_check("fixed_after_grace", r is not None, "Comp created")
	if r:
		doc = frappe.get_doc("Supplier Penalty Computation", r)
		_check("fixed_amount_correct", doc.final_penalty_amount == 500, "Amount: " + str(doc.final_penalty_amount))
		_created.append(("Supplier Penalty Computation", r))

def test_capped_by_max():
	_new_rule(breach_type="SLA Breach", penalty_type="Per Day", per_day_amount=2000, grace_days=0, max_penalty_amount=5000)
	tk = _new_ticket(agreement_status="Failed", response_by=str(add_days(today(), -10)))
	from lavanya_service.tasks.pcomp import compute_penalty_for_ticket
	r = compute_penalty_for_ticket(tk, "SLA Breach", str(add_days(today(), -10)), breach_days=10)
	if r:
		doc = frappe.get_doc("Supplier Penalty Computation", r)
		_check("capped_5000", doc.final_penalty_amount == 5000, "Capped: " + str(doc.final_penalty_amount))
		_created.append(("Supplier Penalty Computation", r))

def test_no_duplicate():
	_new_rule(breach_type="Part Pending Delay", penalty_type="Fixed Amount", fixed_amount=300, grace_days=0)
	tk = _new_ticket(status="Waiting on Part / Approval", modified=str(add_days(today(), -5)))
	from lavanya_service.tasks.pcomp import compute_penalty_for_ticket
	r1 = compute_penalty_for_ticket(tk, "Part Pending Delay", str(add_days(today(), -5)), breach_days=5)
	_check("first_created", r1 is not None)
	r2 = compute_penalty_for_ticket(tk, "Part Pending Delay", str(add_days(today(), -5)), breach_days=5)
	_check("duplicate_blocked", r2 is None, "Second call returned None")
	if r1: _created.append(("Supplier Penalty Computation", r1))

def test_role_gate():
	frappe.set_user("Guest")
	try:
		from lavanya_service.api.prep import get_penalty_summary
		get_penalty_summary()
		_check("role_gate", False, "Should throw")
	except Exception:
		_check("role_gate", True, "Guest blocked")
	frappe.set_user("Administrator")

def test_mgr_review_no_rule():
	tk = _new_ticket(agreement_status="Failed", response_by=str(add_days(today(), -5)))
	from lavanya_service.tasks.pcomp import compute_penalty_for_ticket
	r = compute_penalty_for_ticket(tk, "SLA Breach", str(add_days(today(), -5)), breach_days=5)
	if r:
		doc = frappe.get_doc("Supplier Penalty Computation", r)
		_check("mgr_review_no_rule", doc.manager_review_required == 1)
		_created.append(("Supplier Penalty Computation", r))

def test_report_apis():
	_new_rule(breach_type="SLA Breach", penalty_type="Fixed Amount", fixed_amount=500, grace_days=0)
	tk = _new_ticket(agreement_status="Failed", response_by=str(add_days(today(), -5)))
	from lavanya_service.tasks.pcomp import compute_penalty_for_ticket
	r = compute_penalty_for_ticket(tk, "SLA Breach", str(add_days(today(), -5)), breach_days=5)
	if r:
		_created.append(("Supplier Penalty Computation", r))
		from lavanya_service.api.prep import get_penalty_summary, get_penalty_list, get_penalty_detail
		summary = get_penalty_summary()
		rows = get_penalty_list().get("penalties") or []
		detail = get_penalty_detail(r)
		_check("summary_api_ok", "total_computed" in summary)
		_check("list_api_ok", any(row.get("name") == r for row in rows))
		_check("detail_api_ok", detail.get("name") == r)

def test_approve_flow():
	_new_rule(breach_type="SLA Breach", penalty_type="Fixed Amount", fixed_amount=500, grace_days=0)
	tk = _new_ticket(agreement_status="Failed", response_by=str(add_days(today(), -5)))
	from lavanya_service.tasks.pcomp import compute_penalty_for_ticket
	r = compute_penalty_for_ticket(tk, "SLA Breach", str(add_days(today(), -5)), breach_days=5)
	if r:
		_created.append(("Supplier Penalty Computation", r))
		from lavanya_service.api.prep import approve_penalty
		approve_penalty(r, narration="Test")
		doc = frappe.get_doc("Supplier Penalty Computation", r)
		_check("approve_ok", doc.status == "Approved", "Status: " + doc.status)
		try:
			approve_penalty(r, narration="Double")
			_check("double_approve_blocked", False)
		except: _check("double_approve_blocked", True)

def test_approve_requires_narration():
	_new_rule(breach_type="SLA Breach", penalty_type="Fixed Amount", fixed_amount=500, grace_days=0)
	tk = _new_ticket(agreement_status="Failed", response_by=str(add_days(today(), -5)))
	from lavanya_service.tasks.pcomp import compute_penalty_for_ticket
	r = compute_penalty_for_ticket(tk, "SLA Breach", str(add_days(today(), -5)), breach_days=5)
	if r:
		_created.append(("Supplier Penalty Computation", r))
		from lavanya_service.api.prep import approve_penalty
		try:
			approve_penalty(r, narration="   ")
			_check("approve_requires_narration", False, "Blank narration should throw")
		except Exception:
			_check("approve_requires_narration", True, "Blank narration blocked")

def test_waive_requires_reason_and_zeroes():
	_new_rule(breach_type="SLA Breach", penalty_type="Fixed Amount", fixed_amount=500, grace_days=0)
	tk = _new_ticket(agreement_status="Failed", response_by=str(add_days(today(), -5)))
	from lavanya_service.tasks.pcomp import compute_penalty_for_ticket
	r = compute_penalty_for_ticket(tk, "SLA Breach", str(add_days(today(), -5)), breach_days=5)
	if r:
		_created.append(("Supplier Penalty Computation", r))
		from lavanya_service.api.prep import waive_penalty
		try:
			waive_penalty(r, reason="")
			_check("waive_requires_reason", False, "Blank reason should throw")
		except Exception:
			_check("waive_requires_reason", True, "Blank reason blocked")
		waive_penalty(r, reason="Goodwill waiver")
		doc = frappe.get_doc("Supplier Penalty Computation", r)
		_check("waive_zeroes_amount", doc.status == "Waived" and doc.final_penalty_amount == 0,
			"Status: %s Amt: %s" % (doc.status, doc.final_penalty_amount))

def test_reject_requires_reason():
	_new_rule(breach_type="SLA Breach", penalty_type="Fixed Amount", fixed_amount=500, grace_days=0)
	tk = _new_ticket(agreement_status="Failed", response_by=str(add_days(today(), -5)))
	from lavanya_service.tasks.pcomp import compute_penalty_for_ticket
	r = compute_penalty_for_ticket(tk, "SLA Breach", str(add_days(today(), -5)), breach_days=5)
	if r:
		_created.append(("Supplier Penalty Computation", r))
		from lavanya_service.api.prep import reject_penalty
		try:
			reject_penalty(r, reason=None)
			_check("reject_requires_reason", False, "Missing reason should throw")
		except Exception:
			_check("reject_requires_reason", True, "Missing reason blocked")
		reject_penalty(r, reason="Not supplier fault")
		doc = frappe.get_doc("Supplier Penalty Computation", r)
		_check("reject_sets_status", doc.status == "Rejected", "Status: " + doc.status)

def run():
	global _PASS, _FAIL, _created
	_PASS = []; _FAIL = []; _created = []
	print("=== P2.1 Tests ===\n")
	for fn in [test_no_penalty_before_grace, test_fixed_after_grace, test_capped_by_max,
			   test_no_duplicate, test_role_gate, test_mgr_review_no_rule, test_report_apis, test_approve_flow,
			   test_approve_requires_narration, test_waive_requires_reason_and_zeroes,
			   test_reject_requires_reason]:
		try: fn()
		except Exception: _check(fn.__name__, False, frappe.get_traceback()[:200])
		_cleanup()
	print("\nResults: {} pass, {} fail".format(len(_PASS), len(_FAIL)))
	if _FAIL: print("Failed: " + ", ".join(_FAIL))
	return {"pass": len(_PASS), "fail": len(_FAIL)}
