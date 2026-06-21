# H6D Pilot Regression Report

## Scope

H6D is the final regression and merge-gate phase before merging `feature/phase-2-frappe-ui-scaffold` into `main`. It confirms the full H3B→H6C stack is pilot-stable. No new features are added.

---

## Branch State

```text
Branch: feature/phase-2-frappe-ui-scaffold
HEAD: 49c65f1 feat: add H6C read-only customer 360 view
Worktree: clean
```

---

## Commit Stack (20 commits)

| # | Commit | Phase | Description |
|---|---|---|---|
| 1 | `5c00fa9` | H3B | Component modernization + mobile mode |
| 2 | `e66eb63` | H4 | UI/UX polish + regression evidence |
| 3 | `bb35e0c` | H5 | Workspace scaffold cleanup |
| 4 | `6f54d2e` | H5A | Theme tokens → CSS vars, handler fix, Field Mode fixes |
| 5 | `efcf28c` | H5A | Complete TicketDetail theme token migration |
| 6 | `3172f71` | H5A | Gitignore deferred files |
| 7 | `f066728` | H5B | Operational masters wired into intake + detail |
| 8 | `394f320` | H5C | Technician appointments + receiving UI |
| 9 | `87ec6dd` | H5D | Restore deferred service record modules |
| 10 | `37f91a4` | H5E | Linked record UI wiring |
| 11 | `e35fc31` | H5F | Pilot readiness docs + regression gate |
| 12 | `dfae14c` | Merge | H5A-H5F merge |
| 13 | `1ef79b4` | H6A | Read-only WhatsApp inbox + draft foundation |
| 14 | `769e8bc` | H6A | Server-side guard blocking Sent (External) |
| 15 | `27ff7a5` | Merge | H6A merge |
| 16 | `e99af1c` | H6B | Read-only CRM relationship card |
| 17 | `49c65f1` | H6C | Read-only Customer 360 view |

---

## Static Safety Scan (H6D)

| Check | Result | Detail |
|---|---|---|
| `COLORS.*` in Vue components | 0 | All migrated to CSS custom properties |
| Native `confirm()` | 0 | 9 Vue uses are `useConfirm()` composable |
| Native `alert()` | 0 | No usage |
| Native `prompt()` | 0 | No usage |
| Live WhatsApp API calls | 0 | No Twilio/360dialog/Facebook API references |
| CRM write calls | 0 | 0 insert/save/create on CRM DocTypes |
| ERP posting paths | 0 | `erp_posting_disabled` locked |
| Penalty application paths | 0 | `penalty_apply_disabled` locked |
| Automatic closure paths | 0 | Customer confirmation + satisfaction enforced |

---

## SPA Inventory

### Pages (9)

| Route | Page | Status |
|---|---|---|
| `/` | TodayWork.vue | Complete |
| `/tickets` | Tickets.vue | Complete |
| `/new-ticket` | NewTicket.vue | Complete |
| `/reports` | Reports.vue | Complete |
| `/settings` | Settings.vue | Complete |
| `/field` | FieldMode.vue | Complete |
| `/whatsapp` | WhatsAppInbox.vue | Complete |
| `/customer-360` | Customer360.vue | Complete |
| `/*` | NotFound.vue | Complete |

### Components (18)

LavCard, LavSectionHeader, LavBadge, LavChip, LavStatCard, LavActionBar, LavEmptyState, LavLoadingState, LavSafetyLockPanel, LavThemeToggle, LavWorkflowTimeline, LavCustomerJourneyCard, LavFollowupQualityBadge, LavTicketCard, LavConfirm, LavModal, SlaBadge, AppShell

### TicketDetail sections (19)

Stage, Reminder, AI Advisory, Communication, Follow-up Tracking, Customer, Product, Customer Products, Brand Info, CRM, Workflow, Product Custody, Service Records, Technician, Appointment, Proof, Follow-ups, Activity, Quick Actions

---

## Backend Inventory

### API modules (14)
`stitch_console`, `today_work`, `quick_actions`, `operational_masters`, `whatsapp_inbox`, `customer_360`, `manager_reports`, `qr_intake`, `customer_intake`, `ai_advisory`, `stage_rules`, `reminder_engine`, `notifications`, `prep`

### Setup modules (24)
`masters`, `install`, `operational_masters`, `crm_settings`, `whatsapp_inbox`, `service_receipt`, `customer_profile`, `hd_ticket_fields`, `followup_fields`, `service_stages`, `field_permissions`, `quick_actions_form_script`, `new_ticket_fields`, `comm_log`, `demo_record`, `replacement_record`, `return_record`, `stock_record`, `store_record`, `area_perf_log`, `supplier_sla`, `supplier_payment_block`, `supplier_perf_log`, + more

### Scheduler tasks (2)
`tasks/payment_block.py` (advisory, Pending Review), `tasks/performance_log.py` (read-only logs)

---

## Theme System

| Theme | Tokens | Spacing |
|---|---|---|
| lavanya-light | Default | scale 1.0 |
| lavanya-dark | Dark-adapted | scale 1.0 |
| lavanya-blue | Blue-tinted | scale 1.0 |
| lavanya-green | Green-tinted | scale 1.0 |
| high-contrast | WCAG AAA | scale 1.05 |
| compact-counter | Light tokens | scale 0.75 |

---

## Known Gaps

| Gap | Severity | Notes |
|---|---|---|
| TW-015 group-order mismatch | Low | Known pre-existing; documented |
| Appointment Confirm/Miss/Visited backend handlers | Medium | UI visible, backend partial |
| File upload for proofs | Low | Proof categories are reference-only |
| SPA build requires Windows host `node_modules` | Medium | Build command documented |
| Ticket Detail section density (19 sections) | Low | Functional; future accordion optional |
| No offline/PWA support | Low | Not a pilot requirement |

---

## Merge Instructions

```bash
git checkout main
git pull origin main
git merge --no-ff feature/phase-2-frappe-ui-scaffold -m "merge: H3B-H6C full pilot stack"
git push origin main
```

---

## Prepared: 2026-06-21
