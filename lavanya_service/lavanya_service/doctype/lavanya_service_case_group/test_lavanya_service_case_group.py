# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestLavanyaServiceCaseGroup(FrappeTestCase):
    def setUp(self):
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer SCG",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)

    def test_create_service_case_group(self):
        """Test creating a service case group"""
        group = frappe.get_doc({
            "doctype": "Lavanya Service Case Group",
            "title": "Test Service Case",
            "customer": self.customer.name,
            "primary_contact": "Test Contact",
            "primary_mobile": "9876543210",
            "ticket_type": "Complaint",
            "status": "Active"
        }).insert()
        
        self.assertTrue(group.name.startswith("SCG-"))
        self.assertEqual(group.status, "Active")

    def test_mobile_validation(self):
        """Test mobile number validation"""
        group = frappe.get_doc({
            "doctype": "Lavanya Service Case Group",
            "title": "Test Mobile Validation",
            "customer": self.customer.name,
            "primary_contact": "Test Contact",
            "primary_mobile": "123",  # Invalid
            "ticket_type": "Complaint",
            "status": "Active"
        })
        
        self.assertRaises(frappe.ValidationError, group.insert)

    def test_status_transitions(self):
        """Test status transitions"""
        group = frappe.get_doc({
            "doctype": "Lavanya Service Case Group",
            "title": "Test Status Transitions",
            "customer": self.customer.name,
            "primary_contact": "Test Contact",
            "primary_mobile": "9876543210",
            "ticket_type": "Complaint",
            "status": "Active"
        }).insert()
        
        # Valid transition
        group.status = "In Progress"
        group.save()
        self.assertEqual(group.status, "In Progress")
        
        # Invalid transition (back to Active)
        group.status = "Active"
        self.assertRaises(frappe.ValidationError, group.save)

    def test_auto_close_date(self):
        """Test auto-set closed date"""
        group = frappe.get_doc({
            "doctype": "Lavanya Service Case Group",
            "title": "Test Auto Close",
            "customer": self.customer.name,
            "primary_contact": "Test Contact",
            "primary_mobile": "9876543210",
            "ticket_type": "Complaint",
            "status": "Active"
        }).insert()
        
        group.status = "All Closed"
        group.save()
        
        self.assertEqual(group.closed_date, today())

    def tearDown(self):
        frappe.db.rollback()
