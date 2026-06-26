# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LavanyaCustomerProduct(Document):
    def validate(self):
        self.validate_customer()
        self.validate_serial_number()
        self.validate_warranty()
        self.validate_duplicate_serial()

    def validate_customer(self):
        """Validate customer exists in ERPNext"""
        if self.customer:
            if not frappe.db.exists("Customer", self.customer):
                frappe.throw(f"Customer {self.customer} does not exist")

    def validate_serial_number(self):
        """Validate serial number format if provided"""
        if self.serial_no:
            if len(self.serial_no) != 15:
                frappe.throw("Serial Number must be 15 characters (XXXXXXYYYYYYZZZ)")

    def validate_warranty(self):
        """Validate warranty fields"""
        if self.warranty_type and self.warranty_type != "None":
            if not self.warranty_expiry:
                frappe.throw("Warranty Expiry is required when Warranty Type is set")
            if self.purchase_date and self.warranty_expiry:
                if self.warranty_expiry < self.purchase_date:
                    frappe.throw("Warranty Expiry cannot be before Purchase Date")

    def validate_duplicate_serial(self):
        """Prevent duplicate active Customer Product for same serial"""
        if self.serial_no:
            existing = frappe.get_all(
                "Lavanya Customer Product",
                filters={
                    "serial_no": self.serial_no,
                    "is_active": 1,
                    "name": ["!=", self.name]
                }
            )
            if existing:
                frappe.throw(f"Active Customer Product with serial {self.serial_no} already exists")

    def before_save(self):
        """Update tracking fields"""
        if self.is_active and self.customer:
            # Count tickets for this product
            ticket_count = frappe.db.count(
                "Lavanya Service Ticket Extension",
                filters={"customer_name": self.customer}
            )
            self.ticket_count = ticket_count
