import frappe

def has_permission(doc, ptype, user):
    roles = frappe.get_roles()
    if "Lavanya Owner" in roles or "Service Manager" in roles:
        return True
    if ptype == "read":
        return "Service Staff" in roles or "Front Desk" in roles
    if ptype in ("write", "create"):
        return "Service Staff" in roles or "Front Desk" in roles
    if ptype == "delete":
        return "Lavanya Owner" in roles
    return False
