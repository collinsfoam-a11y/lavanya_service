import frappe


LAVANYA_ROLES = [
    "Lavanya Manager",
    "Lavanya Helpdesk Agent",
    "Lavanya Front Desk",
    "Lavanya Service Coordinator",
    "Lavanya Viewer",
]


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


def _perm(**kwargs):
    row = {field: 0 for field in PERMISSION_FIELDS}
    row.update(kwargs)
    return row


PERMISSION_MATRIX = {
    "HD Ticket": {
        "Lavanya Manager": _perm(
            read=1,
            write=1,
            create=1,
            report=1,
            export=1,
            share=1,
            print=1,
            email=1,
        ),
        "Lavanya Helpdesk Agent": _perm(
            read=1, write=1, create=1, report=1, print=1
        ),
        "Lavanya Front Desk": _perm(read=1, write=1, create=1, print=1),
        "Lavanya Service Coordinator": _perm(
            read=1, write=1, create=1, report=1, print=1
        ),
        "Lavanya Viewer": _perm(read=1, report=1, print=1),
    },
    "HD View": {
        "Lavanya Manager": _perm(read=1, write=1, create=1, report=1),
        "Lavanya Helpdesk Agent": _perm(read=1),
        "Lavanya Front Desk": _perm(read=1),
        "Lavanya Service Coordinator": _perm(read=1),
        "Lavanya Viewer": _perm(read=1),
    },
    "HD Notification": {
        "Lavanya Manager": _perm(read=1, write=1),
        "Lavanya Helpdesk Agent": _perm(read=1, write=1),
        "Lavanya Front Desk": _perm(read=1, write=1),
        "Lavanya Service Coordinator": _perm(read=1, write=1),
        "Lavanya Viewer": _perm(read=1),
    },
    "Brand Service Master": {
        "Lavanya Manager": _perm(
            read=1, write=1, create=1, report=1, export=1, import_=1, print=1
        ),
        "Lavanya Helpdesk Agent": _perm(read=1),
        "Lavanya Front Desk": _perm(read=1),
        "Lavanya Service Coordinator": _perm(read=1),
        "Lavanya Viewer": _perm(read=1, report=1),
    },
    "Service Center Master": {
        "Lavanya Manager": _perm(
            read=1, write=1, create=1, report=1, export=1, import_=1, print=1
        ),
        "Lavanya Helpdesk Agent": _perm(read=1),
        "Lavanya Front Desk": _perm(read=1),
        "Lavanya Service Coordinator": _perm(read=1),
        "Lavanya Viewer": _perm(read=1, report=1),
    },
    "Local Technician Master": {
        "Lavanya Manager": _perm(
            read=1, write=1, create=1, report=1, export=1, import_=1, print=1
        ),
        "Lavanya Helpdesk Agent": _perm(read=1),
        "Lavanya Front Desk": _perm(read=1),
        "Lavanya Service Coordinator": _perm(read=1),
        "Lavanya Viewer": _perm(read=1, report=1),
    },
    "Free Service Rule": {
        "Lavanya Manager": _perm(
            read=1, write=1, create=1, report=1, export=1, import_=1, print=1
        ),
        "Lavanya Helpdesk Agent": _perm(read=1),
        "Lavanya Front Desk": _perm(read=1),
        "Lavanya Service Coordinator": _perm(read=1),
        "Lavanya Viewer": _perm(read=1, report=1),
    },
    "Service Product Receipt": {
        "Lavanya Manager": _perm(
            read=1, write=1, create=1, report=1, export=1, print=1
        ),
        "Lavanya Helpdesk Agent": _perm(
            read=1, write=1, create=1, report=1, print=1
        ),
        "Lavanya Front Desk": _perm(read=1, write=1, create=1, print=1),
        "Lavanya Service Coordinator": _perm(
            read=1, write=1, create=1, report=1, print=1
        ),
        "Lavanya Viewer": _perm(read=1, report=1, print=1),
    },
    "Custody Log Entry": {
        "Lavanya Manager": _perm(read=1, write=1, create=1),
        "Lavanya Helpdesk Agent": _perm(read=1, write=1, create=1),
        "Lavanya Front Desk": _perm(read=1, write=1, create=1),
        "Lavanya Service Coordinator": _perm(read=1, write=1, create=1),
        "Lavanya Viewer": _perm(read=1),
    },
}


def _normalise_permission_row(row):
    normalised = {}

    for key, value in row.items():
        if key == "import_":
            normalised["import"] = value
        else:
            normalised[key] = value

    return normalised


def _get_existing_custom_docperm(doctype, role, permlevel=0):
    rows = frappe.get_all(
        "Custom DocPerm",
        filters={
            "parent": doctype,
            "role": role,
            "permlevel": permlevel,
        },
        fields=["name"],
        limit=1,
    )

    return rows[0].name if rows else None


def upsert_custom_docperm(doctype, role, permissions, permlevel=0):
    if not frappe.db.exists("DocType", doctype):
        frappe.throw(f"DocType missing: {doctype}")

    if not frappe.db.exists("Role", role):
        frappe.throw(f"Role missing: {role}")

    permissions = _normalise_permission_row(permissions)
    existing_name = _get_existing_custom_docperm(doctype, role, permlevel=permlevel)

    if existing_name:
        doc = frappe.get_doc("Custom DocPerm", existing_name)
        created = False
    else:
        doc = frappe.new_doc("Custom DocPerm")
        doc.parent = doctype
        doc.parenttype = "DocType"
        doc.parentfield = "permissions"
        doc.role = role
        doc.permlevel = permlevel
        created = True

    changed = created

    for field in PERMISSION_FIELDS:
        target_value = int(permissions.get(field, 0))
        current_value = int(doc.get(field) or 0)

        if current_value != target_value:
            doc.set(field, target_value)
            changed = True

    if changed:
        if created:
            doc.insert(ignore_permissions=True)
        else:
            doc.save(ignore_permissions=True)

    return {
        "doctype": doctype,
        "role": role,
        "permlevel": permlevel,
        "created": created,
        "changed": changed,
        "name": doc.name,
    }


def configure_lavanya_permissions():
    results = []

    for doctype, role_map in PERMISSION_MATRIX.items():
        for role, permissions in role_map.items():
            results.append(upsert_custom_docperm(doctype, role, permissions))

    frappe.clear_cache()
    frappe.db.commit()

    return {
        "count": len(results),
        "created": [row for row in results if row["created"]],
        "changed": [row for row in results if row["changed"]],
        "unchanged": [row for row in results if not row["changed"]],
    }
