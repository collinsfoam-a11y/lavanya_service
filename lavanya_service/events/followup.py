import frappe

def validate_customer_informed(doc, method):
    """
    Enforce: every service center follow-up log entry must record
    whether the customer was informed. No blank value allowed.
    """
    if doc.action_type == "Service Center Follow-up":
        if doc.customer_informed not in ("Yes", "No", "Not Required"):
            frappe.throw(
                "Customer Informed field is mandatory for Service Center Follow-up entries. "
                "Please select Yes, No, or Not Required (with reason).",
                title="Follow-up Validation"
            )
        if doc.customer_informed == "Not Required" and not doc.customer_informed_reason:
            frappe.throw(
                "Please provide a reason why the customer was not informed.",
                title="Follow-up Validation"
            )
