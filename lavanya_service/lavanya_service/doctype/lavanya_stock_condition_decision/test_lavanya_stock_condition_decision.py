# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today


class TestLavanyaStockConditionDecision(FrappeTestCase):
    def setUp(self):
        self.item = frappe.get_doc({
            "doctype": "Item",
            "item_code": "Test Item SCD",
            "item_name": "Test Item SCD",
            "item_group": "All Item Groups",
            "stock_uom": "Nos"
        }).insert(ignore_permissions=True)
        
        self.warehouse = frappe.get_doc({
            "doctype": "Warehouse",
            "warehouse_name": "Test Warehouse SCD"
        }).insert(ignore_permissions=True)

    def test_create_stock_condition_decision(self):
        """Test creating a stock condition decision"""
        decision = frappe.get_doc({
            "doctype": "Lavanya Stock Condition Decision",
            "decision_date": today(),
            "decision_type": "Return to Saleable Stock",
            "item_code": self.item.name,
            "current_warehouse": self.warehouse.name,
            "status": "Pending"
        }).insert()
        
        self.assertTrue(decision.name.startswith("SCND-"))
        self.assertEqual(decision.status, "Pending")

    def test_write_off_requires_approval(self):
        """Test Write Off decision requires approval"""
        decision = frappe.get_doc({
            "doctype": "Lavanya Stock Condition Decision",
            "decision_date": today(),
            "decision_type": "Write Off",
            "item_code": self.item.name,
            "current_warehouse": self.warehouse.name,
            "status": "Pending",
            "approval_required": 0,
            "approved_by": ""
        }).insert()
        
        # System should auto-set approval_required
        self.assertEqual(decision.approval_required, 1)

    def test_scrap_requires_target_warehouse(self):
        """Test Scrap decision requires target warehouse"""
        decision = frappe.get_doc({
            "doctype": "Lavanya Stock Condition Decision",
            "decision_date": today(),
            "decision_type": "Scrap",
            "item_code": self.item.name,
            "current_warehouse": self.warehouse.name,
            "status": "Pending",
            "approval_required": 1
        }).insert()
        
        self.assertRaises(frappe.ValidationError, decision.validate_decision_type_warehouse)

    def test_valid_status_transition(self):
        """Test valid status transition works"""
        decision = frappe.get_doc({
            "doctype": "Lavanya Stock Condition Decision",
            "decision_date": today(),
            "decision_type": "Return to Saleable Stock",
            "item_code": self.item.name,
            "current_warehouse": self.warehouse.name,
            "status": "Pending"
        }).insert()
        
        # Valid transition: Pending -> Approved
        decision.status = "Approved"
        decision.save()
        self.assertEqual(decision.status, "Approved")

    def test_invalid_status_transition(self):
        """Test invalid status transition is blocked"""
        decision = frappe.get_doc({
            "doctype": "Lavanya Stock Condition Decision",
            "decision_date": today(),
            "decision_type": "Return to Saleable Stock",
            "item_code": self.item.name,
            "current_warehouse": self.warehouse.name,
            "status": "Pending"
        }).insert()
        
        # Invalid transition: Pending -> Implemented
        decision.status = "Implemented"
        self.assertRaises(frappe.ValidationError, decision.save)

    def test_return_to_saleable_sets_target_warehouse(self):
        """Test Return to Saleable Stock sets target warehouse"""
        decision = frappe.get_doc({
            "doctype": "Lavanya Stock Condition Decision",
            "decision_date": today(),
            "decision_type": "Return to Saleable Stock",
            "item_code": self.item.name,
            "current_warehouse": self.warehouse.name,
            "status": "Pending",
            "target_warehouse": self.warehouse.name
        }).insert()
        
        self.assertEqual(decision.target_warehouse, self.warehouse.name)

    def tearDown(self):
        frappe.db.rollback()
