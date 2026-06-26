import frappe


def execute():
    pis = frappe.get_all("Purchase Invoice", {"is_test": 1, "supplier_invoice_no": ["is", "set"]}, ["name", "supplier_invoice_no", "docstatus"])
    for pi in pis:
        print(f"{pi.name}: supplier_invoice_no={pi.supplier_invoice_no}, status={pi.docstatus}")
        if pi.docstatus == 1:
            frappe.get_doc("Purchase Invoice", pi.name).cancel()
        frappe.delete_doc("Purchase Invoice", pi.name, ignore_permissions=True)
    print(f"Cleaned up {len(pis)} Purchase Invoices")
