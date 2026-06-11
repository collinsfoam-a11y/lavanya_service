import frappe


LAVANYA_ROLES = [
    {
        "role_name": "Lavanya Manager",
        "desk_access": 1,
        "description": "Lavanya operational manager with full helpdesk access configured through permissions.",
    },
    {
        "role_name": "Lavanya Helpdesk Agent",
        "desk_access": 1,
        "description": "Lavanya staff role for handling helpdesk tickets and follow-ups.",
    },
    {
        "role_name": "Lavanya Front Desk",
        "desk_access": 1,
        "description": "Lavanya front desk role for ticket creation and customer/product data entry.",
    },
    {
        "role_name": "Lavanya Service Coordinator",
        "desk_access": 1,
        "description": "Lavanya service coordination role for brand registration, service follow-up, and pending cases.",
    },
    {
        "role_name": "Lavanya Viewer",
        "desk_access": 1,
        "description": "Lavanya read-only role for ticket visibility, reports, and dashboards.",
    },
]


def configure_lavanya_roles():
    created = []
    updated = []

    for row in LAVANYA_ROLES:
        role_name = row["role_name"]

        if frappe.db.exists("Role", role_name):
            doc = frappe.get_doc("Role", role_name)
            changed = False

            if doc.desk_access != row["desk_access"]:
                doc.desk_access = row["desk_access"]
                changed = True

            if doc.meta.has_field("description") and doc.description != row["description"]:
                doc.description = row["description"]
                changed = True

            if changed:
                doc.save(ignore_permissions=True)
                updated.append(role_name)
        else:
            doc = frappe.new_doc("Role")
            doc.role_name = role_name
            doc.desk_access = row["desk_access"]

            if doc.meta.has_field("description"):
                doc.description = row["description"]

            doc.insert(ignore_permissions=True)
            created.append(role_name)

    frappe.db.commit()
    frappe.clear_cache()

    return {
        "created": created,
        "updated": updated,
        "expected_roles": [row["role_name"] for row in LAVANYA_ROLES],
    }
