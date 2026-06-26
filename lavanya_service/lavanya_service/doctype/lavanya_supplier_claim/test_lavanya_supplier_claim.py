# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestLavanyaSupplierClaim(FrappeTestCase):
    def setUp(self):
        self.supplier = frappe.get_doc({
            "doctype": "Supplier",
            "supplier_name": "Test Supplier SC",
            "supplier_group": "All Supplier Groups"
        }).insert(ignore_permissions=True)
        
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer SC",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)
        
        self.group = frappe.get_doc({
            "doctype": "Lavanya Service Case Group",
            "title": "Test Group for Claim",
            "customer": self.customer.name,
            "primary_contact": "Test Contact",
            "primary_mobile": "9876543210",
            "ticket_type": "Complaint",
            "status": "Active"
        }).insert(ignore_permissions=True)

    def test_create_supplier_claim(self):
        """Test creating a supplier claim"""
        claim = frappe.get_doc({
            "doctype": "Lavanya Supplier Claim",
            "supplier": self.supplier.name,
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "claim_type": "Defective Product",
            "claim_date": today(),
            "status": "Draft"
        }).insert()
        
        self.assertTrue(claim.name.startswith("SCLM-"))
        self.assertEqual(claim.status, "Draft")

    def test_claim_registered_requires_reference(self):
        """Test Claim Registered status requires reference or override"""
        claim = frappe.get_doc({
            "doctype": "Lavanya Supplier Claim",
            "supplier": self.supplier.name,
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "claim_type": "Defective Product",
            "claim_date": today(),
            "status": "Claim Registered"
            # Missing claim_reference_no and manager_override_reason
        })
        
        self.assertRaises(frappe.ValidationError, claim.insert)

    def test_credit_note_requires_amount(self):
        """Test Credit Note settlement requires expected amount"""
        claim = frappe.get_doc({
            "doctype": "Lavanya Supplier Claim",
            "supplier": self.supplier.name,
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "claim_type": "Defective Product",
            "claim_date": today(),
            "status": "Draft",
            "settlement_type": "Credit Note"
            # Missing expected_credit_note_amount
        })
        
        self.assertRaises(frappe.ValidationError, claim.insert)

    def test_replacement_requires_item(self):
        """Test Replacement settlement requires expected item"""
        claim = frappe.get_doc({
            "doctype": "Lavanya Supplier Claim",
            "supplier": self.supplier.name,
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "claim_type": "Defective Product",
            "claim_date": today(),
            "status": "Draft",
            "settlement_type": "Replacement"
            # Missing expected_replacement_item
        })
        
        self.assertRaises(frappe.ValidationError, claim.insert)

    def test_settled_requires_closure_date(self):
        """Test Settled status requires supplier closure date"""
        claim = frappe.get_doc({
            "doctype": "Lavanya Supplier Claim",
            "supplier": self.supplier.name,
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "claim_type": "Defective Product",
            "claim_date": today(),
            "status": "Settled"
            # Missing supplier_closure_date
        })
        
        self.assertRaises(frappe.ValidationError, claim.insert)

    def test_invalid_status_transition(self):
        """Test invalid status transition is blocked"""
        claim = frappe.get_doc({
            "doctype": "Lavanya Supplier Claim",
            "supplier": self.supplier.name,
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "claim_type": "Defective Product",
            "claim_date": today(),
            "status": "Draft"
        }).insert()
        
        # Invalid transition: Draft -> Settled
        claim.status = "Settled"
        self.assertRaises(frappe.ValidationError, claim.save)

    def test_valid_status_transition(self):
        """Test valid status transition works"""
        claim = frappe.get_doc({
            "doctype": "Lavanya Supplier Claim",
            "supplier": self.supplier.name,
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "claim_type": "Defective Product",
            "claim_date": today(),
            "status": "Draft"
        }).insert()
        
        # Valid transition: Draft -> Claim Registered
        claim.status = "Claim Registered"
        claim.claim_reference_no = "REF-001"
        claim.save()
        self.assertEqual(claim.status, "Claim Registered")

    def test_negative_claim_amount(self):
        """Test negative claim amount is blocked"""
        claim = frappe.get_doc({
            "doctype": "Lavanya Supplier Claim",
            "supplier": self.supplier.name,
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "claim_type": "Defective Product",
            "claim_date": today(),
            "status": "Draft",
            "settlement_type": "Credit Note",
            "expected_credit_note_amount": -100
        })
        
        self.assertRaises(frappe.ValidationError, claim.insert)

    def tearDown(self):
        frappe.db.rollback()
