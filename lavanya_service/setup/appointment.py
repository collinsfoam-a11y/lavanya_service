"""Lavanya Service Appointment doctype — created programmatically (like the
other Lavanya custom doctypes) so site-visit appointments (date+time+technician)
can be scheduled without touching the shared HD Ticket custom-field fixture."""

import frappe

APPOINTMENT_NAME = "Lavanya Service Appointment"
APPOINTMENT_STATUS_OPTIONS = "Scheduled\nCompleted\nCancelled\nNo Show"

_ROLES = [
	"System Manager",
	"Lavanya Manager",
	"Lavanya Service Coordinator",
	"Lavanya Front Desk",
	"Lavanya Helpdesk Agent",
]


def _field(fieldname, label, fieldtype, **kwargs):
	return {"fieldname": fieldname, "label": label, "fieldtype": fieldtype, **kwargs}


def _perm(role):
	return {
		"role": role, "read": 1, "write": 1, "create": 1, "delete": 1,
		"report": 1, "export": 1, "share": 1, "print": 1, "email": 1,
	}


def create_appointment_doctype():
	if frappe.db.exists("DocType", APPOINTMENT_NAME):
		return "exists"

	doc = frappe.get_doc(
		{
			"doctype": "DocType",
			"name": APPOINTMENT_NAME,
			"module": "Lavanya Service",
			"custom": 1,
			"autoname": "LV-APT-.YYYY.-.#####",
			"track_changes": 1,
			"sort_field": "modified",
			"sort_order": "DESC",
			"fields": [
				_field("ticket", "Ticket", "Link", options="HD Ticket", reqd=1, in_list_view=1),
				_field("appointment_datetime", "Appointment", "Datetime", reqd=1, in_list_view=1),
				_field("technician", "Technician", "Data", in_list_view=1),
				_field("status", "Status", "Select", options=APPOINTMENT_STATUS_OPTIONS, default="Scheduled", in_list_view=1),
				_field("notes", "Notes", "Small Text"),
			],
			"permissions": [_perm(r) for r in _ROLES],
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache(doctype=APPOINTMENT_NAME)
	return "created"
