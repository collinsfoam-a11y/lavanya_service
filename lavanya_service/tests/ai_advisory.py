"""AI Advisory tests (reminder engine, Step 6) — advisory-only safety.

Run: bench --site <site> execute lavanya_service.tests.ai_advisory.run

Pure-logic checks use in-memory ticket dicts; the write-path checks (generate /
accept / ignore, and the only-ai_*-fields guarantee) use a real ticket and verify
via same-transaction reads. Everything rolls back — no commit, no cleanup.
"""

import frappe
from frappe.utils import add_to_date, now_datetime

from lavanya_service import ai_advisory as ai

_PASS = []
_FAIL = []


def _check(name, cond, detail=""):
	(_PASS if cond else _FAIL).append(name)
	print(f"[{'PASS' if cond else 'FAIL'}] {name}" + (f" | {detail}" if detail else ""))


def _t(**fields):
	return frappe._dict(fields)


def _new_ticket(**set_values):
	cust = frappe.get_all("HD Customer", limit=1)
	doc = frappe.new_doc("HD Ticket")
	doc.subject = "Step6 AI test"
	doc.ticket_type = "Customer Complaint - Site"
	if cust:
		doc.customer = cust[0].name
	doc.insert(ignore_permissions=True)
	for f, v in set_values.items():
		frappe.db.set_value("HD Ticket", doc.name, f, v, update_modified=False)
	return doc.name


def run():
	print("Running AI advisory (Step 6) tests…")
	frappe.set_user("Administrator")
	frappe.local._lavanya_reminder_rules = None
	now = now_datetime()
	try:
		# 1. Non-risk ticket → Not Required.
		calm = _t(current_service_stage="Brand Registered", stage_due_at=add_to_date(now, days=2),
				  customer_promise_status="None", is_repeated_complaint="No", modified=now, creation=now)
		ok1, _ = ai.is_ai_review_candidate(calm, now)
		adv1 = ai.generate_rule_based_ai_advisory(calm, now)
		_check("AI-01 non-risk not a candidate", ok1 is False)
		_check("AI-01b non-risk → Not Required", adv1["review_status"] == ai.STATUS_NOT_REQUIRED)

		# 2. Overdue ticket → candidate + Suggested with text.
		od = _t(current_service_stage="Brand Registered", stage_due_at=add_to_date(now, hours=-30),
				modified=now, creation=now)
		ok2, _ = ai.is_ai_review_candidate(od, now)
		adv2 = ai.generate_rule_based_ai_advisory(od, now)
		_check("AI-02 overdue is candidate", ok2 is True)
		_check("AI-02b overdue → Suggested + next action", adv2["review_status"] == ai.STATUS_SUGGESTED and bool(adv2.get("next_action")), adv2.get("next_action"))

		# 3. Promise breach → risk reason + immediate-call next action.
		pb = _t(current_service_stage="Brand Registered", stage_due_at=add_to_date(now, days=2),
				customer_promised_update_at=add_to_date(now, hours=-2), customer_promise_status="Pending",
				modified=now, creation=now)
		adv3 = ai.generate_rule_based_ai_advisory(pb, now)
		_check("AI-03 promise breach risk reason", "promis" in (adv3.get("risk_reason") or "").lower(), adv3.get("risk_reason"))
		_check("AI-03b promise breach next action = call now", "call" in (adv3.get("next_action") or "").lower())

		# 4. Repeat complaint → manager-style advisory.
		rp = _t(current_service_stage="Brand Registered", stage_due_at=add_to_date(now, days=2),
				is_repeated_complaint="Yes", modified=now, creation=now)
		adv4 = ai.generate_rule_based_ai_advisory(rp, now)
		_check("AI-04 repeat → manager review", "manager" in (adv4.get("next_action", "") + adv4.get("manager_summary", "")).lower(), adv4.get("next_action"))

		# 5. Product-at-store ageing → custody follow-up.
		ps = _t(service_flow_type="Customer Product at Store", current_service_stage="Handed to Service Center",
				stage_due_at=add_to_date(now, hours=-30), modified=now, creation=now)
		adv5 = ai.generate_rule_based_ai_advisory(ps, now)
		_check("AI-05 product-at-store custody follow-up", "custody" in (adv5.get("next_action") or "").lower(), adv5.get("next_action"))

		# 6. generate_ai_advisory writes ONLY ai_* fields.
		name = _new_ticket(current_service_stage="Brand Registered", stage_due_at=add_to_date(now, hours=-30))
		before = frappe.db.get_value("HD Ticket", name,
			["status", "current_service_stage", "next_action", "next_follow_up_date", "pending_reason"], as_dict=True)
		res = ai.generate_ai_advisory(name)
		after = frappe.db.get_value("HD Ticket", name,
			["status", "current_service_stage", "next_action", "next_follow_up_date", "pending_reason",
			 "ai_review_status", "ai_suggested_next_action"], as_dict=True)
		_check("AI-06 generated Suggested", res.get("review_status") == ai.STATUS_SUGGESTED and after.ai_review_status == "Suggested")
		_check("AI-06b ai_* text written", bool(after.ai_suggested_next_action))
		_check("AI-06c operational fields untouched",
			(before.status, before.current_service_stage, before.next_action, before.next_follow_up_date, before.pending_reason)
			== (after.status, after.current_service_stage, after.next_action, after.next_follow_up_date, after.pending_reason))

		# 7. Accept does not close / change status / change stage.
		ai.accept_ai_suggestion(name, accepted_field="ai_suggested_next_action", note="will call")
		acc = frappe.db.get_value("HD Ticket", name, ["status", "current_service_stage", "ai_review_status"], as_dict=True)
		_check("AI-07 accept → Accepted, state unchanged",
			acc.ai_review_status == "Accepted" and acc.status == before.status and acc.current_service_stage == before.current_service_stage)
		_check("AI-07b accepted comment logged",
			frappe.db.exists("Comment", {"reference_doctype": "HD Ticket", "reference_name": name, "content": ["like", "%" + ai.C_ACCEPTED + "%"]}) is not None)

		# 8. Ignore changes only ai_review_status + logs a Comment.
		name2 = _new_ticket(current_service_stage="Brand Registered", stage_due_at=add_to_date(now, hours=-30))
		ai.generate_ai_advisory(name2)
		s_before = frappe.db.get_value("HD Ticket", name2, ["status", "current_service_stage"], as_dict=True)
		ai.ignore_ai_suggestion(name2, note="not relevant")
		ig = frappe.db.get_value("HD Ticket", name2, ["status", "current_service_stage", "ai_review_status"], as_dict=True)
		_check("AI-08 ignore → Ignored, state unchanged",
			ig.ai_review_status == "Ignored" and ig.status == s_before.status and ig.current_service_stage == s_before.current_service_stage)
		_check("AI-08b ignored comment logged",
			frappe.db.exists("Comment", {"reference_doctype": "HD Ticket", "reference_name": name2, "content": ["like", "%" + ai.C_IGNORED + "%"]}) is not None)

		# 9. Blank-safe read for the drawer (non-candidate fresh ticket).
		name3 = _new_ticket()
		view = ai.get_ai_advisory(name3)
		_check("AI-09 blank read safe", isinstance(view, dict) and view.get("review_status") == ai.STATUS_NOT_REQUIRED and view.get("risk_reason") in (None, ""))

		# ── follow-up flow engine tests ──────────────────────────────────────────
		# 10. _followup_flow_steps — empty ticket, all pending.
		empty_doc = _t(followup_stage="", status="New", current_service_stage="Brand Registered",
					   customer_satisfaction_status="", customer_informed_status="",
					   customer_approved_amount="", part_required="No", escalation_level="None")
		steps0 = ai._followup_flow_steps(empty_doc)
		_check("AI-10 followup flow — all pending", len(steps0) >= 5 and all(s["status"] == "pending" for s in steps0 if s["status"] != "current") and any(s["status"] == "current" for s in steps0))
		_check("AI-10b followup flow — first step is current and inform_customer", steps0[0]["key"] == "inform_customer" and steps0[0]["status"] == "current")

		# 11. _followup_flow_steps — partially completed.
		semi_doc = _t(followup_stage="technician_called", status="Open",
					  current_service_stage="Technician Visit Pending",
					  customer_satisfaction_status="", customer_informed_status="Informed by Call",
					  customer_approved_amount="500", part_required="No", escalation_level="None")
		steps1 = ai._followup_flow_steps(semi_doc)
		inform = [s for s in steps1 if s["key"] == "inform_customer"]
		_check("AI-11 followup flow — inform is completed when informed", len(inform) == 1 and inform[0]["status"] == "completed")
		tech_call = [s for s in steps1 if s["key"] == "verify_tech_called"]
		_check("AI-11b followup flow — tech called is completed when stage matched", len(tech_call) == 1 and tech_call[0]["status"] == "completed")
		current = [s for s in steps1 if s["status"] == "current"]
		_check("AI-11c followup flow — exactly one current step", len(current) == 1, "current: " + current[0]["key"] if current else "none")

		# 12. _followup_flow_steps — full closure (all completed).
		closed_doc = _t(followup_stage="sc_followup_done", status="Closed",
						current_service_stage="Customer Product Delivered",
						customer_satisfaction_status="Satisfied", customer_informed_status="Informed by Call",
						customer_approved_amount="500", part_required="No", escalation_level="None")
		steps2 = ai._followup_flow_steps(closed_doc)
		done_all = [s for s in steps2 if s["status"] != "completed"]
		_check("AI-12 followup flow — closed ticket all completed", len(done_all) == 0, "non-completed: " + ", ".join(s["key"] + "=" + s["status"] for s in done_all))

		# 13. _followup_flow_steps — part tracking step inserted when part_required.
		part_doc = _t(followup_stage="", status="Open", current_service_stage="Spare Pending",
					  customer_satisfaction_status="", customer_informed_status="Informed by Call",
					  customer_approved_amount="", part_required="Yes", part_name="", part_delay_reason="",
					  escalation_level="None")
		steps3 = ai._followup_flow_steps(part_doc)
		part_step = [s for s in steps3 if s["key"] == "track_part"]
		_check("AI-13 followup flow — part step exists when part_required=Yes", len(part_step) == 1)
		_check("AI-13b followup flow — part step not done when part_name empty", len(part_step) == 1 and part_step[0]["status"] != "completed")

		# 14. _followup_flow_steps — tech steps skipped when stage is past.
		past_doc = _t(followup_stage="", status="Open", current_service_stage="Service Center Follow-up",
					  customer_satisfaction_status="", customer_informed_status="",
					  customer_approved_amount="", part_required="No", escalation_level="None")
		steps4 = ai._followup_flow_steps(past_doc)
		keys4 = [s["key"] for s in steps4]
		_check("AI-14 followup flow — skip tech call when past tech stages", "verify_tech_called" not in keys4, "keys: " + ", ".join(keys4))
		_check("AI-14b followup flow — skip tech visit when past tech stages", "verify_tech_visit" not in keys4)

		# 15. _followup_flow_steps — escalation reorder.
		esc_doc = _t(followup_stage="", status="Open", current_service_stage="Brand Registered",
					 customer_satisfaction_status="", customer_informed_status="",
					 customer_approved_amount="", part_required="No",
					 escalation_level="L3 - Manager Escalation")
		steps5 = ai._followup_flow_steps(esc_doc)
		keys5 = [s["key"] for s in steps5]
		sc_idx = keys5.index("record_sc_followup") if "record_sc_followup" in keys5 else 99
		sat_idx = keys5.index("record_satisfaction") if "record_satisfaction" in keys5 else 99
		_check("AI-15 followup flow — escalation moves SC follow-up and satisfaction earlier", sc_idx < len(keys5) - 3 and sat_idx < len(keys5) - 1,
			   "sc_followup_idx=" + str(sc_idx) + " sat_idx=" + str(sat_idx))

		# 16. _followup_alt_actions — normal case.
		normal_doc = _t(followup_stage="", escalation_level="None")
		alt = ai._followup_alt_actions(normal_doc)
		_check("AI-16 alt actions — both available when no restrictions", len(alt) == 2, "alt count=" + str(len(alt)))
		alt_keys = [a["action"] for a in alt]
		_check("AI-16b alt actions — mark_no_update present", "mark_no_update" in alt_keys)
		_check("AI-16c alt actions — escalate_case present", "escalate_case" in alt_keys)

		# 17. _followup_alt_actions — restricted case.
		restricted_doc = _t(followup_stage="no_technician_update", escalation_level="L4 - Owner / Brand Manager Escalation")
		alt2 = ai._followup_alt_actions(restricted_doc)
		_check("AI-17 alt actions — none when at max restrictions", len(alt2) == 0, "alt count=" + str(len(alt2)))

		# 18. get_followup_flow read-only — verify shape.
		name4 = _new_ticket(followup_stage="technician_called", current_service_stage="Technician Visit Pending",
							customer_informed_status="Informed by Call")
		flow = ai.get_followup_flow(name4)
		_check("AI-18 get_followup_flow returns ok", flow.get("ok") is True)
		_check("AI-18b get_followup_flow has steps", isinstance(flow.get("steps"), list) and len(flow["steps"]) > 0)
		_check("AI-18c get_followup_flow has alt_actions", isinstance(flow.get("alt_actions"), list))
		flow_keys = {s["key"] for s in flow["steps"]}
		_check("AI-18d get_followup_flow — core steps present", "inform_customer" in flow_keys and "record_sc_followup" in flow_keys and "close_ticket" in flow_keys)

		# ── end follow-up flow engine tests ──────────────────────────────────────

		print(f"\nTOTAL: {len(_PASS) + len(_FAIL)} | PASS: {len(_PASS)} | FAIL: {len(_FAIL)}")
		if _FAIL:
			print("FAILED: " + ", ".join(_FAIL))
		print("OVERALL: " + ("PASS" if not _FAIL else "FAIL"))
		return {"total": len(_PASS) + len(_FAIL), "failed": len(_FAIL)}
	finally:
		frappe.db.rollback()
		print("TRANSACTION ROLLED BACK - no records persisted")
