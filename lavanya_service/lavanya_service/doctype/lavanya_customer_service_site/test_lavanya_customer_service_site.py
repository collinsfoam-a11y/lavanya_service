# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestLavanyaCustomerServiceSite(FrappeTestCase):
    def setUp(self):
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer CSS",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)

    def test_create_service_site(self):
        """Test creating a service site"""
        site = frappe.get_doc({
            "doctype": "Lavanya Customer Service Site",
            "customer": self.customer.name,
            "site_name": "Test Site",
            "address": "123 Test Street",
            "pin_code": "110001",
            "city": "New Delhi",
            "is_active": 1
        }).insert()
        
        self.assertEqual(site.site_name, "Test Site")
        self.assertEqual(site.is_active, 1)

    def test_pin_code_validation(self):
        """Test PIN code validation"""
        site = frappe.get_doc({
            "doctype": "Lavanya Customer Service Site",
            "customer": self.customer.name,
            "site_name": "Test Site",
            "address": "123 Test Street",
            "pin_code": "123",  # Invalid
            "city": "New Delhi"
        })
        
        self.assertRaises(frappe.ValidationError, site.insert)

    def test_contact_number_validation(self):
        """Test contact number validation"""
        site = frappe.get_doc({
            "doctype": "Lavanya Customer Service Site",
            "customer": self.customer.name,
            "site_name": "Test Site",
            "address": "123 Test Street",
            "pin_code": "110001",
            "city": "New Delhi",
            "site_contact_number": "123"  # Invalid
        })
        
        self.assertRaises(frappe.ValidationError, site.insert)

    def test_gps_coordinates_validation(self):
        """Test GPS coordinates validation"""
        site = frappe.get_doc({
            "doctype": "Lavanya Customer Service Site",
            "customer": self.customer.name,
            "site_name": "Test Site",
            "address": "123 Test Street",
            "pin_code": "110001",
            "city": "New Delhi",
            "gps_coordinates": "invalid"  # Invalid
        })
        
        self.assertRaises(frappe.ValidationError, site.insert)

    def test_valid_gps_coordinates(self):
        """Test valid GPS coordinates"""
        site = frappe.get_doc({
            "doctype": "Lavanya Customer Service Site",
            "customer": self.customer.name,
            "site_name": "Test Site",
            "address": "123 Test Street",
            "pin_code": "110001",
            "city": "New Delhi",
            "gps_coordinates": "28.6139,77.2090"  # Delhi coordinates
        }).insert()
        
        self.assertEqual(site.gps_coordinates, "28.6139,77.2090")

    def tearDown(self):
        frappe.db.rollback()
