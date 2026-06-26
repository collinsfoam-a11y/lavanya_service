// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Stock Complaint', {
    refresh(frm) {
        // Show status indicator
        const status_colors = {
            'Draft': 'orange',
            'Identified': 'blue',
            'Quarantined': 'yellow',
            'Supplier Informed': 'blue',
            'Claim Registered': 'purple',
            'Pickup Pending': 'yellow',
            'Sent to Supplier': 'blue',
            'Repair Pending': 'yellow',
            'Replacement Pending': 'green',
            'Credit Note Pending': 'green',
            'Returned Repaired': 'green',
            'Saleable': 'green',
            'Written Off': 'red',
            'Closed': 'green',
            'Cancelled': 'red'
        };
        if (frm.doc.status) {
            frm.page.set_indicator(frm.doc.status, status_colors[frm.doc.status] || 'gray');
        }

        // Show/hide transport fields based on damage type
        if (frm.doc.damage_type === 'Transit Damage') {
            frm.set_df_property('lr_section', 'hidden', 0);
        } else {
            frm.set_df_property('lr_section', 'hidden', 1);
        }

        // Show/hide missing accessory details
        if (frm.doc.damage_type === 'Missing Accessory') {
            frm.set_df_property('missing_accessory_details', 'hidden', 0);
        } else {
            frm.set_df_property('missing_accessory_details', 'hidden', 1);
        }

        // Add action buttons based on status
        if (!frm.is_new()) {
            if (frm.doc.status === 'Draft') {
                frm.add_custom_button(__('Mark Identified'), function() {
                    frm.set_value('status', 'Identified');
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Identified') {
                frm.add_custom_button(__('Quarantine'), function() {
                    frappe.prompt({
                        label: 'Quarantine Warehouse',
                        fieldname: 'quarantine_warehouse',
                        fieldtype: 'Link',
                        options: 'Warehouse',
                        reqd: 1
                    }, function(values) {
                        frm.set_value('quarantine_warehouse', values.quarantine_warehouse);
                        frm.set_value('status', 'Quarantined');
                        frm.save();
                    }, __('Quarantine Stock'), __('Quarantine'));
                }).addClass('btn-warning');
            }

            if (frm.doc.status === 'Quarantined') {
                frm.add_custom_button(__('Create Supplier Claim'), function() {
                    frappe.new_doc('Lavanya Supplier Claim', {
                        customer: frm.doc.customer,
                        service_case_group: frm.doc.service_case_group,
                        stock_complaint: frm.doc.name
                    });
                }, __('Create'));
            }

            frm.add_custom_button(__('View Service Case Group'), function() {
                frappe.set_route('Form', 'Lavanya Service Case Group', frm.doc.service_case_group);
            }, __('View'));
        }
    },

    damage_type(frm) {
        // Show/hide transport fields based on damage type
        if (frm.doc.damage_type === 'Transit Damage') {
            frm.set_df_property('lr_section', 'hidden', 0);
            frm.set_df_property('lr_number', 'reqd', 1);
            frm.set_df_property('transporter_name', 'reqd', 1);
        } else {
            frm.set_df_property('lr_section', 'hidden', 1);
            frm.set_df_property('lr_number', 'reqd', 0);
            frm.set_df_property('transporter_name', 'reqd', 0);
        }

        // Show/hide missing accessory details
        if (frm.doc.damage_type === 'Missing Accessory') {
            frm.set_df_property('missing_accessory_details', 'hidden', 0);
            frm.set_df_property('missing_accessory_details', 'reqd', 1);
        } else {
            frm.set_df_property('missing_accessory_details', 'hidden', 1);
            frm.set_df_property('missing_accessory_details', 'reqd', 0);
        }
    },

    validate(frm) {
        // Validate transit damage fields
        if (frm.doc.damage_type === 'Transit Damage') {
            if (!frm.doc.lr_number) {
                frappe.msgprint(__('LR Number is required for Transit Damage'));
                frappe.validated = false;
            }
            if (!frm.doc.transporter_name) {
                frappe.msgprint(__('Transporter Name is required for Transit Damage'));
                frappe.validated = false;
            }
        }

        // Validate missing accessory details
        if (frm.doc.damage_type === 'Missing Accessory' && !frm.doc.missing_accessory_details) {
            frappe.msgprint(__('Missing Accessory Details are required'));
            frappe.validated = false;
        }
    }
});
