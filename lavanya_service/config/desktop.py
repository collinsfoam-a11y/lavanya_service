from frappe import _

def get_data():
    return [
        {
            "module_name": "Lavanya Service",
            "color": "#0D9488",
            "icon": "storefront",
            "type": "module",
            "label": _("Lavanya Service"),
            "items": [
                {
                    "type": "page",
                    "name": "lavanya-today",
                    "label": _("Today's Work"),
                    "icon": "bolt",
                    "description": _("Daily action queue — overdue, escalated, waiting"),
                },
                {
                    "type": "page",
                    "name": "lavanya-tickets",
                    "label": _("Tickets"),
                    "icon": "confirmation_number",
                    "description": _("All service complaints"),
                },
                {
                    "type": "page",
                    "name": "lavanya-new-ticket",
                    "label": _("New Ticket"),
                    "icon": "add_circle",
                    "description": _("Register a new customer complaint"),
                },
                {
                    "type": "page",
                    "name": "lavanya-customer360",
                    "label": _("Customer 360"),
                    "icon": "person_search",
                    "description": _("Full customer profile and ticket history"),
                },
                {
                    "type": "page",
                    "name": "lavanya-manager",
                    "label": _("Manager Dashboard"),
                    "icon": "monitoring",
                    "description": _("KPIs, escalations, brand scorecards"),
                    "onboard": 0,
                },
                {
                    "type": "page",
                    "name": "lavanya-whatsapp",
                    "label": _("WhatsApp Inbox"),
                    "icon": "chat",
                    "description": _("Bucketed WhatsApp messages — dry-run mode"),
                },
                {
                    "type": "page",
                    "name": "lavanya-service-centers",
                    "label": _("Service Centers"),
                    "icon": "business",
                    "description": _("Brand, service center and technician master"),
                },
            ],
        }
    ]
