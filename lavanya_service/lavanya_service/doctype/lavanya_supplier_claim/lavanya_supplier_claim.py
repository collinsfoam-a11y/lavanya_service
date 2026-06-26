# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class LavanyaSupplierClaim(Document):
    def validate(self):
        self.validate_required_links()
        self.validate_status_transition()
        self.validate_financial_fields()
        self.validate_claim_reference()
        self.validate_closure_rules()

    def validate_required_links(self):
        """Validate all required linked documents exist"""
        if self.supplier and not frappe.db.exists("Supplier", self.supplier):
            frappe.throw(f"Supplier {self.supplier} does not exist")
        if self.customer and not frappe.db.exists("Customer", self.customer):
            frappe.throw(f"Customer {self.customer} does not exist")
        if self.service_case_group and not frappe.db.exists("Lavanya Service Case Group", self.service_case_group):
            frappe.throw(f"Service Case Group {self.service_case_group} does not exist")

    def validate_status_transition(self):
        """Validate status transitions"""
        valid_transitions = {
            "Draft": ["Claim Registered", "Cancelled"],
            "Claim Registered": ["Document Pending", "Pickup Pending", "Under Review", "Rejected", "Cancelled"],
            "Document Pending": ["Claim Registered", "Pickup Pending", "Cancelled"],
            "Pickup Pending": ["Sent to Supplier", "Cancelled"],
            "Sent to Supplier": ["Under Review", "Cancelled"],
            "Under Review": ["Replacement Expected", "Credit Note Expected", "Repair Expected", "Rejected", "Cancelled"],
            "Replacement Expected": ["Settled", "Cancelled"],
            "Credit Note Expected": ["Settled", "Cancelled"],
            "Repair Expected": ["Settled", "Cancelled"],
            "Rejected": ["Cancelled"],
            "Settled": [],
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

    def validate_financial_fields(self):
        """Validate financial fields based on settlement type"""
        if not self.settlement_type:
            return
        if self.settlement_type == "Credit Note":
            if not self.expected_credit_note_amount:
                frappe.throw("Expected Credit Note Amount is required for Credit Note settlement")
            if self.expected_credit_note_amount and self.expected_credit_note_amount <= 0:
                frappe.throw("Expected Credit Note Amount must be greater than 0")
        if self.settlement_type == "Replacement":
            if not self.expected_replacement_item:
                frappe.throw("Expected Replacement Item is required for Replacement settlement")

    def validate_claim_reference(self):
        """Validate claim reference or manager override"""
        if self.status == "Claim Registered":
            if not self.claim_reference_no and not self.manager_override_reason:
                frappe.throw("Claim Reference No or Manager Override Reason is required when Claim Registered")

    def validate_closure_rules(self):
        """Validate closure rules"""
        if self.status == "Settled":
            if not self.supplier_closure_date:
                frappe.throw("Supplier Closure Date is required when status is Settled")

    def before_submit(self):
        """Validate submit readiness"""
        if self.status == "Draft":
            frappe.throw("Cannot submit Draft claim. Update status first.")

    def on_submit(self):
        """Update case group lifecycle flags"""
        if self.service_case_group:
            # Check if all supplier claims are settled
            unsettled = frappe.get_all(
                "Lavanya Supplier Claim",
                filters={
                    "service_case_group": self.service_case_group,
                    "status": ["!=", "Settled"],
                    "name": ["!=", self.name]
                }
            )
            if not unsettled:
                frappe.db.set_value(
                    "Lavanya Service Case Group",
                    self.service_case_group,
                    "supplier_closure", "Settled"
                )

    def on_cancel(self):
        """Validate cancellation is allowed"""
        if self.status in ["Settled", "Cancelled"]:
            frappe.throw("Cannot cancel settled or cancelled claims")

    def update_follow_up(self):
        """Update follow-up tracking"""
        self.follow_up_count = (self.follow_up_count or 0) + 1
        self.last_follow_up_date = today()
        self.follow_up_date = None
        self.save()
