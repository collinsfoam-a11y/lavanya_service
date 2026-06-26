# /Users/noufi1/frappe-bench-emart/apps/lavanya_service/custom_scripts/uat_import.py
import frappe
import json
from datetime import datetime

def import_uat_cases():
    """
    UAT Import script for Phase 7A - Process real Lavanya cases with masked data
    """
    
    # UAT test cases (masked data from previous templates)
    uat_cases = [
        {
            "case_id": "CUST-001",
            "case_type": "Customer Complaint",
            "customer_code": "LAV-001",
            "primary_mobile": "98XXXXXX42",
            "alt_mobile": "97XXXXXX11", 
            "pin": "673612",
            "area": "Middle Area",
            "product_category": "TV",
            "brand": "TCL",
            "model": "SN-XXXX-1045",
            "invoice": "INV-2026-0001",
            "purchase_date": "2025-10-15",
            "complaint": "TV display blurred on screen",
            "status": "Active",
            "expected_workflow": "Wait for service call",
            "linked_docs": ["Customer-12345"],
            "expected_closure": "Service closure",
            "edge_case": "Repair SLAs met"
        },
        # ... continue with all 30 cases (include them from previous messages)
        {
            "case_id": "CUST-030",
            "case_type": "Demo / Installation",
            "customer_code": "LAV-030",
            "primary_mobile": "91XXXXXX76",
            "alt_mobile": "93XXXXXX87",
            "pin": "673652",
            "area": "Downtown Area",
            "product_category": "Water Purifier",
            "brand": "Havells",
            "model": "SN-XXXX-1964",
            "invoice": "INV-2026-0300",
            "purchase_date": "2026-01-25",
            "complaint": "Installation needed",
            "status": "Assigned",
            "expected_workflow": "Technician dispatch",
            "linked_docs": ["Customer-12374"],
            "expected_closure": "Installation completion",
            "edge_case": "Site access issue"
        }
    ]
    
    import_records_count = 0
    error_records = []
    
    for case_data in uat_cases:
        try:
            # Create Customer if not exists
            customer_name = f"UAT Customer {case_data['customer_code']}"
            customer = frappe.get_doc({
                "doctype": "Customer",
                "customer_name": customer_name,
                "customer_type": "Individual",
                "mobile_no": case_data["primary_mobile"],
                "phone": case_data.get("alt_mobile", ""),
                "territory": "All Territories",
                "customer_group": "UAT Customers"
            }).insert(ignore_permissions=True)
            
            # Create Service Case Group
            group = frappe.get_doc({
                "doctype": "Lavanya Service Case Group",
                "title": f"UAT Case {case_data['case_id']} - {case_data['case_type']}",
                "customer": customer.name,
                "primary_contact": customer_name,
                "primary_mobile": case_data["primary_mobile"],
                "ticket_type": "Complaint" if case_data["case_type"] == "Customer Complaint" else "Installation",
                "status": "Active" if case_data["status"] == "Active" else "In Progress",
                "product_category": case_data["product_category"],
                "product_name": f"{case_data['product_category']} {case_data['brand']}",
                "brand": case_data["brand"],
                "installation_required": 1 if case_data["case_type"] in ["Demo / Installation"] else 0,
                "description": case_data["complaint"],
                "do_you_have_photo": 0,
                "proof_required_by_sla": 1 if case_data["edge_case"] else 0
            }).insert(ignore_permissions=True)
            
            import_records_count += 1
            print(f"✅ Created Service Case Group: {group.name}")
            
            # Create Complaint/Communication based on case type
            if case_data["case_type"] == "Customer Complaint":
                comm_log = frappe.get_doc({
                    "doctype": "Lavanya Customer Communication Log",
                    "service_case_group": group.name,
                    "customer": customer.name,
                    "ticket": "TKT-2026-0001",  # Would be real from Helpdesk
                    "communication_mode": "WhatsApp" if case_data["primary_mobile"].startswith("9") else "Email",
                    "communication_date": datetime.now().strftime("%Y-%m-%d"),
                    "communication_description": f"Initial complaint: {case_data['complaint']}",
                    "communication_type": "Complaint",
                    "status": "Sent" if case_data["status"] == "Active" else "In Progress",
                    "next_action": "Service technician appointment" if case_data["status"] == "Active" else "Investigation",
                    "next_follow_up_date": (datetime.now().replace(day=15) if case_data["case_type"] == "Customer Complaint" else datetime.now()).strftime("%Y-%m-%d")
                }).insert(ignore_permissions=True)
                
            elif case_data["case_type"] == "Stock Complaint":
                stock_complaint = frappe.get_doc({
                    "doctype": "Lavanya Stock Complaint",
                    "customer": customer.name,
                    "service_case_group": group.name,
                    "complaint_type": "Damage",
                    "product_category": case_data["product_category"],
                    "product_name": f"{case_data['product_category']} {case_data['brand']}",
                    "serial_no": case_data["model"],
                    "complaint_date": datetime.now().strftime("%Y-%m-%d"),
                    "description": case_data["complaint"],
                    "reported_to_supplier": 0,
                    "status": "Reported",
                    "quarantine_warehouse": "Lavanya - Customer Return Hold" if case_data["edge_case"] == "Quarantine warehouse not available" else None
                }).insert(ignore_permissions=True)
               
                
            elif case_data["case_type"] == "Spare Request":
                # Get the full workflow into spare request creation
                spare_request = frappe.get_doc({
                    "doctype": "Lavanya Spare Request",  # Changed from Lavanya Spare Request to correct DocType
                    "requestor": frappe.session.user,  # Use the logged in user
                    "service_team": "Lavanya Service Center-001",  # Need to get a valid Service Center
                    "ticket": "TKT-2026-0015",  # Need to create a valid Ticket
                    "service_case_group": group.name,
                    "urgency": "High" if case_data["case_type"] == "Customer Complaint" else "Medium",
                    "reason": case_data["complaint"],
                    "required_by_date": (datetime.now().replace(day=15) if case_data["case_type"] == "Customer Complaint" else datetime.now()).strftime("%Y-%m-%d"),
                    "chargeable": 1 if case_data["case_type"] == "Spare Request" else 0,
                    "customer_payable_amount": 500 if case_data["case_type"] == "Spare Request" and case_data["edge_case"] == "Surcharge applied" else None,
                    "approved_by": "Administrator" if case_data["status"] == "Approved" or case_data["status"] == "Issued" else None,
                    "approval_date": datetime.now().strftime("%Y-%m-%d") if case_data["status"] == "Approved" else None,
                    "source_warehouse": "Lavanya - Service Center",
                    "issued_quantity": 1,
                    "status": "Approved" if case_data["case_type"] in ["Spare Request", "Demo / Installation"] else case_data["status"],
                    "spare_items": [{"spare_item": f"{case_data['product_category']} Part", "quantity": 1}]
                }).insert(ignore_permissions=True)
                
            elif case_data["case_type"] == "Service Visit":
                # Get the full workflow into service visit creation
                service_visit = frappe.get_doc({
                    "doctype": "Lavanya Service Visit",
                    "customer": customer.name,
                    "service_case_group": group.name,
                    "product_name": f"{case_data['product_category']} {case_data['brand']}",
                    "product_category": case_data["product_category"],
                    "serial_no": case_data["model"],
                    "visit_type": "Installation Check" if case_data["case_type"] == "Demo / Installation" else "Follow-Up",
                    "scheduled_date": datetime.now().strftime("%Y-%m-%d") if case_data["status"] == "Scheduled" else case_data["purchase_date"],
                    "technician": "TECH-001",  # Need to get a valid Technician
                    "service_team": "Lavanya Service Center-001",  # Need a valid Service Center
                    "check_in_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if case_data["status"] == "In Progress" else None,
                    "check_out_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if case_data["status"] == "Visit Completed" else None,
                    "visit_result": "Successful" if case_data["status"] == "Visit Completed" else "Failed",
                    "work_done": "Service completed successfully" if case_data["status"] == "Visit Completed" else case_data["complaint"],
                    "customer_feedback": "Excellent service" if case_data["case_type"] == "Service Visit" else "",
                    "customer_rating": 4 if case_data["case_type"] == "Service Visit" else None,
                    "status": "Scheduled" if case_data["status"] == "Scheduled" else "Visit Completed" if case_data["status"] == "Visit Completed" else case_data["status"],
                    "before_photo": None,
                    "after_photo": None,
                    "customer_signature": None if case_data["edge_case"] == "Site access issue" else None,
                    "next_action": "Next maintenance check" if case_data["case_type"] == "Service Visit" else None,
                    "next_follow_up_date": (datetime.now().replace(day=15) if case_data["case_type"] == "Service Visit" else datetime.now().replace(day=20)).strftime("%Y-%m-%d")
                }).insert(ignore_permissions=True)
                
            print(f"✅ Created UAT case: {case_data['case_id']} - {case_data['case_type']} (Group: {group.name})")
            \n        except Exception as e:
            error_records.append({"case": case_data["case_id"], "error": str(e)})
            print(f"❌ Error importing {case_data['case_id']}: {e}")
    
    print(f"\n📊 UAT Import Summary:")
    print(f"  ✅ Successfully imported: {import_records_count} cases")
    print(f"  ❌ Errors encountered: {len(error_records)}")
    
    if error_records:
        print(f"\n⚠️ Error Details:")
        for error in error_records[:5]:  # Show first 5 errors
            print(f"  - {error['case']}: {error['error']}")
    
    return {"success": import_records_count, "errors": error_records}
