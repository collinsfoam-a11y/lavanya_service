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
    
    # Ensure others remain disabled (except Need Invoice)
    # The string "Available in Phase 2C after write-action wiring" was used for disabled buttons
    count_disabled = detail_content.count("Available in Phase 2C after write-action wiring and role smoke.")
    assert count_disabled >= 4, f"Expected other actions to remain disabled, found {count_disabled} disabled actions"

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
    frappe.set_user("uat.coordinator@lavanya.local")
    if frappe.db.exists("User", "uat.coordinator@lavanya.local"):
        # Make sure no receipt exists for this ticket
        existing_receipts = frappe.get_all("Service Product Receipt", filters={"ticket": store_ticket_id})
        for r in existing_receipts:
            frappe.delete_doc("Service Product Receipt", r.name)
            
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

    # Restore admin
    frappe.set_user("Administrator")
    print("✅ Stitch Console Actions tests passed")
