import frappe

class LavanyaCustomer(frappe.model.document.Document):
    def after_insert(self):
        # Auto-link to Frappe CRM Contact if phone matches
        if frappe.db.exists("DocType", "CRM Contacts"):
            match = frappe.db.get_value("CRM Contacts", {"mobile_no": self.customer_phone}, "name")
            if match:
                self.db_set("crm_contact", match)
