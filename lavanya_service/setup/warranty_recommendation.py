import frappe


FORM_SCRIPT_NAMES = [
	"Lavanya Warranty Brand Registration Hint - Ticket Form",
	"Lavanya Warranty Brand Registration Hint - New Ticket",
]


WARRANTY_RECOMMENDATION_FORM_SCRIPT = """
function setupForm({ doc, updateField, toast, createToast }) {
  const recommendedTypes = new Set([
    "Customer Complaint - Site",
    "Customer Product at Store",
    "Installation / Demo",
    "Replacement / DOA",
  ]);

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

  function setFieldIfEmpty(fieldname, value) {
    if (!value || currentValue(fieldname)) return;
    if (typeof updateField === "function") {
      updateField(fieldname, value);
    } else if (doc) {
      doc[fieldname] = value;
    }
  }

  function todayString() {
    return new Date().toISOString().slice(0, 10);
  }

  function shouldRecommend() {
    return currentValue("warranty_status") === "In Warranty"
      && recommendedTypes.has(currentValue("ticket_type"))
      && currentValue("manufacturer_registered") !== "Yes";
  }

  function applyRecommendationHint() {
    if (!shouldRecommend()) return;
    setFieldIfEmpty("pending_reason", "Brand Registration Recommended");
    setFieldIfEmpty("next_follow_up_date", todayString());
    notify("In-warranty case: brand registration is recommended. Register now or record why it is not needed.");
  }

  setTimeout(applyRecommendationHint, 0);

  return {
    onChange: {
      warranty_status: applyRecommendationHint,
      ticket_type: applyRecommendationHint,
      manufacturer_registered: applyRecommendationHint,
    },
  };
}
""".strip()


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
	doc.script = WARRANTY_RECOMMENDATION_FORM_SCRIPT

	if created:
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	return {"name": name, "created": created}


def ensure_warranty_recommendation_form_scripts():
	results = [
		_upsert_hd_form_script(FORM_SCRIPT_NAMES[0], apply_on_new_page=False),
		_upsert_hd_form_script(FORM_SCRIPT_NAMES[1], apply_on_new_page=True),
	]
	frappe.db.commit()
	frappe.clear_cache(doctype="HD Form Script")
	return results
