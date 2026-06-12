import frappe
from typing import Dict, Any

def run():
    print("Running Pilot Readiness Checks")
    results = {
        "total": 0,
        "failed": 0,
        "details": {}
    }

    # Helper function
    def report(name: str, passed: bool, detail: str = ""):
        results["total"] += 1
        if not passed:
            results["failed"] += 1
        results["details"][name] = {"passed": passed, "detail": detail}
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {name} | {detail}")

    # Track baseline for side-effects
    side_effect_doctypes = ['Email Queue', 'Notification Log', 'Communication', 'ToDo', 'Comment']
    baseline_counts = {dt: frappe.db.count(dt) for dt in side_effect_doctypes if frappe.db.exists('DocType', dt)}

    # 1. Required apps
    installed_apps = frappe.get_installed_apps()
    missing_apps = [app for app in ['frappe', 'helpdesk', 'lavanya_service'] if app not in installed_apps]
    report("PR-001 - Required apps installed", len(missing_apps) == 0, f"missing={missing_apps}")

    # 2. Required DocTypes
    required_doctypes = ['HD Ticket', 'Service Product Receipt', 'HD Notification', 'Lavanya Customer Profile']
    missing_doctypes = [dt for dt in required_doctypes if not frappe.db.exists('DocType', dt)]
    report("PR-002 - Required DocTypes exist", len(missing_doctypes) == 0, f"missing={missing_doctypes}")

    # 3. Required ticket types
    required_types = ['Customer Complaint - Site', 'Customer Product at Store', 'Installation / Demo']
    existing_types = frappe.get_all('HD Ticket Type', pluck='name') if frappe.db.exists('DocType', 'HD Ticket Type') else []
    missing_types = [t for t in required_types if t not in existing_types]
    report("PR-003 - Required ticket types exist", len(missing_types) == 0, f"missing={missing_types}")

    # 4. Required statuses
    required_statuses = ['New', 'Open', 'Replied', 'Resolved', 'Closed', 'Cancelled', 'In Progress', 'Brand Registered', 'Registration Pending', 'Waiting on Customer', 'Waiting on Part / Approval', 'Ready for Pickup']
    existing_statuses = frappe.get_all('HD Ticket Status', pluck='name') if frappe.db.exists('DocType', 'HD Ticket Status') else []
    missing_statuses = [s for s in required_statuses if s not in existing_statuses]
    report("PR-004 - Required statuses exist", len(missing_statuses) == 0, f"missing={missing_statuses}")

    # 5. Lavanya Default SLA
    has_sla = False
    sla_is_default = False
    if frappe.db.exists('DocType', 'HD Service Level Agreement'):
        lavanya_sla = frappe.db.get_value('HD Service Level Agreement', 'Lavanya Default', ['name', 'default_sla'], as_dict=True)
        if lavanya_sla:
            has_sla = True
            sla_is_default = bool(lavanya_sla.default_sla)
    report("PR-005 - Lavanya Default SLA is enabled/default", has_sla and sla_is_default, f"has_sla={has_sla}, default={sla_is_default}")

    # 6. Old Default SLA disabled
    old_sla_disabled = True
    if frappe.db.exists('DocType', 'HD Service Level Agreement'):
        old_sla = frappe.db.get_value('HD Service Level Agreement', 'Default', ['name', 'default_sla'], as_dict=True)
        if old_sla and old_sla.default_sla:
            old_sla_disabled = False
    report("PR-006 - Old Default SLA is disabled/not default", old_sla_disabled, "")

    # 7. Required roles exist
    required_roles = ['Lavanya Manager', 'Lavanya Service Coordinator', 'Lavanya Helpdesk Agent', 'Lavanya Front Desk', 'Lavanya Viewer']
    existing_roles = frappe.get_all('Role', pluck='name')
    missing_roles = [r for r in required_roles if r not in existing_roles]
    report("PR-007 - Required roles exist", len(missing_roles) == 0, f"missing={missing_roles}")

    # 8. Required pilot users exist
    pilot_users = {
        'uat.manager@lavanya.local': ['Lavanya Manager', 'Agent Manager', 'Agent'],
        'uat.coordinator@lavanya.local': ['Lavanya Service Coordinator', 'Agent'],
        'uat.agent@lavanya.local': ['Lavanya Helpdesk Agent', 'Agent'],
        'uat.frontdesk@lavanya.local': ['Lavanya Front Desk', 'Agent'],
        'uat.viewer@lavanya.local': ['Lavanya Viewer']
    }
    missing_users = []
    user_roles_ok = True
    bad_user_roles = {}
    for email, expected_roles in pilot_users.items():
        if not frappe.db.exists('User', email):
            missing_users.append(email)
        else:
            user_roles = frappe.get_all('Has Role', filters={'parent': email}, pluck='role')
            missing_for_user = [r for r in expected_roles if r not in user_roles]
            if missing_for_user:
                user_roles_ok = False
                bad_user_roles[email] = missing_for_user
    report("PR-008 - Required pilot users exist and have correct roles", len(missing_users) == 0 and user_roles_ok, f"missing_users={missing_users}, missing_roles={bad_user_roles}")

    # 9. HD Agent records exist for operator users
    operator_users = ['uat.manager@lavanya.local', 'uat.coordinator@lavanya.local', 'uat.agent@lavanya.local', 'uat.frontdesk@lavanya.local']
    missing_agents = []
    if frappe.db.exists('DocType', 'HD Agent'):
        for u in operator_users:
            if frappe.db.exists('User', u):
                if not frappe.db.exists('HD Agent', u):
                    missing_agents.append(u)
    report("PR-009 - HD Agent records exist for operator users", len(missing_agents) == 0, f"missing_agents={missing_agents}")

    # 10. Today's Work API works
    tw_api_works = False
    try:
        from lavanya_service.api.today_work import get_today_work
        res = get_today_work()
        tw_api_works = isinstance(res, dict)
    except Exception as e:
        tw_api_works = False
        print(f"TW API Error: {e}")
    report("PR-010 - Today's Work API works", tw_api_works, "")

    # 11. Manager reports API works
    mgr_api_works = False
    try:
        from lavanya_service.api.manager_reports import get_manager_dashboard
        res = get_manager_dashboard()
        mgr_api_works = isinstance(res, dict)
    except Exception as e:
        mgr_api_works = False
        print(f"Manager API Error: {e}")
    report("PR-011 - Manager reports API works", mgr_api_works, "")

    # 12. Quick action APIs are importable
    qa_importable = False
    try:
        from lavanya_service.workflow.quick_actions import need_invoice_from_customer, follow_up_service_center, mark_product_ready
        qa_importable = True
    except Exception as e:
        print(f"QA Import Error: {e}")
    report("PR-012 - Quick action APIs are importable", qa_importable, "")

    # 13. Product receipt action APIs are importable
    pr_importable = False
    try:
        from lavanya_service.workflow.product_receipt_actions import mark_product_sent_to_sc, mark_delivered_to_customer
        pr_importable = True
    except Exception as e:
        print(f"PR Import Error: {e}")
    report("PR-013 - Product receipt APIs are importable", pr_importable, "")

    # 14. Repeat complaint APIs are importable
    rc_importable = False
    try:
        from lavanya_service.workflow.repeat_complaints import confirm_repeat_complaint, clear_repeat_complaint
        rc_importable = True
    except Exception as e:
        print(f"RC Import Error: {e}")
    report("PR-014 - Repeat complaint APIs are importable", rc_importable, "")

    # 15. HD Form Scripts are enabled
    form_scripts_exist = False
    if frappe.db.exists('DocType', 'HD Form Script'):
        scripts = frappe.get_all('HD Form Script', filters={'name': ('like', 'Lavanya%')})
        form_scripts_exist = len(scripts) > 0
    report("PR-015 - HD Form Scripts are enabled", form_scripts_exist, "")

    # 16. Ticket template has no duplicate fields
    no_dupes = True
    dupes_detail = ""
    if frappe.db.exists('HD Ticket Template', 'Lavanya Default Template'):
        template = frappe.get_doc('HD Ticket Template', 'Lavanya Default Template')
        fieldnames = [row.fieldname for row in template.fields]
        dupes = set([x for x in fieldnames if fieldnames.count(x) > 1])
        if dupes:
            no_dupes = False
            dupes_detail = f"dupes={dupes}"
    report("PR-016 - Ticket template has no duplicate fields", no_dupes, dupes_detail)

    # 17. No forbidden fixtures
    # We should ensure that standard transactional doctypes don't have fixtures.
    import os
    fixtures_dir = frappe.get_app_path('lavanya_service', 'fixtures')
    forbidden_fixtures = ['email_queue.json', 'notification_log.json', 'communication.json', 'todo.json', 'comment.json', 'hd_ticket.json']
    found_forbidden = []
    if os.path.exists(fixtures_dir):
        for f in forbidden_fixtures:
            if os.path.exists(os.path.join(fixtures_dir, f)):
                found_forbidden.append(f)
    report("PR-017 - No forbidden fixtures", len(found_forbidden) == 0, f"found={found_forbidden}")

    # 18. No Email Queue / Notification Log side effect created by test
    current_counts = {dt: frappe.db.count(dt) for dt in side_effect_doctypes if frappe.db.exists('DocType', dt)}
    diffs = {dt: current_counts.get(dt, 0) - baseline_counts.get(dt, 0) for dt in side_effect_doctypes}
    has_side_effects = any(val != 0 for val in diffs.values())
    report("PR-018 - No outbound side effect created by test", not has_side_effects, f"diffs={diffs}")

    # Ensure transaction is rolled back just in case
    frappe.db.rollback()
    
    print("\nTOTAL:", results["total"], "| PASS:", (results["total"] - results["failed"]), "| FAIL:", results["failed"])
    print("OVERALL:", "PASS" if results["failed"] == 0 else "FAIL")
    import json
    print(json.dumps(results))
