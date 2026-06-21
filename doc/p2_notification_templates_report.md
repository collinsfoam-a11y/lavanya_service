# P2.2 Notification Templates Report

## Scope
- Implemented notification template and dry-run queue infrastructure for Lavanya Service.
- Prepared WhatsApp, SMS, Email, and Internal channels without enabling live delivery.
- No live WhatsApp/SMS sending, ERPNext integration, customer portal, CSAT automation, supplier ledger change, or accounting posting was added.

## Backend
- Added `Lavanya Notification Template` DocType.
- Added `Lavanya Notification Queue` DocType.
- Added setup hook wiring for install/migrate.
- Added default seed catalog for all 15 requested notification events.
- Added safe rendering with `{{ variable }}` substitution and explicit missing-variable reporting.
- Added phone normalization before queueing customer-channel messages.
- Added skipped queue records for missing/invalid customer phone.
- Added dry-run queue creation with audit fields, status, approval metadata, provider response, and error reason.
- Added provider abstraction in `lavanya_service.notifications.provider`.

## Safety
- `LIVE_NOTIFICATIONS_ENABLED` defaults to false.
- Provider send raises when live notifications are disabled.
- `queue_notification` never calls live provider send.
- All queued messages are stored with `dry_run = 1`.
- WhatsApp/SMS records use normalized Indian mobile numbers.
- Missing variables and missing phones fail safely without sending.
- No provider credential or token is stored in source code.

## Frontend
- Added `Communication Preview` section in `TicketDetail.vue`.
- Staff can select templates, preview rendered messages, and queue dry-run notifications.
- Added template selection modal using `LavModal`.
- Queue confirmation uses `LavConfirm`/`useConfirm`; no native confirm.
- Added `Notifications` tab in Reports with counts and action table.
- Managers/coordinators can approve/cancel records from Reports.

## Verification
- P2.2 focused tests: 10 pass, 0 fail (after hardening test cleanup).
- P2.1 regression tests: 18 pass, 0 fail.
- Frontend production build passed.
- `bench migrate` completed cleanly.
- Static safety checks: no live provider credentials, no ERP/accounting references, no native `window.confirm()`.
- Screenshots captured under `doc/screenshots/p2_notifications/`.

## Screenshots
- `01-ticket-detail-communication-preview.png`
- `02-template-selection-modal.png`
- `03-whatsapp-preview.png`
- `04-sms-preview.png`
- `05-notification-queue-list.png`
- `06-approval-modal.png`
- `07-reports-notifications-tab.png`
- `08-dark-mode-notifications.png`
