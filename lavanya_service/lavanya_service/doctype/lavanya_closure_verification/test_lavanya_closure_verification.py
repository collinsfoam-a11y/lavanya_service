# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestLavanyaClosureVerification(FrappeTestCase):
    def setUp(self):
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer CV",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)
        
        self.group = frappe.get_doc({
            "doctype": "Lavanya Service Case Group",
            "title": "Test Group for Closure",
            "customer": self.customer.name,
            "primary_contact": "Test Contact",
            "primary_mobile": "9876543210",
            "ticket_type": "Complaint",
            "status": "Active"
        }).insert(ignore_permissions=True)

    def test_create_closure_verification(self):
        """Test creating a closure verification"""
        verification = frappe.get_doc({
            "doctype": "Lavanya Closure Verification",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "verified_by": "Administrator",
            "verified_date": today(),
            "status": "Pending"
        }).insert()
        
        self.assertTrue(verification.name.startswith("CVER-"))
        self.assertEqual(verification.status, "Pending")

    def test_verified_requires_checklist(self):
        """Test Verified status requires all checklist items"""
        verification = frappe.get_doc({
            "doctype": "Lavanya Closure Verification",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "verified_by": "Administrator",
            "verified_date": today(),
            "customer_satisfied": 1,
            "stock_accounted": 1,
            "supplier_claim_handled": 1,
            "accounting_closed": 1,
            # Missing warranty_documented, all_photos_uploaded, all_documents_attached
            "status": "Verified"
        })
        
        self.assertRaises(frappe.ValidationError, verification.insert)

    def test_status_transitions(self):
        """Test status transitions"""
        verification = frappe.get_doc({
            "doctype": "Lavanya Closure Verification",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "verified_by": "Administrator",
            "verified_date": today(),
            "status": "Pending"
        }).insert()
        
        # Valid transition
        verification.status = "Verified"
        verification.customer_satisfied = 1
        verification.stock_accounted = 1
        verification.supplier_claim_handled = 1
        verification.accounting_closed = 1
        verification.warranty_documented = 1
        verification.all_photos_uploaded = 1
        verification.all_documents_attached = 1
        verification.save()
        self.assertEqual(verification.status, "Verified")
        
        # Invalid transition (back to Pending)
        verification.status = "Pending"
        self.assertRaises(frappe.ValidationError, verification.save)

    def tearDown(self):
        frappe.db.rollback()
