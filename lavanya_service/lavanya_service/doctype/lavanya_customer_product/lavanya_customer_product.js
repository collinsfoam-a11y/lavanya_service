// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Customer Product', {
    refresh(frm) {
        // Show ticket count
        if (frm.doc.ticket_count) {
            frm.dashboard.add_comment(`Linked Tickets: ${frm.doc.ticket_count}`, 'blue', true);
        }

        // Show warranty status
        if (frm.doc.warranty_type && frm.doc.warranty_type !== 'None') {
            if (frm.doc.warranty_expiry) {
                const expiry = new Date(frm.doc.warranty_expiry);
                const today = new Date();
                if (expiry > today) {
                    frm.dashboard.add_comment('Warranty: Active', 'green', true);
                } else {
                    frm.dashboard.add_comment('Warranty: Expired', 'red', true);
                }
            }
        }

        // Add custom buttons
        if (!frm.is_new()) {
            frm.add_custom_button(__('Create Ticket'), function() {
                frappe.new_doc('Lavanya Service Ticket Extension', {
                    customer_name: frm.doc.customer,
                    product_category: frm.doc.product_sub_category,
                    serial_no: frm.doc.serial_no
                });
            }, __('Create'));

            frm.add_custom_button(__('View Customer 360'), function() {
                frappe.set_route('Form', 'Customer', frm.doc.customer);
            }, __('View'));
        }
    },

    validate(frm) {
        // Validate serial number format
        if (frm.doc.serial_no && frm.doc.serial_no.length !== 15) {
            frappe.msgprint(__('Serial Number must be 15 characters (XXXXXXYYYYYYZZZ)'));
            frappe.validated = false;
        }

        // Validate warranty expiry required when type set
        if (frm.doc.warranty_type && frm.doc.warranty_type !== 'None') {
            if (!frm.doc.warranty_expiry) {
                frappe.msgprint(__('Warranty Expiry is required when Warranty Type is set'));
                frappe.validated = false;
            }
        }
    }
});
