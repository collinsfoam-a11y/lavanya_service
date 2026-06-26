# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestLavanyaStockComplaint(FrappeTestCase):
    def setUp(self):
        self.customer = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": "Test Customer STK",
            "customer_type": "Individual"
        }).insert(ignore_permissions=True)
        
        self.group = frappe.get_doc({
            "doctype": "Lavanya Service Case Group",
            "title": "Test Group for Stock",
            "customer": self.customer.name,
            "primary_contact": "Test Contact",
            "primary_mobile": "9876543210",
            "ticket_type": "Complaint",
            "status": "Active"
        }).insert(ignore_permissions=True)

    def test_create_stock_complaint(self):
        """Test creating a stock complaint"""
        complaint = frappe.get_doc({
            "doctype": "Lavanya Stock Complaint",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "complaint_date": today(),
            "damage_type": "Physical Damage",
            "stock_item": "_Test Item",
            "description": "Test damage description",
            "status": "Draft"
        }).insert()
        
        self.assertTrue(complaint.name.startswith("SCMP-"))
        self.assertEqual(complaint.status, "Draft")

    def test_transit_damage_requires_lr(self):
        """Test Transit Damage requires LR number"""
        complaint = frappe.get_doc({
            "doctype": "Lavanya Stock Complaint",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "complaint_date": today(),
            "damage_type": "Transit Damage",
            "stock_item": "_Test Item",
            "description": "Transit damage",
            "status": "Draft"
            # Missing lr_number
        })
        
        self.assertRaises(frappe.ValidationError, complaint.insert)

    def test_missing_accessory_requires_details(self):
        """Test Missing Accessory requires details"""
        complaint = frappe.get_doc({
            "doctype": "Lavanya Stock Complaint",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "complaint_date": today(),
            "damage_type": "Missing Accessory",
            "stock_item": "_Test Item",
            "description": "Missing accessory",
            "status": "Draft"
            # Missing missing_accessory_details
        })
        
        self.assertRaises(frappe.ValidationError, complaint.insert)

    def test_quarantined_requires_warehouse(self):
        """Test Quarantined status requires quarantine warehouse"""
        complaint = frappe.get_doc({
            "doctype": "Lavanya Stock Complaint",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "complaint_date": today(),
            "damage_type": "Physical Damage",
            "stock_item": "_Test Item",
            "description": "Damage",
            "status": "Quarantined"
            # Missing quarantine_warehouse
        })
        
        self.assertRaises(frappe.ValidationError, complaint.insert)

    def test_saleable_requires_condition_decision(self):
        """Test Saleable status requires condition decision"""
        complaint = frappe.get_doc({
            "doctype": "Lavanya Stock Complaint",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "complaint_date": today(),
            "damage_type": "Physical Damage",
            "stock_item": "_Test Item",
            "description": "Damage",
            "status": "Saleable"
            # Missing condition_decision
        })
        
        self.assertRaises(frappe.ValidationError, complaint.insert)

    def test_written_off_requires_approval(self):
        """Test Written Off status requires manager approval"""
        complaint = frappe.get_doc({
            "doctype": "Lavanya Stock Complaint",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "complaint_date": today(),
            "damage_type": "Physical Damage",
            "stock_item": "_Test Item",
            "description": "Damage",
            "status": "Written Off"
            # Missing manager_approved_by
        })
        
        self.assertRaises(frappe.ValidationError, complaint.insert)

    def test_invalid_status_transition(self):
        """Test invalid status transition is blocked"""
        complaint = frappe.get_doc({
            "doctype": "Lavanya Stock Complaint",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "complaint_date": today(),
            "damage_type": "Physical Damage",
            "stock_item": "_Test Item",
            "description": "Damage",
            "status": "Draft"
        }).insert()
        
        # Invalid transition: Draft -> Saleable
        complaint.status = "Saleable"
        self.assertRaises(frappe.ValidationError, complaint.save)

    def test_valid_status_transition(self):
        """Test valid status transition works"""
        complaint = frappe.get_doc({
            "doctype": "Lavanya Stock Complaint",
            "customer": self.customer.name,
            "service_case_group": self.group.name,
            "complaint_date": today(),
            "damage_type": "Physical Damage",
            "stock_item": "_Test Item",
            "description": "Damage",
            "status": "Draft"
        }).insert()
        
        # Valid transition: Draft -> Identified
        complaint.status = "Identified"
        complaint.save()
        self.assertEqual(complaint.status, "Identified")

    def tearDown(self):
        frappe.db.rollback()
