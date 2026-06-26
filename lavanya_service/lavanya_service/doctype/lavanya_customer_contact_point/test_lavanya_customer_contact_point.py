# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestLavanyaCustomerContactPoint(FrappeTestCase):
    def setUp(self):
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer CCP",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)

    def test_create_contact_point(self):
        """Test creating a contact point"""
        contact = frappe.get_doc({
            "doctype": "Lavanya Customer Contact Point",
            "customer": self.customer.name,
            "contact_name": "Test Contact",
            "mobile_number": "9876543210",
            "role": "Decision Maker",
            "is_primary": 1
        }).insert()
        
        self.assertEqual(contact.contact_name, "Test Contact")
        self.assertEqual(contact.is_primary, 1)

    def test_mobile_validation(self):
        """Test mobile number validation"""
        contact = frappe.get_doc({
            "doctype": "Lavanya Customer Contact Point",
            "customer": self.customer.name,
            "contact_name": "Test Contact",
            "mobile_number": "123",  # Invalid
            "role": "Decision Maker"
        })
        
        self.assertRaises(frappe.ValidationError, contact.insert)

    def test_email_validation(self):
        """Test email validation"""
        contact = frappe.get_doc({
            "doctype": "Lavanya Customer Contact Point",
            "customer": self.customer.name,
            "contact_name": "Test Contact",
            "mobile_number": "9876543210",
            "role": "Decision Maker",
            "email": "invalid-email"  # Invalid
        })
        
        self.assertRaises(frappe.ValidationError, contact.insert)

    def test_primary_contact_uniqueness(self):
        """Test only one primary contact per customer"""
        # Create first primary contact
        contact1 = frappe.get_doc({
            "doctype": "Lavanya Customer Contact Point",
            "customer": self.customer.name,
            "contact_name": "Primary Contact 1",
            "mobile_number": "9876543210",
            "role": "Decision Maker",
            "is_primary": 1
        }).insert()
        
        # Try to create second primary contact
        contact2 = frappe.get_doc({
            "doctype": "Lavanya Customer Contact Point",
            "customer": self.customer.name,
            "contact_name": "Primary Contact 2",
            "mobile_number": "9876543211",
            "role": "Decision Maker",
            "is_primary": 1
        })
        
        self.assertRaises(frappe.ValidationError, contact2.insert)

    def tearDown(self):
        frappe.db.rollback()
