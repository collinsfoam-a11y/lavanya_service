// Copyright (c) 2026, Lavanya Service
// For license information, please see license.txt

frappe.ui.form.on('Lavanya Product Service Policy', {
    refresh(frm) {
        // Show workflow summary
        if (!frm.is_new()) {
            const items = [];
            if (frm.doc.serial_required) items.push('Serial Required');
            if (frm.doc.installation_required) items.push('Installation Required');
            if (frm.doc.demo_required) items.push('Demo Required');
            if (frm.doc.showroom_intake_allowed) items.push('Showroom Intake OK');
            if (frm.doc.can_repair_locally) items.push('Local Repair OK');
            
            frm.dashboard.add_comment(
                __('Workflow: {0} | Warranty: {1} months | DOA: {2} days', [
                    items.join(', ') || 'Standard',
                    frm.doc.default_warranty_months,
                    frm.doc.doa_period_days
                ]),
                'blue',
                true
            );
        }
    }
});
