# Copyright (c) 2026, Lavanya Service
# For license information, please see license.txt

import frappe

def after_insert(doc, method):
    """Log creation of stock condition decision"""
    frappe.get_doc({
        "doctype": "Comment",
        "comment_type": "Info",
        "reference_doctype": "Lavanya Stock Condition Decision",
        "reference_name": doc.name,
        "content": f"Stock Condition Decision {doc.name} created for {doc.item_code}"
    }).insert(ignore_permissions=True)
