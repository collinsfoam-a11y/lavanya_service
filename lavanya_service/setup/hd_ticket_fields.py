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


PRODUCT_SUBTYPE_OPTIONS = "\n".join(
    [
        "Split AC",
        "Window AC",
        "Front Load",
        "Semi Automatic",
        "Other",
    ]
)


PENDING_REASON_OPTIONS = "\n".join(
    [
        "Invoice Proof Pending",
        "Invoice Pending",
        "Brand Registration Recommended",
        "Manufacturer Registration Pending",
        "Service Follow-up Required",
        "Brand Ticket Number Pending",
        "Customer Details Missing",
        "Technician Not Visited",
        "Service Center Delayed",
        "Service Center Out of Area",
        "Customer Not Reachable",
        "Customer Reappointed",
        "Part Pending",
        "Part Warranty Pending",
        "Replacement Approval Pending",
        "Supplier Approval Pending",
        "Customer Pickup Pending",
        "Manager Escalation Pending",
        "Local Technician Pending",
        "Local Service Transfer Pending",
        "Estimate Approval Pending",
        "Brand Line Busy",
        "Service Center Unreachable",
        "Other",
    ]
)


CLOSURE_TYPE_OPTIONS = "\n".join(
    [
        "Resolved by Brand Service",
        "Resolved by Local Technician",
        "Replacement Completed",
        "Customer Collected Product",
        "Customer Cancelled",
        "Duplicate Ticket",
        "Not Purchased From Lavanya - Guided Only",
        "Brand Denied Warranty",
        "Customer Not Responding",
        "Closed After Manager Approval",
        "Other",
    ]
)


FIELDS = [
    {
        "fieldname": "lavanya_customer_section",
        "label": "Lavanya Customer Details",
        "fieldtype": "Section Break",
        "insert_after": "ticket_type",
    },
    {
        "fieldname": "complaint_source",
        "label": "Complaint Source",
        "fieldtype": "Select",
        "options": "Phone Call\nWhatsApp\nDirect Visit\nStaff Entered\nEmail\nCustomer QR Form",
        "insert_after": "lavanya_customer_section",
        "in_list_view": 1,
        "in_standard_filter": 1,
    },
    {
        "fieldname": "customer_name",
        "label": "Customer Name",
        "fieldtype": "Data",
        "insert_after": "complaint_source",
        "in_list_view": 1,
    },
    {
        "fieldname": "phone_1",
        "label": "Phone 1",
        "fieldtype": "Data",
        "insert_after": "customer_name",
        "in_list_view": 1,
        "in_standard_filter": 1,
    },
    {
        "fieldname": "phone_2",
        "label": "Phone 2",
        "fieldtype": "Data",
        "insert_after": "phone_1",
    },
    {
        "fieldname": "phone_1_raw",
        "label": "Phone 1 Raw",
        "fieldtype": "Data",
        "insert_after": "phone_2",
        "hidden": 1,
        "read_only": 1,
    },
    {
        "fieldname": "phone_1_normalized",
        "label": "Phone 1 Normalized",
        "fieldtype": "Data",
        "insert_after": "phone_1_raw",
        "hidden": 1,
        "read_only": 1,
    },
    {
        "fieldname": "phone_2_raw",
        "label": "Phone 2 Raw",
        "fieldtype": "Data",
        "insert_after": "phone_1_normalized",
        "hidden": 1,
        "read_only": 1,
    },
    {
        "fieldname": "phone_2_normalized",
        "label": "Phone 2 Normalized",
        "fieldtype": "Data",
        "insert_after": "phone_2_raw",
        "hidden": 1,
        "read_only": 1,
    },
    {
        "fieldname": "address",
        "label": "Address",
        "fieldtype": "Small Text",
        "insert_after": "phone_2_normalized",
    },
    {
        "fieldname": "pincode",
        "label": "Pincode",
        "fieldtype": "Data",
        "insert_after": "address",
        "in_standard_filter": 1,
    },
    {
        "fieldname": "lavanya_product_section",
        "label": "Lavanya Product Details",
        "fieldtype": "Section Break",
        "insert_after": "pincode",
    },
    {
        "fieldname": "product_type",
        "label": "Product Type",
        "fieldtype": "Select",
        "options": PRODUCT_TYPE_OPTIONS,
        "insert_after": "lavanya_product_section",
        "in_list_view": 1,
        "in_standard_filter": 1,
    },
    {
        "fieldname": "product_category",
        "label": "Product Category",
        "fieldtype": "Link",
        "options": "Lavanya Product Category",
        "insert_after": "product_type",
        "in_list_view": 1,
        "in_standard_filter": 1,
    },
    {
        "fieldname": "product_item",
        "label": "Product Item",
        "fieldtype": "Link",
        "options": "Lavanya Product Item",
        "insert_after": "product_category",
        "in_list_view": 1,
        "in_standard_filter": 1,
    },
    {
        "fieldname": "product_subtype",
        "label": "Product Subtype",
        "fieldtype": "Select",
        "options": PRODUCT_SUBTYPE_OPTIONS,
        "insert_after": "product_item",
    },
    {
        "fieldname": "brand",
        "label": "Brand",
        "fieldtype": "Link",
        "options": "Brand Service Master",
        "insert_after": "product_subtype",
        "in_list_view": 1,
        "in_standard_filter": 1,
    },
    {
        "fieldname": "model_no",
        "label": "Model No",
        "fieldtype": "Data",
        "insert_after": "brand",
    },
    {
        "fieldname": "serial_no",
        "label": "Serial No",
        "fieldtype": "Data",
        "insert_after": "model_no",
        "in_standard_filter": 1,
    },
    {
        "fieldname": "lavanya_purchase_section",
        "depends_on": "eval: doc.ticket_type === 'Customer Product at Store' || doc.ticket_type === 'Stock Complaint' || doc.service_product_receipt",
        "label": "Lavanya Purchase and Warranty",
        "fieldtype": "Section Break",
        "insert_after": "serial_no",
    },
    {
        "fieldname": "purchased_from_lavanya",
        "label": "Purchased From Lavanya",
        "fieldtype": "Select",
        "options": "Yes\nNo\nUnknown",
        "insert_after": "lavanya_purchase_section",
        "in_standard_filter": 1,
    },
    {
        "fieldname": "invoice_source",
        "label": "Invoice Source",
        "fieldtype": "Select",
        "options": "Old ERP\nManual Bill\nCustomer Claim\nNot Available",
        "insert_after": "purchased_from_lavanya",
    },
    {
        "fieldname": "old_erp_reference",
        "label": "Old ERP Reference",
        "fieldtype": "Data",
        "insert_after": "invoice_source",
    },
    {
        "fieldname": "purchase_date",
        "label": "Purchase Date",
        "fieldtype": "Date",
        "insert_after": "old_erp_reference",
    },
    {
        "fieldname": "warranty_status",
        "label": "Warranty Status",
        "fieldtype": "Select",
        "options": "In Warranty\nOut of Warranty\nUnknown\nExtended Warranty\nBrand Denied",
        "insert_after": "purchase_date",
        "in_standard_filter": 1,
    },
    {
        "fieldname": "lavanya_brand_service_section",
        "depends_on": "eval: doc.brand_registration_recommended || doc.status === 'Registration Pending' || doc.brand_ticket_number || doc.registration_date",
        "label": "Lavanya Brand Service Coordination",
        "fieldtype": "Section Break",
        "insert_after": "warranty_status",
    },
    {
        "fieldname": "manufacturer_registration_required",
        "label": "Manufacturer Registration Required",
        "fieldtype": "Select",
        "options": "Yes\nNo\nNot Applicable",
        "insert_after": "lavanya_brand_service_section",
        "default": "Yes",
    },
    {
        "fieldname": "manufacturer_registered",
        "label": "Manufacturer Registered",
        "fieldtype": "Select",
        "options": "Yes\nNo\nPending\nFailed",
        "insert_after": "manufacturer_registration_required",
        "default": "Pending",
        "in_standard_filter": 1,
    },
    {
        "fieldname": "brand_ticket_number",
        "label": "Brand Ticket Number",
        "fieldtype": "Data",
        "insert_after": "manufacturer_registered",
        "in_list_view": 1,
    },
    {
        "fieldname": "registration_date",
        "label": "Registration Date",
        "fieldtype": "Date",
        "insert_after": "brand_ticket_number",
    },
    {
        "fieldname": "registration_pending_reason",
        "label": "Registration Pending Reason",
        "fieldtype": "Select",
        "options": "Brand Line Busy\nCustomer Details Missing\nInvoice Missing\nService Center Unreachable",
        "insert_after": "registration_date",
    },
    {
        "fieldname": "brand_registration_recommended",
        "label": "Brand Registration Recommended",
        "fieldtype": "Check",
        "insert_after": "registration_pending_reason",
        "default": "0",
        "read_only": 1,
        "permlevel": 1,
    },
    {
        "fieldname": "brand_registration_override_reason",
        "label": "Brand Registration Override Reason",
        "fieldtype": "Small Text",
        "insert_after": "brand_registration_recommended",
        "permlevel": 1,
    },
    {
        "fieldname": "brand_registration_recommended_at",
        "label": "Brand Registration Recommended At",
        "fieldtype": "Datetime",
        "insert_after": "brand_registration_override_reason",
        "read_only": 1,
        "hidden": 1,
        "permlevel": 1,
    },
    {
        "fieldname": "service_center",
        "label": "Service Center",
        "fieldtype": "Link",
        "options": "Service Center Master",
        "insert_after": "brand_registration_recommended_at",
    },
    {
        "fieldname": "local_technician",
        "label": "Local Technician",
        "fieldtype": "Link",
        "options": "Local Technician Master",
        "insert_after": "service_center",
        "read_only": 0,
        "hidden": 0,
    },
    {
        "fieldname": "lavanya_followup_section",
        "label": "Lavanya Follow-up and Closure",
        "fieldtype": "Section Break",
        "insert_after": "local_technician",
    },
    {
        "fieldname": "is_repeated_complaint",
        "depends_on": "eval: doc._is_manager || doc._is_coordinator",
        "label": "Is Repeated Complaint",
        "fieldtype": "Select",
        "options": "Yes\nNo",
        "insert_after": "lavanya_followup_section",
        "default": "No",
        "in_standard_filter": 1,
    },
    {
        "fieldname": "previous_ticket_link",
        "depends_on": "eval: doc._is_manager || doc._is_coordinator",
        "label": "Previous Ticket Link",
        "fieldtype": "Link",
        "options": "HD Ticket",
        "insert_after": "is_repeated_complaint",
    },
    {
        "fieldname": "pending_reason",
        "label": "Pending Reason",
        "fieldtype": "Select",
        "options": PENDING_REASON_OPTIONS,
        "insert_after": "previous_ticket_link",
        "in_list_view": 1,
        "in_standard_filter": 1,
    },
    {
        "fieldname": "next_follow_up_date",
        "label": "Next Follow-up Date",
        "fieldtype": "Date",
        "insert_after": "pending_reason",
        "in_list_view": 1,
        "in_standard_filter": 1,
    },
    {
        "fieldname": "closure_type",
        "depends_on": "eval: (doc.status === 'Resolved' || doc.status === 'Ready for Pickup' || doc.status === 'Closed') && (doc._is_manager || doc._is_coordinator)",
        "label": "Closure Type",
        "fieldtype": "Select",
        "options": CLOSURE_TYPE_OPTIONS,
        "insert_after": "next_follow_up_date",
    },
    {
        "fieldname": "work_narration",
        "depends_on": "eval: (doc.status === 'Resolved' || doc.status === 'Ready for Pickup' || doc.status === 'Closed') && (doc._is_manager || doc._is_coordinator)",
        "label": "Work Narration",
        "fieldtype": "Long Text",
        "insert_after": "closure_type",
    },
    {
        "fieldname": "customer_confirmation_received",
        "depends_on": "eval: (doc.status === 'Resolved' || doc.status === 'Ready for Pickup' || doc.status === 'Closed') && (doc._is_manager || doc._is_coordinator)",
        "label": "Customer Confirmation Received",
        "fieldtype": "Select",
        "options": "Yes\nNo\nNot Required",
        "insert_after": "work_narration",
        "default": "No",
    },
    {
        "fieldname": "closed_by",
        "depends_on": "eval: (doc.status === 'Resolved' || doc.status === 'Ready for Pickup' || doc.status === 'Closed') && (doc._is_manager || doc._is_coordinator)",
        "label": "Closed By",
        "fieldtype": "Link",
        "options": "User",
        "insert_after": "customer_confirmation_received",
        "read_only": 1,
    },
    {
        "fieldname": "closure_date",
        "depends_on": "eval: (doc.status === 'Resolved' || doc.status === 'Ready for Pickup' || doc.status === 'Closed') && (doc._is_manager || doc._is_coordinator)",
        "label": "Closure Date",
        "fieldtype": "Datetime",
        "insert_after": "closed_by",
        "read_only": 1,
    },
]


def _validate_dependencies():
    for doctype in [
        "HD Ticket",
        "Brand Service Master",
        "Lavanya Product Category",
        "Lavanya Product Item",
        "Service Center Master",
        "Local Technician Master",
    ]:
        if not frappe.db.exists("DocType", doctype):
            frappe.throw(f"Missing required DocType: {doctype}")

def ensure_custom_field(config):
    fieldname = config["fieldname"]
    existing_name = frappe.db.exists(
        "Custom Field", {"dt": "HD Ticket", "fieldname": fieldname}
    )

    if existing_name:
        doc = frappe.get_doc("Custom Field", existing_name)
        action = "updated"
    else:
        doc = frappe.new_doc("Custom Field")
        doc.dt = "HD Ticket"
        doc.fieldname = fieldname
        action = "created"

    for key, value in config.items():
        doc.set(key, value)

    doc.dt = "HD Ticket"
    doc.save(ignore_permissions=True)
    return action


def create_hd_ticket_custom_fields():
    _validate_dependencies()

    results = {}
    for config in FIELDS:
        results[config["fieldname"]] = ensure_custom_field(config)

    frappe.db.commit()
    frappe.clear_cache(doctype="HD Ticket")

    return results
