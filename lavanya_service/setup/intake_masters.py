import frappe


CATEGORY_DOCTYPE = "Lavanya Product Category"
ITEM_DOCTYPE = "Lavanya Product Item"

PRODUCT_FORM_SCRIPT_NAMES = [
	"Lavanya Intake Master Shortcuts - Ticket Form",
	"Lavanya Intake Master Shortcuts - New Ticket",
]


PRODUCT_SHORTCUT_FORM_SCRIPT = """
function setupForm({ doc, updateField, call, toast, createToast }) {
  function currentValue(fieldname) {
    return doc && doc[fieldname] ? String(doc[fieldname]).trim() : "";
  }

  function notify(message) {
    if (toast && toast.info) {
      toast.info(message);
    } else if (createToast) {
      createToast({ title: message, icon: "info" });
    }
  }

  function setField(fieldname, value, overwrite = false) {
    if (!value) return;
    if (!overwrite && currentValue(fieldname)) return;
    if (typeof updateField === "function") {
      updateField(fieldname, value);
    } else if (doc) {
      doc[fieldname] = value;
    }
  }

  async function callMethod(method, args) {
    let result = await call(method, args || {});
    return result && result.message ? result.message : result;
  }

  async function applyItemDefaults(value) {
    if (!value) return;
    const result = await callMethod("lavanya_service.api.intake_masters.get_item_defaults", {
      item: value,
    });
    if (!result || !result.found) return;

    setField("brand", result.brand, true);
    setField("product_category", result.item_type, true);
    setField("product_type", result.product_type, true);
    setField("model_no", result.model_no, false);
  }

  async function addWithSimilarityCheck(label, searchMethod, createMethod, argsBuilder, afterCreate) {
    const name = window.prompt("Add " + label + " name");
    if (!name) return;
    const matches = await callMethod(searchMethod, { query: name });
    if (matches && matches.length) {
      const summary = matches.slice(0, 5).map((row) => row.name).join(", ");
      const proceed = window.confirm("Similar " + label + " records found: " + summary + ". Create anyway?");
      if (!proceed) return;
    }
    const created = await callMethod(createMethod, argsBuilder(name));
    if (created && created.name) {
      afterCreate(created);
      notify(label + " added: " + created.name);
    }
  }

  async function addBrand() {
    await addWithSimilarityCheck(
      "Brand",
      "lavanya_service.api.intake_masters.search_similar_brand",
      "lavanya_service.api.intake_masters.create_brand",
      (name) => ({ name }),
      (created) => setField("brand", created.name, true)
    );
  }

  async function addCategory() {
    await addWithSimilarityCheck(
      "Product Category",
      "lavanya_service.api.intake_masters.search_similar_category",
      "lavanya_service.api.intake_masters.create_category",
      (name) => ({ category_name: name }),
      (created) => {
        setField("product_category", created.name, true);
        setField("product_type", created.name, true);
      }
    );
  }

  async function addItem() {
    await addWithSimilarityCheck(
      "Product Item",
      "lavanya_service.api.intake_masters.search_similar_item",
      "lavanya_service.api.intake_masters.create_item",
      (name) => ({
        item_name: name,
        brand: currentValue("brand"),
        item_type: currentValue("product_category") || currentValue("product_type"),
        model_no: currentValue("model_no"),
      }),
      (created) => {
        setField("product_item", created.name, true);
        applyItemDefaults(created.name);
      }
    );
  }

  return {
    actions: [
      { label: "Add Brand", onClick: addBrand },
      { label: "Add Category", onClick: addCategory },
      { label: "Add Item", onClick: addItem },
    ],
    onChange: {
      product_item: applyItemDefaults,
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


def _permission(role="System Manager", *, read=1, write=1, create=1, delete=1):
	return {
		"role": role,
		"read": read,
		"write": write,
		"create": create,
		"delete": delete,
		"submit": 0,
		"cancel": 0,
		"amend": 0,
		"export": read,
		"report": read,
		"share": write,
		"print": read,
		"email": read,
	}


def _ensure_doctype(name, fields, *, autoname, title_field, search_fields):
	if frappe.db.exists("DocType", name):
		return "exists"

	doc = frappe.get_doc(
		{
			"doctype": "DocType",
			"name": name,
			"module": "Lavanya Service",
			"custom": 1,
			"istable": 0,
			"editable_grid": 1,
			"track_changes": 1,
			"allow_rename": 0,
			"autoname": autoname,
			"title_field": title_field,
			"search_fields": search_fields,
			"sort_field": "modified",
			"sort_order": "DESC",
			"fields": fields,
			"permissions": [
				_permission(),
				_permission("All", read=1, write=0, create=0, delete=0),
			],
		}
	)
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache(doctype=name)
	return "created"


def ensure_product_category_doctype():
	return _ensure_doctype(
		CATEGORY_DOCTYPE,
		[
			_field(
				"category_name",
				"Category Name",
				"Data",
				reqd=1,
				unique=1,
				in_list_view=1,
				in_standard_filter=1,
			),
			_field(
				"parent_category",
				"Parent Category",
				"Link",
				options=CATEGORY_DOCTYPE,
				in_list_view=1,
				in_standard_filter=1,
			),
			_field("disabled", "Disabled", "Check", default="0", in_standard_filter=1),
		],
		autoname="field:category_name",
		title_field="category_name",
		search_fields="category_name,parent_category",
	)


def ensure_product_item_doctype():
	if not frappe.db.exists("DocType", CATEGORY_DOCTYPE):
		frappe.throw(f"Missing required DocType: {CATEGORY_DOCTYPE}")
	if not frappe.db.exists("DocType", "Brand Service Master"):
		frappe.throw("Missing required DocType: Brand Service Master")

	return _ensure_doctype(
		ITEM_DOCTYPE,
		[
			_field(
				"item_name",
				"Item Name",
				"Data",
				reqd=1,
				unique=1,
				in_list_view=1,
				in_standard_filter=1,
			),
			_field(
				"item_type",
				"Item Type",
				"Link",
				options=CATEGORY_DOCTYPE,
				in_list_view=1,
				in_standard_filter=1,
			),
			_field(
				"brand",
				"Brand",
				"Link",
				options="Brand Service Master",
				in_list_view=1,
				in_standard_filter=1,
			),
			_field("model_no", "Model No", "Data", in_list_view=1, in_standard_filter=1),
			_field("default_warranty_months", "Default Warranty Months", "Int", default="0"),
			_field("disabled", "Disabled", "Check", default="0", in_standard_filter=1),
		],
		autoname="field:item_name",
		title_field="item_name",
		search_fields="item_name,item_type,brand,model_no",
	)


def _upsert_hd_ticket_custom_field(config):
	existing_name = frappe.db.exists(
		"Custom Field",
		{
			"dt": "HD Ticket",
			"fieldname": config["fieldname"],
		},
	)

	if existing_name:
		doc = frappe.get_doc("Custom Field", existing_name)
		action = "updated"
	else:
		doc = frappe.new_doc("Custom Field")
		doc.dt = "HD Ticket"
		doc.fieldname = config["fieldname"]
		action = "created"

	for key, value in config.items():
		doc.set(key, value)

	doc.dt = "HD Ticket"
	doc.save(ignore_permissions=True)
	return action


def ensure_hd_ticket_product_master_fields():
	if not frappe.db.exists("DocType", CATEGORY_DOCTYPE):
		frappe.throw(f"Missing required DocType: {CATEGORY_DOCTYPE}")
	if not frappe.db.exists("DocType", ITEM_DOCTYPE):
		frappe.throw(f"Missing required DocType: {ITEM_DOCTYPE}")

	results = {
		"product_category": _upsert_hd_ticket_custom_field(
			{
				"fieldname": "product_category",
				"label": "Product Category",
				"fieldtype": "Link",
				"options": CATEGORY_DOCTYPE,
				"insert_after": "product_type",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"permlevel": 0,
			}
		),
		"product_item": _upsert_hd_ticket_custom_field(
			{
				"fieldname": "product_item",
				"label": "Product Item",
				"fieldtype": "Link",
				"options": ITEM_DOCTYPE,
				"insert_after": "product_category",
				"in_list_view": 1,
				"in_standard_filter": 1,
				"permlevel": 0,
			}
		),
		"product_subtype": _upsert_hd_ticket_custom_field(
			{
				"fieldname": "product_subtype",
				"label": "Product Subtype",
				"fieldtype": "Select",
				"options": "Split AC\nWindow AC\nFront Load\nSemi Automatic\nOther",
				"insert_after": "product_item",
				"permlevel": 0,
			}
		),
	}

	frappe.db.commit()
	frappe.clear_cache(doctype="HD Ticket")
	return results


def ensure_default_template_product_fields():
	template = frappe.get_doc("HD Ticket Template", "Default")
	target_rows = [
		{
			"fieldname": "product_category",
			"required": 0,
			"hide_from_customer": 0,
			"placeholder": "Product category",
		},
		{
			"fieldname": "product_item",
			"required": 0,
			"hide_from_customer": 0,
			"placeholder": "Product item",
		},
	]

	existing_rows = [
		{
			"fieldname": row.fieldname,
			"required": row.required,
			"hide_from_customer": row.hide_from_customer,
			"placeholder": row.placeholder,
		}
		for row in template.fields
		if row.fieldname not in {"product_category", "product_item"}
	]

	insert_at = len(existing_rows)
	for idx, row in enumerate(existing_rows):
		if row["fieldname"] == "product_type":
			insert_at = idx + 1
			break

	rebuilt_rows = existing_rows[:insert_at] + target_rows + existing_rows[insert_at:]

	template.set("fields", [])
	for row in rebuilt_rows:
		template.append("fields", row)

	template.save(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache()

	return {
		"template": "Default",
		"fields": [row.fieldname for row in template.fields],
		"field_count": len(template.fields),
	}


def _upsert_hd_form_script(name, apply_on_new_page):
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
	doc.script = PRODUCT_SHORTCUT_FORM_SCRIPT

	if created:
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	return {"name": name, "created": created}


def ensure_intake_master_form_scripts():
	results = [
		_upsert_hd_form_script(PRODUCT_FORM_SCRIPT_NAMES[0], apply_on_new_page=False),
		_upsert_hd_form_script(PRODUCT_FORM_SCRIPT_NAMES[1], apply_on_new_page=True),
	]
	frappe.db.commit()
	frappe.clear_cache(doctype="HD Form Script")
	return results


def configure_intake_masters():
	category_result = ensure_product_category_doctype()
	item_result = ensure_product_item_doctype()
	field_results = ensure_hd_ticket_product_master_fields()
	template_result = ensure_default_template_product_fields()
	script_results = ensure_intake_master_form_scripts()

	return {
		"category_doctype": category_result,
		"item_doctype": item_result,
		"fields": field_results,
		"template": template_result,
		"form_scripts": script_results,
	}
