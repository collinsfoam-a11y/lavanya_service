// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Stock Condition Decision', {
    refresh(frm) {
        // Show status indicator
        const status_colors = {
            'Pending': 'orange',
            'Approved': 'blue',
            'Rejected': 'red',
            'Implemented': 'green',
            'Cancelled': 'red'
        };
        if (frm.doc.status) {
            frm.page.set_indicator(frm.doc.status, status_colors[frm.doc.status] || 'gray');
        }

        // Add action buttons based on status
        if (!frm.is_new()) {
            if (frm.doc.status === 'Pending') {
                frm.add_custom_button(__('Approve'), function() {
                    frm.set_value('status', 'Approved');
                    frm.set_value('approved_by', frappe.session.user);
                    frm.set_value('approval_date', frappe.datetime.get_today());
                    frm.save();
                }).addClass('btn-primary');

                frm.add_custom_button(__('Reject'), function() {
                    frm.set_value('status', 'Rejected');
                    frm.save();
                }).addClass('btn-danger');
            }

            if (frm.doc.status === 'Approved') {
                frm.add_custom_button(__('Implement'), function() {
                    frm.set_value('status', 'Implemented');
                    frm.save();
                }).addClass('btn-primary');
            }

            // Add action buttons based on decision type
            if (frm.doc.decision_type === 'Write Off' || frm.doc.decision_type === 'Scrap') {
                frm.set_df_property('approval_required', 'read_only', 1);
                frm.set_df_property('approval_required', 'default', 1);
            }

            // Show/hide target warehouse based on decision type
            if (frm.doc.decision_type in ['Return to Saleable Stock', 'Move to Refurbished Stock', 'Move to Display Stock', 'Discount Sale']) {
                frm.set_df_property('target_warehouse', 'reqd', 1);
            } else {
                frm.set_df_property('target_warehouse', 'reqd', 0);
            }
        }
    },

    decision_type(frm) {
        // Show/hide target warehouse based on decision type
        if (frm.doc.decision_type in ['Return to Saleable Stock', 'Move to Refurbished Stock', 'Move to Display Stock', 'Discount Sale']) {
            frm.set_df_property('target_warehouse', 'reqd', 1);
        } else {
            frm.set_df_property('target_warehouse', 'reqd', 0);
        }

        // Auto-set approval required for Write Off/Scrap
        if (frm.doc.decision_type in ['Write Off', 'Scrap']) {
            frm.set_value('approval_required', 1);
        }
    },

    validate(frm) {
        // Validate approval for Write Off/Scrap
        if (frm.doc.decision_type in ['Write Off', 'Scrap'] && !frm.doc.approved_by) {
            frappe.msgprint(__('Approval Required for Write Off or Scrap decisions'));
            frappe.validated = false;
        }

        // Validate target warehouse for applicable decision types
        if (frm.doc.decision_type in ['Return to Saleable Stock', 'Move to Refurbished Stock', 'Move to Display Stock', 'Discount Sale']) {
            if (!frm.doc.target_warehouse) {
                frappe.msgprint(__('Target Warehouse is required'));
                frappe.validated = false;
            }
        }
    }
});
