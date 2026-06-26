# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LavanyaCustomerCommunicationLog(Document):
    def validate(self):
        self.validate_customer()
        self.validate_communication_type()
        self.validate_mobile()
        self.validate_call_duration()
        self.validate_whatsapp()

    def validate_customer(self):
        """Validate customer exists in ERPNext"""
        if self.customer:
            if not frappe.db.exists("Customer", self.customer):
                frappe.throw(f"Customer {self.customer} does not exist")

    def validate_communication_type(self):
        """Validate communication type specific fields"""
        if self.communication_type == "Call":
            if not self.call_duration:
                frappe.throw("Call Duration is required for Call communication")
        elif self.communication_type in ["WhatsApp", "SMS"]:
            if not self.recipient_mobile:
                frappe.throw("Recipient Mobile is required for WhatsApp/SMS communication")

    def validate_mobile(self):
        """Validate mobile number is 10 digits"""
        if self.recipient_mobile:
            mobile = self.recipient_mobile.replace(" ", "").replace("-", "")
            if len(mobile) != 10 or not mobile.isdigit():
                frappe.throw("Recipient Mobile must be 10 digits")

    def validate_call_duration(self):
        """Validate call duration is positive"""
        if self.call_duration and self.call_duration < 0:
            frappe.throw("Call Duration cannot be negative")

    def validate_whatsapp(self):
        """Validate WhatsApp message ID if provided"""
        if self.whatsapp_message_id and self.communication_type != "WhatsApp":
            frappe.throw("WhatsApp Message ID should only be set for WhatsApp communication")

    def on_update(self):
        """Update ticket communication log and customer informed flag"""
        if self.ticket:
            # Update last communication date on ticket
            frappe.db.set_value(
                "Lavanya Service Ticket Extension",
                self.ticket,
                "next_action", f"Follow up: {self.summary[:50]}"
            )
