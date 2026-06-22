import frappe
from frappe.utils import now_datetime


RECORD_TO_STAGE = {
	"Replacement Record": "New Unit Dispatched",
	"Return Service Record": "Customer Refund Processed",
	"Store Service Record": "Product Handed Over",
	"Demo Installation Record": "Installation Completed",
	"Stock Complaint Record": "Credit Note Received",
	"Service Product Receipt": "Product Received at Store",
}

# H3: Sync followup_stage when advancing current_service_stage for record
# types that participate in the follow-up tracking loop. Only records that
# represent a service-center or store-service handoff advance followup_stage.
RECORD_TO_FOLLOWUP_STAGE = {
	"Service Product Receipt": "sc_followup_done",
}


def advance_on_record_created(doc, method):
	record_doctype = doc.doctype
	ticket_name = doc.get("ticket")
	if not ticket_name:
		return
	if not frappe.db.exists("HD Ticket", ticket_name):
		return

	target_stage = RECORD_TO_STAGE.get(record_doctype)
	if not target_stage:
		return

	followup_stage = RECORD_TO_FOLLOWUP_STAGE.get(record_doctype)

	ticket = frappe.get_doc("HD Ticket", ticket_name)
	if ticket.status in ("Closed", "Cancelled"):
		return

	ticket.current_service_stage = target_stage
	if followup_stage:
		ticket.followup_stage = followup_stage
	ticket.flags.ignore_lavanya_field_guard = True
	ticket.save(ignore_permissions=True)

	log = "[Auto-Advance] {0} created → stage advanced to '{1}'".format(
		record_doctype, target_stage
	)
	if followup_stage:
		log += " · followup: {0}".format(followup_stage)
	ticket.add_comment("Comment", log)
