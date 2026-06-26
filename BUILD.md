# Lavanya Service — Build & Deploy

## Prerequisites
- Frappe bench v14 or v15
- Node.js 18+
- Python 3.10+

---

## 1. Install the Frappe app

```bash
cd /path/to/frappe-bench
bench get-app lavanya_service /path/to/frappe-app/
bench --site your.site install-app lavanya_service
bench --site your.site migrate
```

---

## 2. Build the Vue bundle

The Vue frontend lives in `lavanya_service/public/js/`.
Vite compiles it to `lavanya_service/public/dist/js/lavanya_bundle.js`.
Frappe's asset pipeline then serves it at `/assets/lavanya_service/js/lavanya_bundle.js`.

```bash
cd lavanya_service/public/js
npm install
npm run build
```

You should see:
```
dist/js/lavanya_bundle.js   ~450 KB (gzipped ~130 KB)
dist/js/lavanya.css         ~60 KB
```

---

## 3. Register assets with Frappe

```bash
bench build --app lavanya_service
bench restart
```

---

## 4. Verify in browser

1. Log into Frappe desk
2. Open the module: **Lavanya Service**
3. Click **Today's Work** — it should load the Vue page
4. Check browser console — no errors means wiring is correct

---

## Development mode (hot reload)

Run Vite dev server alongside bench:

```bash
# Terminal 1
bench start

# Terminal 2
cd lavanya_service/public/js
npm run dev
```

In dev mode, Vite serves at http://localhost:5173 — you can proxy from bench
by pointing `app_include_js` to the Vite dev server URL temporarily.

---

## Environment checklist after install

| Check | Expected |
|-------|----------|
| Lavanya Settings exists | Yes (created by install.py) |
| Closure Guard | ENABLED |
| Live WhatsApp | DISABLED |
| ERP Posting | DISABLED |
| WhatsApp Bot Mode | dry_run |
| Roles created | Service Staff, Front Desk, Service Manager, CRM Manager, Lavanya Owner |

---

## Page routing

Frappe page names → Vue components:

| Page name | Component |
|-----------|-----------|
| lavanya-today | TodaysWork |
| lavanya-tickets | Tickets |
| lavanya-ticket-detail?name=XXX | TicketDetail |
| lavanya-new-ticket | NewTicket |
| lavanya-customer360 | Customer360 |
| lavanya-manager | ManagerDashboard |
| lavanya-whatsapp | WhatsAppInbox |
| lavanya-service-centers | ServiceCenters |
| lavanya-reports | Reports |
| lavanya-settings | Settings |

---

## Whitelisted API methods

All callable from the frontend via `frappe.call()`:

```
lavanya_service.api.tickets.get_list
lavanya_service.api.tickets.get_ticket
lavanya_service.api.tickets.create_ticket
lavanya_service.api.tickets.save_followup
lavanya_service.api.tickets.close_ticket
lavanya_service.api.tickets.escalate_ticket
lavanya_service.api.tickets.search_customer
lavanya_service.api.today.get_todays_work
lavanya_service.api.today.get_sidebar_counts
lavanya_service.api.dashboard.get_manager_dashboard
lavanya_service.api.dashboard.export_report
lavanya_service.api.whatsapp.get_inbox
lavanya_service.api.whatsapp.generate_draft
lavanya_service.api.whatsapp.mark_reviewed
lavanya_service.api.whatsapp.log_customer_reply
lavanya_service.api.reports.get_report_data
lavanya_service.api.settings.get_settings
lavanya_service.api.settings.save_settings
lavanya_service.api.settings.reset_defaults
```
