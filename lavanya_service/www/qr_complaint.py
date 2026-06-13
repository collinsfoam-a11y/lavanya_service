"""Frappe www controller for /qr-complaint public page.

This module enables the route /qr-complaint to load without authentication.
The HTML template (qr_complaint.html) is served by Frappe's www resolver.
"""

import frappe

no_cache = 1


def get_context(context):
    """Allow guest access and set page meta."""
    context.no_cache = 1
    context.title = "Lavanya eMart - Complaint Registration"
    # no login required
    context.update({"no_header": True, "no_sidebar": True})
