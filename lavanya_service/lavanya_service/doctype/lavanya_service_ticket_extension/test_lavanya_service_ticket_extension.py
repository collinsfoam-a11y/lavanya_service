# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestLavanyaServiceTicketExtension(FrappeTestCase):
    def setUp(self):
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer STE",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)
        
        self.group = frappe.get_doc({
            "doctype": "Lavanya Service Case Group",
            "title": "Test Group",
            "customer": self.customer.name,
            "primary_contact": "Test Contact",
            "primary_mobile": "9876543210",
            "ticket_type": "Complaint",
            "status": "Active"
        }).insert(ignore_permissions=True)

    def test_create_ticket_extension(self):
        """Test creating a ticket extension"""
        ticket = frappe.get_doc({
            "doctype": "Lavanya Service Ticket Extension",
            "lavanya_service_case_group": self.group.name,
            "customer_name": "Test Customer",
            "customer_number": "9876543210",
            "product_category": "AC",
            "status": "New"
        }).insert()
        
        self.assertTrue(ticket.name.startswith("TKT-"))
        self.assertEqual(ticket.status, "New")

    def test_mobile_validation(self):
        """Test mobile number validation"""
        ticket = frappe.get_doc({
            "doctype": "Lavanya Service Ticket Extension",
            "lavanya_service_case_group": self.group.name,
            "customer_name": "Test Customer",
            "customer_number": "123",  # Invalid
            "product_category": "AC",
            "status": "New"
        })
        
        self.assertRaises(frappe.ValidationError, ticket.insert)

    def test_pin_code_validation(self):
        """Test PIN code validation"""
        ticket = frappe.get_doc({
            "doctype": "Lavanya Service Ticket Extension",
            "lavanya_service_case_group": self.group.name,
            "customer_name": "Test Customer",
            "customer_number": "9876543210",
            "customer_site_pin": "123",  # Invalid
            "product_category": "AC",
            "status": "New"
        })
        
        self.assertRaises(frappe.ValidationError, ticket.insert)

    def test_payment_fields_validation(self):
        """Test payment fields validation"""
        ticket = frappe.get_doc({
            "doctype": "Lavanya Service Ticket Extension",
            "lavanya_service_case_group": self.group.name,
            "customer_name": "Test Customer",
            "customer_number": "9876543210",
            "product_category": "AC",
            "status": "New",
            "payment_received": 1,
            "payment_amount": 0  # Invalid
        })
        
        self.assertRaises(frappe.ValidationError, ticket.insert)

    def test_token_fields_validation(self):
        """Test token fields validation"""
        ticket = frappe.get_doc({
            "doctype": "Lavanya Service Ticket Extension",
            "lavanya_service_case_group": self.group.name,
            "customer_name": "Test Customer",
            "customer_number": "9876543210",
            "product_category": "AC",
            "status": "New",
            "token_issued": 1
            # Missing token_number
        })
        
        self.assertRaises(frappe.ValidationError, ticket.insert)

    def test_status_transitions(self):
        """Test status transitions"""
        ticket = frappe.get_doc({
            "doctype": "Lavanya Service Ticket Extension",
            "lavanya_service_case_group": self.group.name,
            "customer_name": "Test Customer",
            "customer_number": "9876543210",
            "product_category": "AC",
            "status": "New"
        }).insert()
        
        # Valid transition
        ticket.status = "In Progress"
        ticket.save()
        self.assertEqual(ticket.status, "In Progress")
        
        # Invalid transition (back to New)
        ticket.status = "New"
        self.assertRaises(frappe.ValidationError, ticket.save)

    def test_resolution_time_calculation(self):
        """Test resolution time calculation"""
        ticket = frappe.get_doc({
            "doctype": "Lavanya Service Ticket Extension",
            "lavanya_service_case_group": self.group.name,
            "customer_name": "Test Customer",
            "customer_number": "9876543210",
            "product_category": "AC",
            "status": "New"
        }).insert()
        
        ticket.status = "Resolved"
        ticket.save()
        
        self.assertEqual(ticket.resolution_date, today())
        self.assertIsNotNone(ticket.resolution_days)
        self.assertIsNotNone(ticket.resolution_hours)

    def tearDown(self):
        frappe.db.rollback()
