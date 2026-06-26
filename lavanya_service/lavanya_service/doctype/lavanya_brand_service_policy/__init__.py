# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe

def after_insert(doc, method):
    """Log creation of brand service policy"""
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Lavanya Brand Service Policy",
        "reference_name": doc.name,
        "content": f"Brand Service Policy {doc.name} created for {doc.brand}"
    }).insert(ignore_permissions=True)
