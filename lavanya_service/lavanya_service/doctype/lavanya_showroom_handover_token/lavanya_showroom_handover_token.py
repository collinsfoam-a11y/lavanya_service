# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import random
import string


class LavanyaShowroomHandoverToken(Document):
    def validate(self):
        self.validate_customer()
        self.validate_mobile()
        self.validate_accessories()
        self.validate_status_transitions()

    def validate_customer(self):
        """Validate customer exists in ERPNext"""
        if self.customer:
            if not frappe.db.exists("Customer", self.customer):
                frappe.throw(f"Customer {self.customer} does not exist")

    def validate_mobile(self):
        """Validate mobile number is 10 digits"""
        if self.handover_to_mobile:
            mobile = self.handover_to_mobile.replace(" ", "").replace("-", "")
            if len(mobile) != 10 or not mobile.isdigit():
                frappe.throw("Handover To Mobile must be 10 digits")

    def validate_accessories(self):
        """Validate at least one accessory is listed"""
        if not self.accessories_handed_over or len(self.accessories_handed_over) == 0:
            frappe.throw("At least one accessory must be listed")

    def validate_status_transitions(self):
        """Validate status transitions"""
        valid_transitions = {
            "Draft": ["OTP Sent", "Cancelled"],
            "OTP Sent": ["Verified", "Cancelled"],
            "Verified": ["Completed", "Cancelled"],
            "Completed": [],
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

    def on_update(self):
        """Update linked ticket when token is created/updated"""
        if self.ticket:
            frappe.db.set_value(
                "Lavanya Service Ticket Extension",
                self.ticket,
                "token_issued", 1
            )
            frappe.db.set_value(
                "Lavanya Service Ticket Extension",
                self.ticket,
                "token_number", self.name
            )

    def send_otp(self):
        """Generate and send OTP to customer"""
        otp = ''.join(random.choices(string.digits, k=6))
        self.otp_code = otp
        self.otp_sent = 1
        self.otp_sent_at = frappe.utils.now_datetime()
        self.status = "OTP Sent"
        self.save()
        
        # TODO: Send OTP via WhatsApp/SMS
        frappe.msgprint(f"OTP {otp} sent to {self.handover_to_mobile}")
        return otp

    def verify_otp(self, entered_otp):
        """Verify entered OTP"""
        if self.otp_code == entered_otp:
            self.otp_verified = 1
            self.status = "Verified"
            self.save()
            return True
        else:
            frappe.throw("Invalid OTP")
            return False

    def complete_handover(self):
        """Complete the handover process"""
        if not self.otp_verified:
            frappe.throw("OTP must be verified before completing handover")
        if not self.customer_signature:
            frappe.throw("Customer signature is required before completing handover")
        
        self.status = "Completed"
        self.save()
        
        # Update linked ticket
        if self.ticket:
            frappe.db.set_value(
                "Lavanya Service Ticket Extension",
                self.ticket,
                "closure_verification", None
            )
