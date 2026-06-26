import frappe


def execute():
    if not frappe.db.exists("DocType", "Payment Gateway"):
        dt = frappe.get_doc({
            "doctype": "DocType",
            "name": "Payment Gateway",
            "module": "Accounts",
            "custom": 0,
            "fields": [
                {"fieldname": "gateway", "fieldtype": "Data", "label": "Gateway", "reqd": 1, "in_list_view": 1}
            ],
            "permissions": [
                {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}
            ]
        })
        dt.insert()
        frappe.db.commit()
        print("Created Payment Gateway DocType")
    else:
        print("Payment Gateway DocType already exists")


def clean_test_purchase_invoices():
    pis = frappe.get_all("Purchase Invoice", {"is_test": 1, "supplier_invoice_no": ["is", "set"]}, ["name", "supplier_invoice_no", "docstatus"])
    for pi in pis:
        try:
            if pi.docstatus == 1:
                frappe.get_doc("Purchase Invoice", pi.name).cancel()
            frappe.delete_doc("Purchase Invoice", pi.name, ignore_permissions=True)
            print(f"Deleted {pi.name} (supplier_invoice_no={pi.supplier_invoice_no})")
        except Exception as e:
            print(f"Failed to delete {pi.name}: {e}")
    frappe.db.commit()
    print(f"Cleaned up {len(pis)} Purchase Invoices")
