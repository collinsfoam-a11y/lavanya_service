"""
Patch: Add DB indexes on hot query columns of Lavanya Ticket and Lavanya Followup Log.
Run automatically on bench migrate.

Indexed columns (chosen from the most frequent WHERE / ORDER BY clauses):
  tabLavanya Ticket:
    - next_followup_date  (daily SLA check, Today's Work filter)
    - followup_overdue    (dashboard, Today's Work, reports)
    - quality_badge       (dashboard, reports)
    - sla_breached        (hourly SLA task)
    - escalation_level    (manager dashboard, escalation aging)
    - status              (almost every query)
    - customer            (Customer 360 ticket history)
    - brand               (brand scorecard, reports)

  tabLavanya Followup Log:
    - ticket              (every ticket detail page load)
    - staff + creation    (staff performance report)
"""
import frappe


def execute():
    indexes = [
        # table,                        column(s),                          index_name
        ("tabLavanya Ticket", "next_followup_date",   "idx_lav_tkt_nfd"),
        ("tabLavanya Ticket", "followup_overdue",     "idx_lav_tkt_fo"),
        ("tabLavanya Ticket", "quality_badge",        "idx_lav_tkt_qb"),
        ("tabLavanya Ticket", "sla_breached",         "idx_lav_tkt_sla"),
        ("tabLavanya Ticket", "escalation_level",     "idx_lav_tkt_esc"),
        ("tabLavanya Ticket", "status",               "idx_lav_tkt_status"),
        ("tabLavanya Ticket", "customer",             "idx_lav_tkt_cust"),
        ("tabLavanya Ticket", "brand",                "idx_lav_tkt_brand"),
        ("tabLavanya Followup Log", "ticket",         "idx_lav_fup_ticket"),
        ("tabLavanya Followup Log", "staff",          "idx_lav_fup_staff"),
    ]

    for table, column, idx_name in indexes:
        # Skip if index already exists
        existing = frappe.db.sql("""
            SELECT INDEX_NAME FROM information_schema.STATISTICS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME   = %s
              AND INDEX_NAME   = %s
        """, (table, idx_name))
        if existing:
            continue
        try:
            frappe.db.sql(f"ALTER TABLE `{table}` ADD INDEX `{idx_name}` (`{column}`)")
            frappe.logger().info(f"[Lavanya] Created index {idx_name} on {table}.{column}")
        except Exception as e:
            frappe.logger().warning(f"[Lavanya] Could not create index {idx_name}: {e}")
