# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe

def after_insert(doc, method):
    """Log creation of customer product"""
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Lavanya Customer Product",
        "reference_name": doc.name,
        "content": f"Customer Product {doc.product_name} added for {doc.customer}"
    }).insert(ignore_permissions=True)
