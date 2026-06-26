import frappe

class LavanyaFollowupLog(frappe.model.document.Document):
    def before_save(self):
        from lavanya_service.events.followup import validate_customer_informed
        validate_customer_informed(self, None)

    def after_insert(self):
        # Bump promise breach count if follow-up is overdue
        ticket = frappe.get_doc("Lavanya Ticket", self.ticket)
        if ticket.followup_overdue:
            frappe.db.set_value("Lavanya Ticket", self.ticket,
                "promise_breach_count", (ticket.promise_breach_count or 0) + 1)
