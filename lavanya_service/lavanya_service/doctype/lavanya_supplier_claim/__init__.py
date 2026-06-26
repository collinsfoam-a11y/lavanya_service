# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe

def after_insert(doc, method):
    """Log creation of supplier claim"""
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Lavanya Supplier Claim",
        "reference_name": doc.name,
        "content": f"Supplier Claim {doc.name} created for {doc.supplier}"
    }).insert(ignore_permissions=True)
