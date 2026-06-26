# Graph Report - lavanya_service  (2026-06-26)

## Corpus Check
- 212 files · ~57,928 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1243 nodes · 1703 edges · 167 communities (139 shown, 28 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 88 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]
- [[_COMMUNITY_Community 76|Community 76]]
- [[_COMMUNITY_Community 84|Community 84]]
- [[_COMMUNITY_Community 85|Community 85]]
- [[_COMMUNITY_Community 86|Community 86]]
- [[_COMMUNITY_Community 87|Community 87]]
- [[_COMMUNITY_Community 88|Community 88]]
- [[_COMMUNITY_Community 89|Community 89]]
- [[_COMMUNITY_Community 90|Community 90]]
- [[_COMMUNITY_Community 92|Community 92]]
- [[_COMMUNITY_Community 93|Community 93]]
- [[_COMMUNITY_Community 94|Community 94]]
- [[_COMMUNITY_Community 95|Community 95]]
- [[_COMMUNITY_Community 98|Community 98]]
- [[_COMMUNITY_Community 99|Community 99]]
- [[_COMMUNITY_Community 100|Community 100]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 103|Community 103]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY_Community 105|Community 105]]
- [[_COMMUNITY_Community 106|Community 106]]
- [[_COMMUNITY_Community 107|Community 107]]
- [[_COMMUNITY_Community 111|Community 111]]
- [[_COMMUNITY_Community 118|Community 118]]
- [[_COMMUNITY_Community 120|Community 120]]
- [[_COMMUNITY_Community 122|Community 122]]
- [[_COMMUNITY_Community 127|Community 127]]

## God Nodes (most connected - your core abstractions)
1. `push()` - 23 edges
2. `forEach()` - 16 edges
3. `qe()` - 15 edges
4. `fa()` - 15 edges
5. `fe()` - 14 edges
6. `fl()` - 14 edges
7. `Hn` - 13 edges
8. `ut()` - 13 edges
9. `bi()` - 13 edges
10. `LavanyaReplacementRecovery` - 12 edges

## Surprising Connections (you probably didn't know these)
- `createTicket()` --calls--> `frappeCall()`  [EXTRACTED]
  lavanya_service/public/js/composables/useTickets.js → lavanya_service/public/js/composables/frappe.js
- `searchCustomer()` --calls--> `frappeCall()`  [EXTRACTED]
  lavanya_service/public/js/composables/useTickets.js → lavanya_service/public/js/composables/frappe.js
- `genDraft()` --calls--> `frappeCall()`  [EXTRACTED]
  lavanya_service/public/js/pages/TicketDetail.vue → lavanya_service/public/js/composables/frappe.js
- `get_ticket()` --calls--> `compute_badge()`  [EXTRACTED]
  lavanya_service/api/tickets.py → lavanya_service/utils/quality.py
- `get_ticket()` --calls--> `get_next_action()`  [EXTRACTED]
  lavanya_service/api/tickets.py → lavanya_service/utils/quality.py

## Import Cycles
- None detected.

## Communities (167 total, 28 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.07
Nodes (31): At(), el(), entries(), eo(), every(), filter(), find(), findIndex() (+23 more)

### Community 1 - "Community 1"
Cohesion: 0.06
Nodes (36): close_ticket(), _create_customer(), create_ticket(), escalate_ticket(), get_list(), get_ticket(), Create a new Lavanya Ticket from the 4-step wizard., Create or update a Lavanya Customer Product record on ticket creation. (+28 more)

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (13): ci, en(), Gn(), Hn, jn(), jo(), mo(), set() (+5 more)

### Community 3 - "Community 3"
Cohesion: 0.06
Nodes (29): canSaveFu, closeData, closureAllowed, closureBlockReason, draftLoading, dueLabel, escalateReason, fu (+21 more)

### Community 4 - "Community 4"
Cohesion: 0.12
Nodes (23): ai(), Ay(), bi(), cn(), Cs(), defineProperty(), dn(), E() (+15 more)

### Community 5 - "Community 5"
Cohesion: 0.13
Nodes (20): Ba(), beforeUpdate(), Bo(), Co(), created(), fi(), gt(), Hs() (+12 more)

### Community 6 - "Community 6"
Cohesion: 0.12
Nodes (10): LavanyaReplacementRecovery, Validate cancellation is allowed, Calculate financial difference between old and replacement items, Validate all required linked documents exist, Validate status transitions, Validate fields based on replacement type, Calculate financial difference for cross-SKU replacements, Validate closure rules - all four lifecycle checks required (+2 more)

### Community 7 - "Community 7"
Cohesion: 0.13
Nodes (10): LavanyaServiceTicketExtension, Validate customer number is 10 digits, Validate PIN code is 6 digits, Validate serial number format, Validate payment fields when payment received, Validate token fields when token issued, Validate status transitions, Calculate resolution time when resolved (+2 more)

### Community 8 - "Community 8"
Cohesion: 0.12
Nodes (10): LavanyaStockComplaint, Validate cancellation is allowed, Validate all required linked documents exist, Validate status transitions, Validate required fields based on damage type, Validate serial number is required for serialized items, Validate quarantine warehouse rules, Validate closure rules (+2 more)

### Community 9 - "Community 9"
Cohesion: 0.12
Nodes (10): LavanyaSupplierClaim, Validate cancellation is allowed, Update follow-up tracking, Validate all required linked documents exist, Validate status transitions, Validate financial fields based on settlement type, Validate claim reference or manager override, Validate closure rules (+2 more)

### Community 10 - "Community 10"
Cohesion: 0.10
Nodes (9): Test invalid status transition is blocked, Test valid status transition works, Test financial difference is calculated for Cross SKU, Test creating a replacement recovery, Test Cross SKU requires old and replacement item values, Test Credit Instead requires credit note, Test Closed status requires all four lifecycle checks, Test Closed status requires closure date (+1 more)

### Community 11 - "Community 11"
Cohesion: 0.10
Nodes (9): Test Written Off status requires manager approval, Test invalid status transition is blocked, Test valid status transition works, Test creating a stock complaint, Test Transit Damage requires LR number, Test Missing Accessory requires details, Test Quarantined status requires quarantine warehouse, Test Saleable status requires condition decision (+1 more)

### Community 12 - "Community 12"
Cohesion: 0.10
Nodes (9): Test invalid status transition is blocked, Test valid status transition works, Test negative claim amount is blocked, Test creating a supplier claim, Test Claim Registered status requires reference or override, Test Credit Note settlement requires expected amount, Test Replacement settlement requires expected item, Test Settled status requires supplier closure date (+1 more)

### Community 13 - "Community 13"
Cohesion: 0.14
Nodes (17): ca(), ct(), fn(), m(), pa(), pop(), push(), Q() (+9 more)

### Community 14 - "Community 14"
Cohesion: 0.11
Nodes (8): Test resolution time calculation, Test creating a ticket extension, Test mobile number validation, Test PIN code validation, Test payment fields validation, Test token fields validation, Test status transitions, TestLavanyaServiceTicketExtension

### Community 15 - "Community 15"
Cohesion: 0.11
Nodes (8): Test check-out must be after check-in, Test creating a service visit, Test completed visit requires work done, Test failed visit requires failed reason, Test customer rating must be 1-5, Test valid status transition works, Test invalid status transition is blocked, TestLavanyaServiceVisit

### Community 16 - "Community 16"
Cohesion: 0.11
Nodes (8): Test approval sets approval date, Test used quantity cannot exceed issued, Test creating a spare request, Test used + returned cannot exceed issued, Test chargeable spare requires customer payable amount, Test valid status transition works, Test invalid status transition is blocked, TestLavanyaSpareRequest

### Community 17 - "Community 17"
Cohesion: 0.13
Nodes (12): an(), Go(), has(), indexOf(), lastIndexOf(), Le(), Na(), nl (+4 more)

### Community 18 - "Community 18"
Cohesion: 0.17
Nodes (14): cl(), Dt(), Ei(), Et(), fe(), Fs(), ii(), qe() (+6 more)

### Community 19 - "Community 19"
Cohesion: 0.12
Nodes (7): Test Return to Saleable Stock sets target warehouse, Test creating a stock condition decision, Test Write Off decision requires approval, Test Scrap decision requires target warehouse, Test valid status transition works, Test invalid status transition is blocked, TestLavanyaStockConditionDecision

### Community 20 - "Community 20"
Cohesion: 0.18
Nodes (7): LavanyaClosureVerification, Validate customer exists in ERPNext, Validate verified_by is different from ticket creator, Validate checklist items based on status, Validate status transitions, Update linked ticket and group when status changes, Update parent group status based on closure verification

### Community 21 - "Community 21"
Cohesion: 0.18
Nodes (7): LavanyaCustomerCommunicationLog, Validate customer exists in ERPNext, Validate communication type specific fields, Validate mobile number is 10 digits, Validate call duration is positive, Validate WhatsApp message ID if provided, Update ticket communication log and customer informed flag

### Community 22 - "Community 22"
Cohesion: 0.19
Nodes (7): LavanyaServiceVisit, Validate all required linked documents exist, Validate status transitions, Validate completion rules, Validate failed visit rules, Validate customer rating is 1-5, Validate check-in and check-out times

### Community 23 - "Community 23"
Cohesion: 0.16
Nodes (13): _assert_live_allowed(), _classify_intent(), _classify_message(), generate_draft(), get_inbox(), log_customer_reply(), mark_reviewed(), Generate a WhatsApp message draft — always safe, never sends.     _assert_dry_ru (+5 more)

### Community 24 - "Community 24"
Cohesion: 0.14
Nodes (14): aa(), Bs(), dl(), Es(), gi(), _i(), lr(), mr() (+6 more)

### Community 25 - "Community 25"
Cohesion: 0.24
Nodes (14): As(), hi(), It(), join(), ka(), lo(), mi(), Ne() (+6 more)

### Community 26 - "Community 26"
Cohesion: 0.24
Nodes (13): concat(), fa(), fl(), G(), Je(), jt(), ma(), mn() (+5 more)

### Community 27 - "Community 27"
Cohesion: 0.14
Nodes (13): dependencies, vue, vue-router, devDependencies, vite, @vitejs/plugin-vue, name, private (+5 more)

### Community 28 - "Community 28"
Cohesion: 0.14
Nodes (6): Test creating a service site, Test PIN code validation, Test contact number validation, Test GPS coordinates validation, Test valid GPS coordinates, TestLavanyaCustomerServiceSite

### Community 29 - "Community 29"
Cohesion: 0.14
Nodes (6): Test creating an installation job, Test paid installation requires payment on close, Test valid status transition works, Test invalid status transition is blocked, Test failed visit requires visit status, TestLavanyaInstallationJob

### Community 30 - "Community 30"
Cohesion: 0.21
Nodes (6): LavanyaCustomerProduct, Validate customer exists in ERPNext, Validate serial number format if provided, Validate warranty fields, Prevent duplicate active Customer Product for same serial, Update tracking fields

### Community 31 - "Community 31"
Cohesion: 0.19
Nodes (6): LavanyaServiceCaseGroup, Validate customer exists in ERPNext, Validate mobile number is 10 digits, Validate status transitions, Auto-set resolution date when status changes to All Closed, Update linked tickets when group status changes

### Community 32 - "Community 32"
Cohesion: 0.22
Nodes (6): LavanyaSpareRequest, Validate all required linked documents exist, Validate status transitions, Validate quantity rules - used + returned cannot exceed issued, Validate chargeable spare rules, Validate approval rules

### Community 33 - "Community 33"
Cohesion: 0.15
Nodes (6): Test getting settings, Test auto close days validation, Test escalation days validation, Test reopen days validation, Test get warehouse method, TestLavanyaServiceSettings

### Community 34 - "Community 34"
Cohesion: 0.17
Nodes (5): Test creating a communication log, Test WhatsApp requires recipient mobile, Test Call requires call duration, Test mobile number validation, TestLavanyaCustomerCommunicationLog

### Community 35 - "Community 35"
Cohesion: 0.17
Nodes (5): Test creating a contact point, Test mobile number validation, Test email validation, Test only one primary contact per customer, TestLavanyaCustomerContactPoint

### Community 36 - "Community 36"
Cohesion: 0.17
Nodes (5): Test creating a customer product, Test serial number format validation, Test warranty expiry required when type set, Test duplicate active serial is blocked, TestLavanyaCustomerProduct

### Community 37 - "Community 37"
Cohesion: 0.17
Nodes (5): Test creating a service case group, Test mobile number validation, Test status transitions, Test auto-set closed date, TestLavanyaServiceCaseGroup

### Community 38 - "Community 38"
Cohesion: 0.18
Nodes (10): 1. Install the Frappe app, 2. Build the Vue bundle, 3. Register assets with Frappe, 4. Verify in browser, Development mode (hot reload), Environment checklist after install, Lavanya Service — Build & Deploy, Page routing (+2 more)

### Community 39 - "Community 39"
Cohesion: 0.22
Nodes (5): frappeCall(), createTicket(), searchCustomer(), useTicket(), genDraft()

### Community 40 - "Community 40"
Cohesion: 0.25
Nodes (9): Ds(), Ia(), kn(), _l(), ll, ml(), sa(), Ul() (+1 more)

### Community 41 - "Community 41"
Cohesion: 0.25
Nodes (5): LavanyaInstallationJob, Validate all required linked documents exist, Validate status transitions, Validate completion rules, Validate payment rules for paid installations

### Community 42 - "Community 42"
Cohesion: 0.25
Nodes (5): LavanyaStockConditionDecision, Validate all required linked documents exist, Validate status transitions, Validate approval rules based on decision type, Validate warehouse requirements based on decision type

### Community 43 - "Community 43"
Cohesion: 0.18
Nodes (6): botModes, integrations, isOwner, quickLocks, safetyLocks, tabs

### Community 44 - "Community 44"
Cohesion: 0.18
Nodes (10): API Methods (all whitelisted), App Structure, DocTypes, Frappe Pages → Vue Mapping, Lavanya Service — Frappe App, Quick Install, Roles, Safety Rules (hardcoded defaults) (+2 more)

### Community 45 - "Community 45"
Cohesion: 0.18
Nodes (10): Critical UAT Checks Passed, Integration Test Status, Lavanya Service App — UAT Case Log, Next Steps, Phase 7A — Real Case UAT, Test Case Creation, Test Progress, UAT Case Summary (+2 more)

### Community 46 - "Community 46"
Cohesion: 0.31
Nodes (9): _brand_delay_scores(), export_report(), get_manager_dashboard(), _period_start(), Generate and return a CSV download URL. FIXED: correct file_manager import., Return all data for Manager Dashboard page., _safety_lock_status(), _satisfaction_rate() (+1 more)

### Community 47 - "Community 47"
Cohesion: 0.20
Nodes (6): formattedTimer, inputRefs, maskedPhone, showError, timeLeft, verified

### Community 48 - "Community 48"
Cohesion: 0.20
Nodes (6): AVATAR_COLORS, avatarBg, avatarColor, colorIdx, initials, props

### Community 49 - "Community 49"
Cohesion: 0.29
Nodes (6): navigate(), showAlert(), showError(), submitClose(), submitEscalate(), submitFollowup()

### Community 50 - "Community 50"
Cohesion: 0.38
Nodes (10): Ae(), fr(), G1(), H1(), K1(), pr(), setup(), U() (+2 more)

### Community 51 - "Community 51"
Cohesion: 0.22
Nodes (4): INSTANCES, mountPage(), PAGE_MAP, unmount()

### Community 52 - "Community 52"
Cohesion: 0.20
Nodes (4): Test creating a brand service policy, Test that only one policy per brand is allowed, Test getting SLA for a specific product category, TestLavanyaBrandServicePolicy

### Community 53 - "Community 53"
Cohesion: 0.36
Nodes (8): accounting_closed(), all_documents_attached(), all_photos_uploaded(), customer_satisfied(), stock_accounted(), supplier_claim_handled(), update_status_from_checklist(), warranty_documented()

### Community 54 - "Community 54"
Cohesion: 0.20
Nodes (4): Test creating a closure verification, Test Verified status requires all checklist items, Test status transitions, TestLavanyaClosureVerification

### Community 55 - "Community 55"
Cohesion: 0.33
Nodes (8): _critical_label(), get_sidebar_counts(), get_todays_work(), _important_label(), _is_critical(), _is_important(), Return bucketed tickets for Today's Work command center.     Groups: critical, i, Return counts for sidebar badges.

### Community 56 - "Community 56"
Cohesion: 0.31
Nodes (8): generate_uat_cases(), generate_uat_report(), import_uat_cases_for_phase_7a(), Phase 7A UAT: Import 30 real Lavanya cases with sanitized data     Should be run, Generate 30 UAT test cases for Lavanya Service, Generate UAT test report, Update UAT_CASE_LOG.md with summary, update_uat_case_log()

### Community 57 - "Community 57"
Cohesion: 0.22
Nodes (5): Document, LavanyaAccessoryItem, LavanyaAccessoryTemplateItem, LavanyaPhotoLog, LavanyaSpareRequestItem

### Community 58 - "Community 58"
Cohesion: 0.28
Nodes (4): LavanyaBrandServicePolicy, Validate required linked documents exist, Ensure one policy per brand, Get SLA and rules for a specific product category

### Community 59 - "Community 59"
Cohesion: 0.31
Nodes (4): LavanyaCustomerContactPoint, Validate mobile number is 10 digits, Validate email format, Validate only one primary contact per customer

### Community 60 - "Community 60"
Cohesion: 0.31
Nodes (4): LavanyaCustomerServiceSite, Validate PIN code is 6 digits, Validate contact number is 10 digits, Validate GPS coordinates format

### Community 61 - "Community 61"
Cohesion: 0.22
Nodes (4): Test creating a product service policy, Test that only one policy per category is allowed, Test getting workflow requirements, TestLavanyaProductServicePolicy

### Community 63 - "Community 63"
Cohesion: 0.32
Nodes (8): Al(), bl(), hl(), includes(), mt(), Os(), xi(), Xo()

### Community 65 - "Community 65"
Cohesion: 0.25
Nodes (5): COLORS, GROUPS, qFilters, statStrip, visibleGroups

### Community 66 - "Community 66"
Cohesion: 0.29
Nodes (6): get_settings(), Save Lavanya Settings — manager/owner only., Return current Lavanya Settings (safe fields only)., Reset all settings to safe defaults — owner only., reset_defaults(), save_settings()

### Community 67 - "Community 67"
Cohesion: 0.33
Nodes (3): Enforce: every service center follow-up log entry must record     whether the cu, validate_customer_informed(), LavanyaFollowupLog

### Community 68 - "Community 68"
Cohesion: 0.29
Nodes (3): FrappeTestCase, TestLavanyaAccessoryItem, TestLavanyaAccessoryTemplateItem

### Community 69 - "Community 69"
Cohesion: 0.33
Nodes (3): LavanyaProductServicePolicy, Ensure one policy per product category, Return workflow requirements for this product category

### Community 74 - "Community 74"
Cohesion: 0.33
Nodes (3): bW, chartData, COLORS

### Community 75 - "Community 75"
Cohesion: 0.60
Nodes (4): after_install(), create_default_settings(), create_roles(), Run once after bench install-app lavanya_service

### Community 76 - "Community 76"
Cohesion: 0.40
Nodes (4): auto_escalate_overdue(), check_sla_breaches(), Escalate tickets overdue by configured days, Flag tickets whose SLA due date has passed

## Knowledge Gaps
- **93 isolated node(s):** `LavanyaBrandMaster`, `LavanyaServiceCenter`, `LavanyaTechnician`, `LavanyaWhatsappMessage`, `inputRefs` (+88 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TestLavanyaServiceVisit` connect `Community 15` to `Community 68`?**
  _High betweenness centrality (0.013) - this node is a cross-community bridge._
- **Why does `TestLavanyaServiceSettings` connect `Community 33` to `Community 68`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Why does `TestLavanyaServiceTicketExtension` connect `Community 14` to `Community 68`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `qe()` (e.g. with `Et()` and `It()`) actually correct?**
  _`qe()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Phase 7A UAT: Import 30 real Lavanya cases with sanitized data     Should be run`, `Generate 30 UAT test cases for Lavanya Service`, `Generate UAT test report` to the rest of the system?**
  _332 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.06666666666666667 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.06387921022067364 - nodes in this community are weakly interconnected._