# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class LavanyaStockComplaint(Document):
    def validate(self):
        self.validate_required_links()
        self.validate_status_transition()
        self.validate_damage_type_fields()
        self.validate_serialized_item()
        self.validate_quarantine_rules()
        self.validate_closure_rules()

    def validate_required_links(self):
        """Validate all required linked documents exist"""
        if self.customer and not frappe.db.exists("Customer", self.customer):
            frappe.throw(f"Customer {self.customer} does not exist")
        if self.service_case_group and not frappe.db.exists("Lavanya Service Case Group", self.service_case_group):
            frappe.throw(f"Service Case Group {self.service_case_group} does not exist")
        if self.stock_item and not frappe.db.exists("Item", self.stock_item):
            frappe.throw(f"Item {self.stock_item} does not exist")

    def validate_status_transition(self):
        """Validate status transitions"""
        valid_transitions = {
            "Draft": ["Identified", "Cancelled"],
            "Identified": ["Quarantined", "Cancelled"],
            "Quarantined": ["Supplier Informed", "Claim Registered", "Repair Pending", "Replacement Pending", "Cancelled"],
            "Supplier Informed": ["Claim Registered", "Cancelled"],
            "Claim Registered": ["Pickup Pending", "Sent to Supplier", "Cancelled"],
            "Pickup Pending": ["Sent to Supplier", "Cancelled"],
            "Sent to Supplier": ["Repair Pending", "Replacement Pending", "Credit Note Pending", "Cancelled"],
            "Repair Pending": ["Returned Repaired", "Cancelled"],
            "Replacement Pending": ["Saleable", "Cancelled"],
            "Credit Note Pending": ["Closed", "Cancelled"],
            "Returned Repaired": ["Saleable", "Cancelled"],
            "Saleable": ["Closed"],
            "Written Off": ["Closed"],
            "Closed": [],
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

    def validate_damage_type_fields(self):
        """Validate required fields based on damage type"""
        if self.damage_type == "Transit Damage":
            if not self.lr_number:
                frappe.throw("LR Number is required for Transit Damage")
            if not self.transporter_name:
                frappe.throw("Transporter Name is required for Transit Damage")
        
        if self.damage_type == "Missing Accessory":
            if not self.missing_accessory_details:
                frappe.throw("Missing Accessory Details are required")

    def validate_serialized_item(self):
        """Validate serial number is required for serialized items"""
        if self.stock_item:
            item = frappe.get_doc("Item", self.stock_item)
            if item.has_serial_no and not self.serial_no:
                frappe.throw("Serial Number is required for serialized items")

    def validate_quarantine_rules(self):
        """Validate quarantine warehouse rules"""
        if self.status == "Quarantined":
            if not self.quarantine_warehouse:
                frappe.throw("Quarantine Warehouse is required when status is Quarantined")

    def validate_closure_rules(self):
        """Validate closure rules"""
        if self.status in ["Saleable", "Written Off"]:
            if self.status == "Saleable" and not self.condition_decision:
                frappe.throw("Stock Condition Decision is required for Saleable status")
            if self.status == "Written Off":
                if not self.manager_approved_by:
                    frappe.throw("Manager Approval is required for Written Off status")

    def before_submit(self):
        """Validate submit readiness"""
        if self.status == "Draft":
            frappe.throw("Cannot submit Draft complaint. Update status first.")

    def on_submit(self):
        """Update case group lifecycle flags"""
        if self.service_case_group:
            # Check if all stock complaints are resolved
            unresolved = frappe.get_all(
                "Lavanya Stock Complaint",
                filters={
                    "service_case_group": self.service_case_group,
                    "status": ["not in", ["Closed", "Cancelled"]],
                    "name": ["!=", self.name]
                }
            )
            if not unresolved:
                frappe.db.set_value(
                    "Lavanya Service Case Group",
                    self.service_case_group,
                    "stock_closure", "Settled"
                )

    def on_cancel(self):
        """Validate cancellation is allowed"""
        if self.status in ["Closed", "Cancelled"]:
            frappe.throw("Cannot cancel closed or cancelled complaints")
