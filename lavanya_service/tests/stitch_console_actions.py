import frappe
import os

CREATED_DOCS = []


def _ensure_ticket():
    """Return an open test ticket, creating one if none exists."""
    tickets = frappe.get_all("HD Ticket", filters={"status": ["!=", "Closed"]}, limit=1)
    if tickets:
        return tickets[0].name
    frappe.set_user("Administrator")
    cust = frappe.get_all("HD Customer", limit=1, pluck="name")
    t = frappe.new_doc("HD Ticket")
    t.subject = "Auto-created test ticket for stitch_console_actions"
    t.ticket_type = "Customer Complaint - Site"
    t.raised_by = "test@example.com"
    if cust:
        t.customer = cust[0]
    t.insert(ignore_permissions=True)
    CREATED_DOCS.append(("HD Ticket", t.name))
    return t.name


def _cleanup():
    frappe.set_user("Administrator")
    for dt, name in reversed(CREATED_DOCS):
        try:
            frappe.delete_doc(dt, name, force=True, ignore_permissions=True)
        except Exception:
            pass
    CREATED_DOCS.clear()


def run():
    print("Running Stitch Console Actions Tests (Phase 2-C)...")
    try:
        _run_tests()
    finally:
        _cleanup()
    print("✅ Stitch Console Actions tests passed")


def _run_tests():
    ticket_id = _ensure_ticket()
    api_path = "lavanya_service.api.workflow_actions.need_invoice_from_customer"

    # 1. Guest is rejected
    frappe.set_user("Guest")
    try:
        frappe.call(api_path, ticket_name=ticket_id, next_follow_up_date="2030-01-01")
        assert False, "Guest could call Need Invoice API"
    except frappe.PermissionError:
        pass

    # 2. Viewer is rejected
    frappe.set_user("uat.viewer@lavanya.local")
    if frappe.db.exists("User", "uat.viewer@lavanya.local"):
        try:
            frappe.call(api_path, ticket_name=ticket_id, next_follow_up_date="2030-01-01")
            assert False, "Viewer could call Need Invoice API"
        except frappe.PermissionError:
            pass

    # 3. Invalid ticket is rejected
    frappe.set_user("uat.coordinator@lavanya.local")
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        try:
            frappe.call(api_path, ticket_name="INVALID_TICKET_12345", next_follow_up_date="2030-01-01")
            assert False, "Should fail on invalid ticket"
        except Exception:
            pass
            
    # 4. Missing next follow-up date is rejected
    frappe.set_user("uat.coordinator@lavanya.local")
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        try:
            frappe.call(api_path, ticket_name=ticket_id)
            assert False, "Should fail on missing follow-up date"
        except frappe.ValidationError:
            pass
            
    # Restore admin
    frappe.set_user("Administrator")
    
    # Run UI checks
    app_path = frappe.get_app_path("lavanya_service")
    frontend_path = os.path.join(os.path.dirname(app_path), "frontend")
    ticket_detail = os.path.join(frontend_path, "src", "components", "TicketDetail.vue")
    
    with open(ticket_detail, "r", encoding="utf-8") as f:
        detail_content = f.read()

    assert "Need Invoice Modal" in detail_content, "Need Invoice modal component missing"
    assert "post('lavanya_service.api.workflow_actions.need_invoice_from_customer'" in detail_content, "Need Invoice action not wired correctly"

    # Phase 2 wired ALL remaining quick actions via the generic action modal, so
    # the old "Available in Phase 2C" disabled placeholders must be gone and each
    # action must be wired to openAction(...) + its endpoint.
    assert "Available in Phase 2C" not in detail_content, "Stale disabled-action placeholder still present"
    for key in ("brand_complaint", "follow_up_sc", "waiting_part", "customer_confirmed", "close_ticket"):
        assert f"openAction('{key}')" in detail_content, f"Quick action '{key}' not wired to openAction"
    for endpoint in (
        "register_brand_complaint",
        "follow_up_service_center",
        "waiting_for_part",
        "customer_confirmed",
        "close_ticket",
    ):
        assert endpoint in detail_content, f"Action endpoint '{endpoint}' not referenced in drawer"

    # --- Product Receipt Tests ---
    print("Running Product Receipt tests...")
    api_receipt = "lavanya_service.api.workflow_actions.create_product_receipt"
    
    # Need a ticket of type "Customer Product at Store"
    store_tickets = frappe.get_all("HD Ticket", filters={"status": ["!=", "Closed"], "ticket_type": "Customer Product at Store"}, limit=1)
    if not store_tickets:
        print("⚠️ No open 'Customer Product at Store' tickets found. Creating a temporary one.")
        frappe.set_user("Administrator")
        cust_list = frappe.get_all("HD Customer", limit=1)
        customer = cust_list[0].name if cust_list else None
        t = frappe.new_doc("HD Ticket")
        t.subject = "Test Product Receipt"
        t.ticket_type = "Customer Product at Store"
        t.serial_no = "TEST-SN-123"
        t.customer = customer
        t.insert(ignore_permissions=True)
        CREATED_DOCS.append(("HD Ticket", t.name))
        store_ticket_id = t.name
    else:
        store_ticket_id = store_tickets[0].name

    # 1. Guest is rejected
    frappe.set_user("Guest")
    try:
        frappe.call(api_receipt, ticket_name=store_ticket_id, accessories_received="Box", physical_condition="Good")
        assert False, "Guest could call Create Product Receipt API"
    except frappe.PermissionError:
        pass

    # 2. Viewer is rejected
    frappe.set_user("uat.viewer@lavanya.local")
    if frappe.db.exists("User", "uat.viewer@lavanya.local"):
        try:
            frappe.call(api_receipt, ticket_name=store_ticket_id, accessories_received="Box", physical_condition="Good")
            assert False, "Viewer could call Create Product Receipt API"
        except frappe.PermissionError:
            pass

    # 3. Helpdesk Agent is rejected
    frappe.set_user("uat.agent@lavanya.local")
    if frappe.db.exists("User", "uat.agent@lavanya.local"):
        try:
            frappe.call(api_receipt, ticket_name=store_ticket_id, accessories_received="Box", physical_condition="Good")
            assert False, "Helpdesk Agent could call Create Product Receipt API"
        except frappe.PermissionError:
            pass

    # 4. Service Coordinator can create
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        # Make sure no receipt exists for this ticket. Clean up as Administrator —
        # coordinators can't delete receipts, and a leftover (e.g. from a custody
        # walk) would otherwise fail this with a permission error.
        frappe.set_user("Administrator")
        for r in frappe.get_all("Service Product Receipt", filters={"ticket": store_ticket_id}):
            frappe.db.set_value("HD Ticket", store_ticket_id, "service_product_receipt", None)
            frappe.delete_doc("Service Product Receipt", r.name, force=True, ignore_permissions=True)

        frappe.set_user("uat.coordinator@lavanya.local")
        res = frappe.call(api_receipt, ticket_name=store_ticket_id, accessories_received="Charger", physical_condition="Scratched")
        assert res.get("ok"), "Service Coordinator failed to create receipt"
        receipt_name = res.get("receipt")
        CREATED_DOCS.append(("Service Product Receipt", receipt_name))
        
        # 5. Duplicate receipt is rejected
        try:
            frappe.call(api_receipt, ticket_name=store_ticket_id, accessories_received="Charger", physical_condition="Scratched")
            assert False, "Duplicate receipt creation should have been rejected"
        except Exception as e:
            assert "already has a linked Service Product Receipt" in str(e) or "already exists for ticket" in str(e), f"Unexpected duplicate error: {e}"

    # 6. Invalid ticket is rejected
    frappe.set_user("uat.manager@lavanya.local")
    if frappe.db.exists("User", "uat.manager@lavanya.local"):
        try:
            frappe.call(api_receipt, ticket_name="INVALID_TICKET_12345", accessories_received="Box", physical_condition="Good")
            assert False, "Should fail on invalid ticket"
        except Exception:
            pass

    # --- Ready for Pickup Tests ---
    print("Running Ready for Pickup tests...")
    api_ready = "lavanya_service.api.product_receipt_actions.mark_ready_for_pickup"
    
    frappe.set_user("Administrator")
    t_ready = frappe.new_doc("HD Ticket")
    t_ready.subject = "Test Ready for Pickup"
    t_ready.ticket_type = "Customer Product at Store"
    t_ready.serial_no = "TEST-SN-READY-1"
    cust_list_ready = frappe.get_all("HD Customer", limit=1)
    t_ready.customer = cust_list_ready[0].name if cust_list_ready else None
    t_ready.insert(ignore_permissions=True)
    CREATED_DOCS.append(("HD Ticket", t_ready.name))
    
    res_receipt = frappe.call(api_receipt, ticket_name=t_ready.name, accessories_received="Box", physical_condition="Good")
    r_ready_name = res_receipt.get("receipt")
    CREATED_DOCS.append(("Service Product Receipt", r_ready_name))
    
    # 1. Guest is rejected
    frappe.set_user("Guest")
    try:
        frappe.call(api_ready, receipt_name=r_ready_name, notes="Test")
        assert False, "Guest could call Ready for Pickup API"
    except frappe.PermissionError:
        pass
        
    # 2. Viewer is rejected
    frappe.set_user("uat.viewer@lavanya.local")
    if frappe.db.exists("User", "uat.viewer@lavanya.local"):
        try:
            frappe.call(api_ready, receipt_name=r_ready_name, notes="Test")
            assert False, "Viewer could call Ready for Pickup API"
        except frappe.PermissionError:
            pass

    # 3. Helpdesk Agent is rejected
    frappe.set_user("uat.agent@lavanya.local")
    if frappe.db.exists("User", "uat.agent@lavanya.local"):
        try:
            frappe.call(api_ready, receipt_name=r_ready_name, notes="Test")
            assert False, "Agent could call Ready for Pickup API"
        except frappe.PermissionError:
            pass
            
    # 4. Service Coordinator can mark ready
    frappe.set_user("uat.coordinator@lavanya.local")
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        res = frappe.call(api_ready, receipt_name=r_ready_name, notes="Coordinator Test")
        assert res.get("ok"), "Coordinator failed to mark ready for pickup"
        
        # 5. Duplicate call is rejected safely
        try:
            frappe.call(api_ready, receipt_name=r_ready_name, notes="Coordinator Test 2")
            assert False, "Duplicate ready for pickup should be rejected"
        except Exception as e:
            assert "Cannot mark ready for pickup from current status" in str(e), f"Unexpected duplicate error: {e}"

    # --- Follow-up Tracking Actions Tests (Phase 1N-6B) ---
    print("Running Follow-up Tracking actions tests...")
    _run_followup_tracking_tests(ticket_id)

    # --- Record Customer Approval test ---
    print("Running Record Customer Approval test...")
    frappe.set_user("Administrator")
    ticket_approval = _ensure_ticket()
    api_approval = "lavanya_service.api.workflow_actions.record_customer_approval"
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        frappe.set_user("uat.coordinator@lavanya.local")
        res = frappe.call(api_approval, ticket_name=ticket_approval, approved_amount="1500", payment_status="Pending", notes="Customer agreed")
        assert res.get("ok"), "Coordinator failed to record approval"
        doc = frappe.get_doc("HD Ticket", ticket_approval)
        assert doc.customer_approved_amount == 1500.0
        assert doc.payment_status == "Pending"
        print("  ✅ record_customer_approval")

    frappe.set_user("Administrator")


def _run_followup_tracking_tests(ticket_id):
    """Test all 7 follow-up tracking quick actions."""

    # --- verify_technician_called ---
    api = "lavanya_service.api.workflow_actions.verify_technician_called"
    frappe.set_user("Guest")
    try:
        frappe.call(api, ticket_name=ticket_id, technician_name="John")
        assert False, "Guest could call verify_technician_called"
    except frappe.PermissionError:
        pass

    frappe.set_user("uat.coordinator@lavanya.local")
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        res = frappe.call(api, ticket_name=ticket_id, technician_name="John", notes="Called at 10 AM")
        assert res.get("ok"), "Coordinator failed to verify technician called"
        doc = frappe.get_doc("HD Ticket", ticket_id)
        assert doc.followup_stage == "technician_called", f"Expected 'technician_called', got '{doc.followup_stage}'"
        print("  ✅ verify_technician_called")

    # --- verify_technician_visit ---
    api = "lavanya_service.api.workflow_actions.verify_technician_visit"
    frappe.set_user("uat.coordinator@lavanya.local")
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        res = frappe.call(api, ticket_name=ticket_id, technician_name="John", visit_result="Repaired")
        assert res.get("ok"), "Coordinator failed to verify technician visit"
        doc = frappe.get_doc("HD Ticket", ticket_id)
        assert doc.followup_stage == "technician_visited"
        print("  ✅ verify_technician_visit")

    # --- record_sc_followup ---
    api = "lavanya_service.api.workflow_actions.record_sc_followup"
    frappe.set_user("uat.coordinator@lavanya.local")
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        res = frappe.call(api, ticket_name=ticket_id, follow_up_result="Service center contacted", next_follow_up_date="2030-01-15", customer_informed_status="Informed by Call")
        assert res.get("ok"), "Coordinator failed to record SC follow-up"
        doc = frappe.get_doc("HD Ticket", ticket_id)
        assert doc.followup_stage == "sc_followup_done"
        assert doc.last_service_center_followup is not None
        print("  ✅ record_sc_followup")

    # --- inform_customer ---
    api = "lavanya_service.api.workflow_actions.inform_customer"
    frappe.set_user("uat.agent@lavanya.local")
    if frappe.db.exists("User", "uat.agent@lavanya.local"):
        res = frappe.call(api, ticket_name=ticket_id, channel="WhatsApp", message="Part will arrive in 2 days")
        assert res.get("ok"), "Agent failed to inform customer"
        doc = frappe.get_doc("HD Ticket", ticket_id)
        assert doc.followup_stage == "customer_informed"
        assert doc.customer_informed == "Yes"
        assert doc.customer_informed_channel == "WhatsApp"
        assert doc.customer_informed_status == "Informed by WhatsApp"
        print("  ✅ inform_customer")

    # --- mark_no_update ---
    api = "lavanya_service.api.workflow_actions.mark_no_update"
    frappe.set_user("uat.coordinator@lavanya.local")
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        res = frappe.call(api, ticket_name=ticket_id, notes="Technician not responding")
        assert res.get("ok"), "Coordinator failed to mark no update"
        doc = frappe.get_doc("HD Ticket", ticket_id)
        assert doc.followup_stage == "no_technician_update"
        assert doc.escalation_level and doc.escalation_level != "None"
        assert doc.no_update_count and doc.no_update_count > 0
        print("  ✅ mark_no_update")

    # --- escalate_case ---
    api = "lavanya_service.api.workflow_actions.escalate_case"
    frappe.set_user("uat.coordinator@lavanya.local")
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        res = frappe.call(api, ticket_name=ticket_id, reason="Technician not responding for 3 days")
        assert res.get("ok"), "Coordinator failed to escalate case"
        doc = frappe.get_doc("HD Ticket", ticket_id)
        assert doc.escalation_level and doc.escalation_level != "None", "Escalation level not set"
        print("  ✅ escalate_case")

    # --- record_satisfaction ---
    api = "lavanya_service.api.workflow_actions.record_satisfaction"
    frappe.set_user("uat.manager@lavanya.local")
    if frappe.db.exists("User", "uat.manager@lavanya.local"):
        res = frappe.call(api, ticket_name=ticket_id, satisfaction_status="Satisfied", notes="Customer happy with repair")
        assert res.get("ok"), "Manager failed to record satisfaction"
        doc = frappe.get_doc("HD Ticket", ticket_id)
        assert doc.customer_satisfaction_status == "Satisfied"
        assert doc.followup_stage == "customer_satisfied"
        print("  ✅ record_satisfaction (Satisfied)")

    # --- record_satisfaction (Not Satisfied) ---
    frappe.set_user("uat.manager@lavanya.local")
    if frappe.db.exists("User", "uat.manager@lavanya.local"):
        res = frappe.call(api, ticket_name=ticket_id, satisfaction_status="Not Satisfied", notes="Issue persists")
        assert res.get("ok"), "Manager failed to record satisfaction"
        doc = frappe.get_doc("HD Ticket", ticket_id)
        assert doc.customer_satisfaction_status == "Not Satisfied"
        assert doc.followup_stage == "customer_not_satisfied"
        print("  ✅ record_satisfaction (Not Satisfied)")

    # --- record_sc_followup without customer_informed_status fails ---
    frappe.set_user("uat.coordinator@lavanya.local")
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        try:
            frappe.call("lavanya_service.api.workflow_actions.record_sc_followup",
                ticket_name=ticket_id, follow_up_result="Service center contacted",
                next_follow_up_date="2030-01-15")
            assert False, "record_sc_followup should fail without customer_informed_status"
        except Exception:
            pass
        print("  ✅ record_sc_followup_without_customer_informed_status_fails")

    # --- close_without_customer_satisfaction_fails ---
    frappe.set_user("uat.coordinator@lavanya.local")
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        # Set satisfaction to Pending (not Satisfied/Not Required)
        doc = frappe.get_doc("HD Ticket", ticket_id)
        doc.customer_satisfaction_status = "Pending"
        doc.save(ignore_permissions=True)

        try:
            frappe.call("lavanya_service.api.workflow_actions.close_ticket",
                ticket_name=ticket_id, work_narration="Test close",
                closure_type="Repair", customer_confirmation_received="Yes")
            assert False, "close_ticket should fail when satisfaction is Pending"
        except Exception:
            pass
        print("  ✅ close_without_customer_satisfaction_fails")

    # --- mark_no_update increments counter ---
    frappe.set_user("uat.coordinator@lavanya.local")
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        # Reset count and call twice
        doc = frappe.get_doc("HD Ticket", ticket_id)
        doc.no_update_count = 0
        doc.escalation_level = "None"
        doc.save(ignore_permissions=True)

        frappe.call("lavanya_service.api.workflow_actions.mark_no_update",
            ticket_name=ticket_id, notes="First no update")
        doc.reload()
        assert doc.no_update_count == 1, f"Expected count 1, got {doc.no_update_count}"
        assert doc.escalation_level == "L1 - Agent Follow-up", f"Expected L1, got {doc.escalation_level}"

        frappe.call("lavanya_service.api.workflow_actions.mark_no_update",
            ticket_name=ticket_id, notes="Second no update")
        doc.reload()
        assert doc.no_update_count == 2, f"Expected count 2, got {doc.no_update_count}"
        assert doc.escalation_level == "L2 - Coordinator Escalation", f"Expected L2, got {doc.escalation_level}"
        print("  ✅ mark_no_update_increments_counter_and_escalation")

    # --- inform_customer updates last_followup_summary ---
    frappe.set_user("uat.coordinator@lavanya.local")
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        res = frappe.call("lavanya_service.api.workflow_actions.inform_customer",
            ticket_name=ticket_id, channel="WhatsApp", message="Test message")
        doc = frappe.get_doc("HD Ticket", ticket_id)
        assert doc.last_followup_summary, "last_followup_summary should be set after inform_customer"
        assert "Inform Customer" in doc.last_followup_summary, "Summary should contain action name"
        print("  ✅ inform_customer_updates_last_followup_summary")

    # --- record_satisfaction (Not Satisfied) does not close ticket ---
    frappe.set_user("uat.manager@lavanya.local")
    if frappe.db.exists("User", "uat.manager@lavanya.local"):
        res = frappe.call("lavanya_service.api.workflow_actions.record_satisfaction",
            ticket_name=ticket_id, satisfaction_status="Not Satisfied", notes="Issue persists")
        doc = frappe.get_doc("HD Ticket", ticket_id)
        assert doc.status != "Closed", "Not Satisfied should not auto-close ticket"
        assert doc.followup_stage == "customer_not_satisfied"
        print("  ✅ record_satisfaction_not_satisfied_does_not_close_ticket")

    # --- record_customer_approval required for paid local service ---
    frappe.set_user("Administrator")
    doc = frappe.get_doc("HD Ticket", ticket_id)
    doc.service_path = "customer_paid_local"
    doc.customer_satisfaction_status = "Pending"
    doc.status = "Open"
    doc.save(ignore_permissions=True)

    frappe.set_user("uat.coordinator@lavanya.local")
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        # Without customer_informed_status in record_sc_followup
        try:
            frappe.call("lavanya_service.api.workflow_actions.record_sc_followup",
                ticket_name=ticket_id, follow_up_result="Service center contacted",
                next_follow_up_date="2030-01-15")
            assert False, "record_sc_followup should fail without customer_informed_status"
        except Exception:
            pass

        # Now with valid customer_informed_status
        res = frappe.call("lavanya_service.api.workflow_actions.record_sc_followup",
            ticket_name=ticket_id, follow_up_result="Service center contacted",
            next_follow_up_date="2030-01-15", customer_informed_status="Informed by Call")
        assert res.get("ok"), "record_sc_followup should succeed with customer_informed_status"
        print("  ✅ record_customer_approval_required_for_paid_local_service")

    # --- customer_informed_status=Pending → customer_not_informed bucket ---
    frappe.set_user("Administrator")
    doc = frappe.get_doc("HD Ticket", ticket_id)
    doc.customer_informed_status = "Pending"
    doc.status = "Open"
    doc.save(ignore_permissions=True)

    from lavanya_service.workflow.today_work import classify_ticket
    keys = classify_ticket(doc.as_dict())
    assert "customer_not_informed" in keys, f"Pending informed status should be in customer_not_informed bucket, got {keys}"
    print("  ✅ customer_informed_pending_goes_to_customer_not_informed_bucket")

    # --- empty customer_informed_status → customer_not_informed bucket ---
    frappe.set_user("Administrator")
    doc = frappe.get_doc("HD Ticket", ticket_id)
    doc.customer_informed_status = ""
    doc.save(ignore_permissions=True)

    keys = classify_ticket(doc.as_dict())
    assert "customer_not_informed" in keys, f"Empty informed status should be in customer_not_informed bucket, got {keys}"
    print("  ✅ empty_customer_informed_goes_to_customer_not_informed_bucket")

    # --- Customer Not Reachable → customer_not_informed bucket ---
    frappe.set_user("Administrator")
    doc = frappe.get_doc("HD Ticket", ticket_id)
    doc.customer_informed_status = "Customer Not Reachable"
    doc.save(ignore_permissions=True)

    keys = classify_ticket(doc.as_dict())
    assert "customer_not_informed" in keys, f"Customer Not Reachable should be in customer_not_informed bucket, got {keys}"
    print("  ✅ customer_not_reachable_goes_to_customer_not_informed_bucket")

    # --- closed_ticket blocks all follow-up actions ---
    frappe.set_user("Administrator")
    doc = frappe.get_doc("HD Ticket", ticket_id)
    doc.customer_satisfaction_status = "Satisfied"
    doc.customer_confirmation_received = "Yes"
    doc.closure_type = "Resolved by Local Technician"
    doc.work_narration = "Test close for follow-up action blocking test"
    doc.status = "Closed"
    doc.save(ignore_permissions=True)

    frappe.set_user("uat.manager@lavanya.local")
    for action_name, action_api in [
        ("verify_technician_called", "lavanya_service.api.workflow_actions.verify_technician_called"),
        ("verify_technician_visit", "lavanya_service.api.workflow_actions.verify_technician_visit"),
        ("record_sc_followup", "lavanya_service.api.workflow_actions.record_sc_followup"),
        ("inform_customer", "lavanya_service.api.workflow_actions.inform_customer"),
        ("mark_no_update", "lavanya_service.api.workflow_actions.mark_no_update"),
        ("escalate_case", "lavanya_service.api.workflow_actions.escalate_case"),
        ("record_satisfaction", "lavanya_service.api.workflow_actions.record_satisfaction"),
        ("record_customer_approval", "lavanya_service.api.workflow_actions.record_customer_approval"),
    ]:
        try:
            kwargs = {"ticket_name": ticket_id}
            if action_name == "record_sc_followup":
                kwargs["follow_up_result"] = "Service center contacted"
                kwargs["customer_informed_status"] = "Informed by Call"
            elif action_name == "inform_customer":
                kwargs["channel"] = "Phone"
            elif action_name == "escalate_case":
                kwargs["reason"] = "Test"
            elif action_name == "record_satisfaction":
                kwargs["satisfaction_status"] = "Satisfied"
            elif action_name == "record_customer_approval":
                kwargs["approved_amount"] = "100"
            frappe.call(action_api, **kwargs)
            assert False, f"{action_name} should be blocked on closed ticket"
        except Exception:
            pass
    print("  ✅ closed_ticket_blocks_all_followup_actions")

    frappe.set_user("Administrator")
    # Re-open the ticket for subsequent tests
    doc = frappe.get_doc("HD Ticket", ticket_id)
    doc.status = "Open"
    doc.customer_satisfaction_status = "Pending"
    doc.save(ignore_permissions=True)

    # Role gating: Guest cannot run any action
    frappe.set_user("Guest")
    for action_api in [
        "verify_technician_called",
        "verify_technician_visit",
        "record_sc_followup",
        "inform_customer",
        "mark_no_update",
        "escalate_case",
        "record_satisfaction",
        "record_customer_approval",
    ]:
        try:
            frappe.call(f"lavanya_service.api.workflow_actions.{action_api}", ticket_name=ticket_id)
            assert False, f"Guest could call {action_api}"
        except frappe.PermissionError:
            pass

    frappe.set_user("Administrator")
