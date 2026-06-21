"""Tests for the SPA read endpoints + Reports drill-down + ticket activity.

Covers the methods added for the Lavanya Service Console SPA:
  - stitch_console.get_ticket_list (search/status/pagination, permission)
  - stitch_console.get_ticket_activity / add_ticket_note
  - manager_reports.get_report_catalog / get_report (counts + role gating)
  - a regression guard for the api.js undefined-param bug

Run: bench --site <site> execute lavanya_service.tests.stitch_console_spa.run
Self-contained: creates and deletes its own test ticket.
"""

import os

import frappe

LIST_API = "lavanya_service.api.stitch_console.get_ticket_list"
DETAIL_API = "lavanya_service.api.stitch_console.get_ticket_detail"
ACTIVITY_API = "lavanya_service.api.stitch_console.get_ticket_activity"
NOTE_API = "lavanya_service.api.stitch_console.add_ticket_note"
CATALOG_API = "lavanya_service.api.manager_reports.get_report_catalog"
REPORT_API = "lavanya_service.api.manager_reports.get_report"

UNIQUE = "ZZUNIQUESPATEST"


def _make_ticket():
    frappe.set_user("Administrator")
    cust = frappe.get_all("HD Customer", limit=1)
    t = frappe.new_doc("HD Ticket")
    t.subject = f"{UNIQUE} subject"
    t.ticket_type = "Customer Complaint - Site"
    t.customer = cust[0].name if cust else None
    t.insert(ignore_permissions=True)
    return t.name


def _cleanup_ticket(name):
    frappe.set_user("Administrator")
    if frappe.db.exists("HD Ticket", name):
        frappe.delete_doc("HD Ticket", name, force=True, ignore_permissions=True)


def _test_get_ticket_list():
    print("  get_ticket_list…")
    # Guest rejected
    frappe.set_user("Guest")
    try:
        frappe.call(LIST_API)
        assert False, "Guest could call get_ticket_list"
    except frappe.PermissionError:
        pass

    frappe.set_user("Administrator")
    ticket = _make_ticket()
    try:
        # Shape
        res = frappe.call(LIST_API, page_length=5)
        assert isinstance(res, dict) and "tickets" in res, "get_ticket_list missing 'tickets'"
        assert isinstance(res["has_more"], bool), "has_more not a bool"

        # Search matches the unique ticket
        found = frappe.call(LIST_API, search=UNIQUE)
        names = [t["name"] for t in found["tickets"]]
        assert ticket in names, "search did not find the unique ticket"

        # Bogus search returns nothing (guards the search semantics)
        empty = frappe.call(LIST_API, search="NOSUCHTERMXYZ999")
        assert empty["tickets"] == [], "bogus search should return no tickets"

        # No search returns the ticket too (regression for the undefined-param bug:
        # an omitted search must behave as 'no filter', not match-nothing)
        nofilter = frappe.call(LIST_API, status="All", page_length=100)
        assert ticket in [t["name"] for t in nofilter["tickets"]], "no-search list should include the ticket"

        # page_length is capped at 100
        capped = frappe.call(LIST_API, page_length=9999)
        assert capped["page_length"] <= 100, "page_length not capped"
    finally:
        _cleanup_ticket(ticket)


def _test_activity_and_notes():
    print("  get_ticket_activity / add_ticket_note…")
    frappe.set_user("Administrator")
    ticket = _make_ticket()
    try:
        # Guest rejected on both
        frappe.set_user("Guest")
        for api in (ACTIVITY_API, NOTE_API):
            try:
                frappe.call(api, ticket_id=ticket, note="x") if api == NOTE_API else frappe.call(api, ticket_id=ticket)
                assert False, f"Guest could call {api}"
            except frappe.PermissionError:
                pass

        frappe.set_user("Administrator")
        # Empty note rejected
        try:
            frappe.call(NOTE_API, ticket_id=ticket, note="   ")
            assert False, "empty note should be rejected"
        except frappe.ValidationError:
            pass

        # Add a note → returns a note event
        ev = frappe.call(NOTE_API, ticket_id=ticket, note="Called customer")
        assert ev["kind"] == "note" and "Called customer" in ev["text"], "add_ticket_note returned wrong event"

        # Activity includes the note + a creation event, newest first
        feed = frappe.call(ACTIVITY_API, ticket_id=ticket)
        events = feed["events"]
        assert any(e["kind"] == "note" and "Called customer" in e["text"] for e in events), "note missing from activity"
        assert any(e["text"] == "Ticket created" for e in events), "creation event missing from activity"
        assert events[0]["kind"] == "note", "activity not newest-first"
    finally:
        _cleanup_ticket(ticket)


def _test_reports_catalog_and_drilldown():
    print("  get_report_catalog / get_report…")
    frappe.set_user("Administrator")

    catalog = frappe.call(CATALOG_API)["reports"]
    assert catalog, "catalog is empty for Administrator"
    by_key = {r["key"]: r for r in catalog}

    # Every catalog count must equal len(rows) of its report (the core guarantee)
    for key, meta in by_key.items():
        rep = frappe.call(REPORT_API, report=key)
        assert rep["count"] == len(rep["rows"]), f"{key}: count != len(rows)"
        if meta["count"] is not None:
            assert meta["count"] == rep["count"], f"{key}: catalog count {meta['count']} != report count {rep['count']}"
        assert isinstance(rep["columns"], list) and rep["columns"], f"{key}: no columns"

    # Unknown report rejected
    try:
        frappe.call(REPORT_API, report="no_such_report")
        assert False, "unknown report should raise"
    except Exception:
        pass

    # Role gating: a non-manager must not see/open manager-only reports
    agent = "uat.agent@lavanya.local"
    if frappe.db.exists("User", agent):
        frappe.set_user(agent)
        try:
            agent_catalog = frappe.call(CATALOG_API)["reports"]
            agent_keys = {r["key"] for r in agent_catalog}
            assert "product_at_store_aging" not in agent_keys, "agent should not see manager-only report in catalog"
            try:
                frappe.call(REPORT_API, report="product_at_store_aging")
                assert False, "agent could open a manager-only report"
            except frappe.PermissionError:
                pass
        finally:
            frappe.set_user("Administrator")


def _test_api_js_undefined_guard():
    """Source guard for the fix in api.js: the call() helper must strip
    null/undefined params (else URLSearchParams sends them as 'undefined')."""
    print("  api.js undefined-param guard…")
    app_path = frappe.get_app_path("lavanya_service")
    api_js = os.path.join(os.path.dirname(app_path), "frontend", "src", "api.js")
    with open(api_js, "r", encoding="utf-8") as f:
        content = f.read()
    assert "v !== undefined && v !== null" in content, (
        "api.js call() must drop null/undefined params before building the query string"
    )


def _test_frontend_csrf_injection():
    """Guard: the /frontend www controller must inject a real csrf_token, else the
    literal '{{ csrf_token }}' is served and every POST 400s for non-admins.
    Source check (rendering needs a web-request session the test harness lacks)."""
    print("  /frontend csrf injection guard…")
    app_path = frappe.get_app_path("lavanya_service")
    src = os.path.join(app_path, "www", "frontend.py")
    with open(src, "r", encoding="utf-8") as f:
        content = f.read()
    assert "context.csrf_token" in content and "get_csrf_token" in content, (
        "www/frontend.py must inject a real csrf_token (context.csrf_token = "
        "frappe.sessions.get_csrf_token()) or POST actions 400 for non-admins"
    )


def _test_create_ticket():
    """create_ticket: Guest rejected, required-field validation, and a valid
    staff create returns the ticket name (cleaned up after)."""
    print("  create_ticket…")
    CREATE = "lavanya_service.api.stitch_console.create_ticket"

    frappe.set_user("Guest")
    try:
        frappe.call(CREATE, customer_name="X", mobile="9876500022", complaint_details="d", product_type="AC", brand="Z")
        assert False, "Guest could create a ticket"
    except frappe.PermissionError:
        pass

    frappe.set_user("Administrator")
    # Missing required field is rejected.
    try:
        frappe.call(CREATE, customer_name="X", mobile="9876500022", product_type="AC", brand="Z")
        assert False, "missing complaint_details should be rejected"
    except frappe.ValidationError:
        pass

    brand = (frappe.get_all("Brand Service Master", pluck="name", limit=1) or [None])[0]
    if not brand:
        return
    res = frappe.call(
        CREATE, customer_name="SPA Create Test", mobile="9876500033",
        complaint_details="Test complaint", product_type="AC", brand=brand,
    )
    assert res.get("ok") and res.get("ticket"), "create_ticket should return ok + ticket name"
    name = res["ticket"]
    assert frappe.db.get_value("HD Ticket", name, "complaint_source") == "Staff Entered", "source should be Staff Entered"
    frappe.delete_doc("HD Ticket", name, force=True, ignore_permissions=True)


def _test_ticket_detail_reminder():
    """get_ticket_detail exposes a blank-safe Reminder Intelligence dict (Step 5)."""
    print("  get_ticket_detail reminder…")
    frappe.set_user("Administrator")
    name = (frappe.get_all("HD Ticket", filters={"status": ["not in", ["Closed", "Cancelled"]]}, pluck="name", limit=1) or [None])[0]
    if not name:
        return
    res = frappe.call(DETAIL_API, ticket_id=name)
    assert isinstance(res, dict) and "reminder" in res, "get_ticket_detail missing 'reminder'"
    rem = res["reminder"]
    assert isinstance(rem, dict), "reminder should be a dict"
    # Blank-safe: every advertised key is present (may be None), never raises.
    for key in ("reminder_rule_applied", "overdue_status", "escalation_level",
                "customer_promise_status", "customer_update_due", "manual_followup",
                "computed_stage_due_at", "computed_due_soon_at"):
        assert key in rem, f"reminder missing key {key}"
    # stage dict must still be present (no regression).
    assert "stage" in res, "get_ticket_detail missing 'stage'"


def run():
    print("Running Stitch Console SPA endpoint tests…")
    _test_get_ticket_list()
    _test_ticket_detail_reminder()
    _test_create_ticket()
    _test_activity_and_notes()
    _test_reports_catalog_and_drilldown()
    _test_api_js_undefined_guard()
    _test_frontend_csrf_injection()
    frappe.set_user("Administrator")
    print("✅ Stitch Console SPA endpoint tests passed")
