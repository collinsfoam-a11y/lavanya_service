# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LavanyaProductServicePolicy(Document):
    def validate(self):
        self.validate_unique_category()

    def validate_unique_category(self):
        """Ensure one policy per product category"""
        existing = frappe.db.exists(
            "Lavanya Product Service Policy",
            {"product_category": self.product_category, "name": ["!=", self.name]}
        )
        if existing:
            frappe.throw(f"A Product Service Policy already exists for {self.product_category}")

    def get_workflow_for_product(self):
        """Return workflow requirements for this product category"""
        return {
            "serial_required": self.serial_required,
            "installation_required": self.installation_required,
            "demo_required": self.demo_required,
            "showroom_intake_allowed": self.showroom_intake_allowed,
            "can_repair_locally": self.can_repair_locally,
            "default_warranty_months": self.default_warranty_months,
            "doa_period_days": self.doa_period_days,
            "min_complaint_photos": self.min_complaint_photos,
            "photo_requirements": self.photo_requirements
        }
