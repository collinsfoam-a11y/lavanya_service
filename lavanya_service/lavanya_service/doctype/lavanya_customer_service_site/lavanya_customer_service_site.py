# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LavanyaCustomerServiceSite(Document):
    def validate(self):
        self.validate_pin_code()
        self.validate_contact_number()
        self.validate_gps_coordinates()

    def validate_pin_code(self):
        """Validate PIN code is 6 digits"""
        if self.pin_code:
            pin = self.pin_code.replace(" ", "")
            if len(pin) != 6 or not pin.isdigit():
                frappe.throw("PIN Code must be 6 digits")

    def validate_contact_number(self):
        """Validate contact number is 10 digits"""
        if self.site_contact_number:
            contact = self.site_contact_number.replace(" ", "").replace("-", "")
            if len(contact) != 10 or not contact.isdigit():
                frappe.throw("Site Contact Number must be 10 digits")

    def validate_gps_coordinates(self):
        """Validate GPS coordinates format"""
        if self.gps_coordinates:
            parts = self.gps_coordinates.split(",")
            if len(parts) != 2:
                frappe.throw("GPS Coordinates must be in format: lat,long")
            try:
                lat = float(parts[0].strip())
                lng = float(parts[1].strip())
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    frappe.throw("Invalid GPS coordinates")
            except ValueError:
                frappe.throw("GPS Coordinates must be numeric values")
