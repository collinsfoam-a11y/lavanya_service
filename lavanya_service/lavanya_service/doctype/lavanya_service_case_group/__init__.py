# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe

def after_insert(doc, method):
    """Log creation of service case group"""
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Lavanya Service Case Group",
        "reference_name": doc.name,
        "content": f"Service Case Group {doc.name} created for {doc.customer}"
    }).insert(ignore_permissions=True)
