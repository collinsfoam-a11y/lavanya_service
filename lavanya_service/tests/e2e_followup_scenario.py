"""E2E scenario: Fidha → LG TV complaint → brand registration → full follow-up journey.
Tests every quick action, every follow-up stage transition, all alternative inputs,
escalation ladder, satisfaction recording, AI advisory, and follow-up flow engine.

Usage: bench --site lavanya-dev.localhost execute lavanya_service.tests.e2e_followup_scenario.run
"""
import frappe
from frappe.utils import add_days, now_datetime, today
import json

TICKET = None
CUST = None
PASS = []
FAIL = []
SERVICE_CENTER = None
SERVICE_CENTER_NAME = "LG Service Center Kozhikode - TEST"


def _create_service_center():
    global SERVICE_CENTER
    if frappe.db.exists("Service Center Master", SERVICE_CENTER_NAME):
        SERVICE_CENTER = SERVICE_CENTER_NAME
        return
    doc = frappe.new_doc("Service Center Master")
    doc.service_center_name = SERVICE_CENTER_NAME
    doc.brand = "LG"
    doc.insert(ignore_permissions=True)
    SERVICE_CENTER = doc.name
    print(f"  Created service center: {SERVICE_CENTER}")


def _check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    status = "PASS" if cond else "FAIL"
    print(f"  [{status}] {name}" + (f" | {detail}" if detail else ""))


def _login_as(user):
    frappe.set_user(user)
    frappe.local.session.user = user


def _create_customer():
    global CUST
    name = f"Fidha-TEST-{now_datetime().strftime('%H%M%S')}"
    phone = f"9999{now_datetime().strftime('%H%M%S')}"[:10]
    doc = frappe.new_doc("HD Customer")
    doc.customer_name = name
    doc.phone = phone
    doc.insert(ignore_permissions=True)
    CUST = doc.name
    print(f"  Created customer: {CUST}")


def _create_ticket():
    global TICKET
    _create_customer()
    _create_service_center()
    phone = f"9999{now_datetime().strftime('%H%M%S')}"[:10]
    doc = frappe.new_doc("HD Ticket")
    doc.subject = f"Fidha / LG LED TV 32LM563 - Not Working"
    doc.ticket_type = "Customer Complaint - Site"
    doc.priority = "Medium"
    doc.customer = CUST
    doc.customer_name = "Fidha"
    doc.phone_1 = phone
    doc.description = "TV not working - no power. Purchased 12-11-2024 from Lavanya eMart Koduvally"
    doc.product_type = "TV"
    doc.brand = "LG"
    doc.model_no = "32LM563"
    doc.warranty_status = "In Warranty"
    doc.address = "Karoonhiyi(h), Valiyaparamba, Koduvally"
    doc.pincode = "673572"
    doc.complaint_source = "Phone Call"
    doc.insert(ignore_permissions=True)
    TICKET = doc.name
    print(f"  Created ticket: {TICKET}")
    return doc


def test_01_create_ticket():
    """Step 1: Create the complaint ticket"""
    print("\n=== 1. Create Ticket ===")
    doc = _create_ticket()
    _check("1a Ticket created", bool(TICKET), TICKET)
    _check("1b Status is New", doc.status == "New", doc.status)
    _check("1c Customer name set", doc.customer_name == "Fidha", doc.customer_name)
    _check("1d Product type set", doc.product_type == "TV", doc.product_type)
    _check("1e Brand set", doc.brand == "LG", doc.brand)
    _check("1f Warranty In Warranty", doc.warranty_status == "In Warranty", doc.warranty_status)
    _check("1g Pincode set", doc.pincode == "673572", doc.pincode)
    _check("1h Ticket type", doc.ticket_type == "Customer Complaint - Site", doc.ticket_type)
    _check("1i followup_stage = registration_done (field default)", doc.get("followup_stage") == "registration_done", str(doc.get("followup_stage")))
    _check("1j escalation_level None", doc.get("escalation_level") in (None, "None"), str(doc.get("escalation_level")))


def test_02_register_brand_complaint():
    """Step 2: Register the brand complaint"""
    print("\n=== 2. Register Brand Complaint ===")
    from lavanya_service.workflow.quick_actions import register_brand_complaint
    _login_as("uat.coordinator@lavanya.local")
    frappe.db.set_value("HD Ticket", TICKET, "followup_stage", "")
    frappe.db.set_value("HD Ticket", TICKET, "escalation_level", None)
    TICKET_DOC = frappe.get_doc("HD Ticket", TICKET)

    # Test: missing required fields should throw
    try:
        register_brand_complaint(TICKET)
        _check("2a Missing brand_ticket_number throws", False, "should have thrown")
    except Exception as e:
        _check("2a Missing brand_ticket_number throws", "required" in str(e).lower(), str(e)[:60])

    try:
        register_brand_complaint(TICKET, brand_ticket_number="BRN-LG-001")
        _check("2b Missing registration_date throws", False, "should have thrown")
    except Exception as e:
        _check("2b Missing registration_date throws", "required" in str(e).lower(), str(e)[:60])

    # §3: next_follow_up_date is now auto-derived from the Reminder Rule when the
    # operator omits it (no longer required). Single call with all fields.
    result = register_brand_complaint(
        TICKET,
        brand_ticket_number="BRN-LG-001",
        registration_date=today(),
        service_center=SERVICE_CENTER,
    )
    _check("2c next_follow_up_date auto-derived when omitted", bool(result.get("ok")), str(result)[:60])
    _check("2c2 auto next_follow_up_date is set",
           bool(frappe.db.get_value("HD Ticket", TICKET, "next_follow_up_date")),
           str(frappe.db.get_value("HD Ticket", TICKET, "next_follow_up_date")))

    _check("2d Brand registered ok", result.get("ok"), str(result))
    _check("2e Status Brand Registered", result.get("status") == "Brand Registered", result.get("status"))

    doc = frappe.get_doc("HD Ticket", TICKET)
    _check("2f brand_ticket_number set", doc.brand_ticket_number == "BRN-LG-001", doc.brand_ticket_number)
    _check("2g service_center set", doc.service_center == SERVICE_CENTER, doc.service_center)
    _check("2h followup_stage = registration_done", doc.followup_stage == "registration_done", str(doc.followup_stage))
    _check("2i pending_reason Service Follow-up Required", doc.pending_reason == "Service Follow-up Required", doc.pending_reason)
    _check("2j next_follow_up_date set", bool(doc.next_follow_up_date), str(doc.next_follow_up_date))
    _check("2j2 followup_log has entry", len(doc.followup_log) > 0, str(len(doc.followup_log)))

    # Test: block on final status ticket
    frappe.db.set_value("HD Ticket", TICKET, "status", "Closed")
    try:
        register_brand_complaint(TICKET, brand_ticket_number="BRN-LG-002", registration_date=today(), next_follow_up_date=today())
        _check("2k Block on Closed ticket", False, "should have thrown")
    except Exception as e:
        _check("2k Block on Closed ticket", "closed" in str(e).lower(), str(e)[:60])

    # Reset status
    frappe.db.set_value("HD Ticket", TICKET, "status", "Brand Registered")


def test_03_verify_technician_called():
    """Step 3: Verify technician called"""
    print("\n=== 3. Verify Technician Called ===")
    from lavanya_service.workflow.quick_actions import verify_technician_called, verify_technician_visit
    _login_as("uat.coordinator@lavanya.local")

    # Set up: advance followup_stage to technician_call_pending-like state
    frappe.db.set_value("HD Ticket", TICKET, "followup_stage", "technician_call_pending")

    result = verify_technician_called(TICKET, technician_name="Ramesh", notes="Confirmed call - visit scheduled")
    _check("3a Verify tech call ok", result.get("ok"), str(result))
    doc = frappe.get_doc("HD Ticket", TICKET)
    _check("3b followup_stage = technician_called", doc.followup_stage == "technician_called", str(doc.followup_stage))
    _check("3c last_followup_summary set", bool(doc.last_followup_summary), str(doc.last_followup_summary)[:50])
    _check("3d last_followup_at set", bool(doc.last_followup_at), str(doc.last_followup_at))

    # Test: call without optional params (re-entry requires notes)
    frappe.db.set_value("HD Ticket", TICKET, "followup_stage", "technician_call_pending")
    result2 = verify_technician_called(TICKET, notes="Re-entry test")
    _check("3e Verify tech call without optional params ok", result2.get("ok"), str(result2))
    doc2 = frappe.get_doc("HD Ticket", TICKET)
    _check("3f followup_stage still technician_called", doc2.followup_stage == "technician_called", str(doc2.followup_stage))


def test_04_verify_technician_visit():
    """Step 4: Verify technician visit"""
    print("\n=== 4. Verify Technician Visit ===")
    from lavanya_service.workflow.quick_actions import verify_technician_visit
    _login_as("uat.coordinator@lavanya.local")

    frappe.db.set_value("HD Ticket", TICKET, "followup_stage", "technician_visit_pending")

    result = verify_technician_visit(TICKET, technician_name="Ramesh", visit_result="Visited - Issue diagnosed as panel fault", notes="Need spare panel")
    _check("4a Verify tech visit ok", result.get("ok"), str(result))
    doc = frappe.get_doc("HD Ticket", TICKET)
    _check("4b followup_stage = technician_visited", doc.followup_stage == "technician_visited", str(doc.followup_stage))

    # Test: minimal params (re-entry requires notes)
    frappe.db.set_value("HD Ticket", TICKET, "followup_stage", "technician_visit_pending")
    result2 = verify_technician_visit(TICKET, notes="Re-entry test")
    _check("4c Verify tech visit without optional params ok", result2.get("ok"), str(result2))
    doc2 = frappe.get_doc("HD Ticket", TICKET)
    _check("4d followup_stage still technician_visited", doc2.followup_stage == "technician_visited", str(doc2.followup_stage))


def test_05_record_sc_followup():
    """Step 5: Record service center follow-up"""
    print("\n=== 5. Record SC Follow-up ===")
    from lavanya_service.workflow.quick_actions import record_sc_followup
    _login_as("uat.coordinator@lavanya.local")

    # Test: missing customer_informed_status should throw
    try:
        record_sc_followup(TICKET, follow_up_result="Part pending")
        _check("5a Missing customer_informed_status throws", False, "should have thrown")
    except Exception as e:
        _check("5a Missing customer_informed_status throws", "required" in str(e).lower(), str(e)[:60])

    # Test each follow_up_result option
    for result_val in ["Service center contacted", "Technician assigned", "Customer not reachable",
                        "Service completed", "Part pending", "Approval pending"]:
        frappe.db.set_value("HD Ticket", TICKET, "followup_stage", "sc_followup_done")
        try:
            r = record_sc_followup(TICKET, follow_up_result=result_val, customer_informed_status="Informed by Call", notes=f"Test {result_val}")
            _check(f"5b SC follow-up '{result_val}' ok", r.get("ok"), str(r.get("message", ""))[:50])
        except Exception as e:
            _check(f"5b SC follow-up '{result_val}' FAILED", False, str(e)[:80])

    # Test each customer_informed_status option
    informed_options = ["Informed by Call", "Informed by WhatsApp", "Informed by SMS", "Customer Not Reachable"]
    for status_val in informed_options:
        try:
            r = record_sc_followup(TICKET, follow_up_result="Service center contacted", customer_informed_status=status_val, notes=f"Test {status_val}")
            _check(f"5c Customer informed '{status_val}' ok", r.get("ok"), str(r.get("message", ""))[:50])
        except Exception as e:
            _check(f"5c Customer informed '{status_val}' FAILED", False, str(e)[:80])

    doc = frappe.get_doc("HD Ticket", TICKET)
    _check("5d last_service_center_followup set", bool(doc.last_service_center_followup), str(doc.last_service_center_followup))


def test_06_inform_customer():
    """Step 6: Inform customer with all channels"""
    print("\n=== 6. Inform Customer ===")
    from lavanya_service.workflow.quick_actions import inform_customer
    _login_as("uat.coordinator@lavanya.local")

    # Set an AI suggested message
    frappe.db.set_value("HD Ticket", TICKET, "ai_suggested_customer_message", "We are checking your TV status and will update you soon.")

    # Test each channel
    for channel in ["Phone", "WhatsApp", "SMS", "Email"]:
        try:
            r = inform_customer(TICKET, channel=channel, message=f"Test message via {channel}", notes=f"Test {channel}")
            _check(f"6a Inform via {channel} ok", r.get("ok"), str(r.get("message", ""))[:50])
            doc = frappe.get_doc("HD Ticket", TICKET)
            _check(f"6b {channel} → stage customer_informed", doc.followup_stage == "customer_informed", str(doc.followup_stage))
            _check(f"6c {channel} customer_informed=Yes", doc.customer_informed == "Yes", str(doc.customer_informed))
        except Exception as e:
            _check(f"6a Inform via {channel} FAILED", False, str(e)[:80])

    # Test: missing channel should throw
    try:
        inform_customer(TICKET)
        _check("6d Missing channel throws", False, "should have thrown")
    except Exception as e:
        _check("6d Missing channel throws", "required" in str(e).lower(), str(e)[:60])

    # Test: inform without message (auto-wires AI message, re-entry needs notes)
    frappe.db.set_value("HD Ticket", TICKET, "followup_stage", "customer_informed")
    r3 = inform_customer(TICKET, channel="WhatsApp", notes="Re-entry test AI message")
    _check("6e Inform without message ok", r3.get("ok"), str(r3.get("message", ""))[:50])
    doc3 = frappe.get_doc("HD Ticket", TICKET)
    _check("6e AI message auto-wired", doc3.last_followup_summary and "AI message" in (doc3.last_followup_summary or ""), str(doc3.last_followup_summary or "")[:80])


def test_07_mark_no_update_and_escalate():
    """Step 7: Mark no update + escalation ladder"""
    print("\n=== 7. Mark No Update & Escalate ===")
    from lavanya_service.workflow.quick_actions import mark_no_update, escalate_case
    _login_as("uat.coordinator@lavanya.local")

    # Test escalation chain: consecutive no-updates escalate through all levels
    frappe.db.set_value("HD Ticket", TICKET, "escalation_level", "None")
    frappe.db.set_value("HD Ticket", TICKET, "no_update_count", 0)
    for idx, expected_esc in enumerate(["L1 - Agent Follow-up", "L2 - Coordinator Escalation", "L3 - Manager Escalation", "L4 - Owner / Brand Manager Escalation"]):
        r = mark_no_update(TICKET, notes=f"Test no update #{expected_esc}")
        _check(f"7a Mark no update → {expected_esc}", r.get("ok"), str(r.get("message", ""))[:50])
        doc = frappe.get_doc("HD Ticket", TICKET)
        _check(f"7b escalation_level = {expected_esc}", doc.escalation_level == expected_esc, str(doc.escalation_level))
        _check(f"7c no_update_count incremented", doc.no_update_count == idx + 1, str(doc.no_update_count))
        _check(f"7d followup_stage = no_technician_update", doc.followup_stage == "no_technician_update", str(doc.followup_stage))

    # Test escalate_case through all levels
    frappe.db.set_value("HD Ticket", TICKET, "escalation_level", "None")
    for expected_esc in ["L1 - Agent Follow-up", "L2 - Coordinator Escalation", "L3 - Manager Escalation", "L4 - Owner / Brand Manager Escalation"]:
        r = escalate_case(TICKET, reason=f"Testing escalation to {expected_esc}")
        _check(f"7e Escalate case → {expected_esc}", r.get("ok"), str(r.get("message", ""))[:50])
        doc = frappe.get_doc("HD Ticket", TICKET)
        _check(f"7f escalation_level = {expected_esc}", doc.escalation_level == expected_esc, str(doc.escalation_level))

    # Test escalate_case without reason throws
    try:
        frappe.db.set_value("HD Ticket", TICKET, "escalation_level", "None")
        escalate_case(TICKET)
        _check("7g Escalate without reason throws", False, "should have thrown")
    except Exception as e:
        _check("7g Escalate without reason throws", "required" in str(e).lower(), str(e)[:60])


def test_08_record_satisfaction():
    """Step 8: Record customer satisfaction with all options"""
    print("\n=== 8. Record Satisfaction ===")
    from lavanya_service.workflow.quick_actions import record_satisfaction
    _login_as("uat.coordinator@lavanya.local")

    # Test each satisfaction status
    for sat in ["Satisfied", "Not Satisfied", "Customer Not Reachable", "Not Required"]:
        r = record_satisfaction(TICKET, satisfaction_status=sat, notes=f"Customer said {sat}")
        _check(f"8a Sat status '{sat}' ok", r.get("ok"), str(r.get("message", ""))[:50])
        doc = frappe.get_doc("HD Ticket", TICKET)
        _check(f"8b customer_satisfaction_status = {sat}", doc.customer_satisfaction_status == sat, str(doc.customer_satisfaction_status))

    # Test: invalid satisfaction throws
    try:
        record_satisfaction(TICKET, satisfaction_status="Unknown")
        _check("8c Invalid satisfaction throws", False, "should have thrown")
    except Exception as e:
        _check("8c Invalid satisfaction throws", "not a valid" in str(e).lower(), str(e)[:60])


def test_09_record_customer_approval():
    """Step 9: Record customer approval / payment"""
    print("\n=== 9. Record Customer Approval ===")
    from lavanya_service.workflow.quick_actions import record_customer_approval
    _login_as("uat.coordinator@lavanya.local")

    r = record_customer_approval(TICKET, approved_amount="2500", payment_status="Approved", notes="Customer approved panel replacement")
    _check("9a Approval recorded ok", r.get("ok"), str(r.get("message", ""))[:50])
    doc = frappe.get_doc("HD Ticket", TICKET)
    _check("9b customer_approved_amount = 2500", float(doc.customer_approved_amount or 0) == 2500.0, str(doc.customer_approved_amount))
    _check("9c payment_status = Approved", doc.payment_status == "Approved", str(doc.payment_status))

    # Test: different payment status
    for ps in ["Pending", "Paid"]:
        r2 = record_customer_approval(TICKET, approved_amount="1500", payment_status=ps, notes=f"Payment {ps}")
        _check(f"9d Payment '{ps}' ok", r2.get("ok"), str(r2.get("message", ""))[:50])

    # Test: missing amount throws
    try:
        record_customer_approval(TICKET)
        _check("9e Missing amount throws", False, "should have thrown")
    except Exception as e:
        _check("9e Missing amount throws", "required" in str(e).lower(), str(e)[:60])


def test_10_followup_flow_engine():
    """Step 10: Test the follow-up flow engine at various stages"""
    print("\n=== 10. Follow-up Flow Engine ===")
    from lavanya_service.ai_advisory import get_followup_flow, _followup_flow_steps, _followup_alt_actions

    # Fresh ticket with no follow-up data
    frappe.db.set_value("HD Ticket", TICKET, "followup_stage", "")
    frappe.db.set_value("HD Ticket", TICKET, "customer_informed_status", "")
    frappe.db.set_value("HD Ticket", TICKET, "customer_satisfaction_status", "")
    frappe.db.set_value("HD Ticket", TICKET, "customer_approved_amount", 0)
    flow = get_followup_flow(TICKET)
    _check("10a get_followup_flow ok", flow.get("ok"), str(flow.get("ok")))
    _check("10b Has steps", isinstance(flow.get("steps"), list) and len(flow["steps"]) > 0, str(len(flow["steps"])))
    _check("10c Has alt_actions", isinstance(flow.get("alt_actions"), list), str(len(flow["alt_actions"])))
    step_keys = {s["key"] for s in flow["steps"]}
    _check("10d Core steps present", {"inform_customer", "record_sc_followup", "record_satisfaction", "close_ticket"}.issubset(step_keys), str(step_keys))
    # First step should be current
    _check("10e First step is current (inform_customer)", flow["steps"][0]["key"] == "inform_customer" and flow["steps"][0]["status"] == "current", str(flow["steps"][0]))

    # Ticket with part_required → track_part step should exist
    frappe.db.set_value("HD Ticket", TICKET, "part_required", "1")
    frappe.db.set_value("HD Ticket", TICKET, "part_name", "LED Panel 32LM563")
    frappe.db.set_value("HD Ticket", TICKET, "part_expected_date", add_days(today(), 7))
    flow2 = get_followup_flow(TICKET)
    step_keys2 = {s["key"] for s in flow2["steps"]}
    _check("10f Part step present when part_required=Yes", "track_part" in step_keys2, str(step_keys2))

    # L3/L4 escalation → reorder
    frappe.db.set_value("HD Ticket", TICKET, "escalation_level", "L3 - Manager Escalation")
    flow3 = get_followup_flow(TICKET)
    keys3 = [s["key"] for s in flow3["steps"]]
    if "record_sc_followup" in keys3 and "record_satisfaction" in keys3:
        sc_idx = keys3.index("record_sc_followup")
        sat_idx = keys3.index("record_satisfaction")
        _check("10g Escalation reorder moves SC followup earlier", sc_idx < len(keys3) - 2, f"sc_followup at {sc_idx} of {len(keys3)}")
        _check("10h Escalation reorder moves satisfaction earlier", sat_idx < len(keys3) - 2, f"satisfaction at {sat_idx} of {len(keys3)}")

    # Alt actions: mark_no_update should be present when followup_stage != no_technician_update
    frappe.db.set_value("HD Ticket", TICKET, "followup_stage", "technician_called")
    alt = _followup_alt_actions(frappe.get_doc("HD Ticket", TICKET))
    alt_keys = [a["action"] for a in alt]
    _check("10i Mark no update available when not at no_technician_update", "mark_no_update" in alt_keys, str(alt_keys))

    # Alt actions: both suppressed at max
    frappe.db.set_value("HD Ticket", TICKET, "followup_stage", "no_technician_update")
    frappe.db.set_value("HD Ticket", TICKET, "escalation_level", "L4 - Owner / Brand Manager Escalation")
    alt2 = _followup_alt_actions(frappe.get_doc("HD Ticket", TICKET))
    _check("10j No alt actions at max restrictions", len(alt2) == 0, str(len(alt2)))

    # Test with closed ticket → all steps completed
    frappe.db.set_value("HD Ticket", TICKET, "status", "Closed")
    frappe.db.set_value("HD Ticket", TICKET, "customer_satisfaction_status", "Satisfied")
    frappe.db.set_value("HD Ticket", TICKET, "customer_informed_status", "Informed by Call")
    frappe.db.set_value("HD Ticket", TICKET, "customer_approved_amount", 2500)
    frappe.db.set_value("HD Ticket", TICKET, "current_service_stage", "Service Center Follow-up")
    frappe.db.set_value("HD Ticket", TICKET, "followup_stage", "sc_followup_done")
    flow4 = get_followup_flow(TICKET)
    non_completed = [s for s in flow4["steps"] if s["status"] != "completed"]
    _check("10k Closed ticket all steps completed", len(non_completed) == 0, str([s["key"] + "=" + s["status"] for s in non_completed]) if non_completed else "all done")


def test_11_ai_advisory():
    """Step 11: Test AI advisory generation"""
    print("\n=== 11. AI Advisory ===")
    from lavanya_service.ai_advisory import generate_rule_based_ai_advisory, save_ai_advisory, get_ai_advisory, is_ai_review_candidate
    _login_as("Administrator")

    # Make ticket overdue to trigger advisory
    frappe.db.set_value("HD Ticket", TICKET, "stage_due_at", add_days(now_datetime(), -5))
    frappe.db.set_value("HD Ticket", TICKET, "modified", now_datetime())
    frappe.db.set_value("HD Ticket", TICKET, "creation", now_datetime())

    doc = frappe.get_doc("HD Ticket", TICKET)
    candidate, reasons = is_ai_review_candidate(doc)
    _check("11a AI candidate triggered", candidate, str(reasons))

    advisory = generate_rule_based_ai_advisory(doc)
    _check("11b Advisory generated", advisory["review_status"] == "Suggested", str(advisory.get("review_status")))
    _check("11c Next action present", bool(advisory.get("next_action")), str(advisory.get("next_action", ""))[:60])
    _check("11d Risk reason present", bool(advisory.get("risk_reason")), str(advisory.get("risk_reason", ""))[:60])
    _check("11e Customer message present", bool(advisory.get("customer_message")), str(advisory.get("customer_message", ""))[:60])

    # Save and verify
    save_ai_advisory(doc, advisory)
    view = get_ai_advisory(TICKET)
    _check("11f Advisory saved and retrievable", view.get("review_status") == "Suggested", str(view.get("review_status")))
    _check("11g Suggested next action readable", bool(view.get("suggested_next_action")), str(view.get("suggested_next_action", ""))[:60])

    # Test accept
    from lavanya_service.ai_advisory import accept_ai_suggestion, ignore_ai_suggestion
    r_acc = accept_ai_suggestion(TICKET, accepted_field="ai_suggested_next_action", note="Will follow up")
    _check("11h Accept ok", r_acc.get("review_status") == "Accepted", str(r_acc))
    view2 = get_ai_advisory(TICKET)
    _check("11i Accepted status reflected", view2.get("review_status") == "Accepted", str(view2.get("review_status")))

    # Test ignore on another ticket
    import copy
    phone2 = f"8888{now_datetime().strftime('%H%M%S')}"[:10]
    doc2 = frappe.new_doc("HD Ticket")
    doc2.subject = "AI ignore test"
    doc2.ticket_type = "Customer Complaint - Site"
    doc2.customer_name = "AI Test"
    doc2.phone_1 = phone2
    doc2.brand = "LG"
    doc2.insert(ignore_permissions=True)
    frappe.db.set_value("HD Ticket", doc2.name, "stage_due_at", add_days(now_datetime(), -3), update_modified=False)
    frappe.db.set_value("HD Ticket", doc2.name, "modified", add_days(now_datetime(), -3), update_modified=False)
    doc2b = frappe.get_doc("HD Ticket", doc2.name)
    adv2 = generate_rule_based_ai_advisory(doc2b)
    save_ai_advisory(doc2b, adv2)
    r_ig = ignore_ai_suggestion(doc2.name, note="Manual handling decided")
    _check("11j Ignore ok", r_ig.get("review_status") == "Ignored", str(r_ig))
    view3 = get_ai_advisory(doc2.name)
    _check("11k Ignored status reflected", view3.get("review_status") == "Ignored", str(view3.get("review_status")))


def test_12_part_tracking_fields():
    """Step 12: Test part tracking fields"""
    print("\n=== 12. Part Tracking ===")
    _login_as("uat.coordinator@lavanya.local")

    frappe.db.set_value("HD Ticket", TICKET, "part_required", 1)
    frappe.db.set_value("HD Ticket", TICKET, "part_name", "LED Panel 32LM563")
    frappe.db.set_value("HD Ticket", TICKET, "part_expected_date", add_days(today(), 7))
    frappe.db.set_value("HD Ticket", TICKET, "part_delay_reason", "Supplier delay - ETA revised")
    frappe.db.set_value("HD Ticket", TICKET, "customer_informed_about_part_delay", "Yes")

    doc = frappe.get_doc("HD Ticket", TICKET)
    _check("12a part_required=Yes", doc.part_required == 1, str(doc.part_required))
    _check("12b part_name set", doc.part_name == "LED Panel 32LM563", doc.part_name)
    _check("12c part_expected_date set", str(doc.part_expected_date) == str(add_days(today(), 7)), str(doc.part_expected_date))
    _check("12d part_delay_reason set", doc.part_delay_reason == "Supplier delay - ETA revised", doc.part_delay_reason)
    _check("12e customer_informed_about_part_delay", doc.customer_informed_about_part_delay == "Yes", doc.customer_informed_about_part_delay)


def test_13_today_work_buckets():
    """Step 13: Verify today's work buckets"""
    print("\n=== 13. Today's Work Buckets ===")
    from lavanya_service.workflow.today_work import classify_ticket
    _login_as("uat.coordinator@lavanya.local")

    # Ensure ticket is active
    frappe.db.set_value("HD Ticket", TICKET, "status", "In Progress")

    row = frappe.get_all("HD Ticket", filters={"name": TICKET}, fields=["*"], limit=1)
    if row:
        keys = classify_ticket(row[0])
        _check("13a Ticket classified into buckets", len(keys) > 0, str(keys))

    # Test with escalated ticket
    frappe.db.set_value("HD Ticket", TICKET, "escalation_level", "L2 - Coordinator Escalation")
    frappe.db.set_value("HD Ticket", TICKET, "followup_stage", "technician_called")
    row2 = frappe.get_all("HD Ticket", filters={"name": TICKET}, fields=["*"], limit=1)
    if row2:
        keys2 = classify_ticket(row2[0])
        _check("13b Escalated ticket classified", "escalated_cases" in keys2, str(keys2))


def test_14_closure_rule():
    """Step 14: Test closure rules — v2.1 shared gate contract.

    Proves four things:
    1. close_ticket blocks if satisfaction is missing.
    2. close_ticket succeeds when all gates are satisfied.
    3. customer_confirmed cannot bypass unresolved technician/appointment/service stages.
    4. customer_confirmed succeeds only when the only remaining gate is customer confirmation.
    """
    print("\n=== 14. Closure Rules (v2.1 shared gate) ===")
    from lavanya_service.workflow.quick_actions import close_ticket, customer_confirmed
    _login_as("uat.coordinator@lavanya.local")

    # ── Helper: neutralize all physical/verification gates for clean satisfaction testing ──
    def _prepare_for_closure():
        frappe.db.set_value("HD Ticket", TICKET, {
            "status": "Resolved",
            "part_required": 0,
            "part_fitted_confirmed": 1,
            "followup_stage": "customer_confirmation_pending",
            "customer_confirmation_received": "No",
            "customer_satisfaction_status": "Satisfied",
        })

    # ── 14a: close_ticket blocks when satisfaction is missing ──
    _prepare_for_closure()
    frappe.db.set_value("HD Ticket", TICKET, "customer_satisfaction_status", "Pending")
    try:
        close_ticket(TICKET, work_narration="Fixed", closure_type="Resolved by Local Technician", customer_confirmation_received="Yes")
        _check("14a Close blocks without satisfaction", False, "should have thrown")
    except Exception as e:
        _check("14a Close blocks without satisfaction", "satisfaction" in str(e).lower(), str(e)[:80])

    # ── 14b: close_ticket blocks when part_required=1 and part_fitted_confirmed missing ──
    _prepare_for_closure()
    frappe.db.set_value("HD Ticket", TICKET, "part_required", 1)
    frappe.db.set_value("HD Ticket", TICKET, "part_fitted_confirmed", 0)
    try:
        close_ticket(TICKET, work_narration="Fixed", closure_type="Resolved by Local Technician", customer_confirmation_received="Yes")
        _check("14b Close blocks with part pending", False, "should have thrown")
    except Exception as e:
        _check("14b Close blocks with part pending", "part" in str(e).lower() or "fitted" in str(e).lower(), str(e)[:80])

    # ── 14c: close_ticket succeeds when all gates satisfied ──
    _prepare_for_closure()
    try:
        r = close_ticket(TICKET, work_narration="Panel replaced - TV working", closure_type="Resolved by Local Technician", customer_confirmation_received="Yes")
        _check("14c Close with all gates satisfied", r.get("ok"), str(r.get("message", ""))[:50])
        _check("14d Status = Closed", r.get("status") == "Closed", r.get("status"))
    except Exception as e:
        _check("14c Close with all gates satisfied FAILED", False, str(e)[:80])

    # ── 14e: customer_confirmed blocks unresolved technician_call_pending stage ──
    frappe.db.set_value("HD Ticket", TICKET, {
        "status": "Resolved",
        "followup_stage": "technician_call_pending",
        "customer_satisfaction_status": "Satisfied",
        "customer_confirmation_received": "No",
        "part_required": 0,
        "part_fitted_confirmed": 1,
    })
    try:
        customer_confirmed(TICKET, work_narration="Customer says okay", closure_type="Resolved by Local Technician")
        _check("14e Customer confirmed blocks unresolved tech_call", False, "should have thrown")
    except Exception as e:
        _check("14e Customer confirmed blocks unresolved tech_call",
               "follow-up stage" in str(e).lower() or "verification" in str(e).lower(),
               str(e)[:100])

    # ── 14f: customer_confirmed blocks unresolved appointment_missed stage ──
    frappe.db.set_value("HD Ticket", TICKET, {
        "status": "Resolved",
        "followup_stage": "appointment_missed",
        "customer_satisfaction_status": "Satisfied",
        "customer_confirmation_received": "No",
        "part_required": 0,
        "part_fitted_confirmed": 1,
    })
    try:
        customer_confirmed(TICKET, work_narration="Customer says okay but appointment unresolved", closure_type="Resolved by Local Technician")
        _check("14f Customer confirmed blocks unresolved appointment", False, "should have thrown")
    except Exception as e:
        _check("14f Customer confirmed blocks unresolved appointment",
               "follow-up stage" in str(e).lower() or "verification" in str(e).lower(),
               str(e)[:100])

    # ── 14g: customer_confirmed blocks unresolved no_technician_update stage ──
    frappe.db.set_value("HD Ticket", TICKET, {
        "status": "Resolved",
        "followup_stage": "no_technician_update",
        "customer_satisfaction_status": "Satisfied",
        "customer_confirmation_received": "No",
        "part_required": 0,
        "part_fitted_confirmed": 1,
    })
    try:
        customer_confirmed(TICKET, work_narration="Customer says okay but no tech update", closure_type="Resolved by Local Technician")
        _check("14g Customer confirmed blocks unresolved no_tech_update", False, "should have thrown")
    except Exception as e:
        _check("14g Customer confirmed blocks unresolved no_tech_update",
               "follow-up stage" in str(e).lower() or "verification" in str(e).lower(),
               str(e)[:100])

    # ── 14h: customer_confirmed blocks unresolved part gate even with valid stage ──
    frappe.db.set_value("HD Ticket", TICKET, {
        "status": "Resolved",
        "followup_stage": "customer_confirmation_pending",
        "customer_satisfaction_status": "Satisfied",
        "customer_confirmation_received": "No",
        "part_required": 1,
        "part_fitted_confirmed": 0,
    })
    try:
        customer_confirmed(TICKET, work_narration="Customer confirmed but part still pending", closure_type="Resolved by Local Technician", notes="Re-entry: part gate test")
        _check("14h Customer confirmed blocks with part pending", False, "should have thrown")
    except Exception as e:
        _check("14h Customer confirmed blocks with part pending",
               "part" in str(e).lower() or "fitted" in str(e).lower(),
               str(e)[:100])

    # ── 14i: customer_confirmed succeeds when only customer confirmation is pending ──
    _prepare_for_closure()
    try:
        r2 = customer_confirmed(TICKET, work_narration="Customer confirmed TV working", closure_type="Resolved by Local Technician", notes="Re-entry: positive closure test")
        _check("14i Customer confirmed ok", r2.get("ok"), str(r2.get("message", ""))[:50])
        _check("14j Status = Closed", r2.get("status") == "Closed", r2.get("status"))
    except Exception as e:
        _check("14i Customer confirmed FAILED", False, str(e)[:80])


def test_15_role_gating():
    """Step 15: Test role-based access control"""
    print("\n=== 15. Role Gating ===")
    from lavanya_service.workflow.quick_actions import verify_technician_called, escalate_case
    from lavanya_service.api.coordinator_dashboard import get_coordinator_dashboard

    # Viewer should NOT be able to run quick actions
    _login_as("uat.viewer@lavanya.local")
    try:
        verify_technician_called(TICKET)
        _check("15a Viewer blocked on quick action", False, "should have thrown")
    except Exception as e:
        _check("15a Viewer blocked on quick action", "not permitted" in str(e).lower() or "permission" in str(e).lower(), str(e)[:60])

    # Viewer should be able to view coordinator dashboard (if has HD Ticket read)
    try:
        data = get_coordinator_dashboard()
        _check("15b Viewer can access coordinator dashboard", isinstance(data, dict), str(type(data)))
    except Exception as e:
        _check("15b Viewer access coordinator dashboard", False, str(e)[:60])


def test_16_overdue_flow():
    """Step 16: Test overdue/due-soon flow"""
    print("\n=== 16. Overdue / Due-Soon Flow ===")
    from lavanya_service.reminder_engine import derive_escalation_level, refresh_ticket_reminder_state

    frappe.db.set_value("HD Ticket", TICKET, "status", "In Progress")
    frappe.db.set_value("HD Ticket", TICKET, "next_follow_up_date", None)
    frappe.db.set_value("HD Ticket", TICKET, "stage_due_at", add_days(now_datetime(), -5))
    frappe.db.set_value("HD Ticket", TICKET, "current_service_stage", "Brand Registered")
    frappe.db.set_value("HD Ticket", TICKET, "is_repeated_complaint", "Yes")

    from lavanya_service.reminder_engine import get_active_rules
    rules = get_active_rules()
    state = refresh_ticket_reminder_state(frappe.get_doc("HD Ticket", TICKET), save=False, rules=rules)
    _check("16a Overdue status computed", state.get("overdue_status") == "Overdue", str(state.get("overdue_status")))
    _check("16b Escalation from reminder engine", bool(state.get("computed_escalation_level")), str(state.get("computed_escalation_level")))

    esc = derive_escalation_level(frappe.get_doc("HD Ticket", TICKET))
    _check("16c derive_escalation_level works", bool(esc), str(esc))


def test_17_api_endpoints():
    """Step 17: Test API endpoints respond"""
    print("\n=== 17. API Endpoints ===")
    from lavanya_service.api.workflow_actions import get_current_user_roles
    _login_as("uat.coordinator@lavanya.local")
    roles = get_current_user_roles()
    _check("17a get_current_user_roles", isinstance(roles, dict) and roles.get("is_coordinator"), str(roles))

    _login_as("uat.manager@lavanya.local")
    roles2 = get_current_user_roles()
    _check("17b Manager roles detected", isinstance(roles2, dict) and roles2.get("is_manager"), str(roles2))

    from lavanya_service.api.stitch_console import get_ticket_list
    tl = get_ticket_list(start=0, page_length=5)
    _check("17c Ticket list returns data", isinstance(tl, dict) and isinstance(tl.get("tickets"), list), f"count={len(tl.get('tickets', []))}")


def run():
    """Execute all E2E test scenarios"""
    print("=" * 60)
    print("E2E FOLLOW-UP SCENARIO TEST — Fidha / LG LED TV")
    print("=" * 60)
    frappe.db.set_value("HD Settings", "HD Settings", "allow_customer_portal", 0)

    # Disable scheduler for test isolation
    frappe.db.set_value("HD Settings", "HD Settings", "enable_scheduler", 0)

    try:
        test_01_create_ticket()
        test_02_register_brand_complaint()
        test_03_verify_technician_called()
        test_04_verify_technician_visit()
        test_05_record_sc_followup()
        test_06_inform_customer()
        test_07_mark_no_update_and_escalate()
        test_08_record_satisfaction()
        test_09_record_customer_approval()
        test_10_followup_flow_engine()
        test_11_ai_advisory()
        test_12_part_tracking_fields()
        test_13_today_work_buckets()
        test_14_closure_rule()
        test_15_role_gating()
        test_16_overdue_flow()
        test_17_api_endpoints()

        print("\n" + "=" * 60)
        total = len(PASS) + len(FAIL)
        print(f"TOTAL: {total} | PASS: {len(PASS)} | FAIL: {len(FAIL)}")
        if FAIL:
            print("FAILED: " + ", ".join(FAIL))
        print("OVERALL: " + ("PASS" if not FAIL else "FAIL"))
        return {"total": total, "failed": len(FAIL), "passed": len(PASS)}

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"total": len(PASS) + len(FAIL), "failed": len(FAIL) + 1, "error": str(e)}

    finally:
        # Cleanup the test ticket
        if TICKET and frappe.db.exists("HD Ticket", TICKET):
            frappe.db.set_value("HD Ticket", TICKET, "status", "Cancelled")
        frappe.db.commit()
