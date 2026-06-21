import frappe

def create_or_update_client_script():
    script_name = "Lavanya Status-Aware Ticket Form"
    doctype = "HD Ticket"
    
    script_content = """
// P0.1 Status-Aware Ticket Form (Upgraded with Stitch Banners)
// We handle visibility based on status and role

const PENDING_REGISTRATION = "Registration Pending";
const PRODUCT_AT_STORE = "Customer Product at Store";
const STOCK_COMPLAINT = "Stock Complaint";
const RESOLVED = "Resolved";
const READY_FOR_PICKUP = "Ready for Pickup";
const CLOSED = "Closed";

frappe.ui.form.on("HD Ticket", {
    refresh: function(frm) {
        updateVisibility(frm);
    },
    status: function(frm) {
        updateVisibility(frm);
    },
    ticket_type: function(frm) {
        updateVisibility(frm);
    },
    brand_registration_recommended: function(frm) {
        updateVisibility(frm);
    }
});

function updateVisibility(frm) {
    if (!frm || !frm.doc) return;

    const doc = frm.doc;
    const status = doc.status;
    const ticketType = doc.ticket_type;
    const isBrandRecommended = doc.brand_registration_recommended;

    // Roles
    const isManager = frappe.user.has_role("Lavanya Manager");
    const isCoordinator = frappe.user.has_role("Lavanya Service Coordinator");

    // 1. Warranty / Brand Service
    if (isBrandRecommended || status === PENDING_REGISTRATION || doc.brand_ticket_number || doc.registration_date) {
        frm.toggle_display("brand_service_section", true);
    } else {
        frm.toggle_display("brand_service_section", false);
    }

    // 2. Product at Store
    if (ticketType === PRODUCT_AT_STORE || ticketType === STOCK_COMPLAINT || doc.service_product_receipt) {
        frm.toggle_display("lavanya_purchase_section", true);
    } else {
        frm.toggle_display("lavanya_purchase_section", false);
    }

    // 3. Repeat Complaint
    if (isManager || isCoordinator) {
        frm.toggle_display("lavanya_followup_section", true);
    } else {
        frm.toggle_display("is_repeated_complaint", false);
        frm.toggle_display("previous_ticket_link", false);
    }

    // 4. Closure
    if ((status === RESOLVED || status === READY_FOR_PICKUP || status === CLOSED) && (isManager || isCoordinator)) {
        frm.toggle_display("closure_type", true);
        frm.toggle_display("work_narration", true);
        frm.toggle_display("customer_confirmation_received", true);
        frm.toggle_display("closed_by", true);
        frm.toggle_display("closure_date", true);
    } else {
        frm.toggle_display("closure_type", false);
        frm.toggle_display("work_narration", false);
        frm.toggle_display("customer_confirmation_received", false);
        frm.toggle_display("closed_by", false);
        frm.toggle_display("closure_date", false);
    }

    // 5. Stitch UI Banners
    renderStitchBanners(frm, status, doc);
}

function renderStitchBanners(frm, status, doc) {
    if (!frm || !frm.dashboard) return;
    
    frm.dashboard.clear_headline();

    if (status === "Waiting on Part / Approval" || (doc.ticket_type === PRODUCT_AT_STORE && !doc.service_product_receipt && status !== CLOSED && status !== "Cancelled" && status !== RESOLVED && status !== READY_FOR_PICKUP)) {
        const html = `
            <div style="background: #fff1f0; border: 2px solid #ba1a1a; padding: 16px; border-radius: 8px; font-family: Inter, sans-serif; display: flex; gap: 16px; align-items: flex-start; margin-bottom: 16px;">
                <div style="font-size: 24px; color: #ba1a1a;">&#9888;</div>
                <div>
                    <div style="font-size: 16px; font-weight: 600; color: #1c1a24; margin-bottom: 4px;">Product Receipt Missing</div>
                    <div style="font-size: 14px; color: #494456; margin-bottom: 12px;">This is a Store ticket but no Service Product Receipt is linked.</div>
                    <div style="font-size: 13px; font-weight: 500; color: #ba1a1a;">Action Required: Please Create Product Receipt via Lavanya Actions</div>
                </div>
            </div>
        `;
        if (!doc.service_product_receipt && doc.ticket_type === PRODUCT_AT_STORE) {
            frm.dashboard.set_headline(html);
        }
    } 
    
    if (status === READY_FOR_PICKUP) {
        const html = `
            <div style="background: #eaf6ed; border: 2px solid #1a7f37; padding: 16px; border-radius: 8px; font-family: Inter, sans-serif; display: flex; gap: 16px; align-items: flex-start; margin-bottom: 16px;">
                <div style="font-size: 24px; color: #1a7f37;">&#10004;</div>
                <div style="flex: 1;">
                    <div style="font-size: 16px; font-weight: 600; color: #1c1a24; margin-bottom: 4px;">Ready for Pickup</div>
                    <div style="font-size: 14px; color: #494456;">The product has been repaired and is awaiting customer collection.</div>
                </div>
                <div>
                    <div style="font-size: 12px; font-weight: 600; color: #1a7f37; background: #cce8d5; padding: 4px 12px; border-radius: 99px;">Awaiting Collection</div>
                </div>
            </div>
        `;
        frm.dashboard.set_headline(html);
    }
}
"""

    if frappe.db.exists("Client Script", {"dt": doctype, "name": script_name}):
        doc = frappe.get_doc("Client Script", {"dt": doctype, "name": script_name})
        doc.script = script_content
        doc.save()
        print("Updated existing Client Script.")
    else:
        doc = frappe.get_doc({
            "doctype": "Client Script",
            "dt": doctype,
            "name": script_name,
            "module": "Lavanya Service",
            "script": script_content,
            "enabled": 1,
            "view": "Form"
        })
        doc.insert()
        print("Created new Client Script.")
    frappe.db.commit()

create_or_update_client_script()
