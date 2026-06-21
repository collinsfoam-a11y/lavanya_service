# H7A — Pilot SOP + Staff Training Guide

## Purpose

This guide prepares Lavanya Service for real showroom pilot usage. It defines daily operating routines, ticket lifecycle SOPs, safety policies, and training checklists for all staff roles.

---

## 1. Staff Roles & Access

| Role | Access Level | Key Pages |
|---|---|---|
| **Front Desk** | New Ticket, Field Mode, Today's Work (limited) | `/new-ticket`, `/field`, `/` |
| **Service Staff** | Today's Work, Tickets, Ticket Detail, WhatsApp Inbox, Customer 360 | `/`, `/tickets`, `/whatsapp`, `/customer-360` |
| **Service Manager** | All pages + Reports + Settings | `/reports`, `/settings`, all staff pages |
| **Owner/Admin** | Full access, safety lock management | All pages, backend settings |

---

## 2. Daily Operating Routine

### Morning Review (All Staff)

1. Open Today's Work (`/`)
2. Check Critical tier first — Overdue Follow-up, No Technician Update, Escalated Cases, Customer Not Informed
3. Check Important tier — Technician Call/Visit Due, Due Today, Satisfaction Pending
4. Use the Reminder Intelligence chips (Promise Breach, Escalated, Overdue, Due Soon) to filter

### Service Staff — Follow-up Routine

1. Click a metric card to scroll to that bucket
2. Open each ticket to review:
   - Next Action bar → Run the recommended action
   - Communication Preview → Queue a dry-run draft if needed
   - Follow-up Tracking → Check satisfaction, part status, financials
   - Activity → Add notes after each action
3. Mark actions complete: Verify Technician Called/Visited, Record SC Follow-up, Inform Customer
4. If no update from technician → Mark No Update (auto-escalates)

### Manager — Review Routine

1. Open Reports (`/reports`)
2. Overview tab: check trend chart, executive summary cards
3. Brand Delay tab: which brands are causing delays
4. Follow-up Quality tab: tickets without follow-up, customer not informed
5. Penalty tab: advisory review only (no live penalty application)
6. Notifications tab: review dry-run drafts, approve/reject
7. Settings: verify safety locks are all active

### End-of-Day

1. Check Today's Work — any overdue items remaining?
2. Verify outbound drafts are reviewed
3. Verify CRM opportunities noted (read-only)
4. Report any master data gaps (missing brand/technician/SC)

---

## 3. Ticket Lifecycle SOP

### New Ticket Intake (Front Desk / Service Staff)

1. Open New Ticket (`/new-ticket`)
2. Enter customer mobile → system auto-looks up:
   - Customer name, address, previous brand/product
   - Previous products with warranty status
3. Click a previous product chip to pre-fill brand, model, serial
4. Fill remaining fields: Complaint Details (required)
5. Check brand metadata: toll-free number, default SLA hours
6. Submit

### Brand Complaint Registration

1. Open ticket from Today's Work or Tickets
2. Click "Register Brand Complaint" in Quick Actions
3. Enter: Brand Ticket Number, Registration Date, Next Follow-up, Service Center
4. Submit → Updates ticket to "Brand Registered"

### Local Technician Service

1. Open Ticket Detail → Technician Assignment section
2. View matching technicians (filtered by product type)
3. Click "Assign" on a technician → Opens Schedule Appointment
4. Set date/time → Submit
5. After visit: Verify Technician Visit from Quick Actions

### In-Showroom Product Receiving

1. Open ticket (Ticket Type: Customer Product at Store)
2. Click "Create Product Receipt" in Quick Actions
3. Enter: Accessories Received, Physical Condition, Product/Brand/Model/Serial
4. Submit → Creates Service Product Receipt
5. Custody actions become available: Send to SC, Returned from SC, Mark Ready for Pickup

### Closure Rules

**Ticket can be closed ONLY when:**
1. Customer satisfaction is "Satisfied" or "Not Required"
2. Customer confirmation is received (or documented non-response)
3. Linked service records are complete (replacement/return/stock/store)
4. Product custody is resolved (if product was received in-store)

**The closure guard section in Ticket Detail shows:**
- Green: "Closure Allowed" — with reason
- Red: "Closure Not Allowed" — with reason explaining what's missing

---

## 4. Safety Policies

### WhatsApp — Draft Only

- Inbound messages are captured read-only
- Outbound messages are drafts ONLY
- Drafts go through: Draft → Manager Reviewed → Approved (Ready)
- "Sent (External)" status is blocked — cannot be set
- No live WhatsApp messages are ever sent from the system

### CRM — Read Only

- CRM relationship card shows: contact, organization, open deals
- Service risk and sales opportunity are computed indicators
- No CRM leads or deals are created
- "Create Opportunity" button is disabled

### ERP — Disabled

- ERP posting is disabled
- Accounting entries are not created
- Penalty amounts are advisory only
- "Penalty apply" is disabled

### Manager-Only Settings

- Settings page shows "Read-only mode" for non-managers
- Safety locks panel shows live state
- Manager edit mode allows saving changes
- Reset to safe defaults always available

---

## 5. Quick Reference — Key Actions

| Action | Where | Who |
|---|---|---|
| Register Brand Complaint | Ticket Detail → Quick Actions | Manager, Coordinator |
| Follow Up Service Center | Ticket Detail → Quick Actions | Manager, Coordinator, Agent |
| Verify Technician Called | Ticket Detail → Follow-up Journey | Manager, Coordinator |
| Verify Technician Visit | Ticket Detail → Follow-up Journey | Manager, Coordinator |
| Record SC Follow-up | Ticket Detail → Follow-up Journey | Manager, Coordinator |
| Inform Customer | Ticket Detail → Follow-up Journey | Manager, Coordinator, Agent |
| Mark No Update | Ticket Detail → Quick Actions | Manager, Coordinator |
| Escalate Case | Ticket Detail → Quick Actions | Manager, Coordinator |
| Record Satisfaction | Ticket Detail → Follow-up Journey | Manager, Coordinator |
| Schedule Appointment | Ticket Detail → Quick Actions | Manager, Coordinator |
| Create Product Receipt | Ticket Detail → Quick Actions | Manager, Coordinator, Front Desk |
| Mark Product Ready | Ticket Detail → Quick Actions | Manager, Coordinator, Front Desk |
| Close Ticket | Ticket Detail → Quick Actions | Manager, Coordinator |
| Queue WhatsApp Draft | Ticket Detail → Communication Preview | Any |
| View Customer 360 | Ticket Detail → Customer section | Any |

---

## 6. Pilot Issue Reporting

### Bug Report
```
Title: [Brief description]
Page: [e.g., /tickets, Ticket Detail]
Steps: [1. 2. 3.]
Expected: [What should happen]
Actual: [What happened]
Screenshot: [Attach if possible]
```

### Missing Master Data
```
Type: [Brand / Service Center / Technician / Product]
Name: [Name missing from system]
Details: [Toll-free, phone, skills, coverage area]
```

### UX Confusion
```
Page: [Location]
Question: [What was confusing]
Suggestion: [How could it be clearer]
```

---

## 7. Training Checklist

### Front Desk
- [ ] Can create new ticket with customer lookup
- [ ] Can use previous product chips for faster intake
- [ ] Can search tickets by phone in Field Mode
- [ ] Understands WhatsApp is draft-only

### Service Staff
- [ ] Can navigate Today's Work with filters
- [ ] Can open ticket drawer and use Next Action bar
- [ ] Can run quick actions (Register Brand, Follow-up SC, etc.)
- [ ] Can view Customer 360 for customer context
- [ ] Understands closure guard rules

### Manager
- [ ] Can view Reports (all 8 tabs)
- [ ] Can review penalty advisory data
- [ ] Can approve/reject WhatsApp drafts
- [ ] Can view CRM relationship context
- [ ] Can access Settings and safety locks
- [ ] Understands auto-closure is disabled

### Owner/Admin
- [ ] Can view executive summary
- [ ] Can verify safety locks
- [ ] Can reset settings to safe defaults
- [ ] Understands system boundaries (no live sends, no ERP, no auto-close)

---

## 8. Rollback / Safety Checklist

### Verify before pilot
- [ ] Settings → Safety Locks: all 5 locks active
- [ ] Settings → CRM: Mode = Disabled or Read Only
- [ ] WhatsApp Inbox → Draft tab: no "Sent (External)" drafts exist
- [ ] Ticket Detail → Closure Guard section visible and active
- [ ] Reports → Penalty tab: "advisory only" banner visible

### If rollback needed
- Settings → Reset to safe defaults
- Verify all safety locks are re-enabled
- Do not manually change `live_send_blocked`, `erp_posting_disabled`, or `penalty_apply_disabled`

### What NOT to enable during pilot
- Live WhatsApp/SMS sending
- CRM lead/deal creation
- ERP posting
- Penalty application
- Automatic ticket closure

---

Prepared: 2026-06-21
