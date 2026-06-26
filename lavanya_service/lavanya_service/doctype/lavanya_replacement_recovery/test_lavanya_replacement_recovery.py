# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestLavanyaReplacementRecovery(FrappeTestCase):
    def setUp(self):
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer RR",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)
        
        self.group = frappe.get_doc({
            "doctype": "Lavanya Service Case Group",
            "title": "Test Group for Recovery",
            "customer": self.customer.name,
            "primary_contact": "Test Contact",
            "primary_mobile": "9876543210",
            "ticket_type": "Complaint",
            "status": "Active"
        }).insert(ignore_permissions=True)

    def test_create_replacement_recovery(self):
        """Test creating a replacement recovery"""
        recovery = frappe.get_doc({
            "doctype": "Lavanya Replacement Recovery",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "replacement_type": "Same SKU",
            "old_item": "_Test Item",
            "replacement_item": "_Test Item",
            "status": "Draft"
        }).insert()
        
        self.assertTrue(recovery.name.startswith("RECOV-"))
        self.assertEqual(recovery.status, "Draft")

    def test_cross_sku_requires_financial_values(self):
        """Test Cross SKU requires old and replacement item values"""
        recovery = frappe.get_doc({
            "doctype": "Lavanya Replacement Recovery",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "replacement_type": "Cross SKU",
            "old_item": "_Test Item",
            "replacement_item": "_Test Item",
            "status": "Draft"
            # Missing old_item_value and replacement_item_value
        })
        
        self.assertRaises(frappe.ValidationError, recovery.insert)

    def test_credit_instead_requires_credit_note(self):
        """Test Credit Instead requires credit note"""
        recovery = frappe.get_doc({
            "doctype": "Lavanya Replacement Recovery",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "replacement_type": "Credit Instead",
            "old_item": "_Test Item",
            "replacement_item": "_Test Item",
            "status": "Draft"
            # Missing credit_note
        })
        
        self.assertRaises(frappe.ValidationError, recovery.insert)

    def test_closed_requires_four_lifecycle_checks(self):
        """Test Closed status requires all four lifecycle checks"""
        recovery = frappe.get_doc({
            "doctype": "Lavanya Replacement Recovery",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "replacement_type": "Same SKU",
            "old_item": "_Test Item",
            "replacement_item": "_Test Item",
            "status": "Closed"
            # Missing closure checks
        })
        
        self.assertRaises(frappe.ValidationError, recovery.insert)

    def test_closed_requires_closure_date(self):
        """Test Closed status requires closure date"""
        recovery = frappe.get_doc({
            "doctype": "Lavanya Replacement Recovery",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "replacement_type": "Same SKU",
            "old_item": "_Test Item",
            "replacement_item": "_Test Item",
            "status": "Closed",
            "customer_closure": 1,
            "stock_closure": 1,
            "supplier_closure": 1,
            "accounting_closure": 1
            # Missing closure_date
        })
        
        self.assertRaises(frappe.ValidationError, recovery.insert)

    def test_invalid_status_transition(self):
        """Test invalid status transition is blocked"""
        recovery = frappe.get_doc({
            "doctype": "Lavanya Replacement Recovery",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "replacement_type": "Same SKU",
            "old_item": "_Test Item",
            "replacement_item": "_Test Item",
            "status": "Draft"
        }).insert()
        
        # Invalid transition: Draft -> Closed
        recovery.status = "Closed"
        self.assertRaises(frappe.ValidationError, recovery.save)

    def test_valid_status_transition(self):
        """Test valid status transition works"""
        recovery = frappe.get_doc({
            "doctype": "Lavanya Replacement Recovery",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "replacement_type": "Same SKU",
            "old_item": "_Test Item",
            "replacement_item": "_Test Item",
            "status": "Draft"
        }).insert()
        
        # Valid transition: Draft -> Replacement Approved
        recovery.status = "Replacement Approved"
        recovery.save()
        self.assertEqual(recovery.status, "Replacement Approved")

    def test_financial_difference_calculation(self):
        """Test financial difference is calculated for Cross SKU"""
        recovery = frappe.get_doc({
            "doctype": "Lavanya Replacement Recovery",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "replacement_type": "Cross SKU",
            "old_item": "_Test Item",
            "replacement_item": "_Test Item",
            "old_item_value": 1000,
            "replacement_item_value": 1500,
            "status": "Draft"
        }).insert()
        
        self.assertEqual(recovery.financial_difference, 500)

    def tearDown(self):
        frappe.db.rollback()
