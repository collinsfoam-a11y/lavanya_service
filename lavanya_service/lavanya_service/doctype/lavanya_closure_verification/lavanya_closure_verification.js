// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Closure Verification', {
    refresh(frm) {
        // Show status indicator
        if (frm.doc.status === 'Pending') {
            frm.page.set_indicator('Pending', 'orange');
        } else if (frm.doc.status === 'Verified') {
            frm.page.set_indicator('Verified', 'green');
        } else if (frm.doc.status === 'Rejected') {
            frm.page.set_indicator('Rejected', 'red');
        } else if (frm.doc.status === 'Reopen Required') {
            frm.page.set_indicator('Reopen Required', 'blue');
        } else if (frm.doc.status === 'Closed') {
            frm.page.set_indicator('Closed', 'green');
        }

        // Add action buttons based on status
        if (!frm.is_new()) {
            if (frm.doc.status === 'Pending') {
                frm.add_custom_button(__('Verify'), function() {
                    // Check all required fields
                    const required = [
                        'customer_satisfied', 'stock_accounted', 'supplier_claim_handled',
                        'accounting_closed', 'warranty_documented', 'all_photos_uploaded',
                        'all_documents_attached'
                    ];
                    const missing = required.filter(f => !frm.doc[f]);
                    
                    if (missing.length > 0) {
                        frappe.msgprint(__('Missing checklist items: ') + missing.join(', '));
                        return;
                    }
                    
                    frm.set_value('status', 'Verified');
                    frm.save();
                }).addClass('btn-success');
            }

            if (frm.doc.status === 'Verified') {
                frm.add_custom_button(__('Close'), function() {
                    frappe.confirm(
                        __('Are you sure you want to close this verification?'),
                        function() {
                            frm.set_value('status', 'Closed');
                            frm.save();
                        }
                    );
                }).addClass('btn-primary');
            }

            frm.add_custom_button(__('View Service Case Group'), function() {
                frappe.set_route('Form', 'Lavanya Service Case Group', frm.doc.service_case_group);
            }, __('View'));

            if (frm.doc.ticket) {
                frm.add_custom_button(__('View Ticket'), function() {
                    frappe.set_route('Form', 'Lavanya Service Ticket Extension', frm.doc.ticket);
                }, __('View'));
            }
        }
    },

    customer_satisfied(frm) {
        // Auto-update status based on checklist
        update_status_from_checklist(frm);
    },

    stock_accounted(frm) {
        update_status_from_checklist(frm);
    },

    supplier_claim_handled(frm) {
        update_status_from_checklist(frm);
    },

    accounting_closed(frm) {
        update_status_from_checklist(frm);
    },

    warranty_documented(frm) {
        update_status_from_checklist(frm);
    },

    all_photos_uploaded(frm) {
        update_status_from_checklist(frm);
    },

    all_documents_attached(frm) {
        update_status_from_checklist(frm);
    }
});

function update_status_from_checklist(frm) {
    // Check if all required fields are checked
    const required = [
        'customer_satisfied', 'stock_accounted', 'supplier_claim_handled',
        'accounting_closed', 'warranty_documented', 'all_photos_uploaded',
        'all_documents_attached'
    ];
    const all_checked = required.every(f => frm.doc[f]);
    
    if (all_checked && frm.doc.status === 'Pending') {
        frm.page.set_indicator('Ready to Verify', 'green');
    }
}
