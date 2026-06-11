import frappe


CUSTOMER_PROFILE_DOCTYPE = "Lavanya Customer Profile"

FORM_SCRIPT_NAMES = [
	"Lavanya Customer Mobile Autofill - Ticket Form",
	"Lavanya Customer Mobile Autofill - New Ticket",
]


CUSTOMER_AUTOFILL_FORM_SCRIPT = """
function setupForm({ doc, updateField, call, toast, createToast }) {
  let lastLookupMobile = "";

  function normalizeMobile(value) {
    if (!value) return "";
    let digits = String(value).replace(/\\D+/g, "");
    if (digits.startsWith("91") && digits.length === 12) {
      digits = digits.slice(2);
    }
    if (digits.startsWith("0") && digits.length === 11) {
      digits = digits.slice(1);
    }
    return /^\\d{10}$/.test(digits) ? digits : "";
  }

  function currentValue(fieldname) {
    return doc && doc[fieldname] ? String(doc[fieldname]).trim() : "";
  }

  function setIfBlank(fieldname, value) {
    if (!value || currentValue(fieldname)) return;
    if (typeof updateField === "function") {
      updateField(fieldname, value);
    } else if (doc) {
      doc[fieldname] = value;
    }
  }

  async function lookupAndFill(value) {
    const mobile = normalizeMobile(value);
    if (!mobile || mobile === lastLookupMobile) return;

    lastLookupMobile = mobile;

    let result = await call("lavanya_service.api.customer_intake.lookup_customer_by_mobile", {
      mobile,
    });

    if (result && result.message) {
      result = result.message;
    }

    if (!result || !result.found) return;

    setIfBlank("customer_name", result.customer_name);
    setIfBlank("phone_2", result.alternate_mobile);
    setIfBlank("address", result.address);
    setIfBlank("pincode", result.pincode);
  }

  return {
    actions: [],
    onChange: {
      phone_1: lookupAndFill,
    },
  };
}
""".strip()


def _field(fieldname, label, fieldtype, **kwargs):
	row = {
		"fieldname": fieldname,
		"label": label,
		"fieldtype": fieldtype,
	}
	row.update(kwargs)
	return row


def _permission(role="System Manager"):
	return {
		"role": role,
		"read": 1,
		"write": 1,
		"create": 1,
		"delete": 1,
		"submit": 0,
		"cancel": 0,
		"amend": 0,
		"export": 1,
		"report": 1,
		"share": 1,
		"print": 1,
		"email": 1,
	}


def ensure_lavanya_customer_profile():
	if frappe.db.exists("DocType", CUSTOMER_PROFILE_DOCTYPE):
		return "exists"

	doc = frappe.get_doc(
		{
			"doctype": "DocType",
			"name": CUSTOMER_PROFILE_DOCTYPE,
			"module": "Lavanya Service",
			"custom": 1,
			"istable": 0,
			"editable_grid": 1,
			"track_changes": 1,
			"allow_rename": 0,
			"autoname": "field:primary_mobile",
			"title_field": "customer_name",
			"search_fields": "customer_name, primary_mobile, alternate_mobile",
			"sort_field": "modified",
			"sort_order": "DESC",
			"fields": [
				_field("customer_name", "Customer Name", "Data", reqd=1, in_list_view=1),
				_field(
					"primary_mobile",
					"Primary Mobile",
					"Data",
					reqd=1,
					unique=1,
					in_list_view=1,
					in_standard_filter=1,
				),
				_field("alternate_mobile", "Alternate Mobile", "Data", in_list_view=1),
				_field("address", "Address", "Small Text"),
				_field("pincode", "Pincode", "Data", in_list_view=1),
				_field("last_ticket", "Last Ticket", "Link", options="HD Ticket", in_list_view=1),
				_field("ticket_count", "Ticket Count", "Int", default="0", in_list_view=1),
				_field("last_product_type", "Last Product Type", "Data"),
				_field("last_brand", "Last Brand", "Link", options="Brand Service Master"),
				_field("disabled", "Disabled", "Check", default="0", in_standard_filter=1),
			],
			"permissions": [_permission()],
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache(doctype=CUSTOMER_PROFILE_DOCTYPE)
	return "created"


def _upsert_hd_form_script(name, apply_on_new_page):
	if not frappe.db.exists("DocType", "HD Form Script"):
		frappe.throw("HD Form Script DocType is missing.")

	if frappe.db.exists("HD Form Script", name):
		doc = frappe.get_doc("HD Form Script", name)
		created = False
	else:
		doc = frappe.new_doc("HD Form Script")
		doc.name = name
		created = True

	doc.dt = "HD Ticket"
	doc.apply_to = "Form"
	doc.enabled = 1
	doc.is_standard = 0
	doc.apply_to_customer_portal = 0
	doc.apply_on_new_page = 1 if apply_on_new_page else 0
	doc.script = CUSTOMER_AUTOFILL_FORM_SCRIPT

	if created:
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	return {"name": name, "created": created}


def ensure_customer_intake_form_scripts():
	results = [
		_upsert_hd_form_script(FORM_SCRIPT_NAMES[0], apply_on_new_page=False),
		_upsert_hd_form_script(FORM_SCRIPT_NAMES[1], apply_on_new_page=True),
	]
	frappe.db.commit()
	frappe.clear_cache(doctype="HD Form Script")
	return results


def configure_customer_intake():
	return {
		"doctype": ensure_lavanya_customer_profile(),
		"form_scripts": ensure_customer_intake_form_scripts(),
	}
