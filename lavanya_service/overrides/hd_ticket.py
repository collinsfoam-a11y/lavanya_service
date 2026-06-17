from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import HDTicket

from lavanya_service.api.customer_intake import sync_customer_profile_from_ticket
from lavanya_service.validations.hd_ticket import (
	normalize_ticket_phone_numbers,
	validate_protected_field_permissions,
	validate_ticket,
)


class LavanyaHDTicket(HDTicket):
	def before_validate(self):
		normalize_ticket_phone_numbers(self)
		super().before_validate()

	def validate(self):
		super().validate()
		validate_ticket(self)
		# Stage layer (delta plan): default service_flow_type / current_service_stage
		# / next_action for new or unstaged active tickets. Only fills empties.
		from lavanya_service.stage_rules import assign_defaults

		assign_defaults(self)

	def on_update(self):
		super().on_update()
		sync_customer_profile_from_ticket(self)

	def validate_higher_perm_levels(self):
		validate_protected_field_permissions(self)
		return super().validate_higher_perm_levels()

	def db_insert(self, ignore_if_duplicate=False):
		validate_protected_field_permissions(self)
		return super().db_insert(ignore_if_duplicate=ignore_if_duplicate)

	def db_update(self):
		validate_protected_field_permissions(self)
		return super().db_update()
