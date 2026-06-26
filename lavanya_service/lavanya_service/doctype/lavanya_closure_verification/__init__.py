# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe

def after_insert(doc, method):
    """Log creation of closure verification"""
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Lavanya Closure Verification",
        "reference_name": doc.name,
        "content": f"Closure Verification {doc.name} created"
    }).insert(ignore_permissions=True)
