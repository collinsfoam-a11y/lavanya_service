import frappe


def clean_purchase_invoices():
    frappe.db.sql("DELETE FROM `tabPurchase Invoice` WHERE is_test = 1")
    frappe.db.commit()
    print("Deleted all test Purchase Invoices")
