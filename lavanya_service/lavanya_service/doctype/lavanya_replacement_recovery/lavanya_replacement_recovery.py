# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class LavanyaReplacementRecovery(Document):
    def validate(self):
        self.validate_required_links()
        self.validate_status_transition()
        self.validate_replacement_type_fields()
        self.validate_financial_calculation()
        self.validate_closure_rules()

    def validate_required_links(self):
        """Validate all required linked documents exist"""
        if self.customer and not frappe.db.exists("Customer", self.customer):
            frappe.throw(f"Customer {self.customer} does not exist")
        if self.service_case_group and not frappe.db.exists("Lavanya Service Case Group", self.service_case_group):
            frappe.throw(f"Service Case Group {self.service_case_group} does not exist")
        if self.old_item and not frappe.db.exists("Item", self.old_item):
            frappe.throw(f"Old Item {self.old_item} does not exist")
        if self.replacement_item and not frappe.db.exists("Item", self.replacement_item):
            frappe.throw(f"Replacement Item {self.replacement_item} does not exist")

    def validate_status_transition(self):
        """Validate status transitions"""
        valid_transitions = {
            "Draft": ["Replacement Approved", "Cancelled"],
            "Replacement Approved": ["Replacement Given to Customer", "Cancelled"],
            "Replacement Given to Customer": ["Old Item Received", "Cancelled"],
            "Old Item Received": ["Supplier Claim Pending", "Closed"],
            "Supplier Claim Pending": ["Claim Registered", "Cancelled"],
            "Claim Registered": ["Pickup Pending", "Cancelled"],
            "Pickup Pending": ["Sent to Supplier", "Cancelled"],
            "Sent to Supplier": ["Replacement Expected", "Credit Note Expected", "Repair Expected", "Cancelled"],
            "Replacement Expected": ["Replacement Received", "Cancelled"],
            "Credit Note Expected": ["Converted to Saleable", "Cancelled"],
            "Repair Expected": ["Returned Repaired", "Cancelled"],
            "Returned Repaired": ["Converted to Saleable", "Cancelled"],
            "Replacement Received": ["Closed"],
            "Converted to Saleable": ["Closed"],
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

    def validate_replacement_type_fields(self):
        """Validate fields based on replacement type"""
        if self.replacement_type in ["Cross SKU", "Upgrade", "Downgrade"]:
            # Financial difference calculation required
            if not self.old_item_value:
                frappe.throw("Old Item Value is required for Cross SKU/Upgrade/Downgrade")
            if not self.replacement_item_value:
                frappe.throw("Replacement Item Value is required for Cross SKU/Upgrade/Downgrade")
        
        if self.replacement_type == "Credit Instead":
            if not self.credit_note:
                frappe.throw("Credit Note is required for Credit Instead replacement")

    def validate_financial_calculation(self):
        """Calculate financial difference for cross-SKU replacements"""
        if self.replacement_type in ["Cross SKU", "Upgrade", "Downgrade"]:
            if self.old_item_value and self.replacement_item_value:
                self.financial_difference = self.replacement_item_value - self.old_item_value

    def validate_closure_rules(self):
        """Validate closure rules - all four lifecycle checks required"""
        if self.status == "Closed":
            if not self.customer_closure:
                frappe.throw("Customer Closure must be verified before closing")
            if not self.stock_closure:
                frappe.throw("Stock Closure must be verified before closing")
            if not self.supplier_closure:
                frappe.throw("Supplier Closure must be verified before closing")
            if not self.accounting_closure:
                frappe.throw("Accounting Closure must be verified before closing")
            if not self.closure_date:
                frappe.throw("Closure Date is required when closing")

    def before_submit(self):
        """Validate submit readiness"""
        if self.status == "Draft":
            frappe.throw("Cannot submit Draft recovery. Update status first.")

    def on_submit(self):
        """Update case group lifecycle flags"""
        if self.service_case_group:
            # Check if all replacements are closed
            open_recoveries = frappe.get_all(
                "Lavanya Replacement Recovery",
                filters={
                    "service_case_group": self.service_case_group,
                    "status": ["!=", "Closed"],
                    "name": ["!=", self.name]
                }
            )
            if not open_recoveries:
                frappe.db.set_value(
                    "Lavanya Service Case Group",
                    self.service_case_group,
                    "status", "All Closed"
                )

    def on_cancel(self):
        """Validate cancellation is allowed"""
        if self.status in ["Closed", "Cancelled"]:
            frappe.throw("Cannot cancel closed or cancelled recoveries")
        if self.status == "Replacement Given to Customer":
            frappe.throw("Cannot cancel after replacement given to customer without manager override")

    def calculate_financial_difference(self):
        """Calculate financial difference between old and replacement items"""
        if self.old_item_value and self.replacement_item_value:
            self.financial_difference = self.replacement_item_value - self.old_item_value
            self.save()
