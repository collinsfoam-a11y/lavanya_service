# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LavanyaCustomerContactPoint(Document):
    def validate(self):
        self.validate_mobile()
        self.validate_email()
        self.validate_primary_contact()

    def validate_mobile(self):
        """Validate mobile number is 10 digits"""
        if self.mobile_number:
            mobile = self.mobile_number.replace(" ", "").replace("-", "")
            if len(mobile) != 10 or not mobile.isdigit():
                frappe.throw("Mobile Number must be 10 digits")

    def validate_email(self):
        """Validate email format"""
        if self.email:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.email):
                frappe.throw("Invalid email format")

    def validate_primary_contact(self):
        """Validate only one primary contact per customer"""
        if self.is_primary and self.customer:
            existing = frappe.get_all(
                "Lavanya Customer Contact Point",
                filters={
                    "customer": self.customer,
                    "is_primary": 1,
                    "name": ["!=", self.name]
                }
            )
            if existing:
                frappe.throw("Only one contact can be marked as primary")
