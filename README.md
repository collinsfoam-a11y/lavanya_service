# Lavanya Service — Frappe App

A complete Frappe v14/v15 custom app for Lavanya eMart's service desk operations.

---

## Quick Install

```bash
# On your Frappe bench
cd /path/to/frappe-bench
bench get-app lavanya_service /path/to/this/folder
bench --site your.site install-app lavanya_service
bench --site your.site migrate
bench build --app lavanya_service
bench restart
```

---

## App Structure

```
lavanya_service/
├── hooks.py                    # App config, scheduler, doc_events
├── install.py                  # Post-install: roles + default settings
├── modules.txt                 # Module declaration
├── config/
│   └── desktop.py              # Frappe desk navigation items
├── page/                       # 8 Frappe desk pages (Vue-mounted)
│   ├── lavanya_today/          # Today's Work command center
│   ├── lavanya_tickets/        # Ticket list
│   ├── lavanya_ticket_detail/  # Full ticket workspace
│   ├── lavanya_new_ticket/     # 4-step new ticket wizard
│   ├── lavanya_customer360/    # Customer profile + history
│   ├── lavanya_manager/        # Manager dashboard (role-gated)
│   ├── lavanya_whatsapp/       # WhatsApp inbox (dry-run)
│   └── lavanya_service_centers/# Brand + SC + technician master
├── doctype/
│   ├── lavanya_ticket/         # Core ticket DocType (40+ fields)
│   ├── lavanya_customer/       # Customer master
│   ├── lavanya_followup_log/   # Immutable audit trail per action
│   ├── lavanya_customer_product/ # Warranty + product profile
│   ├── lavanya_brand_master/   # Brand config + auto-reg settings
│   ├── lavanya_service_center/ # Service center master + SLA
│   ├── lavanya_technician/     # Technician directory
│   ├── lavanya_whatsapp_message/ # Incoming WA messages
│   └── lavanya_settings/       # Single doctype — safety locks + rules
├── api/
│   ├── tickets.py              # get_list, get_ticket, create_ticket,
│   │                           # save_followup, close_ticket, escalate
│   ├── today.py                # get_todays_work, get_sidebar_counts
│   ├── dashboard.py            # get_manager_dashboard, export_report
│   └── whatsapp.py             # get_inbox, generate_draft, log_reply
├── events/
│   ├── ticket.py               # on_submit → SLA, on_update → quality badge
│   └── followup.py             # validate_customer_informed enforcement
├── tasks/
│   ├── daily.py                # Flag overdue, compute quality badges
│   └── hourly.py               # SLA breach check, auto-escalation
├── utils/
│   └── quality.py              # compute_badge(), get_next_action()
└── permissions/
    └── ticket.py               # Role-based permission override
```

---

## DocTypes

| DocType | Key Fields | Notes |
|---------|-----------|-------|
| **Lavanya Ticket** | subject, customer, status, service_path, quality_badge, next_action, escalation_level | Core entity. 40+ fields. Auto-computes quality badge + next action on every save. |
| **Lavanya Customer** | customer_name, customer_phone, whatsapp_optin, customer_type | Phone-unique. Auto-links to CRM Contact. |
| **Lavanya Followup Log** | ticket, action_type, customer_informed, channel, staff | Append-only audit trail. customer_informed is mandatory for Service Center Follow-up entries. |
| **Lavanya Customer Product** | customer, brand, model, serial_number, warranty_end_date | Warranty history per customer. |
| **Lavanya Brand Master** | brand_name, toll_free, auto_email_enabled, sla_days | Brand config + auto-registration toggle. |
| **Lavanya Service Center** | brand, area_coverage, phone, sla_days | Service center per brand. |
| **Lavanya Technician** | name, phone, skill_categories, area_coverage, rating | Technician directory. |
| **Lavanya Whatsapp Message** | phone, direction, bot_intent, matched_ticket, reviewed | Every WA message logged. Never auto-acts. |
| **Lavanya Settings** | closure_guard_enabled, live_whatsapp_enabled, whatsapp_bot_mode | Single doctype — manager/owner only write. |

---

## API Methods (all whitelisted)

```python
# Tickets
lavanya_service.api.tickets.get_list(filters, page, page_size, search, status)
lavanya_service.api.tickets.get_ticket(name)
lavanya_service.api.tickets.create_ticket(data)
lavanya_service.api.tickets.save_followup(ticket, action_type, detail, customer_informed, ...)
lavanya_service.api.tickets.close_ticket(ticket, closure_type, remarks, customer_satisfaction, ...)
lavanya_service.api.tickets.escalate_ticket(ticket, reason)
lavanya_service.api.tickets.search_customer(phone)

# Today's Work
lavanya_service.api.today.get_todays_work()
lavanya_service.api.today.get_sidebar_counts()

# Manager Dashboard
lavanya_service.api.dashboard.get_manager_dashboard(period)
lavanya_service.api.dashboard.export_report()

# WhatsApp (dry-run enforced)
lavanya_service.api.whatsapp.get_inbox()
lavanya_service.api.whatsapp.generate_draft(ticket_id, template_key)
lavanya_service.api.whatsapp.mark_reviewed(msg_id)
lavanya_service.api.whatsapp.log_customer_reply(phone, message_text)
```

---

## Frappe Pages → Vue Mapping

| Route | Frappe Page | Vue Component |
|-------|-------------|---------------|
| /lavanya-today | lavanya_today | TodaysWork.vue |
| /lavanya-tickets | lavanya_tickets | Tickets.vue |
| /lavanya-ticket-detail?name=XXX | lavanya_ticket_detail | TicketDetail.vue |
| /lavanya-new-ticket | lavanya_new_ticket | NewTicket.vue |
| /lavanya-customer360 | lavanya_customer360 | Customer360.vue |
| /lavanya-manager | lavanya_manager | ManagerDashboard.vue |
| /lavanya-whatsapp | lavanya_whatsapp | WhatsAppInbox.vue |
| /lavanya-service-centers | lavanya_service_centers | ServiceCenters.vue |

All pages call `LavanyaService.mountPage('ComponentName', domEl, props)`
from the compiled `lavanya_bundle.bundle.js` (build with `bench build --app lavanya_service`).

---

## Scheduled Jobs

| Frequency | Task |
|-----------|------|
| Hourly | Check SLA breaches, auto-escalate overdue tickets |
| Daily at 8 AM | Flag overdue follow-ups, recompute quality badges, send manager digest |

---

## Safety Rules (hardcoded defaults)

| Setting | Default |
|---------|---------|
| Closure Guard | **ENABLED** |
| Customer Confirmation Required | **ENABLED** |
| Live WhatsApp Sending | **DISABLED** |
| ERP Auto-posting | **DISABLED** |
| Penalty Application | **DISABLED** |
| WhatsApp Bot Mode | **dry_run** |
| Automatic Ticket Closure | **DISABLED** |

These are set by `install.py` on first install and enforced in `LavanyaSettings.validate()`.
Only Lavanya Owner role can change them.

---

## Roles

| Role | Permissions |
|------|------------|
| Front Desk | Create + read tickets, search customers |
| Service Staff | Full ticket CRUD, follow-up logs, WhatsApp drafts |
| Service Manager | All above + escalate, delete, manager dashboard, export |
| CRM Manager | CRM opportunity creation and management |
| Lavanya Owner | Full access including safety settings |

---

## Vue Frontend Integration

The `vue-src/` folder (separate download) contains all Vue 3 components.
To wire them into this Frappe app:

1. Copy `vue-src/` into `lavanya_service/public/js/`
2. Add a `package.json` with Vite + @vitejs/plugin-vue
3. In `vite.config.js`:
   ```js
   export default {
     build: {
       lib: { entry: 'main.js', name: 'LavanyaService', fileName: 'lavanya_bundle' },
       rollupOptions: { external: ['frappe'] }
     }
   }
   ```
4. `npm run build` → outputs `lavanya_bundle.bundle.js`
5. In `hooks.py` `app_include_js` → `/assets/lavanya_service/js/lavanya_bundle.bundle.js`
6. `bench build --app lavanya_service && bench restart`
