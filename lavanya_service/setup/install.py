"""Unified, idempotent install/migrate setup for lavanya_service (Phase 1S).

Fresh-site installs previously relied on record fixtures for the app's
``custom=1`` master DocTypes (Brand Service Master, etc.). During fixture
import the master records were processed before the just-created custom
DocType was fully visible, so controller resolution fell back to
``frappe.core.doctype.<dt>`` and raised
``No module named 'frappe.core.doctype.brand_service_master'`` — leaving the
masters empty and breaking QR intake (0 brands).

This module wires the existing idempotent seeders into ``after_install`` and
``after_migrate`` so master/config data is created by code AFTER all DocTypes
exist and are committed. Every step is idempotent: re-running changes nothing
harmful. No users, HD Agents, tickets, customer profiles, product receipts, or
outbound side effects are created here.
"""

import frappe


def _steps():
	"""Ordered (label, callable) setup steps.

	Scope is deliberately narrow: seed only what record fixtures cannot reliably
	provide on a fresh install — the app's ``custom=1`` DocTypes and their master
	data — plus the previously-wired permission/SLA fixes. Statuses, priorities,
	ticket types, custom fields, roles, the ticket template, form scripts and HD
	Views are provided by the (working) metadata fixtures and are intentionally
	NOT re-run here: some of those seeders are not idempotent against Helpdesk's
	protected built-in statuses. Imports are local so a broken module can be
	pinpointed during testing.
	"""
	from lavanya_service.setup.masters import create_supporting_masters
	from lavanya_service.setup.service_receipt import create_service_receipt_doctypes_and_link
	from lavanya_service.setup.customer_profile import ensure_lavanya_customer_profile
	from lavanya_service.setup.permission_fixes import restrict_hd_ticket_all_permission
	from lavanya_service.setup.sla_fixes import ensure_helpdesk_sla_defaults

	from lavanya_service.setup.helpdesk_config import configure_statuses_priorities_types
	from lavanya_service.setup.sla_config import configure_lavanya_default_sla
	from lavanya_service.setup.intake_masters import configure_intake_masters
	from lavanya_service.setup.ticket_template import configure_default_ticket_template_fields
	from lavanya_service.setup.runtime_defaults import configure_runtime_defaults

	return [
		# 1. Base DocTypes and Masters
		("supporting_masters", create_supporting_masters),
		("service_receipt_doctypes", create_service_receipt_doctypes_and_link),
		("customer_profile_doctype", ensure_lavanya_customer_profile),
		
		# 2. Helpdesk configurations (Statuses, Priorities, Types)
		("helpdesk_statuses_priorities_types", configure_statuses_priorities_types),
		
		# 3. Product Categories, Items, and related fields/scripts
		("intake_masters", configure_intake_masters),
		
		# 4. Ticket Template
		("ticket_template", configure_default_ticket_template_fields),
		
		# 5. SLA
		("lavanya_default_sla", configure_lavanya_default_sla),
		
		# 6. Runtime Defaults (Depends on SLA)
		("runtime_defaults", configure_runtime_defaults),

		# 7. Preserved permission/SLA fixes
		("restrict_hd_ticket_all", restrict_hd_ticket_all_permission),
		("helpdesk_sla_defaults", ensure_helpdesk_sla_defaults),
	]


def ensure_lavanya_service_setup():
	"""Idempotently ensure all lavanya_service DocTypes, config and master data.

	Safe to run on install and on every migrate. Returns a per-step summary.
	"""
	results = {}
	for label, fn in _steps():
		results[label] = fn()

	frappe.clear_cache()
	frappe.db.commit()
	return results


def after_install():
	return ensure_lavanya_service_setup()


def after_migrate():
	return ensure_lavanya_service_setup()
