# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestLavanyaProductServicePolicy(FrappeTestCase):
    def test_create_product_service_policy(self):
        """Test creating a product service policy"""
        policy = frappe.get_doc({
            "doctype": "Lavanya Product Service Policy",
            "product_category": "AC",
            "serial_required": 1,
            "installation_required": 1,
            "demo_required": 0,
            "showroom_intake_allowed": 0,
            "can_repair_locally": 1,
            "default_warranty_months": 12,
            "doa_period_days": 7,
            "min_complaint_photos": 2,
            "photo_requirements": "Front panel, Serial label, Error display"
        }).insert()
        
        self.assertTrue(policy.name.startswith("PSP-"))
        self.assertEqual(policy.product_category, "AC")

    def test_unique_category_constraint(self):
        """Test that only one policy per category is allowed"""
        policy1 = frappe.get_doc({
            "doctype": "Lavanya Product Service Policy",
            "product_category": "TV",
            "serial_required": 1,
            "installation_required": 0,
            "demo_required": 0,
            "showroom_intake_allowed": 1,
            "can_repair_locally": 1,
            "default_warranty_months": 12,
            "doa_period_days": 7,
            "min_complaint_photos": 2,
            "photo_requirements": "Screen, Back panel"
        }).insert()
        
        policy2 = frappe.get_doc({
            "doctype": "Lavanya Product Service Policy",
            "product_category": "TV",
            "serial_required": 1,
            "installation_required": 0,
            "demo_required": 0,
            "showroom_intake_allowed": 1,
            "can_repair_locally": 1,
            "default_warranty_months": 24,
            "doa_period_days": 10,
            "min_complaint_photos": 3,
            "photo_requirements": "Screen, Back, Remote"
        })
        
        self.assertRaises(frappe.ValidationError, policy2.insert)

    def test_get_workflow_for_product(self):
        """Test getting workflow requirements"""
        policy = frappe.get_doc({
            "doctype": "Lavanya Product Service Policy",
            "product_category": "Refrigerator",
            "serial_required": 1,
            "installation_required": 0,
            "demo_required": 1,
            "showroom_intake_allowed": 1,
            "can_repair_locally": 1,
            "default_warranty_months": 24,
            "doa_period_days": 10,
            "min_complaint_photos": 2,
            "photo_requirements": "Front, Inside"
        }).insert()
        
        result = policy.get_workflow_for_product()
        self.assertTrue(result["demo_required"])
        self.assertEqual(result["default_warranty_months"], 24)

    def tearDown(self):
        frappe.db.rollback()
