"""HD Form Script that adds Phase 1N-6B quick action buttons to HD Ticket.

The buttons are a convenience layer only. They prompt for the required fields,
call the whitelisted ``lavanya_service.api.workflow_actions.*`` endpoints, show
the result and reload the ticket. All authorization and validation is enforced
server-side; if button visibility is imperfect the backend still blocks
unauthorized or invalid calls.

Install / refresh with:
    bench --site <site> execute \
        lavanya_service.setup.quick_actions_form_script.ensure_quick_action_form_scripts
"""

import frappe


FORM_SCRIPT_NAME = "Lavanya Quick Actions - Ticket Form"


QUICK_ACTIONS_FORM_SCRIPT = r"""
function setupForm({ doc, call, toast, createToast }) {
  const API = "lavanya_service.api.workflow_actions";
  const GROUP = "lavanya-quick-actions";
  const BUTTON_LABEL = "Lavanya Actions";

  function notify(message, isError) {
    const text = String(message || "");
    if (isError) {
      if (toast && toast.error) return toast.error(text);
    } else if (toast && toast.success) {
      return toast.success(text);
    }
    if (createToast) {
      createToast({ title: text, icon: isError ? "alert-circle" : "check" });
    } else {
      // eslint-disable-next-line no-alert
      window.alert(text);
    }
  }

  function ticketName() {
    return doc && doc.name ? String(doc.name) : "";
  }

  function ask(label, hint) {
    const prompt = hint ? label + "\n(" + hint + ")" : label;
    // eslint-disable-next-line no-alert
    const value = window.prompt(prompt, "");
    return value == null ? null : String(value).trim();
  }

  function askRequired(label, hint) {
    const value = ask(label, hint);
    if (value === null) return { cancelled: true };
    if (!value) {
      notify(label + " is required.", true);
      return { cancelled: true };
    }
    return { value };
  }

  function todayString() {
    return new Date().toISOString().slice(0, 10);
  }

  async function runAction(method, args) {
    const name = ticketName();
    if (!name) {
      notify("Save the ticket before running a quick action.", true);
      return;
    }
    try {
      let result = await call(method, Object.assign({ ticket_name: name }, args));
      if (result && result.message) result = result.message;
      notify((result && result.message) || "Action completed.", false);
      setTimeout(function () { window.location.reload(); }, 600);
    } catch (error) {
      const message =
        (error && error.messages && error.messages.join(", ")) ||
        (error && error.message) ||
        "Action failed.";
      notify(message, true);
    }
  }

  function action(label, handler) {
    return { label, buttonLabel: BUTTON_LABEL, group: GROUP, onClick: handler };
  }

  const actions = [
    action("Register Brand Complaint", async function () {
      const brand = askRequired("Brand Ticket Number");
      if (brand.cancelled) return;
      const regDate = askRequired("Registration Date", "YYYY-MM-DD");
      if (regDate.cancelled) return;
      const followUp = askRequired("Next Follow-up Date", "YYYY-MM-DD");
      if (followUp.cancelled) return;
      const serviceCenter = ask("Service Center (optional)");
      await runAction(API + ".register_brand_complaint", {
        brand_ticket_number: brand.value,
        registration_date: regDate.value,
        next_follow_up_date: followUp.value,
        service_center: serviceCenter || "",
      });
    }),

    action("Need Invoice from Customer", async function () {
      const followUp = askRequired("Next Follow-up Date", "YYYY-MM-DD");
      if (followUp.cancelled) return;
      const note = ask("Note (optional)");
      await runAction(API + ".need_invoice_from_customer", {
        next_follow_up_date: followUp.value,
        note: note || "",
      });
    }),

    action("Follow Up Service Center", async function () {
      const result = askRequired(
        "Follow-up Result",
        "Service center contacted | Technician assigned | Customer not reachable | Service completed | Part pending | Approval pending"
      );
      if (result.cancelled) return;
      let followUp = "";
      if (result.value !== "Service completed") {
        const ask2 = askRequired("Next Follow-up Date", "YYYY-MM-DD");
        if (ask2.cancelled) return;
        followUp = ask2.value;
      }
      await runAction(API + ".follow_up_service_center", {
        follow_up_result: result.value,
        next_follow_up_date: followUp,
      });
    }),

    action("Waiting for Part", async function () {
      const reason = askRequired(
        "Pending Reason",
        "e.g. Part Pending | Part Warranty Pending | Estimate Approval Pending"
      );
      if (reason.cancelled) return;
      const followUp = askRequired("Next Follow-up Date", "YYYY-MM-DD");
      if (followUp.cancelled) return;
      await runAction(API + ".waiting_for_part", {
        pending_reason: reason.value,
        next_follow_up_date: followUp.value,
      });
    }),

    action("Product Ready", async function () {
      const followUp = ask("Next Follow-up Date (optional)", "YYYY-MM-DD");
      await runAction(API + ".mark_product_ready", {
        next_follow_up_date: followUp || todayString(),
      });
    }),

    action("Customer Confirmed", async function () {
      const narration = askRequired("Work Narration");
      if (narration.cancelled) return;
      const closure = askRequired(
        "Closure Type",
        "e.g. Resolved by Brand Service | Customer Collected Product | Closed After Manager Approval"
      );
      if (closure.cancelled) return;
      await runAction(API + ".customer_confirmed", {
        work_narration: narration.value,
        closure_type: closure.value,
      });
    }),

    action("Close Ticket", async function () {
      const confirm = askRequired(
        "Customer Confirmation Received",
        "must be Yes to close"
      );
      if (confirm.cancelled) return;
      const narration = askRequired("Work Narration");
      if (narration.cancelled) return;
      const closure = askRequired("Closure Type");
      if (closure.cancelled) return;
      await runAction(API + ".close_ticket", {
        customer_confirmation_received: confirm.value,
        work_narration: narration.value,
        closure_type: closure.value,
      });
    }),

    action("Create Product Receipt", async function () {
      const accessories = ask("Accessories Received (optional)");
      const condition = ask("Physical Condition (optional)");
      await runAction(API + ".create_product_receipt", {
        accessories_received: accessories || "",
        physical_condition: condition || "",
      });
    }),
  ];

  return { actions };
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
	doc.script = QUICK_ACTIONS_FORM_SCRIPT

	if created:
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)

	return {"name": name, "created": created}


def ensure_quick_action_form_scripts():
	# Quick actions require a saved ticket, so only the existing-ticket form
	# variant is registered (apply_on_new_page=False).
	results = [_upsert_hd_form_script(FORM_SCRIPT_NAME, apply_on_new_page=False)]
	frappe.db.commit()
	frappe.clear_cache(doctype="HD Form Script")
	return results
