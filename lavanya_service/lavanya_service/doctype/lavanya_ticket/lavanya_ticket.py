import frappe
from frappe.utils import date_diff, today, now_datetime
import random, string

class LavanyaTicket(frappe.model.document.Document):

    def before_save(self):
        self._update_days_open()
        self._generate_handover_otp_if_needed()

    def _update_days_open(self):
        if self.creation:
            self.days_open = date_diff(today(), str(self.creation)[:10])

    def _generate_handover_otp_if_needed(self):
        if (self.service_path == "In-Showroom Service"
                and self.status == "Customer Confirmation Pending"
                and not self.handover_otp):
            self.handover_otp = ''.join(random.choices(string.digits, k=6))

    def get_closure_eligibility(self):
        """Return (allowed: bool, reason: str)"""
        if not self.customer_informed:
            return False, "Customer has not been informed"
        if self.part_pending and not self.part_received:
            return False, "Spare part pending"
        if self.service_path in ("Brand Warranty","Local Paid Service") and not self.technician_visited:
            return False, "Technician visit not verified"
        if not self.customer_satisfied and self.status != "Customer Confirmation Pending":
            return False, "Customer satisfaction not confirmed"
        return True, ""
