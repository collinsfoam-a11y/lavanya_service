# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LavanyaServiceCaseGroup(Document):
    def validate(self):
        self.validate_customer()
        self.validate_mobile()
        self.validate_status_transitions()

    def validate_customer(self):
        """Validate customer exists in ERPNext"""
        if self.customer:
            if not frappe.db.exists("Customer", self.customer):
                frappe.throw(f"Customer {self.customer} does not exist")

    def validate_mobile(self):
        """Validate mobile number is 10 digits"""
        if self.primary_mobile:
            mobile = self.primary_mobile.replace(" ", "").replace("-", "")
            if len(mobile) != 10 or not mobile.isdigit():
                frappe.throw("Primary mobile must be 10 digits")

    def validate_status_transitions(self):
        """Validate status transitions"""
        valid_transitions = {
            "Active": ["In Progress", "All Closed", "Cancelled"],
            "In Progress": ["All Closed", "Cancelled"],
            "All Closed": [],
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

    def before_save(self):
        """Auto-set resolution date when status changes to All Closed"""
        if self.status == "All Closed" and not self.closed_date:
            self.closed_date = frappe.utils.today()

    def on_update(self):
        """Update linked tickets when group status changes"""
        if self.has_value_changed("status"):
            try:
                tickets = frappe.get_all(
                    "Lavanya Ticket",
                    filters={"lavanya_service_case_group": self.name},
                    fields=["name"]
                )
            except frappe.db.OperationalError:
                tickets = []
            for ticket in tickets:
                frappe.db.set_value("Lavanya Ticket", ticket.name, "status", self.status)
