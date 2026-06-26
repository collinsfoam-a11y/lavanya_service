// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Replacement Recovery', {
    refresh(frm) {
        // Show status indicator
        const status_colors = {
            'Draft': 'orange',
            'Replacement Approved': 'blue',
            'Replacement Given to Customer': 'yellow',
            'Old Item Received': 'yellow',
            'Supplier Claim Pending': 'blue',
            'Claim Registered': 'purple',
            'Pickup Pending': 'yellow',
            'Sent to Supplier': 'blue',
            'Replacement Expected': 'green',
            'Credit Note Expected': 'green',
            'Repair Expected': 'green',
            'Returned Repaired': 'green',
            'Replacement Received': 'green',
            'Converted to Saleable': 'green',
            'Written Off': 'red',
            'Closed': 'green',
            'Cancelled': 'red'
        };
        if (frm.doc.status) {
            frm.page.set_indicator(frm.doc.status, status_colors[frm.doc.status] || 'gray');
        }

        // Calculate financial difference
        if (frm.doc.old_item_value && frm.doc.replacement_item_value) {
            const diff = frm.doc.replacement_item_value - frm.doc.old_item_value;
            frm.set_value('financial_difference', diff);
        }

        // Add action buttons based on status
        if (!frm.is_new()) {
            if (frm.doc.status === 'Draft') {
                frm.add_custom_button(__('Approve Replacement'), function() {
                    frm.set_value('status', 'Replacement Approved');
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Replacement Approved') {
                frm.add_custom_button(__('Mark Given to Customer'), function() {
                    frm.set_value('status', 'Replacement Given to Customer');
                    frm.set_value('replacement_date', frappe.datetime.get_today());
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Replacement Given to Customer') {
                frm.add_custom_button(__('Mark Old Item Received'), function() {
                    frm.set_value('status', 'Old Item Received');
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Old Item Received') {
                frm.add_custom_button(__('Create Supplier Claim'), function() {
                    frappe.new_doc('Lavanya Supplier Claim', {
                        customer: frm.doc.customer,
                        service_case_group: frm.doc.service_case_group,
                        replacement_recovery: frm.doc.name
                    });
                }, __('Create'));
            }

            frm.add_custom_button(__('View Service Case Group'), function() {
                frappe.set_route('Form', 'Lavanya Service Case Group', frm.doc.service_case_group);
            }, __('View'));
        }
    },

    replacement_type(frm) {
        // Show/hide financial fields based on replacement type
        if (frm.doc.replacement_type in ['Cross SKU', 'Upgrade', 'Downgrade']) {
            frm.set_df_property('old_item_value', 'reqd', 1);
            frm.set_df_property('replacement_item_value', 'reqd', 1);
        } else {
            frm.set_df_property('old_item_value', 'reqd', 0);
            frm.set_df_property('replacement_item_value', 'reqd', 0);
        }

        if (frm.doc.replacement_type === 'Credit Instead') {
            frm.set_df_property('credit_note', 'reqd', 1);
        } else {
            frm.set_df_property('credit_note', 'reqd', 0);
        }
    },

    old_item_value(frm) {
        // Calculate financial difference
        if (frm.doc.replacement_item_value) {
            frm.set_value('financial_difference', frm.doc.replacement_item_value - frm.doc.old_item_value);
        }
    },

    replacement_item_value(frm) {
        // Calculate financial difference
        if (frm.doc.old_item_value) {
            frm.set_value('financial_difference', frm.doc.replacement_item_value - frm.doc.old_item_value);
        }
    },

    validate(frm) {
        // Validate Cross SKU/Upgrade/Downgrade requires values
        if (frm.doc.replacement_type in ['Cross SKU', 'Upgrade', 'Downgrade']) {
            if (!frm.doc.old_item_value) {
                frappe.msgprint(__('Old Item Value is required'));
                frappe.validated = false;
            }
            if (!frm.doc.replacement_item_value) {
                frappe.msgprint(__('Replacement Item Value is required'));
                frappe.validated = false;
            }
        }

        // Validate Credit Instead requires credit note
        if (frm.doc.replacement_type === 'Credit Instead' && !frm.doc.credit_note) {
            frappe.msgprint(__('Credit Note is required for Credit Instead'));
            frappe.validated = false;
        }
    }
});
