# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class LavanyaStockConditionDecision(Document):
    def validate(self):
        self.validate_required_links()
        self.validate_status_transition()
        self.validate_approval_rules()
        self.validate_decision_type_warehouse()

    def validate_required_links(self):
        """Validate all required linked documents exist"""
        if self.stock_complaint and not frappe.db.exists("Lavanya Stock Complaint", self.stock_complaint):
            frappe.throw(f"Stock Complaint {self.stock_complaint} does not exist")
        if self.replacement_recovery and not frappe.db.exists("Lavanya Replacement Recovery", self.replacement_recovery):
            frappe.throw(f"Replacement Recovery {self.replacement_recovery} does not exist")
        if self.supplier_claim and not frappe.db.exists("Lavanya Supplier Claim", self.supplier_claim):
            frappe.throw(f"Supplier Claim {self.supplier_claim} does not exist")
        if self.item_code and not frappe.db.exists("Item", self.item_code):
            frappe.throw(f"Item {self.item_code} does not exist")
        if self.current_warehouse and not frappe.db.exists("Warehouse", self.current_warehouse):
            frappe.throw(f"Current Warehouse {self.current_warehouse} does not exist")

    def validate_status_transition(self):
        """Validate status transitions"""
        valid_transitions = {
            "Pending": ["Approved", "Rejected", "Cancelled"],
            "Approved": ["Implemented", "Cancelled"],
            "Rejected": ["Cancelled"],
            "Implemented": [],
            "Cancelled": []
        }
        if self.is_new():
            return
        old_doc = self._doc_before_save
        if not old_doc or old_doc.status not in valid_transitions:
            return
        allowed = valid_transitions[old_doc.status]
        if self.status not in allowed:
            frappe.throw(f"Cannot transition from {old_doc.status} to {self.status}")

    def validate_approval_rules(self):
        """Validate approval rules based on decision type"""
        if self.decision_type in ["Write Off", "Scrap"]:
            if not self.approval_required:
                self.approval_required = 1
            if not self.approved_by:
                frappe.throw("Approval Required for Write Off or Scrap decisions")

    def validate_decision_type_warehouse(self):
        """Validate warehouse requirements based on decision type"""
        if self.decision_type in ["Return to Saleable Stock", "Move to Refurbished Stock", "Move to Display Stock", "Discount Sale"]:
            if not self.target_warehouse:
                frappe.throw("Target Warehouse is required for this decision type")
        pass
        if self.decision_type in ["Write Off", "Scrap"]:
            if not self.approved_by:
                frappe.throw("Approval required for Write Off/Scrap")
