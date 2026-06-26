// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Service Settings', {
    refresh(frm) {
        // Show current settings
        if (frm.doc.name) {
            frm.dashboard.add_comment('Service Settings - Single DocType', 'blue', true);
        }
    },

    validate(frm) {
        // Validate auto close days
        if (frm.doc.auto_close_days && frm.doc.auto_close_days < 1) {
            frappe.msgprint(__('Auto Close Days must be at least 1'));
            frappe.validated = false;
        }

        // Validate escalation days
        if (frm.doc.escalation_days && frm.doc.escalation_days < 1) {
            frappe.msgprint(__('Escalation Days must be at least 1'));
            frappe.validated = false;
        }

        // Validate reopen days
        if (frm.doc.allow_reopen_days && frm.doc.allow_reopen_days < 1) {
            frappe.msgprint(__('Allow Reopen Days must be at least 1'));
            frappe.validated = false;
        }
    }
});
