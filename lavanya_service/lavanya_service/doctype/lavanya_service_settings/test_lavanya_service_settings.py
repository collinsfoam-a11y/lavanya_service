# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestLavanyaServiceSettings(FrappeTestCase):
    def test_get_settings(self):
        """Test getting settings"""
        settings = frappe.get_single("Lavanya Service Settings")
        self.assertIsNotNone(settings)

    def test_validate_auto_close_days(self):
        """Test auto close days validation"""
        settings = frappe.get_single("Lavanya Service Settings")
        settings.auto_close_days = 0
        self.assertRaises(frappe.ValidationError, settings.save)

    def test_validate_escalation_days(self):
        """Test escalation days validation"""
        settings = frappe.get_single("Lavanya Service Settings")
        settings.escalation_days = 0
        self.assertRaises(frappe.ValidationError, settings.save)

    def test_validate_reopen_days(self):
        """Test reopen days validation"""
        settings = frappe.get_single("Lavanya Service Settings")
        settings.allow_reopen_days = 0
        self.assertRaises(frappe.ValidationError, settings.save)

    def test_get_warehouse(self):
        """Test get warehouse method"""
        settings = frappe.get_single("Lavanya Service Settings")
        # This will return None if no warehouse is set
        warehouse = settings.get_warehouse("damaged_stock")
        # Just test the method exists and works
        self.assertTrue(hasattr(settings, 'get_warehouse'))

    def tearDown(self):
        frappe.db.rollback()
