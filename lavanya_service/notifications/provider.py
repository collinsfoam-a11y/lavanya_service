"""Delivery provider abstraction for P2.2 notifications.

Live WhatsApp/SMS delivery is intentionally disabled in P2.2. Providers expose a
stable interface for later integration without storing credentials in code.
"""

import frappe


def live_notifications_enabled():
	return str(frappe.conf.get("LIVE_NOTIFICATIONS_ENABLED") or "").lower() == "true"


class DryRunProvider:
	def __init__(self, channel):
		self.channel = channel

	def send(self, queue_doc):
		if not live_notifications_enabled():
			raise frappe.ValidationError("Live notifications are disabled; dry-run queue only.")
		return {"ok": False, "channel": self.channel, "message": "No live provider configured."}


def get_provider(channel):
	return DryRunProvider(channel)
