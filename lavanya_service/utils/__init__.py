import frappe
import importlib
import sys


def ensure_whitelist():
    """Force-import API modules so decorators fire at startup."""
    # This runs before_request to ensure whitelist is populated
    _API_MODULES = (
        "lavanya_service.api.stitch_console",
        "lavanya_service.api.workflow_actions",
    )
    for mod_path in _API_MODULES:
        if mod_path not in sys.modules:
            try:
                importlib.import_module(mod_path)
            except Exception:
                pass
