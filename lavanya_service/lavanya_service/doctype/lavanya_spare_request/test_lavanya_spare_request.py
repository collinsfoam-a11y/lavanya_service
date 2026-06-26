# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days


class TestLavanyaSpareRequest(FrappeTestCase):
    def setUp(self):
        self.user = frappe.get_doc({
            "doctype": "User",
            "email": "test_spare_request@example.com",
            "first_name": "Test",
            "last_name": "User"
        }).insert(ignore_permissions=True)

    def test_create_spare_request(self):
        """Test creating a spare request"""
        request = frappe.get_doc({
            "doctype": "Lavanya Spare Request",
            "requestor": self.user.name,
            "urgency": "Medium",
            "reason": "Need spare part for repair",
            "required_by_date": add_days(today(), 3),
            "spare_items": [
                {"spare_item": "Test Spare", "quantity": 2}
            ]
        }).insert()
        
        self.assertTrue(request.name.startswith("SPRQ-"))
        self.assertEqual(request.status, "Draft")

    def test_used_plus_returned_exceeds_issued(self):
        """Test used + returned cannot exceed issued"""
        request = frappe.get_doc({
            "doctype": "Lavanya Spare Request",
            "requestor": self.user.name,
            "urgency": "Medium",
            "reason": "Need spare part",
            "required_by_date": add_days(today(), 3),
            "spare_items": [
                {"spare_item": "Test Spare", "quantity": 2}
            ],
            "issued_quantity": 5,
            "used_quantity": 3,
            "returned_quantity": 3
        })
        
        self.assertRaises(frappe.ValidationError, request.insert)

    def test_chargeable_requires_amount(self):
        """Test chargeable spare requires customer payable amount"""
        request = frappe.get_doc({
            "doctype": "Lavanya Spare Request",
            "requestor": self.user.name,
            "urgency": "Medium",
            "reason": "Need spare part",
            "required_by_date": add_days(today(), 3),
            "spare_items": [
                {"spare_item": "Test Spare", "quantity": 2}
            ],
            "chargeable": 1,
            "status": "Closed"
            # Missing customer_payable_amount
        })
        
        self.assertRaises(frappe.ValidationError, request.insert)

    def test_valid_status_transition(self):
        """Test valid status transition works"""
        request = frappe.get_doc({
            "doctype": "Lavanya Spare Request",
            "requestor": self.user.name,
            "urgency": "Medium",
            "reason": "Need spare part",
            "required_by_date": add_days(today(), 3),
            "spare_items": [
                {"spare_item": "Test Spare", "quantity": 2}
            ],
            "status": "Draft"
        }).insert()
        
        # Valid transition: Draft -> Requested
        request.status = "Requested"
        request.save()
        self.assertEqual(request.status, "Requested")

    def test_invalid_status_transition(self):
        """Test invalid status transition is blocked"""
        request = frappe.get_doc({
            "doctype": "Lavanya Spare Request",
            "requestor": self.user.name,
            "urgency": "Medium",
            "reason": "Need spare part",
            "required_by_date": add_days(today(), 3),
            "spare_items": [
                {"spare_item": "Test Spare", "quantity": 2}
            ],
            "status": "Draft"
        }).insert()
        
        # Invalid transition: Draft -> Issued
        request.status = "Issued"
        self.assertRaises(frappe.ValidationError, request.save)

    def test_approval_sets_date(self):
        """Test approval sets approval date"""
        request = frappe.get_doc({
            "doctype": "Lavanya Spare Request",
            "requestor": self.user.name,
            "urgency": "Medium",
            "reason": "Need spare part",
            "required_by_date": add_days(today(), 3),
            "spare_items": [
                {"spare_item": "Test Spare", "quantity": 2}
            ],
            "status": "Requested"
        }).insert()
        
        request.status = "Approved"
        request.approved_by = self.user.name
        request.save()
        
        self.assertEqual(request.approval_date, today())

    def test_used_exceeds_issued(self):
        """Test used quantity cannot exceed issued"""
        request = frappe.get_doc({
            "doctype": "Lavanya Spare Request",
            "requestor": self.user.name,
            "urgency": "Medium",
            "reason": "Need spare part",
            "required_by_date": add_days(today(), 3),
            "spare_items": [
                {"spare_item": "Test Spare", "quantity": 2}
            ],
            "issued_quantity": 2,
            "used_quantity": 3
        })
        
        self.assertRaises(frappe.ValidationError, request.insert)

    def tearDown(self):
        frappe.db.rollback()
