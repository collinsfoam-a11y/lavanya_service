# UAT-R1 — Real Workflow Test Pack

## Purpose

Execute 8 seeded test scenarios covering the full Brand Warranty, Appointment, Part Pending, and Closure Gate workflow. Each test has explicit pass/fail criteria.

---

## Prerequisites

```bash
# Verify branch and safety
git checkout master
git pull origin master
git log --oneline -3
git status --short
```

### Seed test data

```python
# Run in Frappe console (bench --site <site> console)
import frappe

# Create test customer
if not frappe.db.exists("User", "uat-tester@lavanya.in"):
    tester = frappe.new_doc("User")
    tester.email = "uat-tester@lavanya.in"
    tester.first_name = "UAT Tester"
    tester.enabled = 1
    tester.user_type = "System User"
    for role in ["Lavanya Manager", "Lavanya Service Coordinator", "Lavanya Helpdesk Agent"]:
        tester.append("roles", {"role": role})
    tester.insert(ignore_permissions=True)
    print("Created UAT Tester")

# Create test brand if missing
for brand in ["LG", "Samsung"]:
    if not frappe.db.exists("Brand Service Master", brand):
        doc = frappe.new_doc("Brand Service Master")
        doc.brand_name = brand
        doc.toll_free_number = "1800-123-4567"
        doc.default_registration_sla_hours = 4
        doc.insert(ignore_permissions=True)

# Create test service center if missing
if not frappe.db.exists("Service Center Master", "UAT Service Center"):
    sc = frappe.new_doc("Service Center Master")
    sc.service_center_name = "UAT Service Center"
    sc.brand = "LG"
    sc.phone = "9876543210"
    sc.status = "Active"
    sc.insert(ignore_permissions=True)

# Create test technician if missing
if not frappe.db.exists("Local Technician Master", "UAT Technician"):
    tech = frappe.new_doc("Local Technician Master")
    tech.technician_name = "UAT Technician"
    tech.phone = "9876543211"
    tech.skills = "AC, Refrigerator"
    tech.active = 1
    tech.insert(ignore_permissions=True)

frappe.db.commit()
print("Test data seeded.")
```

---

## Test 1 — Brand Warranty Happy Path

**Setup:** Create a Brand Warranty ticket.

```python
ticket = frappe.new_doc("HD Ticket")
ticket.subject = "UAT-1: Brand Warranty Happy Path"
ticket.description = "UAT test — brand warranty, technician visits, customer satisfied"
ticket.ticket_type = "Customer Complaint - Site"
ticket.priority = "Medium"
ticket.customer_name = "UAT Customer 1"
ticket.phone_1 = "9999990001"
ticket.brand = "LG"
ticket.product_type = "Refrigerator"
ticket.warranty_status = "In Warranty"
ticket.insert()
print(f"Created: {ticket.name}")
```

### Execution Steps

| Step | Action | Location | Expected |
|---|---|---|---|
| 1.1 | Open ticket drawer | Today's Work / Tickets | Ticket loads with all sections |
| 1.2 | Check header chips | Ticket header | Status + Priority + SLA badge visible |
| 1.3 | Register Brand Complaint | Quick Actions → Register Brand Complaint | Modal opens, enter brand ticket #, date, follow-up, SC |
| 1.4 | Submit registration | Modal | Ticket updates to "Brand Registered" |
| 1.5 | Verify D+2 auto-task | Today's Work | Ticket appears in "Technician Call Verification Due" |
| 1.6 | Click "Verify Technician Called" | Follow-up Journey or Quick Actions | Modal opens |
| 1.7 | Enter: customer confirms called | Modal → submit | `followup_stage = technician_called` |
| 1.8 | Click "Verify Technician Visit" | Follow-up Journey | Modal opens |
| 1.9 | Enter: customer confirms visited, issue cleared | Modal → submit | `followup_stage = technician_visited` |
| 1.10 | Click "Verify Customer After Visit" | Follow-up Journey | Modal opens |
| 1.11 | Enter: Confirmed = Yes / Cleared / Satisfied | Modal → submit | `customer_satisfaction_status = Satisfied` |
| 1.12 | Click "Close Ticket" | Quick Actions → Close Ticket | Closure guard shows GREEN |
| 1.13 | Enter: work narration + closure type, confirmation = Yes | Modal → submit | Ticket closes |

### Pass Criteria
- [ ] Brand registration updates ticket status
- [ ] Customer Informed chip visible in header after each update
- [ ] Closure guard shows green "Closure Allowed"
- [ ] Ticket closes with customer confirmation = Yes
- [ ] `customer_satisfaction_status` is documented
- [ ] Follow-up log has [Follow-up] entries for each step

### Fail Criteria
- [ ] Ticket closes without customer confirmation
- [ ] Ticket closes without satisfaction documented
- [ ] Any [Follow-up] entry is missing for a verification step

---

## Test 2 — Technician Did Not Call

**Setup:** Create a second Brand Warranty ticket.

```python
ticket = frappe.new_doc("HD Ticket")
ticket.subject = "UAT-2: Technician Did Not Call"
ticket.description = "UAT test — technician does not call customer by D+2"
ticket.ticket_type = "Customer Complaint - Site"
ticket.priority = "High"
ticket.customer_name = "UAT Customer 2"
ticket.phone_1 = "9999990002"
ticket.brand = "Samsung"
ticket.product_type = "Washing Machine"
ticket.warranty_status = "In Warranty"
ticket.insert()
# Register brand
ticket.manufacturer_registered = "Yes"
ticket.brand_ticket_number = "UAT-BR-002"
ticket.registration_date = frappe.utils.now_datetime()
ticket.next_follow_up_date = frappe.utils.add_days(frappe.utils.today(), 2)
ticket.status = "Brand Registered"
ticket.save()
print(f"Created: {ticket.name}")
```

### Execution Steps

| Step | Action | Location | Expected |
|---|---|---|---|
| 2.1 | Open ticket | Tickets list | Ticket shows status "Brand Registered" |
| 2.2 | Open today's work | `/` | Ticket appears in "Technician Call Verification Due" |
| 2.3 | Click "Mark No Update" | Ticket Detail → Quick Actions | Modal opens |
| 2.4 | Enter: no call from technician | Modal → submit | Escalation increments, `no_update_count` increases |
| 2.5 | Click "Follow Up Service Center" | Quick Actions | Modal opens |
| 2.6 | Enter: service center says will call tomorrow | Modal → submit | `[Follow-up]` entry created |
| 2.7 | Click "Inform Customer" | Follow-up Journey | Modal opens |
| 2.8 | Enter: channel = Phone, message = will call tomorrow | Modal → submit | `customer_informed_status = Informed by Call` |
| 2.9 | Click "Set Reverification Date" | Follow-up Journey | Modal opens |
| 2.10 | Enter: reverify date = tomorrow | Modal → submit | `next_follow_up_date` updated |
| 2.11 | Try close ticket | Quick Actions → Close Ticket | **Closure BLOCKED** |

### Pass Criteria
- [ ] "Mark No Update" increments escalation level
- [ ] "Follow Up Service Center" creates [Follow-up] comment
- [ ] "Inform Customer" sets `customer_informed_status`
- [ ] "Set Reverification Date" updates `next_follow_up_date`
- [ ] Closure is **blocked** — reason: "follow-up stage is technician_call_pending" or similar
- [ ] Customer Informed chip visible in header
- [ ] Ticket appears in "Overdue Follow-up" after next_follow_up_date passes

### Fail Criteria
- [ ] Closure succeeds while verification is unresolved
- [ ] Customer informed chip missing or showing "Pending"
- [ ] No escalation after mark_no_update

---

## Test 3 — Technician Called But Did Not Visit

**Setup:** Continue from a brand-registered ticket.

```python
ticket = frappe.get_doc("HD Ticket", "<ticket-name-from-above>")
ticket.followup_stage = "technician_called"
ticket.next_follow_up_date = frappe.utils.add_days(frappe.utils.today(), 1)
ticket.save()
```

### Execution Steps

| Step | Action | Expected |
|---|---|---|
| 3.1 | Verify technician call recorded | `followup_stage = technician_called` |
| 3.2 | Let promised visit date pass | Ticket appears as Overdue in Today's Work |
| 3.3 | Mark no visit / escalate | Escalation level increments |
| 3.4 | Follow up service center | Record new promise date |
| 3.5 | Inform customer of delay | `customer_informed_status` updates |
| 3.6 | Set reverification date | Next follow-up scheduled |
| 3.7 | Try close | **BLOCKED** |

### Pass Criteria
- [ ] Missed visit creates overdue bucket entry
- [ ] Escalation triggers when promise date passes without action
- [ ] Closure blocked while `followup_stage` is in verification state

---

## Test 4 — Technician Visited, Part Required

**Setup:** Simulate technician visited, part required.

```python
ticket = frappe.get_doc("HD Ticket", "<ticket-name>")
ticket.followup_stage = "technician_visited"
ticket.save()
```

### Execution Steps

| Step | Action | Expected |
|---|---|---|
| 4.1 | Click "Record Part Required" | Modal opens |
| 4.2 | Enter: PCB, ETA 5 days, next follow-up 2 days | Modal → submit |
| 4.3 | Check header | "Part pending: <date>" chip visible |
| 4.4 | Try close | **BLOCKED** — reason: "Part 'PCB' is still pending" |
| 4.5 | Update Part ETA (delay) | Enter new ETA + reason |
| 4.6 | Inform customer about delay | Customer informed chip updates |
| 4.7 | Try close again | **STILL BLOCKED** |

### Pass Criteria
- [ ] Part pending chip visible in header with ETA
- [ ] Closure blocked while `part_required = 1`
- [ ] Part ETA update records delay reason
- [ ] Customer informed after each part update

---

## Test 5 — Part ETA Delay

**Setup:** Continue with part-pending ticket from Test 4.

### Execution Steps

| Step | Action | Expected |
|---|---|---|
| 5.1 | Let ETA pass without part arrival | Ticket in overdue bucket |
| 5.2 | Click "Update Part ETA" | Modal opens |
| 5.3 | Enter: new ETA + delay reason = Supplier Delayed | Modal → submit |
| 5.4 | Check delay reason | `part_delay_reason` recorded |
| 5.5 | Click "Inform Customer" | Customer updated about delay |
| 5.6 | Click "Set Reverification Date" | Next follow-up scheduled |

### Pass Criteria
- [ ] Delay reason is mandatory and recorded
- [ ] Customer informed after each delay update
- [ ] Reverification date set for next check

---

## Test 6 — Customer Not Satisfied

**Setup:** Technician visited, issue not cleared.

### Execution Steps

| Step | Action | Expected |
|---|---|---|
| 6.1 | Click "Verify Customer After Visit" | Modal opens |
| 6.2 | Enter: Confirmed = No / Not Cleared | Modal → submit |
| 6.3 | Check follow-up stage | `customer_not_satisfied` |
| 6.4 | Try close | **BLOCKED** — satisfaction not "Satisfied" or "Not Required" |
| 6.5 | Escalate case | Escalation level increments |
| 6.6 | Follow up service center | New promise recorded |
| 6.7 | Inform customer | Customer updated |

### Pass Criteria
- [ ] Closure blocked while dissatisfaction exists
- [ ] Escalation path works after dissatisfaction
- [ ] Ticket remains in active follow-up state

---

## Test 7 — Appointment Completed

**Setup:** Schedule an appointment.

```python
ticket = frappe.get_doc("HD Ticket", "<ticket-name>")
ticket.followup_stage = "technician_visit_pending"
ticket.save()
```

### Execution Steps

| Step | Action | Expected |
|---|---|---|
| 7.1 | Schedule appointment (Quick Actions) | Modal → enter date, technician |
| 7.2 | Confirm Appointment | `followup_stage = appointment_confirmed` |
| 7.3 | Mark Technician Visited | `followup_stage = technician_visited` |
| 7.4 | Verify Customer After Visit | Enter: Cleared |
| 7.5 | Close ticket | Satisfaction documented, close allowed |

### Pass Criteria
- [ ] Appointment flows: Scheduled → Confirmed → Visited → Verified → Closed
- [ ] Each state change creates [Follow-up] entry
- [ ] Closure only after customer verification

---

## Test 8 — Appointment Missed

**Setup:** Simulate missed appointment.

### Execution Steps

| Step | Action | Expected |
|---|---|---|
| 8.1 | Schedule and confirm appointment | Standard flow |
| 8.2 | Click "Mark Appointment Missed" | Modal opens |
| 8.3 | Enter: reason = Customer unavailable, reschedule = tomorrow | Modal → submit |
| 8.4 | Check escalation | Escalation level incremented |
| 8.5 | Check follow-up date | Updated to reschedule date |
| 8.6 | Inform customer | Customer updated |
| 8.7 | Try close | **BLOCKED** — `appointment_missed` in verification states |

### Pass Criteria
- [ ] Missed appointment creates escalation
- [ ] Reschedule date mandatory
- [ ] Closure blocked while in missed state
- [ ] Customer informed about missed appointment

---

## Cross-Cutting Checks (All Tests)

Run after each test:

```bash
git status --short
grep -R "COLORS\." frontend/src --include="*.vue" || true
grep -R "alert(" frontend/src || true  
grep -R "prompt(" frontend/src || true
```

Expected: clean on all counts.

---

## Test Data Cleanup

```python
# Run after UAT complete
for phone in ["9999990001", "9999990002"]:
    tickets = frappe.get_all("HD Ticket", filters={"phone_1": phone}, pluck="name")
    for t in tickets:
        frappe.delete_doc("HD Ticket", t, ignore_permissions=True, force=True)
    frappe.db.commit()
    print(f"Cleaned {len(tickets)} tickets for {phone}")
```

---

## UAT Sign-off

| Test | Executed By | Date | Result | Notes |
|---|---|---|---|---|
| 1 — Happy Path | | | | |
| 2 — No Call | | | | |
| 3 — No Visit | | | | |
| 4 — Part Required | | | | |
| 5 — ETA Delay | | | | |
| 6 — Not Satisfied | | | | |
| 7 — Appointment OK | | | | |
| 8 — Missed Appt | | | | |

---

Prepared: 2026-06-21
