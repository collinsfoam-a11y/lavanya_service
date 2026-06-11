import frappe


PRODUCT_TYPE_OPTIONS = "\n".join(
    [
        "AC",
        "Refrigerator",
        "Washing Machine",
        "Mixer",
        "Induction Cooker",
        "Chimney",
        "Hob",
        "Gas Stove",
        "TV",
        "Water Purifier",
        "Other",
    ]
)


CUSTODY_STATUS_OPTIONS = "\n".join(
    [
        "Received at Store",
        "Handed to Service Center",
        "With Local Technician",
        "Returned to Store",
        "Ready for Customer Pickup",
        "Delivered to Customer",
        "Cancelled",
    ]
)


CUSTODY_ACTION_OPTIONS = "\n".join(
    [
        "Received",
        "Handed Over",
        "Returned",
        "Ready for Pickup",
        "Delivered",
        "Cancelled",
        "Note",
    ]
)


def field(fieldname, label, fieldtype, **kwargs):
    row = {
        "fieldname": fieldname,
        "label": label,
        "fieldtype": fieldtype,
    }
    row.update(kwargs)
    return row


def permission(role="System Manager"):
    return {
        "role": role,
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 1,
        "submit": 0,
        "cancel": 0,
        "amend": 0,
        "export": 1,
        "report": 1,
        "share": 1,
        "print": 1,
        "email": 1,
    }


def _require_doctype(name):
    if not frappe.db.exists("DocType", name):
        frappe.throw(f"Missing required DocType: {name}")


def _ensure_doctype(name, fields, *, istable=0, autoname=None, title_field=None):
    if frappe.db.exists("DocType", name):
        return "exists"

    doc = frappe.get_doc(
        {
            "doctype": "DocType",
            "name": name,
            "module": "Lavanya Service",
            "custom": 1,
            "istable": istable,
            "editable_grid": 1,
            "track_changes": 1,
            "allow_rename": 0,
            "autoname": autoname or "",
            "title_field": title_field or "",
            "sort_field": "modified",
            "sort_order": "DESC",
            "fields": fields,
            "permissions": [permission()] if not istable else [],
        }
    )
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache(doctype=name)
    return "created"


def create_custody_log_entry():
    return _ensure_doctype(
        "Custody Log Entry",
        [
            field(
                "custody_action",
                "Custody Action",
                "Select",
                options=CUSTODY_ACTION_OPTIONS,
                reqd=1,
                in_list_view=1,
            ),
            field(
                "custody_status",
                "Custody Status",
                "Select",
                options=CUSTODY_STATUS_OPTIONS,
                reqd=1,
                in_list_view=1,
            ),
            field(
                "action_datetime",
                "Action Datetime",
                "Datetime",
                reqd=1,
                in_list_view=1,
            ),
            field("from_party", "From Party", "Data", in_list_view=1),
            field("to_party", "To Party", "Data", in_list_view=1),
            field("handled_by", "Handled By", "Link", options="User", in_list_view=1),
            field("notes", "Notes", "Small Text"),
        ],
        istable=1,
    )


def create_service_product_receipt():
    _require_doctype("HD Ticket")
    _require_doctype("Brand Service Master")
    _require_doctype("Service Center Master")
    _require_doctype("Local Technician Master")
    _require_doctype("Custody Log Entry")

    return _ensure_doctype(
        "Service Product Receipt",
        [
            field(
                "naming_series",
                "Naming Series",
                "Select",
                options="LV-SR-.YYYY.-.####",
                default="LV-SR-.YYYY.-.####",
                reqd=1,
            ),
            field(
                "ticket",
                "HD Ticket",
                "Link",
                options="HD Ticket",
                reqd=1,
                in_list_view=1,
                in_standard_filter=1,
            ),
            field(
                "current_custody_status",
                "Current Custody Status",
                "Select",
                options=CUSTODY_STATUS_OPTIONS,
                default="Received at Store",
                reqd=1,
                in_list_view=1,
                in_standard_filter=1,
            ),
            field("receipt_date", "Receipt Date", "Datetime", reqd=1, in_list_view=1),
            field("received_by", "Received By", "Link", options="User", in_list_view=1),
            field("customer_section", "Customer Details", "Section Break"),
            field("customer_name", "Customer Name", "Data", in_list_view=1),
            field("phone", "Phone", "Data", in_list_view=1),
            field("address", "Address", "Small Text"),
            field("product_section", "Product Details", "Section Break"),
            field(
                "product_type",
                "Product Type",
                "Select",
                options=PRODUCT_TYPE_OPTIONS,
                in_list_view=1,
                in_standard_filter=1,
            ),
            field(
                "brand",
                "Brand",
                "Link",
                options="Brand Service Master",
                in_list_view=1,
                in_standard_filter=1,
            ),
            field("model_no", "Model No", "Data"),
            field("serial_no", "Serial No", "Data", in_standard_filter=1),
            field("accessories_received", "Accessories Received", "Small Text"),
            field("physical_condition", "Physical Condition", "Small Text"),
            field("service_section", "Service Handling", "Section Break"),
            field("service_center", "Service Center", "Link", options="Service Center Master"),
            field(
                "local_technician",
                "Local Technician",
                "Link",
                options="Local Technician Master",
            ),
            field("expected_return_date", "Expected Return Date", "Date"),
            field("actual_return_date", "Actual Return Date", "Date"),
            field("customer_pickup_date", "Customer Pickup Date", "Datetime"),
            field("cost_section", "Cost Details", "Section Break"),
            field("estimated_cost", "Estimated Cost", "Currency"),
            field("approved_cost", "Approved Cost", "Currency"),
            field("final_cost", "Final Cost", "Currency"),
            field("customer_approval_required", "Customer Approval Required", "Check"),
            field("customer_approval_received", "Customer Approval Received", "Check"),
            field("custody_log_section", "Custody Log", "Section Break"),
            field("custody_log", "Custody Log", "Table", options="Custody Log Entry"),
        ],
        autoname="naming_series:",
        title_field="ticket",
    )


def ensure_service_product_receipt_link_field():
    _require_doctype("HD Ticket")
    _require_doctype("Service Product Receipt")

    existing_name = frappe.db.exists(
        "Custom Field",
        {
            "dt": "HD Ticket",
            "fieldname": "service_product_receipt",
        },
    )

    if existing_name:
        doc = frappe.get_doc("Custom Field", existing_name)
        action = "updated"
    else:
        doc = frappe.new_doc("Custom Field")
        doc.dt = "HD Ticket"
        doc.fieldname = "service_product_receipt"
        action = "created"

    doc.label = "Service Product Receipt"
    doc.fieldtype = "Link"
    doc.options = "Service Product Receipt"
    doc.insert_after = "next_follow_up_date"
    doc.read_only = 0
    doc.hidden = 0
    doc.in_list_view = 1
    doc.in_standard_filter = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()
    frappe.clear_cache(doctype="HD Ticket")

    return action


def create_service_receipt_doctypes_and_link():
    result = {}

    result["Custody Log Entry"] = create_custody_log_entry()
    result["Service Product Receipt"] = create_service_product_receipt()
    result["HD Ticket service_product_receipt"] = (
        ensure_service_product_receipt_link_field()
    )

    frappe.db.commit()
    frappe.clear_cache()

    return result
