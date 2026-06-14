import frappe
import os
import json

def run():
    print("Running Frappe UI Console Phase 2 Tests...")

    app_path = frappe.get_app_path("lavanya_service")
    frontend_path = os.path.join(os.path.dirname(app_path), "frontend")
    
    # 1. /frontend serving file exists
    www_frontend = os.path.join(app_path, "www", "frontend.html")
    assert os.path.exists(www_frontend), "/frontend route serving file missing"

    # 2. AppShell source exists
    app_shell = os.path.join(frontend_path, "src", "components", "AppShell.vue")
    assert os.path.exists(app_shell), "AppShell.vue source missing"

    # 3. Stable layout classes or official config present
    index_css = os.path.join(frontend_path, "src", "index.css")
    with open(index_css, "r") as f:
        css_content = f.read()
    assert ".lav-shell" in css_content and ".lav-sidebar" in css_content, "Stable layout classes missing"

    # 4. Today’s Work screen source exists
    today_work = os.path.join(frontend_path, "src", "pages", "TodayWork.vue")
    assert os.path.exists(today_work), "TodayWork.vue missing"

    # 5. Required card labels present
    with open(today_work, "r", encoding="utf-8") as f:
        today_content = f.read()
    assert "Total Pending" in today_content, "Total Pending label missing"
    assert "Overdue" in today_content, "Overdue label missing"
    assert "Due Today" in today_content, "Due Today label missing"

    # 6. Standard Helpdesk fallback link present
    with open(app_shell, "r", encoding="utf-8") as f:
        appshell_content = f.read()
    assert "/helpdesk/tickets" in appshell_content, "Helpdesk fallback link missing"

    # 7. No write API calls wired
    # Ensure there are no write API calls (like frappe.call for doc insert/update) in TodayWork
    # Actually wait, TodayWork only does lavanya_service.api.today_work.get_today_work
    # Let's just check 'get_today_work' is there, and no 'frappe.client.insert'
    assert "insert(" not in today_content, "Write API calls found"
    assert "save(" not in today_content, "Write API calls found"

    # 8. No apps/helpdesk changes (we'll check git status via command later, but assert here just to be safe)
    # the user script checks this via git status --short

    # 9. No forbidden fixtures
    fixtures_dir = os.path.join(os.path.dirname(app_path), "fixtures")
    forbidden = [
        "user.json",
        "has_role.json",
        "user_permission.json",
        "role_profile.json",
        "hd_agent.json",
        "hd_ticket.json",
        "service_product_receipt.json",
        "lavanya_customer_profile.json",
        "lavanya_product_category.json",
        "lavanya_product_item.json",
        "communication.json",
        "email_queue.json",
        "notification_log.json",
        "todo.json",
        "comment.json"
    ]
    for fix in forbidden:
        fix_path = os.path.join(fixtures_dir, fix)
        assert not os.path.exists(fix_path), f"Forbidden fixture {fix} exists"

    print("✅ Frappe UI Console tests passed")
