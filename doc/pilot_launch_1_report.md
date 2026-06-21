# PILOT-LAUNCH-1 — Showroom Pilot Deployment Report

## Date: 2026-06-21

---

## 1. Deployment Verification

### Static Verification (Automated)

| Check | Result |
|---|---|
| Branch | `master` |
| HEAD | `ac40b86 docs: add H7A pilot SOP and staff training guide` |
| Tag | `pilot-uiux-h6d-2026-06-21` |
| Worktree | Clean |
| `COLORS.*` in Vue | 0 |
| Native `alert/prompt` | 0 |
| Live WhatsApp API calls | 0 |
| CRM write calls | 0 |

### Runtime Verification (Manual — requires Frappe bench)

Run these commands on the pilot server:

```bash
cd /path/to/frappe-bench
git -C apps/lavanya_service checkout master
git -C apps/lavanya_service pull origin master
git -C apps/lavanya_service log --oneline -3

bench --site <pilot-site> migrate
bench --site <pilot-site> clear-cache
bench build
bench restart
```

Expected: migrate completes, SPA loads at `/frontend`.

---

## 2. Safety Lock Verification

### Static Analysis (Confirmed)

| Safety Lock | Field | Expected | Verified |
|---|---|---|---|
| Live notifications blocked | `live_notifications_blocked` | 1 | Settings UI |
| ERP posting disabled | `erp_posting_disabled` | 1 | Settings UI |
| Penalty apply disabled | `penalty_apply_disabled` | 1 | Settings UI |
| CRM automation disabled | `crm_enabled=0, crm_mode=Disabled` | Disabled | Settings UI |
| WhatsApp live send blocked | `live_send_blocked=1` | Blocked | hooks.py validate |
| Dry-run mode | `dry_run_mode_on` | 1 | Settings UI |

### Runtime Verification (Manual)

```bash
bench --site <pilot-site> console
```

```python
settings = frappe.get_single("Lavanya Service Settings")
assert settings.live_notifications_blocked == 1
assert settings.erp_posting_disabled == 1
assert settings.penalty_apply_disabled == 1
assert settings.dry_run_mode_on == 1
assert settings.crm_enabled == 0
assert settings.crm_mode == "Disabled"
print("All safety locks confirmed.")
```

---

## 3. Staff and Role Setup

### Required Pilot Users

| Role | Username | Permissions |
|---|---|---|
| Front Desk | `pilot-frontdesk` | New Ticket, Field Mode, Today's Work |
| Service Staff | `pilot-service` | Today's Work, Tickets, Ticket Detail, WhatsApp Inbox, Customer 360 |
| Service Manager | `pilot-manager` | All + Reports + Settings |
| Owner/Admin | `pilot-owner` | Full (including safety lock view) |

### Create Users (Manual)

```bash
bench --site <pilot-site> console
```

```python
roles_and_users = [
    ("Lavanya Front Desk", "pilot-frontdesk@lavanya.in", "Front Desk"),
    ("Lavanya Helpdesk Agent", "pilot-service@lavanya.in", "Service Staff"),
    ("Lavanya Manager", "pilot-manager@lavanya.in", "Manager"),
    ("System Manager", "pilot-owner@lavanya.in", "Owner"),
]
for role, email, first_name in roles_and_users:
    if not frappe.db.exists("User", email):
        user = frappe.new_doc("User")
        user.email = email
        user.first_name = first_name
        user.enabled = 1
        user.user_type = "System User"
        user.append("roles", {"role": role})
        user.insert(ignore_permissions=True)
        print(f"Created: {email} ({role})")
    else:
        print(f"Exists: {email}")
```

### Permission Verification

```python
from lavanya_service.workflow.today_work import _allowed_group_keys_for_user

for email in ["pilot-frontdesk@lavanya.in", "pilot-service@lavanya.in", "pilot-manager@lavanya.in"]:
    frappe.set_user(email)
    user = frappe.session.user
    groups = _allowed_group_keys_for_user(user)
    can_create = frappe.has_permission("HD Ticket", "create")
    print(f"{email}: create={can_create}, groups={len(groups)}")
frappe.set_user("Administrator")
```

---

## 4. Minimum Master Data

### Brand Seeds (auto-installed)
The app auto-seeds: LG, Samsung, Whirlpool, Voltas, Preethi, Bajaj, Prestige, Crompton, Kent, Faber.

### Manual Master Data Entry

**Add Service Centers:**
```
Service Center Master:
- Name, Brand, Phone, Coverage Pincodes, Status=Active
```

**Add Local Technicians:**
```
Local Technician Master:
- Name, Phone, Skills, Area, Active=1
```

**Add Product Categories (auto-installed):**
AC, Refrigerator, Washing Machine, Mixer, Induction Cooker, Chimney, Hob, Gas Stove, TV, Water Purifier, Other

### Verify (Manual)

```python
brands = frappe.db.count("Brand Service Master")
sc = frappe.db.count("Service Center Master")
techs = frappe.db.count("Local Technician Master")
print(f"Ready: {brands} brands, {sc} service centers, {techs} technicians")
```

---

## 5. Pilot Smoke Test

Run these tests with each role after deployment:

| Test | Role | Expected |
|---|---|---|
| Load `/frontend` | Any | SPA loads with Today's Work |
| Create ticket via `/new-ticket` | Front Desk | Customer lookup works, ticket created |
| Open ticket drawer | Service Staff | All sections visible, closure guard active |
| Run "Follow Up Service Center" | Service Staff | Action saves, follow-up logged |
| Mark customer informed | Service Staff | Status updates in timeline |
| Try close without satisfaction | Service Staff | Closure guard blocks |
| Record satisfaction then close | Manager | Closure allowed |
| Open Customer 360 | Any | Loads identity, products, tickets |
| Open WhatsApp Inbox | Any | Shows "draft-only" banner, no send button |
| Open Reports → Penalty tab | Manager | "Advisory only" banner visible |
| Open Settings | Non-Manager | Read-only mode, safety locks visible |
| Open Settings | Manager | Edit mode, can save/reset |
| Open Field Mode on mobile | Front Desk | Search, recent work, action buttons |

---

## 6. Staff Training (from H7A SOP)

Train each role using `doc/h7a_pilot_sop_staff_training_guide.md`:

- [ ] Front Desk: New ticket, Field Mode, customer lookup
- [ ] Service Staff: Today's Work, quick actions, follow-up routine
- [ ] Manager: Reports, safety locks, WhatsApp draft review
- [ ] Owner/Admin: Executive summary, safety verification

---

## 7. First-Week Monitoring Template

### Daily Pilot Review Note

| Date | Tickets Created | Due Today | Overdue | Not Informed | Tech Call Pending | Tech Visit Pending | Part Pending | Sat. Pending | Reopened |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |

### Staff Feedback (Daily)

| Staff | Issue Type | Page | Description | Severity |
|---|---|---|---|---|
| | | | | |

---

## 8. Pilot Issue Register

Template: `doc/pilot_issue_register.md`

Categories: Bug, UX Confusion, Missing Master Data, Wrong Workflow, Permission Issue, Report Mismatch, Training Issue, Safety Concern

---

## 9. Summary

| Area | Status |
|---|---|
| Git state verified | Pass |
| Tag confirmed | `pilot-uiux-h6d-2026-06-21` |
| Static safety scan | Pass (0 COLORS, 0 dialogs, 0 live WA, 0 CRM writes) |
| Bench deploy | **Manual — requires pilot server** |
| Safety lock verification | **Manual — requires Frappe console** |
| Staff/role creation | **Manual — requires Frappe console** |
| Master data entry | **Manual — requires Frappe Desk** |
| Smoke test | **Manual — requires browser + staff roles** |
| Staff training | **Manual — use H7A SOP guide** |
| Daily monitoring | **Template provided below** |

---

## 10. Pilot Restrictions (DO NOT CHANGE)

- Live WhatsApp/SMS: OFF
- CRM lead/deal creation: OFF
- ERP posting: OFF
- Penalty application: OFF
- Automatic closure: OFF
- Safety locks: DO NOT CHANGE

Report any attempt to enable these as a Safety Concern in the pilot issue register.
