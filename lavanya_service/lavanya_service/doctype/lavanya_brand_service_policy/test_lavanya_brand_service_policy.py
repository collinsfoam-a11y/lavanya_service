# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestLavanyaBrandServicePolicy(FrappeTestCase):
    def setUp(self):
        self.brand = frappe.get_doc({
            "doctype": "Supplier",
            "supplier_name": "Test Brand Policy",
            "supplier_group": "All Supplier Groups",
            "supplier_type": "Company"
        }).insert(ignore_permissions=True)

    def test_create_brand_service_policy(self):
        """Test creating a brand service policy"""
        policy = frappe.get_doc({
            "doctype": "Lavanya Brand Service Policy",
            "brand": self.brand.name,
            "toll_free_number": "1800-123-456",
            "whatsapp_contact": "+919876543210",
            "email": "service@testbrand.com",
            "asm_name": "Test ASM",
            "asm_contact": "+919876543211",
            "doa_period_days": 7,
            "warranty_period_months": 12,
            "average_sla_days": 5,
            "installation_required_categories": "AC, Washing Machine",
            "claim_document_requirement": "Invoice, Photo, Customer ID"
        }).insert()
        
        self.assertTrue(policy.name.startswith("BSP-"))
        self.assertEqual(policy.brand, self.brand.name)

    def test_unique_brand_constraint(self):
        """Test that only one policy per brand is allowed"""
        policy1 = frappe.get_doc({
            "doctype": "Lavanya Brand Service Policy",
            "brand": self.brand.name,
            "doa_period_days": 7,
            "warranty_period_months": 12,
            "installation_required_categories": "AC"
        }).insert()
        
        policy2 = frappe.get_doc({
            "doctype": "Lavanya Brand Service Policy",
            "brand": self.brand.name,
            "doa_period_days": 10,
            "warranty_period_months": 24,
            "installation_required_categories": "AC"
        })
        
        self.assertRaises(frappe.ValidationError, policy2.insert)

    def test_get_sla_for_product_category(self):
        """Test getting SLA for a specific product category"""
        policy = frappe.get_doc({
            "doctype": "Lavanya Brand Service Policy",
            "brand": self.brand.name,
            "doa_period_days": 7,
            "warranty_period_months": 12,
            "average_sla_days": 5,
            "installation_required_categories": "AC, Washing Machine",
            "escalation_path": "L1: Support → L2: Manager → L3: Director"
        }).insert()
        
        result = policy.get_sla_for_product_category("AC")
        self.assertTrue(result["installation_required"])
        self.assertEqual(result["doa_period_days"], 7)

    def tearDown(self):
        frappe.db.rollback()
