"""Reminder Rule Resolution Engine tests (reminder engine, Step 3).

Run: bench --site <site> execute lavanya_service.tests.reminder_engine.run

Covers rule resolution (priority / specificity / fallback / disabled), the timing
computations, escalation derivation, customer-update-due, manual-follow-up
preservation, and the old-ticket fallback. Pure-compute tests use in-memory
ticket/rule dicts; the disabled-rule test creates + rolls back real records.
"""

import frappe
from frappe.utils import add_to_date, get_datetime, now_datetime

from lavanya_service import reminder_engine as re
from lavanya_service import stage_rules as sr

_PASS = []
_FAIL = []


def _check(name, cond, detail=""):
	(_PASS if cond else _FAIL).append(name)
	print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" | {detail}" if detail else ""))


def _rule(name, priority=100, **fields):
	base = {"name": name, "priority": priority, "modified": now_datetime(), "enabled": 1}
	base.update(fields)
	return frappe._dict(base)


def _ticket(**fields):
	return frappe._dict(fields)


def run():
	print("Running reminder-engine (Step 3) tests…")
	frappe.set_user("Administrator")
	now = now_datetime()

	# 1. Global fallback when no rule matches → None + hardcoded first-followup.
	t = _ticket(creation=now)
	_check("RE-01 no rule → resolve None", re.resolve_reminder_rule(t, rules=[]) is None)
	nf = re.calculate_next_followup(t, None, now)
	_check(
		"RE-01 fallback first-followup = creation + 24h",
		nf == add_to_date(now, minutes=re.FALLBACK_FIRST_FOLLOWUP_MIN),
		str(nf),
	)

	# 2. Brand + stage rule beats service-flow default (equal priority → specificity).
	t2 = _ticket(brand="LG", current_service_stage="Spare Pending", service_flow_type="Customer Complaint - Site")
	r_brand_stage = _rule("BrandStage", brand="LG", current_service_stage="Spare Pending")
	r_flow = _rule("FlowDefault", service_flow_type="Customer Complaint - Site")
	picked = re.resolve_reminder_rule(t2, rules=[r_flow, r_brand_stage])
	_check("RE-02 brand+stage beats flow default", picked and picked.name == "BrandStage", picked and picked.name)

	# 3. Brand + product rule beats global fallback rule.
	t3 = _ticket(brand="LG", product_type="TV")
	r_brand_prod = _rule("BrandProduct", brand="LG", product_type="TV")
	r_global = _rule("Global")  # no constraints → matches everything, specificity 0
	picked3 = re.resolve_reminder_rule(t3, rules=[r_global, r_brand_prod])
	_check("RE-03 brand+product beats global fallback", picked3 and picked3.name == "BrandProduct", picked3 and picked3.name)
	_check("RE-03b global fallback still matches alone", re.resolve_reminder_rule(t3, rules=[r_global]).name == "Global")

	# 4. Higher priority (lower number) wins over equal-specificity lower priority.
	t4 = _ticket(ticket_type="X")
	r_hi = _rule("Hi", priority=10, ticket_type="X")
	r_lo = _rule("Lo", priority=200, ticket_type="X")
	picked4 = re.resolve_reminder_rule(t4, rules=[r_lo, r_hi])
	_check("RE-04 higher priority wins", picked4 and picked4.name == "Hi", picked4 and picked4.name)

	# 5. Disabled rule is ignored by get_active_rules (real records, rolled back).
	_check("RE-05 disabled rule ignored", _disabled_rule_ignored())

	# 6. Manual next_follow_up_date preserved unless force=True.
	manual_date = add_to_date(now, days=3)
	t6 = _ticket(creation=now, next_follow_up_date=manual_date)
	_check("RE-06 manual follow-up preserved", re.calculate_next_followup(t6, None, now) == get_datetime(manual_date))
	_check(
		"RE-06b force overrides manual",
		re.calculate_next_followup(t6, None, now, force=True) == add_to_date(now, minutes=re.FALLBACK_FIRST_FOLLOWUP_MIN),
	)

	# 7. Due Soon is calculated before stage due.
	t7 = _ticket(creation=now, modified=now, current_service_stage="Spare Pending")
	due = re.calculate_stage_due_at(t7, None, now)
	soon = re.calculate_due_soon_at(t7, None, now)
	_check("RE-07 due-soon before stage-due", due and soon and soon < due, f"soon={soon} due={due}")

	# 8. Escalation derives from overdue age.
	def esc_for(hours_overdue):
		tk = _ticket(stage_due_at=add_to_date(now, hours=-hours_overdue), current_service_stage="Brand Registered")
		return re.derive_escalation_level(tk, None, now)

	_check("RE-08a overdue <1d → Coordinator", esc_for(10) == "Coordinator", esc_for(10))
	_check("RE-08b overdue 2d → Manager", esc_for(48) == "Manager", esc_for(48))
	_check("RE-08c overdue 5d → Owner", esc_for(120) == "Owner", esc_for(120))
	t8_notdue = _ticket(stage_due_at=add_to_date(now, days=2), current_service_stage="Brand Registered")
	_check("RE-08d not overdue → None", re.derive_escalation_level(t8_notdue, None, now) == "None")

	# 9. Customer promise breach raises escalation even when not overdue.
	t9 = _ticket(
		stage_due_at=add_to_date(now, days=2),  # Not Due
		current_service_stage="Brand Registered",
		customer_promised_update_at=add_to_date(now, hours=-2),  # promised time passed
		customer_promise_status="Pending",
	)
	_check("RE-09 promise breach → ≥ Coordinator", re.derive_escalation_level(t9, None, now) == "Coordinator", re.derive_escalation_level(t9, None, now))

	# 10. Customer update due when rule requires it and none has happened.
	r_update = _rule("Update", customer_update_required=1, customer_update_every_minutes=120)
	t10 = _ticket(current_service_stage="Brand Registered")  # no customer_informed_at
	_check("RE-10 update due when none yet", re.derive_customer_update_due(t10, r_update, now) is True)
	t10b = _ticket(customer_informed_at=now)  # just informed
	_check("RE-10b not due right after update", re.derive_customer_update_due(t10b, r_update, now) is False)
	_check("RE-10c no rule → not due", re.derive_customer_update_due(t10, None, now) is False)

	# 11. Old ticket without rule/stage fields → engine falls back to next_follow_up_date.
	old = _ticket(creation=add_to_date(now, days=-10), modified=add_to_date(now, days=-10),
		next_follow_up_date=add_to_date(now, days=-2))  # past due, no stage
	state = re.refresh_ticket_reminder_state(old, now=now, rules=[])
	_check("RE-11 old ticket: no rule applied", state["reminder_rule_applied"] is None)
	_check("RE-11b old ticket: no fabricated stage-due", state["computed_stage_due_at"] is None, str(state["computed_stage_due_at"]))
	_check("RE-11c old ticket: overdue via next_follow_up fallback", state["overdue_status"] == "Overdue", state["overdue_status"])

	print(f"\nTOTAL: {len(_PASS) + len(_FAIL)} | PASS: {len(_PASS)} | FAIL: {len(_FAIL)}")
	if _FAIL:
		print("FAILED: " + ", ".join(_FAIL))
	print("OVERALL: " + ("PASS" if not _FAIL else "FAIL"))
	return {"total": len(_PASS) + len(_FAIL), "failed": len(_FAIL)}


def _disabled_rule_ignored():
	"""Create one enabled + one disabled rule (Data match fields only, no Links),
	confirm get_active_rules() returns only the enabled one, then roll back."""
	created = []
	try:
		for name, enabled in (("ZZTest Enabled", 1), ("ZZTest Disabled", 0)):
			if not frappe.db.exists(re.REMINDER_RULE, name):
				doc = frappe.get_doc({
					"doctype": re.REMINDER_RULE,
					"rule_name": name,
					"enabled": enabled,
					"priority": 100,
					"ticket_type": "ZZTESTTYPE",
				}).insert(ignore_permissions=True)
				created.append(doc.name)
		frappe.local._lavanya_reminder_rules = None  # bust the per-request cache
		active = {r.name for r in re.get_active_rules()}
		ok = "ZZTest Enabled" in active and "ZZTest Disabled" not in active
		# Resolution against a ticket matching both only returns the enabled rule.
		tk = _ticket(ticket_type="ZZTESTTYPE")
		picked = re.resolve_reminder_rule(tk)
		ok = ok and picked is not None and picked.name == "ZZTest Enabled"
		return ok
	finally:
		for name in created:
			frappe.delete_doc(re.REMINDER_RULE, name, ignore_permissions=True, force=True)
		frappe.local._lavanya_reminder_rules = None
		frappe.db.rollback()
