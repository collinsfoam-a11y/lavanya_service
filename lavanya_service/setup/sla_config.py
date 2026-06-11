import frappe


SLA_NAME = "Lavanya Default"


PRIORITY_TARGETS = [
    {
        "priority": "Urgent",
        "default_priority": 0,
        "response_time": 7200,
        "resolution_time": 86400,
    },
    {
        "priority": "High",
        "default_priority": 0,
        "response_time": 14400,
        "resolution_time": 172800,
    },
    {
        "priority": "Medium",
        "default_priority": 1,
        "response_time": 28800,
        "resolution_time": 259200,
    },
    {
        "priority": "Low",
        "default_priority": 0,
        "response_time": 86400,
        "resolution_time": 432000,
    },
]


WORKING_DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]


def _require_record(doctype, name):
    if not frappe.db.exists(doctype, name):
        frappe.throw(f"Missing required {doctype}: {name}")


def _validate_dependencies():
    for status in ["New", "In Progress"]:
        _require_record("HD Ticket Status", status)

    for priority in ["Urgent", "High", "Medium", "Low"]:
        _require_record("HD Ticket Priority", priority)

    _require_record("HD Service Holiday List", "Default")


def _set_if_field_exists(doc, fieldname, value):
    if doc.meta.has_field(fieldname):
        doc.set(fieldname, value)


def configure_lavanya_default_sla():
    _validate_dependencies()

    if frappe.db.exists("HD Service Level Agreement", SLA_NAME):
        sla = frappe.get_doc("HD Service Level Agreement", SLA_NAME)
        action = "updated"
    else:
        sla = frappe.new_doc("HD Service Level Agreement")
        sla.service_level = SLA_NAME
        action = "created"

    _set_if_field_exists(sla, "enabled", 1)
    _set_if_field_exists(sla, "default_sla", 1)
    _set_if_field_exists(sla, "default_priority", "Medium")
    _set_if_field_exists(sla, "condition", None)
    _set_if_field_exists(sla, "condition_json", None)
    _set_if_field_exists(sla, "apply_sla_for_resolution", 1)
    _set_if_field_exists(sla, "default_ticket_status", "New")
    _set_if_field_exists(sla, "ticket_reopen_status", "In Progress")
    _set_if_field_exists(sla, "holiday_list", "Default")

    if hasattr(sla, "priorities"):
        sla.set("priorities", [])
        for row in PRIORITY_TARGETS:
            sla.append("priorities", row)

    if hasattr(sla, "support_and_resolution"):
        sla.set("support_and_resolution", [])
        for day in WORKING_DAYS:
            sla.append(
                "support_and_resolution",
                {
                    "workday": day,
                    "start_time": "09:30:00",
                    "end_time": "20:30:00",
                },
            )

    sla.save(ignore_permissions=True)

    # Preserve the system-created SLA record while ensuring Lavanya is the active default.
    if frappe.db.exists("HD Service Level Agreement", "Default") and SLA_NAME != "Default":
        default_sla = frappe.get_doc("HD Service Level Agreement", "Default")
        if getattr(default_sla, "default_sla", 0):
            default_sla.default_sla = 0
            default_sla.save(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache()

    return {
        "sla": SLA_NAME,
        "action": action,
        "default_sla": frappe.get_value(
            "HD Service Level Agreement", SLA_NAME, "default_sla"
        ),
        "old_default_sla": frappe.get_value(
            "HD Service Level Agreement", "Default", "default_sla"
        )
        if frappe.db.exists("HD Service Level Agreement", "Default")
        else None,
    }
