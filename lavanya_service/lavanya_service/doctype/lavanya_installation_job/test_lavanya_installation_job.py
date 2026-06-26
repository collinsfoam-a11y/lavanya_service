# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days


class TestLavanyaInstallationJob(FrappeTestCase):
    def setUp(self):
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer Inst",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)

    def test_create_installation_job(self):
        """Test creating an installation job"""
        job = frappe.get_doc({
            "doctype": "Lavanya Installation Job",
            "customer": self.customer.name,
            "installation_type": "Free",
            "product_name": "Test AC",
            "product_category": "AC",
            "scheduled_date": add_days(today(), 1),
            "status": "Draft"
        }).insert()
        
        self.assertTrue(job.name.startswith("INST-"))
        self.assertEqual(job.status, "Draft")

    def test_paid_installation_requires_payment(self):
        """Test paid installation requires payment on close"""
        job = frappe.get_doc({
            "doctype": "Lavanya Installation Job",
            "customer": self.customer.name,
            "installation_type": "Paid",
            "product_name": "Test AC",
            "product_category": "AC",
            "scheduled_date": add_days(today(), 1),
            "status": "Closed",
            "completion_date": today(),
            "visit_status": "Successful",
            "customer_confirmation": 1
            # Missing payment fields
        })
        
        self.assertRaises(frappe.ValidationError, job.insert)

    def test_valid_status_transition(self):
        """Test valid status transition works"""
        job = frappe.get_doc({
            "doctype": "Lavanya Installation Job",
            "customer": self.customer.name,
            "installation_type": "Free",
            "product_name": "Test AC",
            "product_category": "AC",
            "scheduled_date": add_days(today(), 1),
            "status": "Draft"
        }).insert()
        
        # Valid transition: Draft -> Pending Assignment
        job.status = "Pending Assignment"
        job.save()
        self.assertEqual(job.status, "Pending Assignment")

    def test_invalid_status_transition(self):
        """Test invalid status transition is blocked"""
        job = frappe.get_doc({
            "doctype": "Lavanya Installation Job",
            "customer": self.customer.name,
            "installation_type": "Free",
            "product_name": "Test AC",
            "product_category": "AC",
            "scheduled_date": add_days(today(), 1),
            "status": "Draft"
        }).insert()
        
        # Invalid transition: Draft -> Closed
        job.status = "Closed"
        self.assertRaises(frappe.ValidationError, job.save)

    def test_failed_visit_sets_status(self):
        """Test failed visit requires visit status"""
        job = frappe.get_doc({
            "doctype": "Lavanya Installation Job",
            "customer": self.customer.name,
            "installation_type": "Free",
            "product_name": "Test AC",
            "product_category": "AC",
            "scheduled_date": add_days(today(), 1),
            "status": "Visit Completed"
            # Missing visit_status
        })
        
        self.assertRaises(frappe.ValidationError, job.insert)

    def tearDown(self):
        frappe.db.rollback()
