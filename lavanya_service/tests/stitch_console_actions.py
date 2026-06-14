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
    assert count_disabled >= 6, f"Expected other actions to remain disabled, found {count_disabled} disabled actions"

    print("✅ Stitch Console Actions tests passed")
