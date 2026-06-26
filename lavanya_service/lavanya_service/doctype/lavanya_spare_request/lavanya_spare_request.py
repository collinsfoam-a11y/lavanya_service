# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class LavanyaSpareRequest(Document):
    def validate(self):
        self.validate_required_links()
        self.validate_status_transition()
        self.validate_quantity_rules()
        self.validate_chargeable_rules()
        self.validate_approval_rules()

    def validate_required_links(self):
        """Validate all required linked documents exist"""
        if self.ticket and not frappe.db.exists("HD Ticket", self.ticket):
            frappe.throw(f"Ticket {self.ticket} does not exist")
        if self.service_case_group and not frappe.db.exists("Lavanya Service Case Group", self.service_case_group):
            frappe.throw(f"Service Case Group {self.service_case_group} does not exist")

    def validate_status_transition(self):
        """Validate status transitions"""
        valid_transitions = {
            "Draft": ["Requested", "Cancelled"],
            "Requested": ["Approved", "Cancelled"],
            "Approved": ["Issued", "Cancelled"],
            "Issued": ["Partially Used", "Used", "Returned"],
            "Partially Used": ["Used", "Returned"],
            "Used": ["Closed"],
            "Returned": ["Closed"],
            "Cancelled": [],
            "Closed": []
        }
        if self.is_new():
            return
        old_doc = self._doc_before_save
        if not old_doc or old_doc.status not in valid_transitions:
            return
        allowed = valid_transitions[old_doc.status]
        if self.status not in allowed:
            frappe.throw(f"Cannot transition from {old_doc.status} to {self.status}")

    def validate_quantity_rules(self):
        """Validate quantity rules - used + returned cannot exceed issued"""
        if self.used_quantity and self.returned_quantity:
            if self.used_quantity + self.returned_quantity > (self.issued_quantity or 0):
                frappe.throw("Used Quantity + Returned Quantity cannot exceed Issued Quantity")
        if self.used_quantity and self.issued_quantity:
            if self.used_quantity > self.issued_quantity:
                frappe.throw("Used Quantity cannot exceed Issued Quantity")
        if self.returned_quantity and self.issued_quantity:
            if self.returned_quantity > self.issued_quantity:
                frappe.throw("Returned Quantity cannot exceed Issued Quantity")

    def validate_chargeable_rules(self):
        """Validate chargeable spare rules"""
        if self.chargeable and self.status == "Closed":
            if not self.customer_payable_amount:
                frappe.throw("Customer Payable Amount is required for chargeable spares")

    def validate_approval_rules(self):
        """Validate approval rules"""
        if self.status == "Approved" and not self.approved_by:
            frappe.throw("Approved By is required when status is Approved")
        if self.status == "Approved" and not self.approval_date:
            self.approval_date = today()
