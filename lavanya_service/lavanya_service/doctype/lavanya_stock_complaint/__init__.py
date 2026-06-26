# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe

def after_insert(doc, method):
    """Log creation of stock complaint"""
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Lavanya Stock Complaint",
        "reference_name": doc.name,
        "content": f"Stock Complaint {doc.name} created for {doc.stock_item}"
    }).insert(ignore_permissions=True)
