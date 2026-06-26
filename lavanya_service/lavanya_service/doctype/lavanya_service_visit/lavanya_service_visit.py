# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class LavanyaServiceVisit(Document):
    def validate(self):
        self.validate_required_links()
        self.validate_status_transition()
        self.validate_completion_rules()
        self.validate_failed_visit_rules()
        self.validate_rating()
        self.validate_time_rules()

    def validate_required_links(self):
        """Validate all required linked documents exist"""
        if self.customer and not frappe.db.exists("Customer", self.customer):
            frappe.throw(f"Customer {self.customer} does not exist")
        if self.service_case_group and not frappe.db.exists("Lavanya Service Case Group", self.service_case_group):
            frappe.throw(f"Service Case Group {self.service_case_group} does not exist")

    def validate_status_transition(self):
        """Validate status transitions"""
        valid_transitions = {
            "Scheduled": ["In Progress", "Failed Visit", "Cancelled"],
            "In Progress": ["Visit Completed", "Failed Visit"],
            "Visit Completed": [],
            "Failed Visit": ["Scheduled"],
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
        if self.status == "Visit Completed":
            if not self.work_done:
                frappe.throw("Work Done is required for completed visits")
            if not self.before_photo or not self.after_photo:
                frappe.throw("Before and After photos are required for completed visits")
            if not self.customer_signature:
                frappe.throw("Customer Signature is required for completed visits")

    def validate_failed_visit_rules(self):
        """Validate failed visit rules"""
        if self.status == "Failed Visit":
            if not self.failed_reason:
                frappe.throw("Failed Reason is required for failed visits")
            if not self.next_action:
                frappe.throw("Next Action is required for failed visits")
            if not self.next_follow_up_date:
                frappe.throw("Next Follow-up Date is required for failed visits")

    def validate_rating(self):
        """Validate customer rating is 1-5"""
        if self.customer_rating and (self.customer_rating < 1 or self.customer_rating > 5):
            frappe.throw("Customer Rating must be between 1 and 5")

    def validate_time_rules(self):
        """Validate check-in and check-out times"""
        if self.check_in_time and self.check_out_time:
            if self.check_out_time <= self.check_in_time:
                frappe.throw("Check-out Time must be after Check-in Time")
