# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class LavanyaServiceSettings(Document):
    def validate(self):
        self.validate_auto_close_days()
        self.validate_escalation_days()
        self.validate_reopen_days()

    def validate_auto_close_days(self):
        if self.auto_close_days is not None and self.auto_close_days < 1:
            frappe.throw("Auto Close Days must be at least 1")

    def validate_escalation_days(self):
        if self.escalation_days is not None and self.escalation_days < 1:
            frappe.throw("Escalation Days must be at least 1")

    def validate_reopen_days(self):
        if self.allow_reopen_days is not None and self.allow_reopen_days < 1:
            frappe.throw("Allow Reopen Days must be at least 1")

    def get_warehouse(self, warehouse_type):
        """Get warehouse by type"""
        field_map = {
            "damaged_stock": "warehouse_damaged_stock",
            "supplier_claim_hold": "warehouse_supplier_claim_hold",
            "repair_in_progress": "warehouse_repair_in_progress",
            "refurbished": "warehouse_refurbished",
            "scrap": "warehouse_scrap",
            "transit": "warehouse_transit",
            "installation": "warehouse_installation",
            "service_parts": "warehouse_service_parts",
            "accessories": "warehouse_accessories"
        }
        field = field_map.get(warehouse_type)
        if field:
            return self.get(field)
        return None
