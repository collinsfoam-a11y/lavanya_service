// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Supplier Claim', {
    refresh(frm) {
        // Show status indicator
        const status_colors = {
            'Draft': 'orange',
            'Claim Registered': 'blue',
            'Document Pending': 'yellow',
            'Pickup Pending': 'yellow',
            'Sent to Supplier': 'blue',
            'Under Review': 'purple',
            'Replacement Expected': 'green',
            'Credit Note Expected': 'green',
            'Repair Expected': 'green',
            'Rejected': 'red',
            'Settled': 'green',
            'Cancelled': 'red'
        };
        if (frm.doc.status) {
            frm.page.set_indicator(frm.doc.status, status_colors[frm.doc.status] || 'gray');
        }

        // Add action buttons based on status
        if (!frm.is_new()) {
            if (frm.doc.status === 'Draft') {
                frm.add_custom_button(__('Register Claim'), function() {
                    frappe.prompt({
                        label: 'Claim Reference No',
                        fieldname: 'claim_reference_no',
                        fieldtype: 'Data',
                        reqd: 1
                    }, function(values) {
                        frm.set_value('claim_reference_no', values.claim_reference_no);
                        frm.set_value('status', 'Claim Registered');
                        frm.save();
                    }, __('Register Claim'), __('Register'));
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Claim Registered') {
                frm.add_custom_button(__('Send to Supplier'), function() {
                    frm.set_value('status', 'Sent to Supplier');
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Sent to Supplier') {
                frm.add_custom_button(__('Mark Under Review'), function() {
                    frm.set_value('status', 'Under Review');
                    frm.save();
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Under Review') {
                frm.add_custom_button(__('Mark Settled'), function() {
                    frappe.prompt({
                        label: 'Settlement Type',
                        fieldname: 'settlement_type',
                        fieldtype: 'Select',
                        options: 'Credit Note\nReplacement\nRepair\nReturn\nWrite Off\nOther',
                        reqd: 1
                    }, function(values) {
                        frm.set_value('settlement_type', values.settlement_type);
                        frm.set_value('status', 'Settled');
                        frm.set_value('supplier_closure_date', frappe.datetime.get_today());
                        frm.save();
                    }, __('Settlement Type'), __('Settle'));
                }).addClass('btn-success');
            }

            frm.add_custom_button(__('Log Follow-up'), function() {
                frappe.call({
                    method: 'update_follow_up',
                    doc: frm.doc,
                    callback: function() {
                        frm.reload_doc();
                    }
                });
            });

            frm.add_custom_button(__('View Service Case Group'), function() {
                frappe.set_route('Form', 'Lavanya Service Case Group', frm.doc.service_case_group);
            }, __('View'));
        }
    },

    settlement_type(frm) {
        // Toggle required fields based on settlement type
        if (frm.doc.settlement_type === 'Credit Note') {
            frm.set_df_property('expected_credit_note_amount', 'reqd', 1);
            frm.set_df_property('expected_replacement_item', 'reqd', 0);
        } else if (frm.doc.settlement_type === 'Replacement') {
            frm.set_df_property('expected_replacement_item', 'reqd', 1);
            frm.set_df_property('expected_credit_note_amount', 'reqd', 0);
        } else {
            frm.set_df_property('expected_credit_note_amount', 'reqd', 0);
            frm.set_df_property('expected_replacement_item', 'reqd', 0);
        }
    },

    validate(frm) {
        // Validate claim reference or manager override
        if (frm.doc.status === 'Claim Registered') {
            if (!frm.doc.claim_reference_no && !frm.doc.manager_override_reason) {
                frappe.msgprint(__('Claim Reference No or Manager Override Reason is required'));
                frappe.validated = false;
            }
        }

        // Validate settlement fields
        if (frm.doc.settlement_type === 'Credit Note' && !frm.doc.expected_credit_note_amount) {
            frappe.msgprint(__('Expected Credit Note Amount is required'));
            frappe.validated = false;
        }

        if (frm.doc.settlement_type === 'Replacement' && !frm.doc.expected_replacement_item) {
            frappe.msgprint(__('Expected Replacement Item is required'));
            frappe.validated = false;
        }
    }
});
