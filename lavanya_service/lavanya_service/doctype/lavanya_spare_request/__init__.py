# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe

def after_insert(doc, method):
    """Log creation of spare request"""
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Lavanya Spare Request",
        "reference_name": doc.name,
        "content": f"Spare Request {doc.name} created by {doc.requestor}"
    }).insert(ignore_permissions=True)
