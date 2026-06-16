"""HD Form Script that adds Lavanya quick action buttons to HD Ticket.

The buttons open a single modal dialog (Stitch "Lavanya Service Framework"
design) that collects the required fields, calls the whitelisted
``lavanya_service.api.workflow_actions.*`` / ``repeat_complaints.*`` endpoints,
shows the result and reloads the ticket. The dialog is a convenience layer
only — all authorization and validation is enforced server-side; if button
visibility is imperfect the backend still blocks unauthorized or invalid
calls, and the error surfaces inside the modal.

Modal primitive: the Helpdesk form-script context provides ``$dialog`` (the
frappe-ui Dialog via globalStore) in both the agent and customer ticket views.
frappe-ui's Dialog has no native field inputs, so the form is injected as HTML
and read back from the DOM on submit — the standard Helpdesk form-script
pattern. Select option lists are injected from the Python source constants
(``LV_OPTIONS``) so they can never drift from the field definitions.

Install / refresh with:
    bench --site <site> execute \
        lavanya_service.setup.quick_actions_form_script.ensure_quick_action_form_scripts
"""

import json

import frappe

from lavanya_service.setup.hd_ticket_fields import (
	CLOSURE_TYPE_OPTIONS,
	PENDING_REASON_OPTIONS,
)


FORM_SCRIPT_NAME = "Lavanya Quick Actions - Ticket Form"


# Select option lists injected into the form script, sourced from the field
# definitions so the modal selects always match the stored field options.
_LV_OPTIONS = {
	"pending_reason": PENDING_REASON_OPTIONS.split("\n"),
	"closure_type": CLOSURE_TYPE_OPTIONS.split("\n"),
	"follow_up_result": [
		"Service center contacted",
		"Technician assigned",
		"Customer not reachable",
		"Service completed",
		"Part pending",
		"Approval pending",
	],
	"customer_confirmation": ["Yes", "No", "Not Required"],
}


_FORM_SCRIPT_BODY = r"""
function setupForm({ doc, call, toast, createToast, $dialog }) {
  const API = "lavanya_service.api.workflow_actions";
  const REPEAT_API = "lavanya_service.api.repeat_complaints";
  const GROUP = "lavanya-quick-actions";
  const BUTTON_LABEL = "Lavanya Actions";

  const INPUT_STYLE =
    "width:100%;min-height:40px;padding:8px 10px;border:1px solid #e2e8f0;border-radius:4px;background:#fff;font-size:14px;color:#1c1a24;box-sizing:border-box;";
  const LABEL_STYLE =
    "display:block;font-size:13px;font-weight:500;color:#494456;margin:0 0 4px;letter-spacing:0.01em;";
  const HINT_STYLE = "font-size:12px;color:#7a7487;margin-top:2px;";
  const ROW_STYLE = "margin-bottom:14px;";
  const ERR_STYLE =
    "color:#ba1a1a;font-size:13px;font-weight:500;min-height:18px;margin-top:4px;";

  let modalSeq = 0;

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

  function todayString() {
    return new Date().toISOString().slice(0, 10);
  }

  function esc(value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function fieldHtml(uid, f) {
    const id = uid + "-" + f.name;
    const req = f.required ? ' <span style="color:#ba1a1a;">*</span>' : "";
    let input;
    if (f.type === "select") {
      const opts = (f.options || [])
        .map(function (o) { return '<option value="' + esc(o) + '">' + esc(o) + "</option>"; })
        .join("");
      input =
        '<select id="' + id + '" style="' + INPUT_STYLE + '">' +
        '<option value=""></option>' + opts + "</select>";
    } else if (f.type === "date") {
      input =
        '<input id="' + id + '" type="date" style="' + INPUT_STYLE +
        '" value="' + esc(f.default || "") + '">';
    } else if (f.type === "textarea") {
      input =
        '<textarea id="' + id + '" rows="3" style="' + INPUT_STYLE +
        'resize:vertical;">' + esc(f.default || "") + "</textarea>";
    } else {
      input =
        '<input id="' + id + '" type="text" style="' + INPUT_STYLE +
        '" value="' + esc(f.default || "") + '">';
    }
    return (
      '<div style="' + ROW_STYLE + '">' +
      '<label style="' + LABEL_STYLE + '" for="' + id + '">' + esc(f.label) + req + "</label>" +
      input +
      (f.hint ? '<div style="' + HINT_STYLE + '">' + esc(f.hint) + "</div>" : "") +
      "</div>"
    );
  }

  // Open a modal form, collect + validate fields, call the API, reload.
  function lavanyaModal(opts) {
    const name = ticketName();
    if (!name) {
      notify("Save the ticket before running a quick action.", true);
      return;
    }
    if (!$dialog) {
      notify("This view does not support quick action dialogs.", true);
      return;
    }
    const fields = opts.fields || [];
    const uid = "lvm-" + ++modalSeq;
    const html =
      '<div id="' + uid + '">' +
      (opts.intro ? '<p style="font-size:13px;color:#494456;margin:0 0 12px;">' + esc(opts.intro) + "</p>" : "") +
      fields.map(function (f) { return fieldHtml(uid, f); }).join("") +
      '<div id="' + uid + '-err" style="' + ERR_STYLE + '"></div>' +
      "</div>";

    $dialog({
      title: opts.title,
      html: html,
      actions: [
        {
          label: opts.submitLabel || "Confirm",
          variant: "solid",
          onClick: async function (ctx) {
            const args = Object.assign({ ticket_name: name }, opts.staticArgs || {});
            const missing = [];
            for (let i = 0; i < fields.length; i++) {
              const f = fields[i];
              const el = document.getElementById(uid + "-" + f.name);
              const val = el ? String(el.value || "").trim() : "";
              if (f.required && !val) missing.push(f.label);
              args[f.name] = val;
            }
            const errEl = document.getElementById(uid + "-err");
            if (missing.length) {
              if (errEl) errEl.textContent = "Required: " + missing.join(", ");
              return;
            }
            if (errEl) errEl.textContent = "";
            try {
              let result = await call(opts.api, args);
              if (result && result.message) result = result.message;
              notify((result && result.message) || "Action completed.", false);
              ctx.close();
              setTimeout(function () { window.location.reload(); }, 600);
            } catch (error) {
              const msg =
                (error && error.messages && error.messages.join(", ")) ||
                (error && error.message) ||
                "Action failed.";
              if (errEl) errEl.textContent = msg; else notify(msg, true);
            }
          },
        },
        { label: "Cancel" },
      ],
    });
  }

  // Simple confirm modal (no field inputs).
  function confirmModal(opts) {
    const name = ticketName();
    if (!name) {
      notify("Save the ticket first.", true);
      return;
    }
    if (!$dialog) {
      notify("This view does not support quick action dialogs.", true);
      return;
    }
    $dialog({
      title: opts.title,
      message: opts.message,
      actions: [
        {
          label: opts.submitLabel || "Confirm",
          variant: "solid",
          onClick: async function (ctx) {
            try {
              let result = await call(opts.api, Object.assign({ ticket_name: name }, opts.staticArgs || {}));
              if (result && result.message) result = result.message;
              notify((result && result.message) || "Done.", false);
              ctx.close();
              setTimeout(function () { window.location.reload(); }, 600);
            } catch (error) {
              const msg =
                (error && error.messages && error.messages.join(", ")) ||
                (error && error.message) ||
                "Action failed.";
              notify(msg, true);
            }
          },
        },
        { label: "Cancel" },
      ],
    });
  }

  function action(label, handler) {
    return { label, buttonLabel: BUTTON_LABEL, group: GROUP, onClick: handler };
  }

  const actions = [
    action("Register Brand Complaint", function () {
      lavanyaModal({
        title: "Register Brand Complaint",
        submitLabel: "Register",
        api: API + ".register_brand_complaint",
        fields: [
          { name: "brand_ticket_number", label: "Brand Ticket Number", type: "text", required: true },
          { name: "registration_date", label: "Registration Date", type: "date", required: true },
          { name: "next_follow_up_date", label: "Next Follow-up Date", type: "date", required: true, default: todayString() },
          { name: "service_center", label: "Service Center", type: "text", hint: "Optional" },
        ],
      });
    }),

    action("Need Invoice from Customer", function () {
      lavanyaModal({
        title: "Need Invoice from Customer",
        submitLabel: "Request Invoice",
        api: API + ".need_invoice_from_customer",
        fields: [
          { name: "next_follow_up_date", label: "Next Follow-up Date", type: "date", required: true, default: todayString() },
          { name: "note", label: "Note", type: "text", hint: "Optional" },
        ],
      });
    }),

    action("Follow Up Service Center", function () {
      lavanyaModal({
        title: "Follow Up Service Center",
        submitLabel: "Record Follow-up",
        api: API + ".follow_up_service_center",
        fields: [
          { name: "follow_up_result", label: "Follow-up Result", type: "select", required: true, options: LV_OPTIONS.follow_up_result },
          { name: "next_follow_up_date", label: "Next Follow-up Date", type: "date", hint: "Required unless result is 'Service completed'", default: todayString() },
        ],
      });
    }),

    action("Waiting for Part", function () {
      lavanyaModal({
        title: "Waiting for Part / Approval",
        submitLabel: "Mark Waiting",
        api: API + ".waiting_for_part",
        fields: [
          { name: "pending_reason", label: "Pending Reason", type: "select", required: true, options: LV_OPTIONS.pending_reason },
          { name: "next_follow_up_date", label: "Next Follow-up Date", type: "date", required: true, default: todayString() },
        ],
      });
    }),

    action("Product Ready", function () {
      lavanyaModal({
        title: "Product Ready for Pickup",
        submitLabel: "Mark Ready",
        api: API + ".mark_product_ready",
        fields: [
          { name: "next_follow_up_date", label: "Next Follow-up Date", type: "date", hint: "Optional; defaults to today", default: todayString() },
        ],
      });
    }),

    action("Customer Confirmed", function () {
      lavanyaModal({
        title: "Customer Confirmed — Close Ticket",
        submitLabel: "Confirm & Close",
        api: API + ".customer_confirmed",
        fields: [
          { name: "work_narration", label: "Work Narration", type: "textarea", required: true },
          { name: "closure_type", label: "Closure Type", type: "select", required: true, options: LV_OPTIONS.closure_type },
        ],
      });
    }),

    action("Close Ticket", function () {
      lavanyaModal({
        title: "Close Ticket",
        submitLabel: "Close Ticket",
        api: API + ".close_ticket",
        fields: [
          { name: "customer_confirmation_received", label: "Customer Confirmation Received", type: "select", required: true, options: LV_OPTIONS.customer_confirmation, hint: "Must be Yes to close" },
          { name: "work_narration", label: "Work Narration", type: "textarea", required: true },
          { name: "closure_type", label: "Closure Type", type: "select", required: true, options: LV_OPTIONS.closure_type },
        ],
      });
    }),

    action("Create Product Receipt", function () {
      lavanyaModal({
        title: "Create Product Receipt",
        submitLabel: "Create Receipt",
        api: API + ".create_product_receipt",
        fields: [
          { name: "accessories_received", label: "Accessories Received", type: "text", hint: "Optional" },
          { name: "physical_condition", label: "Physical Condition", type: "text", hint: "Optional" },
        ],
      });
    }),

    action("Check Repeat Complaint", async function () {
      const name = ticketName();
      if (!name) {
        notify("Save the ticket before checking repeat complaints.", true);
        return;
      }
      try {
        let result = await call(REPEAT_API + ".find_repeat_candidates", { ticket_name: name });
        if (result && result.message) result = result.message;
        const candidates = (result && result.candidates) || [];
        if (!candidates.length) {
          notify("No likely repeat complaint found.", false);
          return;
        }
        const options = candidates.map(function (c) {
          const product = [c.brand, c.product_item || c.product_type, c.serial_no]
            .filter(Boolean)
            .join(" / ");
          const label =
            c.ticket + " [" + (c.status || "") + "] " +
            (c.customer_name || "") + (product ? " — " + product : "") +
            " — " + (c.match_reasons || []).join(", ");
          return { value: c.ticket, label: label };
        });
        const uid = "lvm-" + ++modalSeq;
        const optsHtml = options
          .map(function (o) { return '<option value="' + esc(o.value) + '">' + esc(o.label) + "</option>"; })
          .join("");
        const html =
          '<div id="' + uid + '">' +
          '<p style="font-size:13px;color:#494456;margin:0 0 12px;">Select a previous ticket to link as a repeat complaint:</p>' +
          '<label style="' + LABEL_STYLE + '" for="' + uid + '-prev">Previous Ticket</label>' +
          '<select id="' + uid + '-prev" style="' + INPUT_STYLE + '">' + optsHtml + "</select>" +
          '<div id="' + uid + '-err" style="' + ERR_STYLE + '"></div>' +
          "</div>";
        $dialog({
          title: "Repeat Complaint Suggestions",
          html: html,
          actions: [
            {
              label: "Confirm Repeat",
              variant: "solid",
              onClick: async function (ctx) {
                const el = document.getElementById(uid + "-prev");
                const previous = el ? el.value : "";
                const errEl = document.getElementById(uid + "-err");
                if (!previous) {
                  if (errEl) errEl.textContent = "Select a ticket to link.";
                  return;
                }
                try {
                  let r = await call(REPEAT_API + ".confirm_repeat_complaint", {
                    ticket_name: name,
                    previous_ticket_link: previous,
                  });
                  if (r && r.message) r = r.message;
                  notify((r && r.message) || "Repeat complaint linked.", false);
                  ctx.close();
                  setTimeout(function () { window.location.reload(); }, 600);
                } catch (error) {
                  const msg =
                    (error && error.messages && error.messages.join(", ")) ||
                    (error && error.message) || "Action failed.";
                  if (errEl) errEl.textContent = msg; else notify(msg, true);
                }
              },
            },
            { label: "Cancel" },
          ],
        });
      } catch (error) {
        const message =
          (error && error.messages && error.messages.join(", ")) ||
          (error && error.message) || "Repeat complaint check failed.";
        notify(message, true);
      }
    }),

    action("Clear Repeat Link", function () {
      confirmModal({
        title: "Clear Repeat Link",
        message: "Clear the repeat complaint flag and previous ticket link?",
        submitLabel: "Clear",
        api: REPEAT_API + ".clear_repeat_complaint",
      });
    }),
  ];

  return { actions };
}
"""


QUICK_ACTIONS_FORM_SCRIPT = (
	"const LV_OPTIONS = " + json.dumps(_LV_OPTIONS) + ";\n" + _FORM_SCRIPT_BODY
).strip()


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
