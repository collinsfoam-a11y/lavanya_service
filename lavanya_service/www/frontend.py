import frappe


def get_context(context):
	"""Serve the Lavanya Service Console SPA shell.

	The page (frontend.html) is the Vite-built index.html, regenerated on every
	build with fresh hashed asset names. Disable caching so /frontend always
	reflects the latest build without a manual `bench clear-cache`.

	Inject the real CSRF token so the SPA's `window.csrf_token = '{{ csrf_token }}'`
	resolves to a valid value. Without this the placeholder is served literally
	and every POST action fails with 400 for non-Administrator users (Administrator
	bypasses CSRF, which masked the bug).
	"""
	context.no_cache = 1
	frappe.flags.no_cache = 1
	context.csrf_token = frappe.sessions.get_csrf_token()
	return context
