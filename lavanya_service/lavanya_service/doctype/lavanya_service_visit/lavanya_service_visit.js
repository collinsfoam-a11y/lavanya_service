// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Service Visit', {
    refresh(frm) {
        // Show status indicator
        const status_colors = {
            'Scheduled': 'blue',
            'In Progress': 'orange',
            'Visit Completed': 'green',
            'Failed Visit': 'red',
            'Cancelled': 'red'
        };
        if (frm.doc.status) {
            frm.page.set_indicator(frm.doc.status, status_colors[frm.doc.status] || 'gray');
        }

        // Add action buttons based on status
        if (!frm.is_new()) {
            if (frm.doc.status === 'Scheduled') {
                frm.add_custom_button(__('Start Visit'), function() {
                    frm.set_value('status', 'In Progress');
                    frm.set_value('check_in_time', frappe.datetime.now_datetime());
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'In Progress') {
                frm.add_custom_button(__('Complete Visit'), function() {
                    frm.set_value('status', 'Visit Completed');
                    frm.set_value('check_out_time', frappe.datetime.now_datetime());
                    frm.set_value('visit_result', 'Successful');
                    frm.save();
                }).addClass('btn-primary');

                frm.add_custom_button(__('Mark Failed'), function() {
                    frm.set_value('status', 'Failed Visit');
                    frm.set_value('check_out_time', frappe.datetime.now_datetime());
                    frm.save();
                }).addClass('btn-danger');
            }

            if (frm.doc.status === 'Failed Visit') {
                frm.add_custom_button(__('Reschedule'), function() {
                    frm.set_value('status', 'Scheduled');
                    frm.save();
                }).addClass('btn-primary');
            }

            // Add view buttons
            frm.add_custom_button(__('View Service Case Group'), function() {
                frappe.set_route('Form', 'Lavanya Service Case Group', frm.doc.service_case_group);
            }, __('View'));

            if (frm.doc.installation_job) {
                frm.add_custom_button(__('View Installation Job'), function() {
                    frappe.set_route('Form', 'Lavanya Installation Job', frm.doc.installation_job);
                }, __('View'));
            }
        }

        // Show warning for failed visit without next action
        if (frm.doc.status === 'Failed Visit' && !frm.doc.next_action) {
            frm.dashboard.add_comment(__('Warning: Failed visit requires next action'), 'red', true);
        }
    },

    status(frm) {
        // Show/hide fields based on status
        if (frm.doc.status === 'Failed Visit') {
            frm.set_df_property('failed_reason', 'reqd', 1);
            frm.set_df_property('next_action', 'reqd', 1);
            frm.set_df_property('next_follow_up_date', 'reqd', 1);
        } else {
            frm.set_df_property('failed_reason', 'reqd', 0);
            frm.set_df_property('next_action', 'reqd', 0);
            frm.set_df_property('next_follow_up_date', 'reqd', 0);
        }

        if (frm.doc.status === 'Visit Completed') {
            frm.set_df_property('work_done', 'reqd', 1);
            frm.set_df_property('before_photo', 'reqd', 1);
            frm.set_df_property('after_photo', 'reqd', 1);
            frm.set_df_property('customer_signature', 'reqd', 1);
        } else {
            frm.set_df_property('work_done', 'reqd', 0);
            frm.set_df_property('before_photo', 'reqd', 0);
            frm.set_df_property('after_photo', 'reqd', 0);
            frm.set_df_property('customer_signature', 'reqd', 0);
        }
    },

    validate(frm) {
        // Validate rating
        if (frm.doc.customer_rating && (frm.doc.customer_rating < 1 || frm.doc.customer_rating > 5)) {
            frappe.msgprint(__('Customer Rating must be between 1 and 5'));
            frappe.validated = false;
        }

        // Validate failed visit requirements
        if (frm.doc.status === 'Failed Visit') {
            if (!frm.doc.failed_reason) {
                frappe.msgprint(__('Failed Reason is required'));
                frappe.validated = false;
            }
            if (!frm.doc.next_action) {
                frappe.msgprint(__('Next Action is required'));
                frappe.validated = false;
            }
            if (!frm.doc.next_follow_up_date) {
                frappe.msgprint(__('Next Follow-up Date is required'));
                frappe.validated = false;
            }
        }

        // Validate completion requirements
        if (frm.doc.status === 'Visit Completed') {
            if (!frm.doc.work_done) {
                frappe.msgprint(__('Work Done is required'));
                frappe.validated = false;
            }
            if (!frm.doc.before_photo || !frm.doc.after_photo) {
                frappe.msgprint(__('Before and After photos are required'));
                frappe.validated = false;
            }
            if (!frm.doc.customer_signature) {
                frappe.msgprint(__('Customer Signature is required'));
                frappe.validated = false;
            }
        }
    }
});
