# P2.3 ERPNext Mapping Matrix

## Date
2026-06-20

## Format
For each Lavanya Service DocType, this document identifies the corresponding ERPNext DocType, mapping strategy, integration mode, and any gaps.

---

## Master Data

| Lavanya DocType | Lavanya Key Field | ERPNext DocType | ERPNext Key Field | Integration Mode | Notes |
|---|---|---|---|---|---|
| `Brand Service Master` | `brand_name` | `Supplier` | `supplier_name` | Draft creation | Auto-create during install/sync. Map brand_name → supplier_name, toll_free_number → mobile_no, portal_url → website. |
| `Lavanya Customer Profile` | `customer_name` | `Customer` | `customer_name` | Draft creation | Sync primary_mobile → mobile_no. Use HD Customer or Lavanya Customer Profile as source. |
| `HD Customer` | `customer_name` | `Customer` | `customer_name` | Draft creation | Fallback if Lavanya Customer Profile not available. |
| `Lavanya Product Item` | `item_name` | `Item` | `item_name` | Draft creation | Map category → Item Group, brand → Supplier reference. |
| `Service Center Master` | `service_center_name` | `Supplier` | `supplier_name` | Draft creation | Separate supplier group "Service Center". |
| `Local Technician Master` | `technician_name` | `Supplier` | `supplier_name` | Read-only lookup | Optional; may use expense claims instead. |

---

## Transactional Data

| Lavanya DocType | Lavanya Key Field | ERPNext DocType | ERPNext Key Field | Integration Mode | Trigger | Notes |
|---|---|---|---|---|---|---|
| `Supplier Penalty Computation` | `name` | `Purchase Invoice` (Debit Note) | `name` | Manager-approved posting | Status = Approved + Manager action | One Debit Note per computation. Amount = final_penalty_amount. |
| `Stock Complaint Record` | `name` | `Purchase Receipt` / `Purchase Return` | `name` | Manager-approved posting | credit_note_received_at is set | Auto-draft. Manager reviews. |
| `Replacement Record` | `name` | `Delivery Note` + `Sales Return` | `name` | Manager-approved posting | new_unit_dispatched_at set | Two-step: DN for replacement, SR for old unit. |
| `Return Service Record` | `name` | `Sales Return` / `Credit Note` | `name` | Manager-approved posting | refund_status = Processed | Credit Note for refund amount. |
| `Store Service Record` | `name` | `Stock Entry` (Material Transfer) | `name` | Draft creation | product_received_at is set | Track product movement to/from service center. |
| `Supplier Payment Block` | `name` | `Payment Request` or Invoice hold | `name` | Draft creation | block_status = Active | Create Payment Request with hold flag. Release when resolved. |
| `Product Receipt` | `name` | `Stock Entry` (Material Receipt) | `name` | Draft creation | Receipt created | Track inbound product custody. |
| `Demo Installation Record` | `name` | N/A | N/A | Read-only lookup | N/A | No ERP posting needed. Service-only record. |

---

## Lookup-Only Mappings

| Lavanya Data Need | ERPNext Source | Lookup Key | Use Case |
|---|---|---|---|
| Customer invoice history | `Sales Invoice` | Customer name or mobile | Ticket Detail: show past invoices |
| Customer warranty status | `Serial No` | Serial number entered by customer | Ticket Detail: verify warranty |
| Supplier open balance | `Supplier` → `GL Entry` or `Accounts Receivable` | Supplier name | Payment block: check existing dues |
| Item details / price | `Item` | Item code from product catalog | Ticket Detail: product info |

---

## GL Impact Summary (Future Only)

| Business Event | Debit Account | Credit Account | Amount Source |
|---|---|---|---|
| Penalty Debit Note posted | Supplier (Creditors) | Penalty Income / Cost Recovery | penalty_computation.final_penalty_amount |
| Credit Note for stock complaint | Supplier (Creditors) | Stock Received But Not Billed | stock_complaint.credit_note_amount |
| Replacement delivery | Cost of Goods Sold | Stock Asset | Replacement item cost |
| Refund credit note | Customer (Debtors) | Bank / Cash | return_service.customer_refund_amount |

---

## Gap Analysis

| Gap | Severity | Resolution |
|---|---|---|
| No ERPNext installed | Critical | Install ERPNext app first |
| No Chart of Accounts | Critical | Configure during ERPNext setup |
| No Supplier Group mapping | High | Create "Brand Supplier" and "Service Center" groups |
| No Item Group mapping | High | Create "Service Item" and "Penalty Item" groups |
| Brand names may not match supplier names | Medium | Maintain mapping table or enforce naming convention |
| HD Customer vs Lavanya Customer Profile duality | Medium | Designate single source of truth for customer sync |
| No UOM defined | Medium | Create "Nos" (Numbers) UOM and "Service" UOM |
| Serial Number tracking missing for items | Low | Optional; useful for warranty verification |
