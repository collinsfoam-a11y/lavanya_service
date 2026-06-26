# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe

def after_insert(doc, method):
    """Log creation of installation job"""
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Lavanya Installation Job",
        "reference_name": doc.name,
        "content": f"Installation Job {doc.name} created for {doc.customer}"
    }).insert(ignore_permissions=True)
