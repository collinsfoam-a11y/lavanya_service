# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LavanyaBrandServicePolicy(Document):
    def validate(self):
        self.validate_required_links()
        self.validate_unique_brand()

    def validate_required_links(self):
        """Validate required linked documents exist"""
        if self.brand and not frappe.db.exists("Supplier", self.brand):
            frappe.throw(f"Brand (Supplier) {self.brand} does not exist")

    def validate_unique_brand(self):
        """Ensure one policy per brand"""
        existing = frappe.db.exists(
            "Lavanya Brand Service Policy",
            {"brand": self.brand, "name": ["!=", self.name]}
        )
        if existing:
            frappe.throw(f"A Brand Service Policy already exists for {self.brand}")

    def get_sla_for_product_category(self, product_category):
        """Get SLA and rules for a specific product category"""
        if self.installation_required_categories and product_category in self.installation_required_categories:
            return {
                "installation_required": True,
                "doa_period_days": self.doa_period_days,
                "warranty_period_months": self.warranty_period_months,
                "average_sla_days": self.average_sla_days,
                "escalation_path": self.escalation_path,
                "claim_document_requirement": self.claim_document_requirement
            }
        return {
            "installation_required": False,
            "doa_period_days": self.doa_period_days,
            "warranty_period_months": self.warranty_period_months,
            "average_sla_days": self.average_sla_days,
            "escalation_path": self.escalation_path,
            "claim_document_requirement": self.claim_document_requirement
        }
