# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class LavanyaClosureVerification(Document):
    def validate(self):
        self.validate_customer()
        self.validate_verified_by()
        self.validate_checklist()
        self.validate_status_transitions()

    def validate_customer(self):
        """Validate customer exists in ERPNext"""
        if self.customer:
            if not frappe.db.exists("Customer", self.customer):
                frappe.throw(f"Customer {self.customer} does not exist")

    def validate_verified_by(self):
        """Validate verified_by is different from ticket creator"""
        if self.ticket and self.verified_by:
            ticket_owner = frappe.db.get_value("Lavanya Service Ticket Extension", self.ticket, "owner")
            if self.verified_by == ticket_owner:
                frappe.throw("Verified By must be different from Ticket Creator")

    def validate_checklist(self):
        """Validate checklist items based on status"""
        if self.status == "Verified":
            # All checklist items must be checked for Verified status
            required_checks = [
                "customer_satisfied",
                "stock_accounted",
                "supplier_claim_handled",
                "accounting_closed",
                "warranty_documented",
                "all_photos_uploaded",
                "all_documents_attached"
            ]
            for field in required_checks:
                if not self.get(field):
                    frappe.throw(f"All checklist items must be checked for Verified status. Missing: {field}")

    def validate_status_transitions(self):
        """Validate status transitions"""
        valid_transitions = {
            "Pending": ["Verified", "Rejected", "Reopen Required"],
            "Verified": ["Closed"],
            "Rejected": ["Pending"],
            "Reopen Required": ["Pending"],
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

    def on_update(self):
        """Update linked ticket and group when status changes"""
        if self.has_value_changed("status"):
            if self.ticket:
                frappe.db.set_value(
                    "Lavanya Service Ticket Extension",
                    self.ticket,
                    "closure_verification", self.name
                )
            
            # Update group status if all closures complete
            if self.service_case_group and self.status == "Verified":
                self.update_group_status()

    def update_group_status(self):
        """Update parent group status based on closure verification"""
        if self.service_case_group:
            # Check if all verifications are complete
            verifications = frappe.get_all(
                "Lavanya Closure Verification",
                filters={
                    "service_case_group": self.service_case_group,
                    "status": ["!=", "Verified"]
                }
            )
            
            if not verifications:
                # All verifications complete, close the group
                frappe.db.set_value(
                    "Lavanya Service Case Group",
                    self.service_case_group,
                    "status", "All Closed"
                )
                frappe.db.set_value(
                    "Lavanya Service Case Group",
                    self.service_case_group,
                    "closed_date", today()
                )
                frappe.db.set_value(
                    "Lavanya Service Case Group",
                    self.service_case_group,
                    "closure_verified_by", self.verified_by
                )
                frappe.db.set_value(
                    "Lavanya Service Case Group",
                    self.service_case_group,
                    "closure_verified_date", today()
                )
