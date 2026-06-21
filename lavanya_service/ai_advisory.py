"""AI Advisory for high-risk tickets (reminder engine, Step 6) — ADVISORY ONLY.

Rule-first, deterministic suggestions a human must review and act on. This module
writes ONLY `ai_*` fields and Comments. It never closes a ticket, changes status
or stage, sends a message, or touches payment / stock / warranty records.

Generation is rule-based and offline. A disabled-by-default extension point
(`_llm_advisory`) is left for a future provider; no external LLM is called here.
"""

import frappe
from frappe.utils import now_datetime

from lavanya_service import reminder_engine as re

AI_SOURCE_RULE = "rule-based"

STATUS_NOT_REQUIRED = "Not Required"
STATUS_REVIEW_NEEDED = "Review Needed"
STATUS_SUGGESTED = "Suggested"
STATUS_ACCEPTED = "Accepted"
STATUS_IGNORED = "Ignored"
STATUS_ERROR = "Error"

C_SUGGESTED = "[AI Advisory] suggestion generated"
C_ACCEPTED = "[AI Advisory Accepted] staff accepted suggestion"
C_IGNORED = "[AI Advisory Ignored] staff ignored suggestion"

_AI_FIELDS = (
	"ai_review_status", "ai_suggested_next_action", "ai_suggested_customer_message",
	"ai_risk_reason", "ai_manager_summary", "ai_advisory_source",
	"ai_last_reviewed_at", "ai_reviewed_by",
)

_PRODUCT_AT_STORE_FLOW = "Customer Product at Store"
_REPLACEMENT_FLOW = "Replacement / Exchange"
_RETURN_STAGES = {"Return Requested", "Return Reason Verified", "Brand Notified for Return", "Customer Refund Processed"}
_REIMBURSEMENT_STAGES = {"Brand Reimbursement Pending", "Reimbursement Received"}
_STORE_SERVICE_DIAGNOSIS_STAGES = {"Brand SC Diagnosis Pending", "Brand SC Notified"}
_TECH_STAGES = {"Technician Visit Pending", "Technician Visited - Issue Pending"}
_NO_RESPONSE_STAGES = {"Service Center Follow-up", "Provider Follow-up", "Handed to Service Center"}


def _g(ticket, field):
	return ticket.get(field) if hasattr(ticket, "get") else getattr(ticket, field, None)


# ── candidate detection ─────────────────────────────────────────────────────────
def is_ai_review_candidate(ticket, now=None):
	"""Return (is_candidate, [reason_code, ...]) in priority order. AI advisory runs
	only for high-risk tickets; reasons drive which suggestion template applies."""
	now = now or now_datetime()
	state = re.refresh_ticket_reminder_state(ticket, now=now, save=False)
	overdue = state.get("overdue_status") == "Overdue"
	breached = state.get("customer_promise_status") == "Breached"
	escalation = state.get("computed_escalation_level")
	stage = _g(ticket, "current_service_stage")
	flow = _g(ticket, "service_flow_type")

	reasons = []
	if breached:
		reasons.append("promise_breach")
	if _g(ticket, "is_repeated_complaint") == "Yes":
		reasons.append("repeat_complaint")
	if flow == _PRODUCT_AT_STORE_FLOW and overdue:
		reasons.append("product_at_store_ageing")
	if flow == _PRODUCT_AT_STORE_FLOW and stage in _STORE_SERVICE_DIAGNOSIS_STAGES and overdue:
		reasons.append("store_service_ageing")
	if flow == _REPLACEMENT_FLOW and stage in _REIMBURSEMENT_STAGES and overdue:
		reasons.append("reimbursement_pending")
	if stage in _RETURN_STAGES and overdue:
		reasons.append("return_pending")
	if stage == "Spare Pending" and overdue:
		reasons.append("spare_pending")
	if stage in _TECH_STAGES and overdue:
		reasons.append("technician_pending")
	if stage in _NO_RESPONSE_STAGES and overdue:
		reasons.append("no_response")
	if stage == "Customer Not Reachable" and overdue:
		reasons.append("customer_unreachable")
	if (stage == "Provider Denied") or (flow == "Extended Warranty Claim" and overdue):
		reasons.append("ext_warranty_denied")
	if overdue and stage == "Brand Registered":
		reasons.append("overdue_brand_registered")
	if escalation in ("L3 - Manager Escalation", "L4 - Owner / Brand Manager Escalation"):
		reasons.append("escalated")
	if overdue:
		reasons.append("overdue")

	# de-dupe preserving priority order
	seen, ordered = set(), []
	for r in reasons:
		if r not in seen:
			seen.add(r)
			ordered.append(r)
	return (bool(ordered), ordered)


# ── context (also the future-LLM prompt payload) ────────────────────────────────
def build_ai_ticket_context(ticket, now=None):
	now = now or now_datetime()
	state = re.refresh_ticket_reminder_state(ticket, now=now, save=False)
	_, reasons = is_ai_review_candidate(ticket, now)
	return {
		"ticket": _g(ticket, "name"),
		"status": _g(ticket, "status"),
		"service_flow_type": _g(ticket, "service_flow_type"),
		"current_service_stage": _g(ticket, "current_service_stage"),
		"next_action": _g(ticket, "next_action"),
		"brand": _g(ticket, "brand"),
		"product": _g(ticket, "product_item") or _g(ticket, "product_type"),
		"customer_name": _g(ticket, "customer_name"),
		"pending_reason": _g(ticket, "pending_reason"),
		"is_repeat": _g(ticket, "is_repeated_complaint") == "Yes",
		"overdue_status": state.get("overdue_status"),
		"escalation_level": state.get("computed_escalation_level"),
		"customer_promise_status": state.get("customer_promise_status"),
		"customer_promised_update_at": _g(ticket, "customer_promised_update_at"),
		"reasons": reasons,
	}


# ── rule-based templates ────────────────────────────────────────────────────────
def _customer(ticket):
	return _g(ticket, "customer_name") or "Customer"


_TEMPLATES = {
	"promise_breach": lambda t: {
		"next_action": "Call the customer immediately, apologise, and give a firm next update time.",
		"risk_reason": "Promised update time passed without being given — high disappointment risk.",
		"manager_summary": "Customer promise breached; needs an immediate apology call and a committed update window.",
		"customer_message": "Sorry for the delay in updating you. We are actively checking your service status now and will call you back with a confirmed update by end of day today.",
	},
	"repeat_complaint": lambda t: {
		"next_action": "Route to manager review before any normal closure; verify the earlier fix.",
		"risk_reason": "Repeat complaint indicates an unresolved or recurring issue.",
		"manager_summary": "Repeat complaint — review the previous ticket's resolution before closing again.",
		"customer_message": "We see this issue has recurred and we're sorry for the trouble. A senior team member is reviewing your case and we'll update you shortly.",
	},
	"product_at_store_ageing": lambda t: {
		"next_action": "Check custody / service-centre status and inform the customer of the current position.",
		"risk_reason": "Customer product has been in the store / service process too long.",
		"manager_summary": "Product-at-store ageing past SLA; confirm custody status and give the customer an update.",
		"customer_message": "An update on your product with us: we're confirming the current service status and will inform you of the expected timeline by end of day today.",
	},
	"spare_pending": lambda t: {
		"next_action": "Ask the service centre for a spare-part ETA and inform the customer.",
		"risk_reason": "Spare pending for too long can create customer dissatisfaction.",
		"manager_summary": "Spare pending ageing; chase the part ETA and set customer expectations.",
		"customer_message": "Your repair is awaiting a spare part. We're following up on the part ETA and will share the expected date with you soon.",
	},
	"technician_pending": lambda t: {
		"next_action": "Confirm the technician visit date with the service centre and notify the customer.",
		"risk_reason": "Technician visit pending beyond the expected window.",
		"manager_summary": "Technician visit overdue; confirm the appointment and update the customer.",
		"customer_message": "We're scheduling the technician visit for your complaint and will confirm the date with you shortly.",
	},
	"no_response": lambda t: {
		"next_action": "Escalate the follow-up with the service centre / provider and record the response.",
		"risk_reason": "Service centre / provider has not responded within the follow-up window.",
		"manager_summary": "No response from service centre/provider; escalate the follow-up.",
		"customer_message": "We're following up with the service centre on your case and will update you as soon as we have a confirmed status.",
	},
	"customer_unreachable": lambda t: {
		"next_action": "Try an alternate channel (WhatsApp/alternate number) and record the attempt.",
		"risk_reason": "Customer could not be reached; repeated misses may delay closure.",
		"manager_summary": "Customer unreachable; try alternate contact and log attempts.",
		"customer_message": "We tried to reach you regarding your service request. Please let us know a convenient time to call, or reply here.",
	},
	"ext_warranty_denied": lambda t: {
		"next_action": "Review the extended-warranty decision with the provider and explain options to the customer.",
		"risk_reason": "Extended warranty denied or delayed — needs careful customer handling.",
		"manager_summary": "Extended-warranty claim denied/delayed; manager to confirm options before informing the customer.",
		"customer_message": "We're reviewing the warranty position on your product and will explain the available options to you shortly.",
	},
	"store_service_ageing": lambda t: {
		"next_action": "Follow up with the service centre on the diagnosis status and update the customer.",
		"risk_reason": "Product at store awaiting diagnosis beyond expected time.",
		"manager_summary": "Store service diagnosis pending — chase the service centre for an update.",
		"customer_message": "We're following up with our service centre on your product's diagnostic status and will update you shortly.",
	},
	"reimbursement_pending": lambda t: {
		"next_action": "Follow up with the brand on the pending reimbursement and escalate if delayed.",
		"risk_reason": "Brand reimbursement overdue — may affect replacement closure.",
		"manager_summary": "Brand reimbursement pending beyond SLA; escalate to brand manager if needed.",
		"customer_message": "We're following up with the brand on the reimbursement for your replacement and will keep you posted.",
	},
	"return_pending": lambda t: {
		"next_action": "Check return processing status and update the customer on the expected refund timeline.",
		"risk_reason": "Return processing delayed — customer expecting refund.",
		"manager_summary": "Return process overdue; confirm brand decision or refund status.",
		"customer_message": "Your return request is being processed. We're confirming the expected refund timeline and will update you soon.",
	},
	"overdue_brand_registered": lambda t: {
		"next_action": "Call the service centre and confirm the technician visit / brand ticket progress.",
		"risk_reason": "Follow-up overdue after brand registration.",
		"manager_summary": "Brand-registered ticket overdue; confirm service-centre progress.",
		"customer_message": "Your complaint is registered with the brand and we're confirming the next service step. We'll update you with the technician details soon.",
	},
}

_GENERIC = lambda t: {
	"next_action": "Follow up now: confirm the current status and give the customer an update.",
	"risk_reason": "Follow-up is overdue / escalated and needs attention.",
	"manager_summary": "Overdue/escalated ticket needing follow-up and a customer update.",
	"customer_message": "We're checking the current status of your service request and will update you shortly.",
}


def generate_rule_based_ai_advisory(ticket, now=None):
	"""Deterministic advisory from the highest-priority risk reason. Returns a dict
	with review_status; Not Required when the ticket is not a high-risk candidate."""
	now = now or now_datetime()
	ok, reasons = is_ai_review_candidate(ticket, now)
	if not ok:
		return {"review_status": STATUS_NOT_REQUIRED, "source": AI_SOURCE_RULE, "reasons": []}

	# Optional future LLM enrichment (disabled by default; never raises).
	advisory = _llm_advisory(build_ai_ticket_context(ticket, now)) or _TEMPLATES.get(reasons[0], _GENERIC)(ticket)
	advisory["review_status"] = STATUS_SUGGESTED
	advisory["source"] = advisory.get("source", AI_SOURCE_RULE)
	advisory["reasons"] = reasons
	return advisory


def _llm_advisory(context):
	"""Extension point for a future LLM provider. Disabled by default — returns
	None so the rule-based templates are used. Enable only behind explicit,
	reviewed config; it must still write only ai_* fields via save_ai_advisory."""
	if not frappe.conf.get("lavanya_ai_llm_enabled"):
		return None
	raise NotImplementedError("LLM provider not wired — implement _llm_advisory body or keep lavanya_ai_llm_enabled=False")


# ── persistence (ai_* fields + Comment only) ────────────────────────────────────
def _name(ticket):
	return _g(ticket, "name")


def _has(field):
	return frappe.get_meta("HD Ticket").has_field(field)


def save_ai_advisory(ticket, advisory, add_comment=True):
	"""Persist an advisory into the ai_* fields ONLY, and log one [AI Advisory]
	Comment (guarded so repeat generation never duplicates it)."""
	name = _name(ticket)
	if not name or not frappe.db.exists("HD Ticket", name):
		return
	values = {"ai_advisory_source": advisory.get("source", AI_SOURCE_RULE),
			  "ai_last_reviewed_at": now_datetime()}
	if _has("ai_review_status"):
		values["ai_review_status"] = advisory.get("review_status", STATUS_SUGGESTED)
	for src, field in (
		("next_action", "ai_suggested_next_action"),
		("customer_message", "ai_suggested_customer_message"),
		("risk_reason", "ai_risk_reason"),
		("manager_summary", "ai_manager_summary"),
	):
		if _has(field):
			values[field] = advisory.get(src)
	values = {k: v for k, v in values.items() if _has(k)}
	frappe.db.set_value("HD Ticket", name, values, update_modified=False)

	if add_comment and advisory.get("review_status") == STATUS_SUGGESTED:
		_add_comment_once(name, C_SUGGESTED, advisory.get("risk_reason"))


def _add_comment_once(name, marker, detail=None):
	if frappe.db.exists("Comment", {"reference_doctype": "HD Ticket", "reference_name": name,
									"content": ["like", "%" + marker + "%"]}):
		return False
	text = marker + (" — " + detail if detail else "")
	frappe.get_doc("HD Ticket", name).add_comment("Comment", text)
	return True


# ── whitelisted actions (explicit, permission-scoped) ──────────────────────────
@frappe.whitelist(methods=["POST"])
def generate_ai_advisory(ticket_name):
	"""On-demand: generate + save the rule-based advisory for one ticket. Write
	permission required. Writes only ai_* fields + one Comment."""
	_require_write(ticket_name)
	doc = frappe.get_doc("HD Ticket", ticket_name)
	advisory = generate_rule_based_ai_advisory(doc)
	if advisory.get("review_status") == STATUS_NOT_REQUIRED:
		if _has("ai_review_status"):
			frappe.db.set_value("HD Ticket", ticket_name, "ai_review_status", STATUS_NOT_REQUIRED, update_modified=False)
		return {"ok": True, "review_status": STATUS_NOT_REQUIRED}
	save_ai_advisory(doc, advisory)
	return {"ok": True, "review_status": STATUS_SUGGESTED, "advisory": advisory}


@frappe.whitelist(methods=["POST"])
def accept_ai_suggestion(ticket_name, accepted_field=None, note=None):
	"""Staff accepts the suggestion. Records the decision in ai_* + a Comment ONLY —
	it does NOT change status, stage, or send anything. Staff act manually."""
	_require_write(ticket_name)
	if _has("ai_review_status"):
		frappe.db.set_value("HD Ticket", ticket_name, {
			"ai_review_status": STATUS_ACCEPTED,
			"ai_reviewed_by": frappe.session.user,
			"ai_last_reviewed_at": now_datetime(),
		}, update_modified=False)
	picked = frappe.db.get_value("HD Ticket", ticket_name, accepted_field) if (accepted_field and _has(accepted_field)) else None
	detail = " | ".join([p for p in [accepted_field, picked, note] if p])
	frappe.get_doc("HD Ticket", ticket_name).add_comment("Comment", C_ACCEPTED + (" — " + detail if detail else ""))
	return {"ok": True, "review_status": STATUS_ACCEPTED}


@frappe.whitelist(methods=["POST"])
def ignore_ai_suggestion(ticket_name, note=None):
	"""Staff ignores the suggestion — changes only ai_review_status + logs a Comment."""
	_require_write(ticket_name)
	if _has("ai_review_status"):
		frappe.db.set_value("HD Ticket", ticket_name, {
			"ai_review_status": STATUS_IGNORED,
			"ai_reviewed_by": frappe.session.user,
			"ai_last_reviewed_at": now_datetime(),
		}, update_modified=False)
	frappe.get_doc("HD Ticket", ticket_name).add_comment("Comment", C_IGNORED + (" — " + note if note else ""))
	return {"ok": True, "review_status": STATUS_IGNORED}


@frappe.whitelist()
def get_ai_advisory(ticket_name):
	"""Read-only: stored ai_* fields plus the live candidate flag/reasons."""
	if not frappe.has_permission("HD Ticket", "read", doc=ticket_name):
		frappe.throw("Not permitted", frappe.PermissionError)
	doc = frappe.get_doc("HD Ticket", ticket_name)
	candidate, reasons = is_ai_review_candidate(doc)
	return {
		"review_status": doc.get("ai_review_status") or STATUS_NOT_REQUIRED,
		"suggested_next_action": doc.get("ai_suggested_next_action"),
		"suggested_customer_message": doc.get("ai_suggested_customer_message"),
		"risk_reason": doc.get("ai_risk_reason"),
		"manager_summary": doc.get("ai_manager_summary"),
		"advisory_source": doc.get("ai_advisory_source"),
		"last_reviewed_at": doc.get("ai_last_reviewed_at"),
		"reviewed_by": doc.get("ai_reviewed_by"),
		"is_candidate": candidate,
		"reasons": reasons,
	}


def _require_write(ticket_name):
	if frappe.session.user == "Guest":
		frappe.throw("Not permitted", frappe.PermissionError)
	if not frappe.db.exists("HD Ticket", ticket_name):
		frappe.throw("Ticket not found.")
	if not frappe.has_permission("HD Ticket", "write", doc=ticket_name):
		frappe.throw("Not permitted", frappe.PermissionError)


# ── follow-up flow engine (AI-powered journey stepper) ────────────────────────

_FOLLOWUP_BUTTON_LABELS = {
	"inform_customer": "Inform Now",
	"verify_tech_called": "Verify Call",
	"verify_tech_visit": "Verify Visit",
	"record_sc_followup": "Record",
	"track_part": "Track Part",
	"record_approval": "Record Approval",
	"record_satisfaction": "Record Now",
	"close_ticket": "Close Now",
}

_FOLLOWUP_BUTTON_CLASSES = {
	"track_part": "bg-secondary-container text-secondary",
	"record_approval": "bg-secondary text-on-secondary",
	"record_satisfaction": "bg-tertiary text-on-tertiary",
	"close_ticket": "bg-error text-on-error",
}

_STAGES_PAST_TECH_CALL = {
	"Technician Visited - Issue Pending", "Spare Pending",
	"Service Center Follow-up", "Provider Follow-up", "Handed to Service Center",
	"Provider Denied", "Customer Not Reachable", "Customer Product Delivered",
}

_STAGES_PAST_TECH_VISIT = {
	"Spare Pending", "Service Center Follow-up", "Provider Follow-up",
	"Handed to Service Center", "Provider Denied", "Customer Not Reachable",
	"Customer Product Delivered",
}


def _followup_flow_steps(doc):
	followup_stage = doc.get("followup_stage") or ""
	status = doc.get("status") or ""
	stage = doc.get("current_service_stage") or ""
	has_satisfaction = bool(doc.get("customer_satisfaction_status"))
	has_informed = bool(doc.get("customer_informed_status"))
	has_approval = bool(doc.get("customer_approved_amount"))
	is_closed = status in ("Closed", "Cancelled", "Resolved")
	part_required = doc.get("part_required") in (1, "1", "Yes", True)
	part_done = bool(doc.get("part_name")) and not doc.get("part_delay_reason")
	escalation = doc.get("escalation_level") or ""

	steps = [
		{"key": "inform_customer", "label": "Inform Customer", "icon": "campaign", "is_done": has_informed},
	]

	# Skip verify_tech_called if stage has moved past the call phase
	if stage not in _STAGES_PAST_TECH_CALL:
		steps.append({"key": "verify_tech_called", "label": "Verify Technician Called", "icon": "phone_in_talk",
					  "is_done": followup_stage == "technician_called"})

	if stage not in _STAGES_PAST_TECH_VISIT:
		steps.append({"key": "verify_tech_visit", "label": "Verify Technician Visit", "icon": "handyman",
					  "is_done": followup_stage == "technician_visited"})

	steps.append({"key": "record_sc_followup", "label": "Record SC Follow-up", "icon": "support_agent",
				  "is_done": followup_stage == "sc_followup_done"})

	# Insert part-tracking step when a part is required
	idx = -1
	if part_required:
		idx = len(steps)
		steps.append({"key": "track_part", "label": "Track Part Delivery", "icon": "inventory_2",
					  "is_done": part_done})

	steps.append({"key": "record_approval", "label": "Record Customer Approval", "icon": "contract",
				  "is_done": has_approval})
	steps.append({"key": "record_satisfaction", "label": "Record Satisfaction", "icon": "sentiment_satisfied",
				  "is_done": has_satisfaction})
	steps.append({"key": "close_ticket", "label": "Close Ticket", "icon": "task_alt", "is_done": is_closed})

	# Escalation reorder: move significant steps (SC follow-up, satisfaction, part) earlier
	if escalation in ("L3 - Manager Escalation", "L4 - Owner / Brand Manager Escalation"):
		move_keys = {"record_sc_followup", "record_satisfaction", "track_part"}
		moved = [s for s in steps if s["key"] in move_keys]
		kept = [s for s in steps if s["key"] not in move_keys]
		steps = kept[:1] + moved + kept[1:]

	found = False
	for s in steps:
		if s["is_done"]:
			s["status"] = "completed"
		elif not found:
			found = True
			s["status"] = "current"
		else:
			s["status"] = "pending"
		s["action"] = s["key"]
		s["buttonLabel"] = _FOLLOWUP_BUTTON_LABELS.get(s["key"], s["label"])
		if s["key"] in _FOLLOWUP_BUTTON_CLASSES:
			s["buttonClass"] = _FOLLOWUP_BUTTON_CLASSES[s["key"]]
		s["completedLabel"] = "Done" if s["status"] == "completed" else None
		del s["is_done"]
	return steps


def _followup_alt_actions(doc):
	followup_stage = doc.get("followup_stage") or ""
	escalation = doc.get("escalation_level") or ""
	alt = []
	if followup_stage != "no_technician_update":
		alt.append({"action": "mark_no_update", "label": "Mark No Update", "icon": "warning",
					"buttonClass": "bg-surface-container-highest text-on-surface"})
	if escalation != "L4 - Owner / Brand Manager Escalation":
		alt.append({"action": "escalate_case", "label": "Escalate Case", "icon": "escalator_warning",
					"buttonClass": "bg-error-container text-error"})
	return alt


@frappe.whitelist(methods=["POST"])
def get_followup_flow(ticket_name):
	"""AI engine for the follow-up journey flow stepper.

	Analyzes the ticket's follow-up state and returns structured flow steps
	(completed/current/pending) and available alternative actions. Rule-based
	by default (deterministic, matching the old frontend logic); the LLM
	extension point is available when configured.
	"""
	if not frappe.has_permission("HD Ticket", "read", doc=ticket_name):
		frappe.throw("Not permitted", frappe.PermissionError)
	if not frappe.db.exists("HD Ticket", ticket_name):
		frappe.throw("Ticket not found.")

	doc = frappe.get_doc("HD Ticket", ticket_name)

	steps = _followup_flow_steps(doc)

	llm_result = _llm_followup_advisory(doc, steps)
	if llm_result:
		steps = llm_result.get("steps", steps)

	return {
		"ok": True,
		"steps": steps,
		"alt_actions": _followup_alt_actions(doc),
	}


def _llm_followup_advisory(doc, steps):
	"""Extension point for LLM-powered follow-up flow refinement.
	Disabled by default — returns None so the rule-based flow is used."""
	if not frappe.conf.get("lavanya_ai_llm_enabled"):
		return None
	raise NotImplementedError("LLM provider not wired — implement _llm_followup_advisory body or keep lavanya_ai_llm_enabled=False")
