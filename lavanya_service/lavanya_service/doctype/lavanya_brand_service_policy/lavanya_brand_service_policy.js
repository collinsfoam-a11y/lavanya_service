// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Brand Service Policy', {
    refresh(frm) {
        // Show brand info
        if (frm.doc.brand) {
            frm.add_custom_button(__('View Brand'), function() {
                frappe.set_route('Form', 'Supplier', frm.doc.brand);
            }, __('View'));
        }

        // Show policy summary
        if (!frm.is_new()) {
            frm.dashboard.add_comment(
                __('DOA: {0} days | Warranty: {1} months | SLA: {2} days', [
                    frm.doc.doa_period_days,
                    frm.doc.warranty_period_months,
                    frm.doc.average_sla_days || 'N/A'
                ]),
                'blue',
                true
            );
        }
    }
});
