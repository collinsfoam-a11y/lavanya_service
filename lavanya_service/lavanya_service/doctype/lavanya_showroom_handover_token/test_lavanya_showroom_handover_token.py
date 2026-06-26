# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestLavanyaShowroomHandoverToken(FrappeTestCase):
    def setUp(self):
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer SHT",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)
        
        self.group = frappe.get_doc({
            "doctype": "Lavanya Service Case Group",
            "title": "Test Group for Token",
            "customer": self.customer.name,
            "primary_contact": "Test Contact",
            "primary_mobile": "9876543210",
            "ticket_type": "Complaint",
            "status": "Active"
        }).insert(ignore_permissions=True)

    def test_create_token(self):
        """Test creating a showroom handover token"""
        token = frappe.get_doc({
            "doctype": "Lavanya Showroom Handover Token",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "customer_name": "Test Customer",
            "product_name": "Test AC",
            "accessories_handed_over": [
                {"item_name": "Remote", "qty": 1},
                {"item_name": "User Manual", "qty": 1}
            ],
            "product_condition_out": "Good",
            "handover_to_name": "Test Person",
            "handover_to_mobile": "9876543210",
            "handover_date": "2026-06-26",
            "status": "Draft"
        }).insert()
        
        self.assertTrue(token.name.startswith("TOKEN-"))
        self.assertEqual(token.status, "Draft")

    def test_mobile_validation(self):
        """Test mobile number validation"""
        token = frappe.get_doc({
            "doctype": "Lavanya Showroom Handover Token",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "customer_name": "Test Customer",
            "product_name": "Test AC",
            "accessories_handed_over": [
                {"item_name": "Remote", "qty": 1}
            ],
            "product_condition_out": "Good",
            "handover_to_name": "Test Person",
            "handover_to_mobile": "123",  # Invalid
            "handover_date": "2026-06-26",
            "status": "Draft"
        })
        
        self.assertRaises(frappe.ValidationError, token.insert)

    def test_accessories_required(self):
        """Test at least one accessory required"""
        token = frappe.get_doc({
            "doctype": "Lavanya Showroom Handover Token",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "customer_name": "Test Customer",
            "product_name": "Test AC",
            "accessories_handed_over": [],  # Empty
            "product_condition_out": "Good",
            "handover_to_name": "Test Person",
            "handover_to_mobile": "9876543210",
            "handover_date": "2026-06-26",
            "status": "Draft"
        })
        
        self.assertRaises(frappe.ValidationError, token.insert)

    def test_status_transitions(self):
        """Test status transitions"""
        token = frappe.get_doc({
            "doctype": "Lavanya Showroom Handover Token",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "customer_name": "Test Customer",
            "product_name": "Test AC",
            "accessories_handed_over": [
                {"item_name": "Remote", "qty": 1}
            ],
            "product_condition_out": "Good",
            "handover_to_name": "Test Person",
            "handover_to_mobile": "9876543210",
            "handover_date": "2026-06-26",
            "status": "Draft"
        }).insert()
        
        # Valid transition
        token.status = "OTP Sent"
        token.save()
        self.assertEqual(token.status, "OTP Sent")
        
        # Invalid transition (back to Draft)
        token.status = "Draft"
        self.assertRaises(frappe.ValidationError, token.save)

    def tearDown(self):
        frappe.db.rollback()
