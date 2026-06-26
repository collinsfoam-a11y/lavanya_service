// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Showroom Handover Token', {
    refresh(frm) {
        // Show status indicator
        if (frm.doc.status === 'Draft') {
            frm.page.set_indicator('Draft', 'orange');
        } else if (frm.doc.status === 'OTP Sent') {
            frm.page.set_indicator('OTP Sent', 'blue');
        } else if (frm.doc.status === 'Verified') {
            frm.page.set_indicator('Verified', 'green');
        } else if (frm.doc.status === 'Completed') {
            frm.page.set_indicator('Completed', 'green');
        } else if (frm.doc.status === 'Cancelled') {
            frm.page.set_indicator('Cancelled', 'red');
        }

        // Add action buttons based on status
        if (!frm.is_new()) {
            if (frm.doc.status === 'Draft') {
                frm.add_custom_button(__('Send OTP'), function() {
                    frappe.call({
                        method: 'send_otp',
                        doc: frm.doc,
                        callback: function(r) {
                            if (r.message) {
                                frappe.msgprint(__('OTP sent: ' + r.message));
                                frm.reload_doc();
                            }
                        }
                    });
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'OTP Sent') {
                frm.add_custom_button(__('Verify OTP'), function() {
                    frappe.prompt({
                        label: 'Enter OTP',
                        fieldname: 'otp',
                        fieldtype: 'Data',
                        reqd: 1
                    }, function(values) {
                        frappe.call({
                            method: 'verify_otp',
                            doc: frm.doc,
                            args: { entered_otp: values.otp },
                            callback: function(r) {
                                if (r.message) {
                                    frappe.msgprint(__('OTP verified successfully'));
                                    frm.reload_doc();
                                }
                            }
                        });
                    }, __('Verify OTP'), __('Verify'));
                }).addClass('btn-primary');
            }

            if (frm.doc.status === 'Verified') {
                frm.add_custom_button(__('Complete Handover'), function() {
                    frappe.confirm(
                        __('Are you sure you want to complete the handover?'),
                        function() {
                            frappe.call({
                                method: 'complete_handover',
                                doc: frm.doc,
                                callback: function(r) {
                                    frappe.msgprint(__('Handover completed successfully'));
                                    frm.reload_doc();
                                }
                            });
                        }
                    );
                }).addClass('btn-success');
            }

            frm.add_custom_button(__('View Service Case Group'), function() {
                frappe.set_route('Form', 'Lavanya Service Case Group', frm.doc.service_case_group);
            }, __('View'));
        }
    },

    validate(frm) {
        // Validate mobile number
        if (frm.doc.handover_to_mobile) {
            const mobile = frm.doc.handover_to_mobile.replace(/\s/g, '').replace(/-/g, '');
            if (mobile.length !== 10 || !/^\d+$/.test(mobile)) {
                frappe.msgprint(__('Handover To Mobile must be 10 digits'));
                frappe.validated = false;
            }
        }

        // Validate accessories
        if (!frm.doc.accessories_handed_over || frm.doc.accessories_handed_over.length === 0) {
            frappe.msgprint(__('At least one accessory must be listed'));
            frappe.validated = false;
        }
    }
});
