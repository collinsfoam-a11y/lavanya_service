// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Service Case Group', {
    refresh(frm) {
        // Show linked tickets count
        if (frm.doc.name && !frm.is_new()) {
            frappe.call({
                method: 'frappe.client.get_count',
                args: {
                    doctype: 'Lavanya Ticket',
                    filters: {
                        lavanya_service_case_group: frm.doc.name
                    }
                },
                callback: function(r) {
                    if (r.message) {
                        frm.dashboard.add_comment(`Linked Tickets: ${r.message}`, 'blue', true);
                    }
                }
            });
        }

        // Add custom buttons
        if (!frm.is_new()) {
            frm.add_custom_button(__('Create Ticket'), function() {
                frappe.new_doc('Lavanya Ticket', {
                    lavanya_service_case_group: frm.doc.name,
                    customer: frm.doc.customer,
                    primary_contact: frm.doc.primary_contact,
                    primary_mobile: frm.doc.primary_mobile
                });
            }, __('Create'));

            frm.add_custom_button(__('Create Stock Complaint'), function() {
                frappe.new_doc('Lavanya Stock Complaint', {
                    lavanya_service_case_group: frm.doc.name,
                    customer: frm.doc.customer
                });
            }, __('Create'));

            frm.add_custom_button(__('View Customer 360'), function() {
                frappe.set_route('Form', 'Customer', frm.doc.customer);
            }, __('View'));
        }
    },

    validate(frm) {
        // Validate mobile number
        if (frm.doc.primary_mobile) {
            const mobile = frm.doc.primary_mobile.replace(/\s/g, '').replace(/-/g, '');
            if (mobile.length !== 10 || !/^\d+$/.test(mobile)) {
                frappe.msgprint(__('Primary Mobile must be 10 digits'));
                frappe.validated = false;
            }
        }
    }
});
