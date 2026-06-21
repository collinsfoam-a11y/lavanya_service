import frappe


PERMLEVEL_1_FIELDS = [
    "manufacturer_registration_required",
    "manufacturer_registered",
    "brand_ticket_number",
    "registration_date",
    "registration_pending_reason",
    "brand_registration_recommended",
    "brand_registration_override_reason",
    "brand_registration_recommended_at",
    "service_center",
    "local_technician",
    "is_repeated_complaint",
    "previous_ticket_link",
    "pending_reason",
    "next_follow_up_date",
    "service_product_receipt",
    "work_narration",
    "store_service_reference",
    "replacement_reference",
    "return_reference",
    "demo_installation_reference",
    "stock_complaint_reference",
    "payment_block_eligible",
]


PERMLEVEL_2_FIELDS = [
    "closure_type",
    "customer_confirmation_received",
    "closed_by",
    "closure_date",
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


PERMLEVEL_DOCPERM_MATRIX = {
    1: {
        "Lavanya Manager": {"read": 1, "write": 1},
        "Lavanya Helpdesk Agent": {"read": 1, "write": 1},
        "Lavanya Front Desk": {"read": 1},
        "Lavanya Service Coordinator": {"read": 1, "write": 1},
        "Lavanya Viewer": {"read": 1},
    },
    2: {
        "Lavanya Manager": {"read": 1, "write": 1},
        "Lavanya Helpdesk Agent": {"read": 1},
        "Lavanya Front Desk": {},
        "Lavanya Service Coordinator": {"read": 1, "write": 1},
        "Lavanya Viewer": {"read": 1},
    },
}


def _custom_field_name(fieldname):
    return frappe.db.get_value(
        "Custom Field",
        {
            "dt": "HD Ticket",
            "fieldname": fieldname,
        },
        "name",
    )


def _set_custom_field_permlevel(fieldname, permlevel):
    name = _custom_field_name(fieldname)

    if not name:
        frappe.throw(f"HD Ticket Custom Field missing: {fieldname}")

    doc = frappe.get_doc("Custom Field", name)
    changed = int(doc.permlevel or 0) != int(permlevel)

    if changed:
        doc.permlevel = permlevel
        doc.save(ignore_permissions=True)

    return {
        "fieldname": fieldname,
        "permlevel": permlevel,
        "changed": changed,
    }


def _get_existing_custom_docperm(role, permlevel):
    rows = frappe.get_all(
        "Custom DocPerm",
        filters={
            "parent": "HD Ticket",
            "role": role,
            "permlevel": permlevel,
        },
        fields=["name"],
        limit=1,
    )

    return rows[0].name if rows else None


def _upsert_hd_ticket_permlevel_docperm(role, permlevel, permissions):
    if not frappe.db.exists("Role", role):
        frappe.throw(f"Role missing: {role}")

    existing_name = _get_existing_custom_docperm(role, permlevel)

    if existing_name:
        doc = frappe.get_doc("Custom DocPerm", existing_name)
        created = False
    else:
        doc = frappe.new_doc("Custom DocPerm")
        doc.parent = "HD Ticket"
        doc.role = role
        doc.permlevel = permlevel
        created = True

    changed = created

    for field in PERMISSION_FIELDS:
        target = int(permissions.get(field, 0))
        current = int(doc.get(field) or 0)

        if current != target:
            doc.set(field, target)
            changed = True

    if changed:
        if created:
            doc.insert(ignore_permissions=True)
        else:
            doc.save(ignore_permissions=True)

    return {
        "role": role,
        "permlevel": permlevel,
        "created": created,
        "changed": changed,
        "name": doc.name,
    }


def configure_hd_ticket_field_permissions():
    field_results = []
    perm_results = []

    for fieldname in PERMLEVEL_1_FIELDS:
        field_results.append(_set_custom_field_permlevel(fieldname, 1))

    for fieldname in PERMLEVEL_2_FIELDS:
        field_results.append(_set_custom_field_permlevel(fieldname, 2))

    for permlevel, role_matrix in PERMLEVEL_DOCPERM_MATRIX.items():
        for role, permissions in role_matrix.items():
            perm_results.append(
                _upsert_hd_ticket_permlevel_docperm(role, permlevel, permissions)
            )

    frappe.clear_cache()
    frappe.db.commit()

    return {
        "field_results": field_results,
        "perm_results": perm_results,
        "field_changed_count": len([row for row in field_results if row["changed"]]),
        "perm_created_count": len([row for row in perm_results if row["created"]]),
        "perm_changed_count": len([row for row in perm_results if row["changed"]]),
    }
