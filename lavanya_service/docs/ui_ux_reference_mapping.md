# UI UX Reference Mapping

## UI Upgrade Plan with Reference Images

This document maps the visual design references from the `stitch_guided_service_workflow` package to the actual Lavanya Helpdesk workflow.

### Reference Image: today_s_work_dashboard/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/today_s_work_dashboard/screen.png`
- **Intended Lavanya use**: Existing lavanya_today_work page
- **Similar current feature**: Today's Work page
- **Reusable design pattern**: Use for card layout, counts, colors, click-to-filter groups
- **Should implement now**: P0 (Safe now, low risk)
- **Should defer**: No
- **Risk**: Low

### Reference Image: new_ticket_form/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/new_ticket_form/screen.png`
- **Intended Lavanya use**: HD Ticket creation
- **Similar current feature**: Standard Helpdesk Ticket Form
- **Reusable design pattern**: Use for phone-first intake layout
- **Should implement now**: P0 (Safe now, low risk)
- **Should defer**: No
- **Risk**: Low

### Reference Image: ticket_detail_view/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/ticket_detail_view/screen.png`
- **Intended Lavanya use**: HD Ticket detail screen
- **Similar current feature**: Standard Helpdesk Ticket Form
- **Reusable design pattern**: Use for customer/product summary and quick action panel
- **Should implement now**: P1 (After pilot feedback)
- **Should defer**: Yes (until after pilot feedback)
- **Risk**: Medium

### Reference Image: register_brand_complaint_modal/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/register_brand_complaint_modal/screen.png`
- **Intended Lavanya use**: Existing Register Brand Complaint quick action
- **Similar current feature**: Backend quick action API
- **Reusable design pattern**: Use modal layout only
- **Should implement now**: P0 (Safe now, low risk)
- **Should defer**: No
- **Risk**: Low

### Reference Image: need_invoice_modal/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/need_invoice_modal/screen.png`
- **Intended Lavanya use**: Existing Need Invoice quick action
- **Similar current feature**: Backend quick action API
- **Reusable design pattern**: Use modal layout only
- **Should implement now**: P0 (Safe now, low risk)
- **Should defer**: No
- **Risk**: Low

### Reference Image: service_center_follow_up_modal/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/service_center_follow_up_modal/screen.png`
- **Intended Lavanya use**: Existing Follow Up Service Center quick action
- **Similar current feature**: Backend quick action API
- **Reusable design pattern**: Use modal layout only
- **Should implement now**: P0 (Safe now, low risk)
- **Should defer**: No
- **Risk**: Low

### Reference Image: create_product_receipt/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/create_product_receipt/screen.png`
- **Intended Lavanya use**: Existing Service Product Receipt workflow
- **Similar current feature**: Service Product Receipt custom doctype
- **Reusable design pattern**: Use receipt layout/token flow
- **Should implement now**: P0 (Safe now, low risk)
- **Should defer**: No
- **Risk**: Low

### Reference Image: ticket_detail_receipt_pending/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/ticket_detail_receipt_pending/screen.png`
- **Intended Lavanya use**: Product-at-store pending state
- **Similar current feature**: Status-aware ticket view
- **Reusable design pattern**: Use status-aware ticket view reference
- **Should implement now**: P0 (Safe now, low risk)
- **Should defer**: No
- **Risk**: Low

### Reference Image: ticket_detail_ready_for_pickup/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/ticket_detail_ready_for_pickup/screen.png`
- **Intended Lavanya use**: Ready for Pickup status
- **Similar current feature**: Ticket form banner
- **Reusable design pattern**: Use pickup banner/action style
- **Should implement now**: P0 (Safe now, low risk)
- **Should defer**: No
- **Risk**: Low

### Reference Image: close_ticket_modal/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/close_ticket_modal/screen.png`
- **Intended Lavanya use**: Existing Close Ticket quick action
- **Similar current feature**: Backend quick action API
- **Reusable design pattern**: Use closure modal layout
- **Should implement now**: P0 (Safe now, low risk)
- **Should defer**: No
- **Risk**: Low

### Reference Image: manager_s_performance_dashboard/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/manager_s_performance_dashboard/screen.png`
- **Intended Lavanya use**: Manager dashboard/reports
- **Similar current feature**: Number cards/Dashboards
- **Reusable design pattern**: Use dashboard card style
- **Should implement now**: P1 (After pilot feedback)
- **Should defer**: Yes
- **Risk**: Medium

### Reference Image: coordinator_overview_dashboard/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/coordinator_overview_dashboard/screen.png`
- **Intended Lavanya use**: Service Coordinator home
- **Similar current feature**: Dashboards
- **Reusable design pattern**: Use dashboard concept after pilot
- **Should implement now**: P1 (After pilot feedback)
- **Should defer**: Yes
- **Risk**: Medium

### Reference Image: triage_assignment_workspace/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/triage_assignment_workspace/screen.png`
- **Intended Lavanya use**: Deferred Phase 2
- **Similar current feature**: N/A
- **Reusable design pattern**: Do not implement before pilot
- **Should implement now**: P2 (Defer)
- **Should defer**: Yes
- **Risk**: High

### Reference Image: parts_procurement_tracker/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/parts_procurement_tracker/screen.png`
- **Intended Lavanya use**: Deferred Phase 2
- **Similar current feature**: N/A
- **Reusable design pattern**: Do not implement before pilot
- **Should implement now**: P2 (Defer)
- **Should defer**: Yes
- **Risk**: High

### Reference Image: team_capacity_skill_map/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/team_capacity_skill_map/screen.png`
- **Intended Lavanya use**: Deferred Phase 2
- **Similar current feature**: N/A
- **Reusable design pattern**: Do not implement before pilot
- **Should implement now**: P2 (Defer)
- **Should defer**: Yes
- **Risk**: High

### Reference Image: brand_complaints_dashboard/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/brand_complaints_dashboard/screen.png`
- **Intended Lavanya use**: Manager/Coordinator report upgrade
- **Similar current feature**: Standard reports
- **Reusable design pattern**: Defer unless reports need redesign
- **Should implement now**: P2 (Defer)
- **Should defer**: Yes
- **Risk**: Medium

### Reference Image: brand_complaint_detailed_view/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/brand_complaint_detailed_view/screen.png`
- **Intended Lavanya use**: Brand pending workflow
- **Similar current feature**: Ticket detail view
- **Reusable design pattern**: Defer to Phase 2
- **Should implement now**: P2 (Defer)
- **Should defer**: Yes
- **Risk**: High

### Reference Image: field_service_parts_report/screen.png
- **File**: `ui_references/stitch_guided_service_workflow/field_service_parts_report/screen.png`
- **Intended Lavanya use**: Advanced report
- **Similar current feature**: N/A
- **Reusable design pattern**: Defer to Phase 2
- **Should implement now**: P2 (Defer)
- **Should defer**: Yes
- **Risk**: Low
