// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Spare Request', {
    refresh(frm) {
        // Show status indicator
        const status_colors = {
            'Draft': 'orange',
            'Requested': 'yellow',
            'Approved': 'blue',
            'Issued': 'green',
            'Partially Used': 'yellow',
            'Used': 'green',
            'Returned': 'blue',
            'Cancelled': 'red',
            'Closed': 'green'
        };
        if (frm.doc.status) {
            frm.page.set_indicator(frm.doc.status, status_colors[frm.doc.status] || 'gray');
        }

        // Add action buttons based on status
        if (!frm.is_new()) {
            if (frm.doc.status === 'Draft') {
                frm.add_custom_button(__('Submit Request'), function() {
                    frm.set_value('status', 'Requested');
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Requested') {
                frm.add_custom_button(__('Approve'), function() {
                    frm.set_value('status', 'Approved');
                    frm.set_value('approved_by', frappe.session.user);
                    frm.set_value('approval_date', frappe.datetime.get_today());
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Approved') {
                frm.add_custom_button(__('Mark Issued'), function() {
                    frm.set_value('status', 'Issued');
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Issued' || frm.doc.status === 'Partially Used') {
                frm.add_custom_button(__('Mark Used'), function() {
                    frm.set_value('status', 'Used');
                    frm.save();
                }).addClass('btn-primary');

                frm.add_custom_button(__('Mark Returned'), function() {
                    frm.set_value('status', 'Returned');
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Used' || frm.doc.status === 'Returned') {
                frm.add_custom_button(__('Close Request'), function() {
                    frm.set_value('status', 'Closed');
                    frm.save();
                }).addClass('btn-primary');
            }

            // Add view buttons
            frm.add_custom_button(__('View Service Case Group'), function() {
                frappe.set_route('Form', 'Lavanya Service Case Group', frm.doc.service_case_group);
            }, __('View'));
        }

        // Show chargeable warning
        if (frm.doc.chargeable && !frm.doc.customer_payable_amount && frm.doc.status !== 'Draft') {
            frm.dashboard.add_comment(__('Warning: Chargeable spare requires Customer Payable Amount'), 'red', true);
        }

        // Show quantity warning
        if (frm.doc.issued_quantity && frm.doc.used_quantity && frm.doc.returned_quantity) {
            const total = frm.doc.used_quantity + frm.doc.returned_quantity;
            if (total > frm.doc.issued_quantity) {
                frm.dashboard.add_comment(__('Warning: Used + Returned exceeds Issued quantity'), 'red', true);
            }
        }
    },

    chargeable(frm) {
        // Show/hide chargeable amount based on chargeable flag
        if (frm.doc.chargeable) {
            frm.set_df_property('customer_payable_amount', 'reqd', 1);
        } else {
            frm.set_df_property('customer_payable_amount', 'reqd', 0);
        }
    },

    validate(frm) {
        // Validate chargeable requires amount
        if (frm.doc.chargeable && frm.doc.status === 'Closed' && !frm.doc.customer_payable_amount) {
            frappe.msgprint(__('Customer Payable Amount is required for chargeable spares'));
            frappe.validated = false;
        }

        // Validate quantity rules
        if (frm.doc.used_quantity && frm.doc.returned_quantity && frm.doc.issued_quantity) {
            if (frm.doc.used_quantity + frm.doc.returned_quantity > frm.doc.issued_quantity) {
                frappe.msgprint(__('Used + Returned cannot exceed Issued quantity'));
                frappe.validated = false;
            }
        }
    }
});
