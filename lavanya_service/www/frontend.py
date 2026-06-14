import frappe


def get_context(context):
	"""Serve the Lavanya Service Console SPA shell.

	The page (frontend.html) is the Vite-built index.html, regenerated on every
	build with fresh hashed asset names. Disable caching so /frontend always
	reflects the latest build without a manual `bench clear-cache`.
	"""
	context.no_cache = 1
	frappe.flags.no_cache = 1
	return context
