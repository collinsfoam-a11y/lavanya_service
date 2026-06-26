// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Service Ticket Extension', {
    refresh(frm) {
        // Show linked information
        if (frm.doc.name && !frm.is_new()) {
            // Show resolution time
            if (frm.doc.resolution_days) {
                frm.dashboard.add_comment(`Resolved in ${frm.doc.resolution_days} days`, 'green', true);
            }
        }

        // Add custom buttons
        if (!frm.is_new()) {
            frm.add_custom_button(__('Create Stock Complaint'), function() {
                frappe.new_doc('Lavanya Stock Complaint', {
                    lavanya_service_case_group: frm.doc.lavanya_service_case_group,
                    customer: frm.doc.customer_name,
                    ticket: frm.doc.name
                });
            }, __('Create'));

            frm.add_custom_button(__('Create Replacement Recovery'), function() {
                frappe.new_doc('Lavanya Replacement Recovery', {
                    lavanya_service_case_group: frm.doc.lavanya_service_case_group,
                    customer: frm.doc.customer_name,
                    ticket: frm.doc.name
                });
            }, __('Create'));

            frm.add_custom_button(__('Create Supplier Claim'), function() {
                frappe.new_doc('Lavanya Supplier Claim', {
                    lavanya_service_case_group: frm.doc.lavanya_service_case_group,
                    customer: frm.doc.customer_name,
                    ticket: frm.doc.name
                });
            }, __('Create'));

            frm.add_custom_button(__('View Service Case Group'), function() {
                frappe.set_route('Form', 'Lavanya Service Case Group', frm.doc.lavanya_service_case_group);
            }, __('View'));

            frm.add_custom_button(__('View Customer 360'), function() {
                frappe.set_route('Form', 'Customer', frm.doc.customer_name);
            }, __('View'));
        }

        // Show hold information
        if (frm.doc.status === 'On Hold' && frm.doc.hold_reason) {
            frm.dashboard.add_comment(`On Hold: ${frm.doc.hold_reason}`, 'orange', true);
        }
    },

    validate(frm) {
        // Validate mobile number
        if (frm.doc.customer_number) {
            const mobile = frm.doc.customer_number.replace(/\s/g, '').replace(/-/g, '');
            if (mobile.length !== 10 || !/^\d+$/.test(mobile)) {
                frappe.msgprint(__('Customer Number must be 10 digits'));
                frappe.validated = false;
            }
        }

        // Validate PIN code
        if (frm.doc.customer_site_pin) {
            const pin = frm.doc.customer_site_pin.replace(/\s/g, '');
            if (pin.length !== 6 || !/^\d+$/.test(pin)) {
                frappe.msgprint(__('Customer Site PIN must be 6 digits'));
                frappe.validated = false;
            }
        }

        // Validate serial number format
        if (frm.doc.serial_no && frm.doc.serial_no.length !== 15) {
            frappe.msgprint(__('Serial Number must be 15 characters (XXXXXXYYYYYYZZZ)'));
            frappe.validated = false;
        }
    },

    payment_received(frm) {
        // Toggle payment amount required
        if (frm.doc.payment_received) {
            frm.set_df_property('payment_amount', 'reqd', 1);
        } else {
            frm.set_df_property('payment_amount', 'reqd', 0);
            frm.set_value('payment_amount', 0);
            frm.set_value('payment_reference', '');
        }
    },

    token_issued(frm) {
        // Toggle token number required
        if (frm.doc.token_issued) {
            frm.set_df_property('token_number', 'reqd', 1);
        } else {
            frm.set_df_property('token_number', 'reqd', 0);
            frm.set_value('token_number', '');
        }
    },

    status(frm) {
        // Show hold fields when status is On Hold
        if (frm.doc.status === 'On Hold') {
            frm.set_df_property('status_before_hold', 'reqd', 1);
            frm.set_df_property('hold_reason', 'reqd', 1);
            frm.set_df_property('hold_date', 'reqd', 1);
        } else {
            frm.set_df_property('status_before_hold', 'reqd', 0);
            frm.set_df_property('hold_reason', 'reqd', 0);
            frm.set_df_property('hold_date', 'reqd', 0);
        }
    }
});
