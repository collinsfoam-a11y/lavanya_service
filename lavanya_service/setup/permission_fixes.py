import frappe


PERMISSION_FIELDS = [
    "read",
    "write",
    "create",
    "delete",
    "submit",
    "cancel",
    "amend",
    "report",
    "export",
    "import",
    "share",
    "print",
    "email",
]


HD_TICKET_ALL_TARGET = {
    "read": 1,
    "write": 0,
    "create": 0,
    "delete": 0,
    "submit": 0,
    "cancel": 0,
    "amend": 0,
    "report": 0,
    "export": 0,
    "import": 0,
    "share": 0,
    "print": 1,
    "email": 0,
}


def _get_existing_custom_docperms(parent, role, permlevel=0):
    return frappe.get_all(
        "Custom DocPerm",
        filters={
            "parent": parent,
            "role": role,
            "permlevel": permlevel,
        },
        fields=["name"],
        order_by="creation asc",
        pluck="name",
    )


def restrict_hd_ticket_all_permission():
    """Restrict broad HD Ticket All permission without touching role-specific rows.

    Handles duplicate rows: fresh installs get one broad All row from the
    helpdesk install plus the restricted row from the lavanya fixture. The
    first row (by creation) is kept and forced to the restricted target;
    every additional row is deleted.
    """

    existing = _get_existing_custom_docperms("HD Ticket", "All", 0)

    deleted = []
    for duplicate in existing[1:]:
        frappe.delete_doc(
            "Custom DocPerm", duplicate, force=True, ignore_permissions=True
        )
        deleted.append(duplicate)

    if existing:
        doc = frappe.get_doc("Custom DocPerm", existing[0])
        created = False
    else:
        doc = frappe.new_doc("Custom DocPerm")
        doc.parent = "HD Ticket"
        doc.role = "All"
        doc.permlevel = 0
        created = True

    changed = created

    for field in PERMISSION_FIELDS:
        target_value = int(HD_TICKET_ALL_TARGET.get(field, 0))
        current_value = int(doc.get(field) or 0)

        if current_value != target_value:
            doc.set(field, target_value)
            changed = True

    if changed:
        if created:
            doc.insert(ignore_permissions=True)
        else:
            doc.save(ignore_permissions=True)

    frappe.clear_cache()
    frappe.db.commit()

    return {
        "created": created,
        "changed": changed,
        "deleted_duplicates": deleted,
        "name": doc.name,
        "target": HD_TICKET_ALL_TARGET,
    }
