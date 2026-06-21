import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def _require_doctype(name):
    if not frappe.db.exists("DocType", name):
        frappe.throw(f"Missing required DocType: {name}")


def _ensure_doctype(name, fields, *, istable=0):
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
            "sort_field": "modified",
            "sort_order": "DESC",
            "fields": fields,
            "permissions": [] if istable else [{"role": "System Manager", "read": 1, "write": 1, "create": 1}],
        }
    )
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.clear_cache(doctype=name)
    return "created"


def _field(fieldname, label, fieldtype, **kwargs):
    row = {"fieldname": fieldname, "label": label, "fieldtype": fieldtype}
    row.update(kwargs)
    return row


def create_followup_log_entry():
    return _ensure_doctype(
        "Follow-up Log Entry",
        [
            _field("stage", "Stage", "Select", options=FOLLOWUP_STAGE_OPTIONS, reqd=1, in_list_view=1),
            _field("completed_at", "Completed At", "Datetime", reqd=1, in_list_view=1),
            _field("user", "User", "Link", options="User", reqd=1, in_list_view=1),
            _field("is_re_entry", "Re-entry", "Check", default=0, in_list_view=1),
            _field("action_label", "Action", "Data", in_list_view=1),
            _field("notes", "Notes", "Small Text"),
        ],
        istable=1,
    )


FOLLOWUP_STAGE_OPTIONS = "\n".join([
    "registration_done",
    "technician_call_pending",
    "technician_called",
    "technician_visit_pending",
    "technician_visited",
    "no_technician_update",
    "sc_followup_done",
    "customer_informed",
    "part_pending",
    "customer_confirmation_pending",
    "customer_satisfied",
    "customer_not_satisfied",
])

SERVICE_PATH_OPTIONS = "\n".join([
    "brand_warranty",
    "brand_denied_local",
    "out_of_warranty_local",
    "customer_paid_local",
    "lavanya_paid_goodwill",
    "demo_installation",
    "stock_supplier",
    "store_service",
    "replacement_brand",
    "return_service",
])

SERVICE_CHARGE_TYPE_OPTIONS = "\n".join([
    "Brand Warranty - No Charge",
    "Customer Paid Local Service",
    "Customer Pays Technician Directly",
    "Customer Pays Lavanya",
    "Lavanya Pays Technician",
    "Commission Receivable",
    "Goodwill / Free Service",
    "Brand Reimbursement Expected",
])

CUSTOMER_SATISFACTION_OPTIONS = "\n".join([
    "Pending",
    "Satisfied",
    "Not Satisfied",
    "Customer Not Reachable",
    "Not Required",
])

CUSTOMER_INFORMED_STATUS_OPTIONS = "\n".join([
    "Not Required",
    "Pending",
    "Informed by Call",
    "Informed by WhatsApp",
    "Informed by SMS",
    "Customer Not Reachable",
])

PAYMENT_STATUS_OPTIONS = "\n".join([
    "Not Applicable",
    "Pending",
    "Approved",
    "Paid",
])


def create_followup_fields():
    create_followup_log_entry()
    fields = {
        "HD Ticket": [
            {
                "fieldname": "lavanya_followup_tracking_section",
                "label": "Follow-up Tracking",
                "fieldtype": "Section Break",
                "insert_after": "escalation_level",
                "collapsible": 1,
            },
            {
                "fieldname": "service_path",
                "label": "Service Path",
                "fieldtype": "Select",
                "options": SERVICE_PATH_OPTIONS,
                "insert_after": "lavanya_followup_tracking_section",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "followup_stage",
                "label": "Follow-up Stage",
                "fieldtype": "Select",
                "options": FOLLOWUP_STAGE_OPTIONS,
                "insert_after": "service_path",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "followup_tracking_col",
                "fieldtype": "Column Break",
                "insert_after": "followup_stage",
            },
            {
                "fieldname": "service_charge_type",
                "label": "Service Charge Type",
                "fieldtype": "Select",
                "options": SERVICE_CHARGE_TYPE_OPTIONS,
                "insert_after": "followup_tracking_col",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "customer_satisfaction_status",
                "label": "Customer Satisfaction",
                "fieldtype": "Select",
                "options": CUSTOMER_SATISFACTION_OPTIONS,
                "default": "Pending",
                "insert_after": "service_charge_type",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "customer_informed_status",
                "label": "Customer Informed Status",
                "fieldtype": "Select",
                "options": CUSTOMER_INFORMED_STATUS_OPTIONS,
                "default": "Pending",
                "insert_after": "customer_satisfaction_status",
                "in_standard_filter": 1,
            },
            {
                "fieldname": "last_service_center_followup",
                "label": "Last SC Follow-up At",
                "fieldtype": "Datetime",
                "insert_after": "customer_informed_status",
                "read_only": 1,
            },
            {
                "fieldname": "last_followup_summary",
                "label": "Last Follow-up Summary",
                "fieldtype": "Small Text",
                "insert_after": "last_service_center_followup",
                "read_only": 1,
            },
            {
                "fieldname": "last_followup_at",
                "label": "Last Follow-up At",
                "fieldtype": "Datetime",
                "insert_after": "last_followup_summary",
                "read_only": 1,
            },
            {
                "fieldname": "no_update_count",
                "label": "No Update Count",
                "fieldtype": "Int",
                "insert_after": "last_followup_at",
                "default": "0",
                "read_only": 1,
            },
            {
                # §5 bounded non-response: when no_update_count breaches the
                # configured max, the ticket parks here and leaves Today's Work
                # until the customer responds (resume_followup re-enters the loop).
                "fieldname": "parked_pending_customer",
                "label": "Parked - Pending Customer Response",
                "fieldtype": "Check",
                "insert_after": "no_update_count",
                "default": "0",
                "read_only": 1,
                "in_standard_filter": 1,
            },
            {
                "fieldname": "parked_at",
                "label": "Parked At",
                "fieldtype": "Datetime",
                "insert_after": "parked_pending_customer",
                "read_only": 1,
            },
            {
                "fieldname": "parked_reason",
                "label": "Parked Reason",
                "fieldtype": "Small Text",
                "insert_after": "parked_at",
                "read_only": 1,
            },
            {
                "fieldname": "lavanya_followup_log_section",
                "label": "Follow-up Log",
                "fieldtype": "Section Break",
                "insert_after": "parked_reason",
                "collapsible": 1,
            },
            {
                "fieldname": "followup_log",
                "label": "Follow-up Log",
                "fieldtype": "Table",
                "options": "Follow-up Log Entry",
                "insert_after": "lavanya_followup_log_section",
            },
            {
                "fieldname": "lavanya_part_section",
                "label": "Part Tracking",
                "fieldtype": "Section Break",
                "insert_after": "followup_log",
                "collapsible": 1,
            },
            {
                "fieldname": "part_required",
                "label": "Part Required",
                "fieldtype": "Check",
                "insert_after": "lavanya_part_section",
                "default": "0",
            },
            {
                "fieldname": "part_name",
                "label": "Part Name / Description",
                "fieldtype": "Data",
                "insert_after": "part_required",
            },
            {
                "fieldname": "part_expected_date",
                "label": "Part Expected Date",
                "fieldtype": "Date",
                "insert_after": "part_name",
            },
            {
                "fieldname": "part_fitted_confirmed",
                "label": "Part Fitted Confirmed",
                "fieldtype": "Check",
                "insert_after": "part_expected_date",
                "default": "0",
            },
            {
                "fieldname": "part_col",
                "fieldtype": "Column Break",
                "insert_after": "part_fitted_confirmed",
            },
            {
                "fieldname": "part_delay_reason",
                "label": "Part Delay Reason",
                "fieldtype": "Small Text",
                "insert_after": "part_col",
            },
            {
                "fieldname": "customer_informed_about_part_delay",
                "label": "Customer Informed About Part Delay",
                "fieldtype": "Select",
                "options": "Yes\nNo",
                "insert_after": "part_delay_reason",
                "default": "No",
            },
            {
                "fieldname": "lavanya_finance_section",
                "label": "Service Finance",
                "fieldtype": "Section Break",
                "insert_after": "customer_informed_about_part_delay",
                "collapsible": 1,
            },
            {
                "fieldname": "estimated_amount",
                "label": "Estimated Amount",
                "fieldtype": "Currency",
                "insert_after": "lavanya_finance_section",
            },
            {
                "fieldname": "customer_approved_amount",
                "label": "Customer Approved Amount",
                "fieldtype": "Currency",
                "insert_after": "estimated_amount",
            },
            {
                "fieldname": "finance_col",
                "fieldtype": "Column Break",
                "insert_after": "customer_approved_amount",
            },
            {
                "fieldname": "technician_payable",
                "label": "Technician Payable",
                "fieldtype": "Currency",
                "insert_after": "finance_col",
            },
            {
                "fieldname": "commission_amount",
                "label": "Commission Amount",
                "fieldtype": "Currency",
                "insert_after": "technician_payable",
            },
            {
                "fieldname": "payment_status",
                "label": "Payment Status",
                "fieldtype": "Select",
                "options": PAYMENT_STATUS_OPTIONS,
                "default": "Not Applicable",
                "insert_after": "commission_amount",
            },
        ]
    }
    create_custom_fields(fields, update=True)
    frappe.clear_cache(doctype="HD Ticket")
    return "ok"
