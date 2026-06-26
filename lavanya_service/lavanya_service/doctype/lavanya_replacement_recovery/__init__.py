# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe

def after_insert(doc, method):
    """Log creation of replacement recovery"""
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Lavanya Replacement Recovery",
        "reference_name": doc.name,
        "content": f"Replacement Recovery {doc.name} created for {doc.customer}"
    }).insert(ignore_permissions=True)
