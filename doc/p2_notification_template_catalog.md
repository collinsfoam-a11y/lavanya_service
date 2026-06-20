# P2.2 Notification Template Catalog

## Channels
- WhatsApp
- SMS
- Email
- Internal

## Languages
- English
- Malayalam
- Mixed

## Supported Variables
- `customer_name`
- `ticket_id`
- `product_type`
- `brand`
- `brand_ticket_number`
- `service_center`
- `next_follow_up_date`
- `last_followup_summary`
- `customer_informed_status`
- `part_name`
- `part_expected_date`
- `closure_type`
- `store_name`
- `store_phone`

## Seeded English Templates
- Ticket created: WhatsApp customer acknowledgement.
- Brand complaint registered: WhatsApp brand reference update.
- Technician call pending: SMS status update.
- Technician visit scheduled: WhatsApp appointment update.
- Service center follow-up update: WhatsApp follow-up summary.
- Customer not informed reminder: Internal staff alert.
- Part pending update: WhatsApp part status update.
- Product ready for pickup: SMS pickup update.
- Customer satisfaction request: WhatsApp satisfaction prompt for staff follow-up only.
- Ticket closed: WhatsApp closure update.
- Replacement update: WhatsApp replacement status update.
- Return/refund update: WhatsApp return/refund status update.
- Stock complaint update: Internal supplier/stock alert.
- Demo/installation appointment: WhatsApp appointment update.
- Payment block / supplier internal alert: Internal supplier control alert.

## Approval Defaults
- WhatsApp and SMS templates require approval by default.
- Internal templates do not require customer-message approval by default.
- Approval changes queue status only; it does not send messages while live notifications remain disabled.

## Operational Notes
- Staff/agents may preview and queue dry-run messages.
- Only System Manager, Lavanya Manager, or Lavanya Service Coordinator can approve/cancel/skip queue records.
- Missing phone creates an auditable `Skipped` queue row.
- Missing template variables return a safe preview error and queue as `Skipped` if queued.
