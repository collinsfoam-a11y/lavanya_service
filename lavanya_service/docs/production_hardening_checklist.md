# Lavanya Service — Production Hardening Checklist (Phase 1R)

Last verified against: frappe 15.110.0, helpdesk 1.25.1, lavanya_service @ `61e2cd2` (+ this commit).
Dev site: `lavanya-dev.localhost`. Reference report: `final_phase1_readiness_report.md`.

This is a **Go/No-Go gate**, not a launch script. Every box must be ticked (or its
limitation documented) before production go-live.

---

## 1. Environment
- [ ] Docker host sized for prod (CPU/RAM/disk headroom; separate from dev).
- [ ] Frappe `version-15` branch pinned; helpdesk `1.25.x` pinned; lavanya_service pinned to a released tag/commit.
- [ ] `bench --version`, app versions recorded in the deployment runbook.
- [ ] Separate prod bench (do NOT reuse the dev bench/site).

## 2. Domain / SSL
- [ ] Production domain points at the prod host.
- [ ] HTTPS/TLS terminated (Traefik/nginx-proxy/Caddy) with auto-renew (see `frappe_docker/overrides/`).
- [ ] `site_config.json` `host_name` set to the https URL.
- [ ] QR public URL (`https://<domain>/qr-complaint`) reachable over HTTPS only.

## 3. Bench / App Versions & Required Apps
- [ ] `required_apps = ["helpdesk"]` satisfied (helpdesk installed before lavanya_service).
- [ ] `telephony` installed if used (dev parity).
- [ ] No edits to `apps/helpdesk` (verify `git status --short` clean).

## 4. Scheduler / Worker Health
- [ ] `bench doctor` reports workers online and Redis reachable.
- [ ] `bench --site <site> scheduler status` = Enabled (prod requires scheduler ON).
- [ ] Only the approved daily job runs: `lavanya_service.reminders.notification_output.run_daily_reminder_notifications_dry_safe`.
- [ ] No email/SMS/WhatsApp side effects from the scheduler (dry-safe by design).

## 5. Database Backup Policy
- [ ] `bench --site <site> backup --with-files` scheduled (cron / `frappe_docker` `compose.backup-cron.yaml`).
- [ ] Off-host backup target (restic/S3) configured and tested.
- [ ] Retention policy defined (e.g. hourly→6h, daily→14d).

## 6. File Backup Policy
- [ ] `public/` and `private/files` included in backups (`--with-files`).
- [ ] Off-host copy verified.

## 7. Restore Procedure
- [ ] Documented restore steps (new-site + `bench restore <db> --with-private-files <pf> --with-public-files <pubf>`).
- [ ] Restore drill executed against a scratch site at least once before go-live.

## 8. User / Role Setup
- [ ] Real staff users created (NOT exported as fixtures).
- [ ] Roles assigned: Lavanya Manager / Service Coordinator / Helpdesk Agent / Front Desk / Viewer.
- [ ] `All` DocPerm on HD Ticket stays restricted (read+print) — self-healed by `setup.permission_fixes`.

## 9. HD Agent Setup
- [ ] Operator users have HD Agent records (helpdesk requirement).

## 10. Email / WhatsApp / SMS Status
- [ ] Outbound automation = OFF by design this phase. Email Queue / Notification Log must stay empty from custom code.
- [ ] If transactional email is later enabled, re-run the negative side-effect checks.

## 11. QR Public URL Checklist
- [ ] `/qr-complaint` loads without login.
- [ ] Brand + Product Type dropdowns populate from `get_qr_intake_options` (no free text).
- [ ] Valid submit creates an internal HD Ticket (`complaint_source = Customer QR Form`).
- [ ] Invalid brand/product_type rejected with a friendly message (no traceback).
- [ ] Honeypot submission creates no ticket.
- [ ] Rate limits active (mobile 3/hr, IP 10/hr) behind the real proxy IP.
- [ ] Response exposes only `{ok, message, reference}` (no internal ticket name).

## 12. Security Checklist
- [ ] `allow_guest=True` only on `submit_qr_complaint` and `get_qr_intake_options`.
- [ ] Protected-field guard (`validations.hd_ticket`) blocks Front Desk / Viewer; never bypassable by Guest.
- [ ] Quick actions preserve the real `modified_by` (no Administrator impersonation).
- [ ] CSRF/headers per `frappe_docker` nginx security headers.

## 13. Fixture Checklist
- [ ] Only metadata/config fixtures present (DocTypes, Custom Field[HD Ticket], statuses, types, priorities, SLA, views, roles, docperms, brand masters, print format, form scripts, settings, template).
- [ ] NO forbidden fixtures: user, has_role, user_permission, role_profile, hd_agent, hd_ticket, service_product_receipt, lavanya_customer_profile, lavanya_product_category, lavanya_product_item, communication, email_queue, notification_log, todo, comment, hd_ticket_template_field.
- [ ] `custom_field.json` scoped to HD Ticket only.

## 14. Regression Checklist
- [ ] Full suite green (see `production_readiness.py` + the 17 suites).
- [ ] No persistent test garbage beyond approved baseline.

## 15. Fresh-Site Install Checklist
- [ ] new-site → install telephony → helpdesk → lavanya_service succeeds.
- [ ] `ticket_template_integrity`, `pilot_readiness`, `qr_intake` pass on the fresh site.

## 16. Existing-Site Migrate Checklist
- [ ] `bench migrate` run twice is idempotent (no duplicate template fields / roles / perms).
- [ ] `after_migrate` (permission_fixes + sla_fixes) leaves exactly one restricted `All` row and one default SLA.

## 17. Rollback Plan
- [ ] Tag the prod commit before deploy.
- [ ] Roll back app: `git checkout <prev_tag>` in `apps/lavanya_service` + `bench migrate`.
- [ ] If migrate introduced data changes, restore from the pre-deploy backup (Section 7).
- [ ] `apps/helpdesk` is never modified, so no helpdesk rollback is required.

## 18. Go / No-Go Decision
- [ ] All gates above ticked or limitation explicitly accepted by owner.
- [ ] Restore drill complete (or accepted as a pre-go-live condition).
- [ ] Owner sign-off recorded with date + commit.
