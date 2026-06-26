from . import __version__ as app_version

app_name      = "lavanya_service"
app_title     = "Lavanya Service"
app_publisher = "Lavanya eMart"
app_description = "Service Platform — Complaint management, brand warranty follow-up, WhatsApp"
app_email     = "tech@lavanyaemart.com"
app_license   = "MIT"
app_version   = app_version

# ── Desk includes (loaded on every desk page) ─────────────────────────────────
# After `bench build --app lavanya_service`, Frappe copies
# public/dist/js/ → /assets/lavanya_service/js/
# public/dist/css/ is similarly available
app_include_css = ["/assets/lavanya_service/js/lavanya.css"]
app_include_js  = ["/assets/lavanya_service/js/lavanya_bundle.js"]

# Google Font loaded via CSS @import in lavanya.css — no extra link needed

# ── Fixtures ──────────────────────────────────────────────────────────────────
fixtures = [
    {"dt": "Role", "filters": [["name", "in", [
        "Service Staff", "Service Manager", "Front Desk", "CRM Manager", "Lavanya Owner"
    ]]]},
]

# ── Scheduler ─────────────────────────────────────────────────────────────────
scheduler_events = {
    "daily": [
        "lavanya_service.tasks.daily.run_daily_tasks",
    ],
    "hourly": [
        "lavanya_service.tasks.hourly.check_sla_breaches",
        "lavanya_service.tasks.hourly.auto_escalate_overdue",
    ],
    "cron": {
        "0 8 * * *": [
            "lavanya_service.tasks.daily.send_morning_digest",
        ],
    },
}

# ── Website routes (WhatsApp webhook) ────────────────────────────────────────
website_route_rules = [
    {"from_route": "/api/lavanya/whatsapp-webhook", "to_route": "lavanya_service.api.whatsapp.webhook_receiver"},
]

# ── Doc events ────────────────────────────────────────────────────────────────
# NOTE: Lavanya Ticket is NOT submittable (is_submittable=0).
# Use after_insert (not on_submit) for post-creation logic.
doc_events = {
    "Lavanya Ticket": {
        "after_insert": "lavanya_service.events.ticket.after_insert",
        "on_update":    "lavanya_service.events.ticket.on_update",
    },
    "Lavanya Followup Log": {
        "before_save": "lavanya_service.events.followup.validate_customer_informed",
    },
}

# ── DB Indexes (applied on migrate) ─────────────────────────────────────────
# Defined in patches.txt — see below for the patch file

# ── Permissions ───────────────────────────────────────────────────────────────
has_permission = {
    "Lavanya Ticket": "lavanya_service.permissions.ticket.has_permission",
}

# ── Post-install ──────────────────────────────────────────────────────────────
after_install = "lavanya_service.install.after_install"
