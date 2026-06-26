# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, date_diff, time_diff_in_hours


class LavanyaServiceTicketExtension(Document):
    def validate(self):
        self.validate_mobile()
        self.validate_pin_code()
        self.validate_serial_number()
        self.validate_payment_fields()
        self.validate_token_fields()
        self.validate_status_transitions()

    def validate_mobile(self):
        """Validate customer number is 10 digits"""
        if self.customer_number:
            mobile = self.customer_number.replace(" ", "").replace("-", "")
            if len(mobile) != 10 or not mobile.isdigit():
                frappe.throw("Customer Number must be 10 digits")

    def validate_pin_code(self):
        """Validate PIN code is 6 digits"""
        if self.customer_site_pin:
            pin = self.customer_site_pin.replace(" ", "")
            if len(pin) != 6 or not pin.isdigit():
                frappe.throw("Customer Site PIN must be 6 digits")

    def validate_serial_number(self):
        """Validate serial number format"""
        if self.serial_no:
            if len(self.serial_no) != 15:
                frappe.throw("Serial Number must be 15 characters (XXXXXXYYYYYYZZZ)")

    def validate_payment_fields(self):
        """Validate payment fields when payment received"""
        if self.payment_received and not self.payment_amount:
            frappe.throw("Payment Amount is required when Payment Received is checked")
        if self.payment_amount and not self.payment_received:
            frappe.throw("Payment Received must be checked when Payment Amount is entered")

    def validate_token_fields(self):
        """Validate token fields when token issued"""
        if self.token_issued and not self.token_number:
            frappe.throw("Token Number is required when Token Issued is checked")

    def validate_status_transitions(self):
        """Validate status transitions"""
        valid_transitions = {
            "New": ["In Progress", "On Hold", "Resolved", "Closed"],
            "In Progress": ["On Hold", "Resolved", "Closed"],
            "On Hold": ["In Progress", "Resolved", "Closed"],
            "Resolved": ["Closed", "In Progress"],
            "Closed": ["In Progress"]
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
        """Calculate resolution time when resolved"""
        if self.status == "Resolved" and not self.resolution_date:
            self.resolution_date = today()
            if self.creation:
                creation = self.creation
                if isinstance(creation, str):
                    from frappe.utils import get_datetime
                    creation = get_datetime(creation)
                self.resolution_days = date_diff(today(), creation.date())
                self.resolution_hours = int(time_diff_in_hours(today(), creation))

    def on_update(self):
        """Update parent group status"""
        if self.has_value_changed("status"):
            self.update_group_status()

    def update_group_status(self):
        """Update parent group status based on linked tickets"""
        if self.lavanya_service_case_group:
            tickets = frappe.get_all(
                "Lavanya Service Ticket Extension",
                filters={"lavanya_service_case_group": self.lavanya_service_case_group},
                fields=["status"]
            )
            
            statuses = [t.status for t in tickets]
            
            if all(s == "Closed" for s in statuses):
                new_status = "All Closed"
            elif any(s == "In Progress" for s in statuses):
                new_status = "In Progress"
            else:
                new_status = "Active"
            
            frappe.db.set_value(
                "Lavanya Service Case Group",
                self.lavanya_service_case_group,
                "status",
                new_status
            )
