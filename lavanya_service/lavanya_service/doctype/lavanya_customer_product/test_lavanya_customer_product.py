# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestLavanyaCustomerProduct(FrappeTestCase):
    def setUp(self):
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer CP",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)

    def test_create_customer_product(self):
        """Test creating a customer product"""
        product = frappe.get_doc({
            "doctype": "Lavanya Customer Product",
            "customer": self.customer.name,
            "product_name": "Test AC",
            "product_brand": "Samsung",
            "serial_no": "SAMS12345678901",
            "is_active": 1
        }).insert()
        
        self.assertTrue(product.name.startswith("PROD-"))
        self.assertEqual(product.is_active, 1)

    def test_serial_number_validation(self):
        """Test serial number format validation"""
        product = frappe.get_doc({
            "doctype": "Lavanya Customer Product",
            "customer": self.customer.name,
            "product_name": "Test AC",
            "serial_no": "123",  # Invalid
            "is_active": 1
        })
        
        self.assertRaises(frappe.ValidationError, product.insert)

    def test_warranty_validation(self):
        """Test warranty expiry required when type set"""
        product = frappe.get_doc({
            "doctype": "Lavanya Customer Product",
            "customer": self.customer.name,
            "product_name": "Test AC",
            "warranty_type": "Manufacturer",
            # Missing warranty_expiry
            "is_active": 1
        })
        
        self.assertRaises(frappe.ValidationError, product.insert)

    def test_duplicate_serial_prevention(self):
        """Test duplicate active serial is blocked"""
        # Create first product
        product1 = frappe.get_doc({
            "doctype": "Lavanya Customer Product",
            "customer": self.customer.name,
            "product_name": "Test AC 1",
            "serial_no": "SAMS12345678901",
            "is_active": 1
        }).insert()
        
        # Try to create second product with same serial
        product2 = frappe.get_doc({
            "doctype": "Lavanya Customer Product",
            "customer": self.customer.name,
            "product_name": "Test AC 2",
            "serial_no": "SAMS12345678901",  # Duplicate
            "is_active": 1
        })
        
        self.assertRaises(frappe.ValidationError, product2.insert)

    def tearDown(self):
        frappe.db.rollback()
