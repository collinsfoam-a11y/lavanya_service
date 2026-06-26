# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe

def after_insert(doc, method):
    """Log creation of communication log"""
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Lavanya Customer Communication Log",
        "reference_name": doc.name,
        "content": f"Communication logged: {doc.communication_type} - {doc.summary[:50]}"
    }).insert(ignore_permissions=True)
