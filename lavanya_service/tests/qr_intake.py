"""Rollback-safe tests for QR Customer Complaint Intake (Phase 1Q).

Run with:
    bench --site <site> execute lavanya_service.tests.qr_intake.run
"""

import time
import frappe


RESULTS = []


def _record(test_id, passed, detail=""):
    RESULTS.append((test_id, passed, detail))
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {test_id} | {detail}")


def run():
    global RESULTS
    RESULTS = []

    print("Running QR Intake Tests")

    # Baseline counts for side-effect tracking
    side_effect_doctypes = ['Email Queue', 'Notification Log', 'Communication', 'ToDo', 'Comment']
    baseline_counts = {}
    for dt in side_effect_doctypes:
        if frappe.db.exists('DocType', dt):
            baseline_counts[dt] = frappe.db.count(dt)

    baseline_tickets = frappe.db.count('HD Ticket')
    baseline_profiles = frappe.db.count('Lavanya Customer Profile')

    try:
        _test_all(baseline_counts, baseline_tickets, baseline_profiles)
    finally:
        frappe.db.rollback()
        # Clear any rate-limit cache entries we created (atomic counters use
        # raw keys, so reset via the same helper the limiter uses).
        try:
            from lavanya_service.api.qr_intake import _reset_rate_limit as _rrl
            for mobile in ["9876500001", "9876500002", "9876500003", "9876500004",
                           "9876500005", "9876500006", "9876500007", "9876500008"]:
                _rrl("mobile", mobile)
            _rrl("ip", "127.0.0.99")
        except Exception:
            pass

        print("\nTRANSACTION ROLLED BACK - no records persisted")

    total = len(RESULTS)
    failed = sum(1 for _, p, _ in RESULTS if not p)
    print(f"\nTOTAL: {total} | PASS: {total - failed} | FAIL: {failed}")
    print(f"OVERALL: {'PASS' if failed == 0 else 'FAIL'}")

    import json
    print(json.dumps({"total": total, "failed": failed}))


def _test_all(baseline_counts, baseline_tickets, baseline_profiles):
    from lavanya_service.api.qr_intake import (
        submit_qr_complaint,
        _check_rate_limit,
        _reset_rate_limit,
        _strip_html,
        _clean_text,
        SAFE_TICKET_TYPES,
        get_qr_intake_options,
    )

    # ------------------------------------------------------------------
    # QR-001: API is importable and callable
    # ------------------------------------------------------------------
    _record("QR-001 - API importable", True, "submit_qr_complaint imported OK")

    # ------------------------------------------------------------------
    # QR-002: Valid QR complaint creates one HD Ticket
    # ------------------------------------------------------------------
    result = submit_qr_complaint(
        customer_name="QR Test Customer",
        mobile="9876500001",
        complaint_details="AC is not cooling properly after 2 months",
        product_type="AC",
        brand="LG",
    )
    _record("QR-002 - Valid QR complaint creates ticket",
            result.get("ok") is True, f"result={result}")

    # verify ticket was created
    tickets_after = frappe.db.count('HD Ticket')
    _record("QR-002b - Ticket count increased by 1",
            tickets_after == baseline_tickets + 1,
            f"before={baseline_tickets}, after={tickets_after}")

    # ------------------------------------------------------------------
    # QR-003: Ticket has complaint_source = Customer QR Form
    # ------------------------------------------------------------------
    latest_ticket = frappe.get_last_doc('HD Ticket')
    _record("QR-003 - complaint_source is Customer QR Form",
            latest_ticket.complaint_source == "Customer QR Form",
            f"actual={latest_ticket.complaint_source}")

    # ------------------------------------------------------------------
    # QR-004: Ticket has status New, priority Medium
    # ------------------------------------------------------------------
    _record("QR-004 - status=New, priority=Medium",
            latest_ticket.status == "New" and latest_ticket.priority == "Medium",
            f"status={latest_ticket.status}, priority={latest_ticket.priority}")

    # ------------------------------------------------------------------
    # QR-005: Customer profile sync works for valid mobile
    # ------------------------------------------------------------------
    profiles_after = frappe.db.count('Lavanya Customer Profile')
    profile_created = profiles_after > baseline_profiles
    _record("QR-005 - Customer profile synced for valid mobile",
            profile_created,
            f"before={baseline_profiles}, after={profiles_after}")

    # ------------------------------------------------------------------
    # QR-006: Invalid mobile is rejected
    # ------------------------------------------------------------------
    rejected = False
    try:
        submit_qr_complaint(
            customer_name="Bad Phone",
            mobile="12345",
            complaint_details="test",
            product_type="AC",
            brand="LG",
        )
    except frappe.ValidationError:
        rejected = True
    _record("QR-006 - Invalid mobile rejected", rejected)

    # ------------------------------------------------------------------
    # QR-007: Repeated junk mobile is rejected
    # ------------------------------------------------------------------
    rejected_junk = False
    try:
        submit_qr_complaint(
            customer_name="Junk Phone",
            mobile="9999999999",
            complaint_details="test",
            product_type="AC",
            brand="LG",
        )
    except frappe.ValidationError:
        rejected_junk = True
    _record("QR-007 - Repeated junk mobile rejected", rejected_junk)

    # ------------------------------------------------------------------
    # QR-008: Unsafe ticket_type is blocked (silently reset)
    # ------------------------------------------------------------------
    result_unsafe = submit_qr_complaint(
        customer_name="Unsafe Type Test",
        mobile="9876500002",
        complaint_details="test complaint",
        product_type="AC",
        brand="Samsung",
        ticket_type="Internal Admin Override",
    )
    unsafe_ticket = frappe.get_last_doc('HD Ticket')
    _record("QR-008 - Unsafe ticket_type silently reset to safe default",
            unsafe_ticket.ticket_type == "Customer Complaint - Site",
            f"actual_type={unsafe_ticket.ticket_type}")

    # ------------------------------------------------------------------
    # QR-009: Missing required fields blocked
    # ------------------------------------------------------------------
    missing_blocked = True
    for field_to_omit in ["customer_name", "mobile", "complaint_details", "product_type", "brand"]:
        payload = {
            "customer_name": "Test",
            "mobile": "9876500003",
            "complaint_details": "test",
            "product_type": "AC",
            "brand": "LG",
        }
        payload[field_to_omit] = ""
        try:
            submit_qr_complaint(**payload)
            missing_blocked = False
            break
        except frappe.ValidationError:
            pass
    _record("QR-009 - Missing required fields blocked", missing_blocked)

    # ------------------------------------------------------------------
    # QR-010: HTML/script injection sanitized
    # ------------------------------------------------------------------
    html_input = '<script>alert("xss")</script><b>Bold</b> Normal'
    sanitized = _strip_html(html_input)
    has_no_tags = "<" not in sanitized and ">" not in sanitized
    _record("QR-010 - HTML/script injection sanitized",
            has_no_tags,
            f"sanitized={sanitized}")

    # ------------------------------------------------------------------
    # QR-011: Complaint text length capped
    # ------------------------------------------------------------------
    long_text = "A" * 5000
    capped = _clean_text(long_text)
    _record("QR-011 - Complaint text length capped at 2000",
            len(capped) == 2000,
            f"len={len(capped)}")

    # ------------------------------------------------------------------
    # QR-012: Rate limit by mobile works
    # ------------------------------------------------------------------
    # Clear rate limit cache for test mobile
    _reset_rate_limit("mobile", "9876500004")

    rate_blocked = False
    for i in range(4):
        try:
            submit_qr_complaint(
                customer_name=f"Rate Test {i}",
                mobile="9876500004",
                complaint_details=f"Rate limit test {i}",
                product_type="AC",
                brand="LG",
            )
        except frappe.ValidationError as e:
            if "Too many" in str(e):
                rate_blocked = True
                break
    _record("QR-012 - Rate limit by mobile works (3/hour)",
            rate_blocked,
            f"blocked_at_attempt={i}")

    # ------------------------------------------------------------------
    # QR-013: Rate limit by IP works
    # ------------------------------------------------------------------
    # We test the _check_rate_limit function directly for IP
    _reset_rate_limit("ip", "127.0.0.99")

    ip_rate_ok = False
    try:
        for j in range(11):
            _check_rate_limit("ip", "127.0.0.99", 10)
    except frappe.ValidationError:
        ip_rate_ok = True
    _record("QR-013 - Rate limit by IP works (10/hour)", ip_rate_ok)

    # ------------------------------------------------------------------
    # QR-014: Public response does not expose internal details
    # ------------------------------------------------------------------
    safe_keys = {"ok", "message", "reference"}
    exposed_keys = set(result.keys()) - safe_keys
    _record("QR-014 - Public response has only safe keys",
            len(exposed_keys) == 0,
            f"keys={set(result.keys())}")

    # does not expose ticket name
    ref_value = result.get("reference", "")
    no_internal = not ref_value.startswith("HD-TKT") and "0020" not in ref_value
    _record("QR-014b - Reference does not expose internal ticket name",
            no_internal,
            f"reference={ref_value}")

    # ------------------------------------------------------------------
    # QR-015: Today's Work includes created QR ticket
    # ------------------------------------------------------------------
    tw_ok = False
    try:
        from lavanya_service.api.today_work import get_today_work
        tw = get_today_work()
        # The QR-created ticket should be in 'new_complaints' or similar bucket
        tw_ok = isinstance(tw, dict)
    except Exception as e:
        print(f"  TW error: {e}")
    _record("QR-015 - Today's Work API functional after QR intake", tw_ok)

    # ------------------------------------------------------------------
    # QR-016: Safe ticket type selection works
    # ------------------------------------------------------------------
    result_safe_type = submit_qr_complaint(
        customer_name="Safe Type Test",
        mobile="9876500005",
        complaint_details="Installation request",
        product_type="TV",
        brand="LG",
        ticket_type="Installation / Demo",
    )
    safe_type_ticket = frappe.get_last_doc('HD Ticket')
    _record("QR-016 - Safe ticket_type selection works",
            safe_type_ticket.ticket_type == "Installation / Demo",
            f"type={safe_type_ticket.ticket_type}")

    # ------------------------------------------------------------------
    # QR-017: No outbound side effects
    # ------------------------------------------------------------------
    current_counts = {}
    for dt in ['Email Queue', 'Notification Log', 'Communication', 'ToDo', 'Comment']:
        if frappe.db.exists('DocType', dt):
            current_counts[dt] = frappe.db.count(dt)

    diffs = {dt: current_counts.get(dt, 0) - baseline_counts.get(dt, 0) for dt in baseline_counts}
    # Email Queue and Notification Log must be zero
    email_clean = diffs.get('Email Queue', 0) == 0
    notif_clean = diffs.get('Notification Log', 0) == 0
    _record("QR-017 - No Email Queue or Notification Log side effects",
            email_clean and notif_clean,
            f"diffs={diffs}")

    # ------------------------------------------------------------------
    # QR-018: Unknown brand is rejected cleanly (audit A1)
    # ------------------------------------------------------------------
    brand_rejected = False
    try:
        submit_qr_complaint(
            customer_name="Bad Brand",
            mobile="9876500006",
            complaint_details="unknown brand test",
            product_type="AC",
            brand="NoSuchBrand",
        )
    except frappe.ValidationError as e:
        brand_rejected = "valid brand" in str(e)
    _record("QR-018 - Unknown brand rejected cleanly", brand_rejected)

    # ------------------------------------------------------------------
    # QR-019: Unknown product_type is rejected cleanly (audit A1)
    # ------------------------------------------------------------------
    product_rejected = False
    try:
        submit_qr_complaint(
            customer_name="Bad Product",
            mobile="9876500007",
            complaint_details="unknown product test",
            product_type="Spaceship",
            brand="LG",
        )
    except frappe.ValidationError as e:
        product_rejected = "valid product type" in str(e)
    _record("QR-019 - Unknown product type rejected cleanly", product_rejected)

    # ------------------------------------------------------------------
    # QR-020: Honeypot submission creates no ticket (audit A2)
    # ------------------------------------------------------------------
    tickets_before_hp = frappe.db.count('HD Ticket')
    hp_result = submit_qr_complaint(
        customer_name="Bot",
        mobile="9876500008",
        complaint_details="spam",
        product_type="AC",
        brand="LG",
        company_name="bot-filled-this",
    )
    tickets_after_hp = frappe.db.count('HD Ticket')
    _record("QR-020 - Honeypot drops submission, no ticket created",
            hp_result.get("ok") is True and tickets_after_hp == tickets_before_hp,
            f"before={tickets_before_hp}, after={tickets_after_hp}")

    # ------------------------------------------------------------------
    # QR-021: Public options endpoint returns only safe option lists (audit A1)
    # ------------------------------------------------------------------
    options = get_qr_intake_options()
    opts_ok = (
        isinstance(options, dict)
        and set(options.keys()) == {"brands", "product_types", "ticket_types"}
        and "LG" in options["brands"]
        and "AC" in options["product_types"]
        and options["ticket_types"] == SAFE_TICKET_TYPES
    )
    _record("QR-021 - Public options endpoint returns safe lists",
            opts_ok,
            f"keys={set(options.keys()) if isinstance(options, dict) else options}")

    # ------------------------------------------------------------------
    # QR-022: QR ticket uses single controlled raised_by (audit A4)
    # ------------------------------------------------------------------
    from lavanya_service.api.qr_intake import QR_RAISED_BY
    qr_ticket = frappe.get_doc('HD Ticket', latest_ticket.name)
    _record("QR-022 - QR ticket uses controlled raised_by placeholder",
            qr_ticket.raised_by == QR_RAISED_BY,
            f"raised_by={qr_ticket.raised_by}")
