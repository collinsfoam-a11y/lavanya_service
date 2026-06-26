# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime


class TestLavanyaCustomerCommunicationLog(FrappeTestCase):
    def setUp(self):
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer CCL",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)

    def test_create_communication_log(self):
        """Test creating a communication log"""
        log = frappe.get_doc({
            "doctype": "Lavanya Customer Communication Log",
            "customer": self.customer.name,
            "communication_type": "Call",
            "direction": "Outbound",
            "communicated_at": now_datetime(),
            "summary": "Called customer to confirm appointment",
            "communicated_by": "Test Staff",
            "call_duration": 120
        }).insert()
        
        self.assertTrue(log.name.startswith("COMM-"))
        self.assertEqual(log.communication_type, "Call")

    def test_whatsapp_requires_mobile(self):
        """Test WhatsApp requires recipient mobile"""
        log = frappe.get_doc({
            "doctype": "Lavanya Customer Communication Log",
            "customer": self.customer.name,
            "communication_type": "WhatsApp",
            "direction": "Outbound",
            "communicated_at": now_datetime(),
            "summary": "Sent WhatsApp update",
            # Missing recipient_mobile
        })
        
        self.assertRaises(frappe.ValidationError, log.insert)

    def test_call_requires_duration(self):
        """Test Call requires call duration"""
        log = frappe.get_doc({
            "doctype": "Lavanya Customer Communication Log",
            "customer": self.customer.name,
            "communication_type": "Call",
            "direction": "Outbound",
            "communicated_at": now_datetime(),
            "summary": "Called customer",
            # Missing call_duration
        })
        
        self.assertRaises(frappe.ValidationError, log.insert)

    def test_mobile_validation(self):
        """Test mobile number validation"""
        log = frappe.get_doc({
            "doctype": "Lavanya Customer Communication Log",
            "customer": self.customer.name,
            "communication_type": "WhatsApp",
            "direction": "Outbound",
            "communicated_at": now_datetime(),
            "summary": "Sent WhatsApp",
            "recipient_mobile": "123"  # Invalid
        })
        
        self.assertRaises(frappe.ValidationError, log.insert)

    def tearDown(self):
        frappe.db.rollback()
