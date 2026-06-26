// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Installation Job', {
    refresh(frm) {
        // Show status indicator
        const status_colors = {
            'Draft': 'orange',
            'Pending Assignment': 'yellow',
            'Assigned': 'blue',
            'Customer Contacted': 'blue',
            'Visit Scheduled': 'green',
            'Visit Completed': 'green',
            'Failed Visit': 'red',
            'Customer Confirmed': 'green',
            'Closed': 'green',
            'Cancelled': 'red'
        };
        if (frm.doc.status) {
            frm.page.set_indicator(frm.doc.status, status_colors[frm.doc.status] || 'gray');
        }

        // Add action buttons based on status
        if (!frm.is_new()) {
            if (frm.doc.status === 'Draft') {
                frm.add_custom_button(__('Assign Technician'), function() {
                    frm.set_value('status', 'Pending Assignment');
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Pending Assignment' && frm.doc.technician) {
                frm.add_custom_button(__('Mark Assigned'), function() {
                    frm.set_value('status', 'Assigned');
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Assigned') {
                frm.add_custom_button(__('Contact Customer'), function() {
                    frm.set_value('status', 'Customer Contacted');
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Customer Contacted') {
                frm.add_custom_button(__('Schedule Visit'), function() {
                    frm.set_value('status', 'Visit Scheduled');
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Visit Scheduled') {
                frm.add_custom_button(__('Mark Visit Completed'), function() {
                    frm.set_value('status', 'Visit Completed');
                    frm.set_value('completion_date', frappe.datetime.get_today());
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Visit Completed') {
                frm.add_custom_button(__('Confirm with Customer'), function() {
                    frm.set_value('status', 'Customer Confirmed');
                    frm.set_value('customer_confirmation', 1);
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Customer Confirmed') {
                frm.add_custom_button(__('Close Job'), function() {
                    frm.set_value('status', 'Closed');
                    frm.save();
                }).addClass('btn-primary');
            }

            // Add view buttons
            frm.add_custom_button(__('View Service Case Group'), function() {
                frappe.set_route('Form', 'Lavanya Service Case Group', frm.doc.service_case_group);
            }, __('View'));
        }

        // Show payment warning for paid installations
        if (frm.doc.installation_type === 'Paid' && !frm.doc.payment_received && frm.doc.status !== 'Draft') {
            frm.dashboard.add_comment(__('Warning: Payment not yet received'), 'red', true);
        }
    },

    installation_type(frm) {
        // Show/hide payment fields based on installation type
        if (frm.doc.installation_type === 'Paid') {
            frm.set_df_property('payment_amount', 'reqd', 1);
        } else {
            frm.set_df_property('payment_amount', 'reqd', 0);
        }
    },

    validate(frm) {
        // Validate paid installation requires payment on close
        if (frm.doc.installation_type === 'Paid' && frm.doc.status === 'Closed') {
            if (!frm.doc.payment_amount) {
                frappe.msgprint(__('Payment Amount is required for paid installations'));
                frappe.validated = false;
            }
            if (!frm.doc.payment_received) {
                frappe.msgprint(__('Payment Received confirmation is required'));
                frappe.validated = false;
            }
        }
    }
});
