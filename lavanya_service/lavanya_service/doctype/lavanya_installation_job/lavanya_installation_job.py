# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class LavanyaInstallationJob(Document):
    def validate(self):
        self.validate_required_links()
        self.validate_status_transition()
        self.validate_completion_rules()
        self.validate_payment_rules()

    def validate_required_links(self):
        """Validate all required linked documents exist"""
        if self.customer and not frappe.db.exists("Customer", self.customer):
            frappe.throw(f"Customer {self.customer} does not exist")
        if self.service_case_group and not frappe.db.exists("Lavanya Service Case Group", self.service_case_group):
            frappe.throw(f"Service Case Group {self.service_case_group} does not exist")

    def validate_status_transition(self):
        """Validate status transitions"""
        valid_transitions = {
            "Draft": ["Pending Assignment", "Cancelled"],
            "Pending Assignment": ["Assigned", "Cancelled"],
            "Assigned": ["Customer Contacted", "Failed Visit", "Cancelled"],
            "Customer Contacted": ["Visit Scheduled", "Failed Visit", "Cancelled"],
            "Visit Scheduled": ["Visit Completed", "Failed Visit", "Cancelled"],
            "Visit Completed": ["Customer Confirmed", "Failed Visit", "Closed"],
            "Failed Visit": ["Assigned", "Cancelled"],
            "Customer Confirmed": ["Closed"],
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

    def validate_completion_rules(self):
        """Validate completion rules"""
        if self.status in ["Visit Completed", "Customer Confirmed", "Closed"]:
            if not self.completion_date:
                self.completion_date = today()
            if not self.visit_status:
                frappe.throw("Visit Status is required for completion")
            if not self.customer_confirmation and self.status == "Closed":
                frappe.throw("Customer Confirmation is required for closure")

    def validate_payment_rules(self):
        """Validate payment rules for paid installations"""
        if self.installation_type == "Paid" and self.status == "Closed":
            if not self.payment_amount:
                frappe.throw("Payment Amount is required for paid installations")
            if not self.payment_received:
                frappe.throw("Payment Received confirmation is required for paid installations")
