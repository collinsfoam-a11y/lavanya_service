import frappe

class LavanyaSettings(frappe.model.document.Document):
    def validate(self):
        # Never allow live + auto-closure at same time without explicit Owner confirmation
        if self.live_whatsapp_enabled and self.auto_closure_enabled:
            frappe.throw(
                "Live WhatsApp and Automatic Closure cannot both be enabled simultaneously. "
                "Disable one before enabling the other.",
                title="Safety Check"
            )
