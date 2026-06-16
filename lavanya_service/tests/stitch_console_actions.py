import frappe
import os

def run():
    print("Running Stitch Console Actions Tests (Phase 2-C)...")

    # We need a test ticket
    tickets = frappe.get_all("HD Ticket", filters={"status": ["!=", "Closed"]}, limit=1)
    if not tickets:
        print("⚠️ No open tickets found to test Need Invoice action. Skipping backend tests.")
        return
        
    ticket_id = tickets[0].name
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
        
        # 5. Duplicate receipt is rejected
        try:
            frappe.call(api_receipt, ticket_name=store_ticket_id, accessories_received="Charger", physical_condition="Scratched")
            assert False, "Duplicate receipt creation should have been rejected"
        except Exception as e:
            assert "already has a linked Service Product Receipt" in str(e) or "already exists for ticket" in str(e), f"Unexpected duplicate error: {e}"
            
        # Clean up test receipt
        frappe.set_user("Administrator")
        # un-link
        frappe.db.set_value("HD Ticket", store_ticket_id, "service_product_receipt", None)
        frappe.delete_doc("Service Product Receipt", receipt_name)

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
    # Need a ticket with a receipt that is not already "Ready for Customer Pickup"
    # To keep it safe, we'll create one and link it.
    t_ready = frappe.new_doc("HD Ticket")
    t_ready.subject = "Test Ready for Pickup"
    t_ready.ticket_type = "Customer Product at Store"
    t_ready.serial_no = "TEST-SN-READY-1"
    cust_list_ready = frappe.get_all("HD Customer", limit=1)
    t_ready.customer = cust_list_ready[0].name if cust_list_ready else None
    t_ready.insert(ignore_permissions=True)
    
    res_receipt = frappe.call(api_receipt, ticket_name=t_ready.name, accessories_received="Box", physical_condition="Good")
    r_ready_name = res_receipt.get("receipt")
    
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

    # Clean up test ticket and receipt
    frappe.set_user("Administrator")
    frappe.db.set_value("HD Ticket", t_ready.name, "service_product_receipt", None)
    frappe.delete_doc("Service Product Receipt", r_ready_name)
    frappe.delete_doc("HD Ticket", t_ready.name)

    # Restore admin
    frappe.set_user("Administrator")
    print("✅ Stitch Console Actions tests passed")
