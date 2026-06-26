# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe

def after_insert(doc, method):
    """Log creation of showroom handover token"""
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Lavanya Showroom Handover Token",
        "reference_name": doc.name,
        "content": f"Handover Token {doc.name} created for {doc.customer_name}"
    }).insert(ignore_permissions=True)
