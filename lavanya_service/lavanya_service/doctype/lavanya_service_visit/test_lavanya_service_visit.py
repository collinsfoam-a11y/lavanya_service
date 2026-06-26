# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days


class TestLavanyaServiceVisit(FrappeTestCase):
    def setUp(self):
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer Visit",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)

    def test_create_service_visit(self):
        """Test creating a service visit"""
        visit = frappe.get_doc({
            "doctype": "Lavanya Service Visit",
            "customer": self.customer.name,
            "product_name": "Test AC",
            "visit_type": "Preventive",
            "scheduled_date": add_days(today(), 1),
            "status": "Scheduled"
        }).insert()
        
        self.assertTrue(visit.name.startswith("VSIT-"))
        self.assertEqual(visit.status, "Scheduled")

    def test_completed_visit_requires_work_done(self):
        """Test completed visit requires work done"""
        visit = frappe.get_doc({
            "doctype": "Lavanya Service Visit",
            "customer": self.customer.name,
            "product_name": "Test AC",
            "visit_type": "Preventive",
            "scheduled_date": today(),
            "status": "Visit Completed"
            # Missing work_done
        })
        
        self.assertRaises(frappe.ValidationError, visit.insert)

    def test_failed_visit_requires_reason(self):
        """Test failed visit requires failed reason"""
        visit = frappe.get_doc({
            "doctype": "Lavanya Service Visit",
            "customer": self.customer.name,
            "product_name": "Test AC",
            "visit_type": "Preventive",
            "scheduled_date": today(),
            "status": "Failed Visit"
            # Missing failed_reason
        })
        
        self.assertRaises(frappe.ValidationError, visit.insert)

    def test_rating_validation(self):
        """Test customer rating must be 1-5"""
        visit = frappe.get_doc({
            "doctype": "Lavanya Service Visit",
            "customer": self.customer.name,
            "product_name": "Test AC",
            "visit_type": "Preventive",
            "scheduled_date": today(),
            "status": "Scheduled",
            "customer_rating": 6
        })
        
        self.assertRaises(frappe.ValidationError, visit.insert)

    def test_valid_status_transition(self):
        """Test valid status transition works"""
        visit = frappe.get_doc({
            "doctype": "Lavanya Service Visit",
            "customer": self.customer.name,
            "product_name": "Test AC",
            "visit_type": "Preventive",
            "scheduled_date": today(),
            "status": "Scheduled"
        }).insert()
        
        # Valid transition: Scheduled -> In Progress
        visit.status = "In Progress"
        visit.save()
        self.assertEqual(visit.status, "In Progress")

    def test_invalid_status_transition(self):
        """Test invalid status transition is blocked"""
        visit = frappe.get_doc({
            "doctype": "Lavanya Service Visit",
            "customer": self.customer.name,
            "product_name": "Test AC",
            "visit_type": "Preventive",
            "scheduled_date": today(),
            "status": "Scheduled"
        }).insert()
        
        # Invalid transition: Scheduled -> Visit Completed
        visit.status = "Visit Completed"
        self.assertRaises(frappe.ValidationError, visit.save)

    def test_time_validation(self):
        """Test check-out must be after check-in"""
        visit = frappe.get_doc({
            "doctype": "Lavanya Service Visit",
            "customer": self.customer.name,
            "product_name": "Test AC",
            "visit_type": "Preventive",
            "scheduled_date": today(),
            "status": "Scheduled"
        }).insert()
        
        visit.check_in_time = "2026-06-26 10:00:00"
        visit.check_out_time = "2026-06-26 09:00:00"
        self.assertRaises(frappe.ValidationError, visit.save)

    def tearDown(self):
        frappe.db.rollback()
