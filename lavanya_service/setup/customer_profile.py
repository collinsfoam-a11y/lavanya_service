import frappe


CUSTOMER_PROFILE_DOCTYPE = "Lavanya Customer Profile"

FORM_SCRIPT_NAMES = [
	"Lavanya Customer Mobile Autofill - Ticket Form",
	"Lavanya Customer Mobile Autofill - New Ticket",
]


CUSTOMER_AUTOFILL_FORM_SCRIPT = """
function setupForm({ doc, updateField, call, toast, createToast }) {
  let lastLookupMobile = "";

  // Python source of truth: lavanya_service.utils.phone.normalize_phone.
  // Keep this JS mirror synchronized.
  function normalizeMobile(value) {
    const raw = value == null ? "" : String(value);
    const cleanRaw = raw.trim();
    const result = {
      raw,
      normalized: null,
      is_valid_mobile: false,
      reason: "blank",
    };

    if (!cleanRaw) {
      result.raw = "";
      return result;
    }

    const digits = cleanRaw.replace(/\\D+/g, "");
    if (!digits) {
      result.reason = "too_short";
      return result;
    }

    let candidate = null;
    let prefixedWithZero = false;

    if (digits.length === 10) {
      candidate = digits;
    } else if (digits.length === 12 && digits.startsWith("91")) {
      candidate = digits.slice(2);
    } else if (digits.length === 11 && digits.startsWith("0")) {
      candidate = digits.slice(1);
      prefixedWithZero = true;
    } else {
      if (digits.length < 10) {
        result.reason = "too_short";
      } else if ([11, 12].includes(digits.length)) {
        result.reason = "not_indian_mobile";
      } else {
        result.reason = "too_long";
      }
      return result;
    }

    if (new Set(candidate.split("")).size === 1) {
      result.reason = "repeated_junk";
      return result;
    }

    if (!["6", "7", "8", "9"].includes(candidate[0])) {
      result.reason = prefixedWithZero ? "not_indian_mobile" : "invalid_mobile_range";
      return result;
    }

    result.normalized = candidate;
    result.is_valid_mobile = true;
    result.reason = "valid";
    return result;
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
    if (!mobile.is_valid_mobile || mobile.normalized === lastLookupMobile) return;

    lastLookupMobile = mobile.normalized;

    let result = await call("lavanya_service.api.customer_intake.lookup_customer_by_mobile", {
      mobile: mobile.normalized,
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


CUSTOMER_PROFILE_FIELDS = [
	_field("customer_name", "Customer Name", "Data", reqd=1, in_list_view=1),
	_field(
		"primary_mobile",
		"Primary Mobile",
		"Data",
		reqd=1,
		unique=1,
		search_index=1,
		in_list_view=1,
		in_standard_filter=1,
	),
	_field(
		"primary_mobile_raw",
		"Primary Mobile Raw",
		"Data",
		hidden=1,
		read_only=1,
	),
	_field("alternate_mobile", "Alternate Mobile", "Data", in_list_view=1),
	_field(
		"alternate_mobile_raw",
		"Alternate Mobile Raw",
		"Data",
		hidden=1,
		read_only=1,
	),
	_field("address", "Address", "Small Text"),
	_field("pincode", "Pincode", "Data", in_list_view=1),
	_field("last_ticket", "Last Ticket", "Link", options="HD Ticket", in_list_view=1),
	_field("ticket_count", "Ticket Count", "Int", default="0", in_list_view=1),
	_field("last_product_type", "Last Product Type", "Data"),
	_field("last_brand", "Last Brand", "Link", options="Brand Service Master"),
	_field("disabled", "Disabled", "Check", default="0", in_standard_filter=1),
]


def _apply_customer_profile_config(doc):
	doc.module = "Lavanya Service"
	doc.custom = 1
	doc.istable = 0
	doc.editable_grid = 1
	doc.track_changes = 1
	doc.allow_rename = 0
	doc.autoname = "LV-CUST-.#####"
	doc.title_field = "customer_name"
	doc.search_fields = "customer_name, primary_mobile, alternate_mobile"
	doc.sort_field = "modified"
	doc.sort_order = "DESC"

	doc.set("fields", [])
	for field in CUSTOMER_PROFILE_FIELDS:
		doc.append("fields", field)

	doc.set("permissions", [])
	doc.append("permissions", _permission())


def ensure_lavanya_customer_profile():
	if frappe.db.exists("DocType", CUSTOMER_PROFILE_DOCTYPE):
		doc = frappe.get_doc("DocType", CUSTOMER_PROFILE_DOCTYPE)
		action = "updated"
	else:
		doc = frappe.new_doc("DocType")
		doc.name = CUSTOMER_PROFILE_DOCTYPE
		action = "created"

	_apply_customer_profile_config(doc)

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	frappe.db.commit()
	frappe.clear_cache(doctype=CUSTOMER_PROFILE_DOCTYPE)
	return action


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
