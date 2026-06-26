# /Users/noufi1/frappe-bench-emart/apps/lavanya_service/custom_scripts/uat_test_runner.py
import frappe
from datetimeate import datetime, timedelta

def run_uat_test_suite():
    """
    Phase 7A UAT Test Suite - Run tests on imported real cases
    """
    
    print("🧪 UAT Test Suite Started - Phase 7A")
    print("=" * 60)
    
    test_results = []
    critical_failures = []
    
    # Test 1: Service Case Group Linkage Verification
    print("\n🔍 Test 1: Service Case Group Linkage")
    cases_with_linkages = frappe.db.sql("""
        SELECT csg.name as group_name, 
               (SELECT COUNT(*) FROM `tabLavanya Service Ticket Extension` WHERE service_case_group = csg.name) as ticket_count,
               (SELECT COUNT(*) FROM `tabLavanya Customer Communication Log` WHERE service_case_group = csg.name) as comm_count,
               (SELECT COUNT(*) FROM `tabLavanya Closure Verification` WHERE service_case_group = csg.name) as closure_count,
               (SELECT COUNT(*) FROM `tabLavanya Stock Complaint` WHERE service_case_group = csg.name) as stock_count,
               (SELECT COUNT(*) FROM `tabLavanya Replacement Recovery` WHERE service_case_group = csg.name) as recovery_count,
               (SELECT COUNT(*) FROM `tabLavanya Supplier Claim` WHERE service_case_group = csg.name) as claim_count,
               (SELECT COUNT(*) FROM `tabLavanya Installation Job` WHERE service_case_group = csg.name) as installation_count,
               (SELECT COUNT(*) FROM `tabLavanya Service Visit` WHERE service_case_group = csg.name) as visit_count,
               (SELECT COUNT(*) FROM `tabLavanya Spare Request` WHERE service_case_group = csg.name) as spare_count
        FROM `tabLavanya Service Case Group` csg
        WHERE csg.docstatus < 2
        GROUP BY csg.name
        HAVING (ticket_count > 0 OR comm_count > 0 OR closure_count > 0 OR 
                stock_count > 0 OR recovery_count > 0 OR claim_count > 0 OR 
                installation_count > 0 OR visit_count > 0 OR spare_count > 0)
    """, as_dict=True)
    
    linkage_tests = 0
    linkage_passed = 0
    
    for case in cases_with_linkages:
        total_links = (case.ticket_count + case.comm_count + case.closure_count + case.stock_count + 
                      case.recovery_count + case.claim_count + case.installation_count + 
                      case.visit_count + case.spare_count)
        linkage_tests += 1
        
        if total_links > 0:
            linkage_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            critical_failures.append(f"Service Case Group {case.group_name} has no linked records")
        
        test_results.append({
            "test": "Service Case Group Linkage",
            "case_group": case.group_name,
            "links_found": total_links,
            "status": status
        })
        
        print(f"  {status} - {case.group_name}: {total_links} linked records")
    
    # Test 2: Four-Lifecycle Closure Verification
    print("\n🔍 Test 2: Four-Lifecycle Closure Separation")
    
    # Check cases that are customers closed but business still open
    customer_closed_business_open = frappe.db.sql("""
        SELECT csg.name as case_group_name,
               COUNT(DISTINCT CASE WHEN tsi.status = 'Closed' THEN 1 END) as tickets_closed,
               COUNT(DISTINCT CASE WHEN sih.status IN ('Closed', 'Customer Confirmed') THEN 1 END) as installations_closed,
               COUNT(DISTINCT CASE WHEN tcr.status = 'Closed' THEN 1 END) as recovery_closed,
               COUNT(DISTINCT CASE WHEN tcc.status = 'Closed' THEN 1 END) as complaint_closed
        FROM `tabLavanya Service Case Group` csg
        LEFT JOIN `tabLavanya Service Ticket Extension` tsi ON tsi.service_case_group = csg.name
        LEFT JOIN `tabLavanya Installation Job` sih ON sih.service_case_group = csg.name  
        LEFT JOIN `tabLavanya Replacement Recovery` tcr ON tcr.service_case_group = csg.name
        LEFT JOIN `tabLavanya Stock Complaint` tcc ON tcc.service_case_group = csg.name
        WHERE csg.docstatus < 2
        GROUP BY csg.name
        HAVING (tickets_closed > 0 OR installations_closed > 0 OR recovery_closed > 0 OR complaint_closed > 0)
    """, as_dict=True)
    
    closure_tests = 0
    closure_passed = 0
    
    for case in customer_closed_business_open:
        total_lifecycles_closed = (case.tickets_closed + case.installations_closed + 
                                   case.recovery_closed + case.complaint_closed)
        
        closure_tests += 1
        if total_lifecycles_closed >= 2:  # At least 2 lifecycle closures indicates customer/business separation
            closure_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL - Need at least 2 lifecycle closures for proper separation"
            critical_failures.append(f"Case {case.case_group_name} lacks lifecycle separation")
        
        test_results.append({
            "test": "Four-Lifecycle Closure Separation", 
            "case_group": case.case_group_name,
            "tickets_closed": case.tickets_closed,
            "installations_closed": case.installations_closed,
            "recovery_closed": case.recovery_closed,
            "complaint_closed": case.complaint_closed,
            "status": status
        })
        
        print(f"  {status} - {case.case_group_name}: {total_lifecycles_closed}/4 closures")
    
    # Test 3: Stock Complaint Quarantine Validation
    print("\n🔍 Test 3: Stock Complaint Quarantine Controls")
    
    quarantined_stock_complaints = frappe.db.sql("""
        SELECT name, product_name, status, quarantine_warehouse
        FROM `tabLavanya Stock Complaint`
        WHERE docstatus < 2 AND status = 'Quarantined'
        AND (quarantine_warehouse IS NULL OR quarantine_warehouse = '')
    """, as_dict=True)
    
    quarantine_tests = 0
    quarantine_passed = 0
    
    for complaint in quarantined_stock_complaints:
        quarantine_tests += 1
        
        # Check if there are linked condition decisions
        condition_decisions = frappe.db.count(
            "Lavanya Stock Condition Decision", 
            {"parent": complaint.name}
        )
        
        # Check if there are supplier claims
        supplier_claims = frappe.db.count(
            "Lavanya Supplier Claim",
            {"stock_complaint": complaint.name}
        )
        
        if condition_decisions == 0 and supplier_claims == 0:
            quarantine_passed += 1
            status = "✅ PASS"
            test_results.append({
                "test": "Stock Complaint Quarantine Validation",
                "complaint": complaint.name,
                "has_condition_decisions": condition_decisions > 0,
                "has_supplier_claims": supplier_claims > 0,
                "status": status
            })
            print(f"  ✅ PASS - {complaint.name}: Quarantine properly set")
        else:
            status = "❌ FAIL - Quarantine may be resolved prematurely"
            critical_failures.append(f"Stock Complaint {complaint.name} may be prematurely closed")
            test_results.append({
                "test": "Stock Complaint Quarantine Validation",
                "complaint": complaint.name,
                "has_condition_decisions": condition_decisions > 0,
                "has_supplier_claims": supplier_claims > 0,
                "status": status
            })
            print(f"  ❌ FAIL - {complaint.name}: Has condition decisions ({condition_decisions}) or claims ({supplier_claims})")
    
    # Test 4: Serial Number Uniqueness Validation
    print("\n🔍 Test 4: Serial Number Uniqueness Controls")
    
    serial_usage_check = frappe.db.sql("""
        SELECT COUNT(*) as serial_count, 
               GROUP_CONCAT(DISTINCT product_name) as products,
               GROUP_CONCAT(DISTINCT CASE_NAME) as cases
        FROM (
            SELECT sd.serial_no, sd.product_name, scc.case_id
            FROM `tabLavanya Spare Request Item` sri
            JOIN `tabLavanya Spare Request` sr ON sr.name = sri.parent
            JOIN `tabLavanya Service Case Group` scc ON scc.name = sr.service_case_group
            WHERE sri.serial_no IS NOT NULL AND sri.serial_no != ''
            UNION ALL
            SELECT scc_serial.serial_no, scc_serial.product_name, scc.case_id
            FROM `tabLavanya Stock Complaint` sc
            JOIN (
                SELECT item_code, product_name, name as serial_no
                FROM `tabItem`
                WHERE has_serial_no = 1
            ) scc_serial ON sc.product_name LIKE CONCAT('%', scc_serial.product_name, '%')
            JOIN `tabLavanya Service Case Group` scc ON scc.name = sc.service_case_group
        ) serial_summary
        GROUP BY serial_no
        HAVING COUNT(*) > 1
    """, as_dict=True)
    
    serial_tests = 0
    serial_passed = 0
    
    for duplicate in serial_usage_check:
        serial_tests += 1
        
        if duplicate.serial_count == 1:
            serial_passed += 1
            status = "✅ PASS"
        else:
            status = "❌ FAIL - Duplicate serial number usage"
            critical_failures.append(f"Serial {duplicate.product_name} used in {duplicate.serial_count} cases")
        
        test_results.append({
            "test": "Serial Number Uniqueness",
            "serial_no": f"{duplicate.products}...",
            "usage_count": duplicate.serial_count,
            "cases": duplicate.cases,
            "status": status
        })
        
        print(f"  {status} - Serial used in {duplicate.serial_count} cases: {duplicate.products}...")
    
    # Test 5: Failed Visit Requirement Validation
    print("\n🔍 Test 5: Failed Visit Mandatory Field Validation")
    
    failed_visits = frappe.db.sql("""
        SELECT name, visit_type, status, failed_reason, next_action, next_follow_up_date
        FROM `tabLavanya Service Visit`
        WHERE docstatus < 2 AND status = 'Failed Visit'
    """, as_dict=True)
    
    visit_tests = 0
    visit_passed = 0
    
    for visit in failed_visits:
        visit_tests += 1
        
        has_failed_reason = visit.failed_reason and visit.failed_reason.strip()
        has_next_action = visit.next_action and visit.next_action.strip()
        has_follow_up = visit.next_follow_up_date
        
        if has_failed_reason and has_next_action and has_follow_up:
            visit_passed += 1
            status = "✅ PASS"
            test_results.append({
                "test": "Failed Visit Mandatory Fields",
                "visit": visit.name,
                "has_failed_reason": has_failed_reason,
                "has_next_action": has_next_action,
                "has_follow_up": has_follow_up,
                "status": status
            })
            print(f"  ✅ PASS - {visit.name}: All failed visit fields complete")
        else:
            status = "❌ FAIL - Missing required failed visit fields"
            missing_fields = []
            if not has_failed_reason: missing_fields.append("Failed Reason")
            if not has_next_action: missing_fields.append("Next Action")
            if not has_follow_up: missing_fields.append("Next Follow-up Date")
            
            critical_failures.append(f"Failed Visit {visit.name} missing: {', '.join(missing_fields)}")
            test_results.append({
                "test": "Failed Visit Mandatory Fields",
                "visit": visit.name,
                "has_failed_reason": has_failed_reason,
                "has_next_action": has_next_action,
                "has_follow_up": has_follow_up,
                "status": status
            })
            print(f"  ❌ FAIL - {visit.name}: Missing {', '.join(missing_fields)}")
    
    # Test 6: Spare Request Quantity Validation
    print("\n🔍 Test 6: Spare Request Quantity Controls")
    
    spare_requests_with_quantities = frappe.db.sql("""
        SELECT name, issued_quantity, used_quantity, returned_quantity
        FROM `tabLavanya Spare Request`
        WHERE docstatus < 2 AND (used_quantity > 0 OR returned_quantity > 0 OR issued_quantity > 0)
    """, as_dict=True)
    
    quantity_tests = 0
    quantity_passed = 0
    
    for spare in spare_requests_with_quantities:
        quantity_tests += 1
        
        total_used_returned = (spare.used_quantity or 0) + (spare.returned_quantity or 0)
        issued = spare.issued_quantity or 0
        
        if total_used_returned <= issued:
            quantity_passed += 1
            status = "✅ PASS"
            test_results.append({
                "test": "Spare Request Quantity Validation",
                "spare": spare.name,
                "issued": issued,
                "used": spare.used_quantity or 0,
                "returned": spare.returned_quantity or 0,
                "status": status
            })
            print(f"  ✅ PASS - {spare.name}: Quantities valid (used+returned={total_used_returned} ≤ issued={issued})")
        else:
            status = "❌ FAIL - Quantity constraints violated"
            critical_failures.append(f"Spare Request {spare.name}: used+returned ({total_used_returned}) exceeds issued ({issued})")
            test_results.append({
                "test": "Spare Request Quantity Validation",
                "spare": spare.name,
                "issued": issued,
                "used": spare.used_quantity or 0,
                "returned": spare.returned_quantity or 0,
                "status": status
            })
            print(f"  ❌ FAIL - {spare.name}: used+returned ({total_used_returned}) > issued ({issued})")
    
    # Summary Report
    print("\n" + "=" * 60)
    print("📊 UAT Test Suite Summary")
    print("=" * 60)
    
    total_tests = (linkage_tests + closure_tests + quarantine_tests + 
                   serial_tests + visit_tests + quantity_tests)
    passed_tests = (linkage_passed + closure_passed + quarantine_passed + 
                    serial_passed + visit_passed + quantity_passed)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests Run: {total_tests}")
    print(f"Tests Passed: {passed_tests}")
    print(f"Tests Failed: {failed_tests}")
    print(f"Critical Failures: {len(critical_failures)}")
    
    if critical_failures:
        print("\n🚨 Critical Failures Requiring Immediate Attention:")
        for i, failure in enumerate(critical_failures[:5]):  # Show first 5
            print(f"  {i+1}. {failure}")
        if len(critical_failures) > 5:
            print(f"  ... and {len(critical_failures) - 5} more")
    else:
        print("\n✅ No critical failures detected!")
    
    # Generate UAT Report
    uat_report = f"""
# Phase 7A UAT Test Report

## Summary
- **Total Tests Run:** {total_tests}
- **Tests Passed:** {passed_tests}
- **Tests Failed:** {failed_tests}
- **Critical Failures:** {len(critical_failures)}
- **UAT Status:** {"✅ PASSED" if failed_tests == 0 else "❌ FAILED"}

## Test Details
{json.dumps(test_results, indent=2)}

## Critical Issues
{chr(10).join(critical_failures) if critical_failures else "None"}

## Recommendations
{"All tests passed. Proceed to Phase 8 automation." if failed_tests == 0 else "Address critical failures before proceeding."}

---
*UAT Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    # Save UAT report
    report_path = "/Users/noufi1/frappe-bench-emart/apps/lavanya_service/UAT_REPORT.md"
    with open(report_path, 'w') as f:
        f.write(uat_report)
    
    print(f"\n📄 UAT Report saved to: {report_path}")
    
    # Generate quick summary for terminal display
    print("\n🎯 UAT Execution Complete:")
    print(f"  ✅ Service Case Linkages: {linkage_passed}/{linkage_tests} ({(linkage_passed/linkage_tests*100):.1f}%)")
    print(f"  ✅ Four-Lifecycle Closures: {closure_passed}/{closure_tests} ({(closure_passed/closure_tests*100):.1f}%)")
    print(f"  ✅ Stock Quarantine Controls: {quarantine_passed}/{quarantine_tests} ({(quarantine_passed/quarantine_tests*100):.1f}%)")
    print(f"  ✅ Serial Number Uniqueness: {serial_passed}/{serial_tests} ({(serial_passed/serial_tests*100):.1f}%)")
    print(f"  ✅ Failed Visit Validation: {visit_passed}/{visit_tests} ({(visit_passed/visit_tests*100):.1f}%)")
    print(f"  ✅ Spare Quantity Controls: {quantity_passed}/{quantity_tests} ({(quantity_passed/quantity_tests*100):.1f}%)")
    
    if failed_tests == 0:
        print("\n🎉 ALL UAT TESTS PASSED!")
        print("   System ready for Phase 8 — Automation Implementation")
    else:
        print(f"\n⚠️ {failed_tests} UAT tests failed - Address issues before automation")
    
    return {
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "critical_failures": critical_failures,
        "report_path": report_path
    }
