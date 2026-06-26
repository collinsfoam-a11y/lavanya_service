# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe

def after_insert(doc, method):
    """Log creation of service ticket extension"""
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Lavanya Service Ticket Extension",
        "reference_name": doc.name,
        "content": f"Service Ticket Extension {doc.name} created for {doc.customer_name}"
    }).insert(ignore_permissions=True)
