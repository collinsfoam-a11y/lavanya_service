# P2.3 ERPNext Integration Design

## Date
2026-06-20

## Status
Design / Sandbox Only. No ERPNext code has been written. No accounting data has been posted.

---

## 1. Current State

### 1.1 Environment
- **Frappe v15.110.0** with `helpdesk`, `telephony`, and `lavanya_service` apps installed.
- **ERPNext is NOT installed.**
- Only `Address` and `Contact` from Frappe core are available as shared DocTypes.
- Lavanya Service maintains its own data representations in custom DocTypes.

### 1.2 Lavanya Service Data Model (ERP-relevant)
| Lavanya DocType | Role | ERPNext Equivalent |
|---|---|---|
| `Brand Service Master` | Supplier/brand identity | `Supplier` |
| `Lavanya Customer Profile` | Customer identity | `Customer` |
| `HD Ticket` (via helpdesk) | Service ticket | N/A (service-specific) |
| `HD Customer` (via helpdesk) | Helpdesk customer entity | `Customer` |
| `Lavanya Product Item` | Product catalog entry | `Item` |
| `Supplier Payment Block` | Payment hold for supplier | `Payment Request` / `Purchase Invoice` hold |
| `Supplier Penalty Computation` | Computed penalty exposure | `Debit Note` / `Journal Entry` |
| `Supplier Penalty Rule` | Penalty rule definition | N/A (business rule) |
| `Stock Complaint Record` | Stock defect tracking | `Stock Entry` / `Purchase Receipt` |
| `Replacement Record` | Replacement tracking | `Delivery Note` / `Sales Return` |
| `Return Service Record` | Return/refund tracking | `Sales Return` / `Credit Note` |
| `Service Product Receipt` | Product custody receipt | `Stock Entry` |
| `Supplier SLA Definition` | Supplier SLA definitions | N/A (contractual) |

### 1.3 Data Gaps
- No `Company`, `Fiscal Year`, `Account`, `Cost Center` — ERPNext prerequisites.
- No `Warehouse` or `Item Group` — required for inventory transactions.
- No `Supplier Group` or `Customer Group` — required for party master creation.
- No `Price List` or `UOM` — required for transaction line items.

---

## 2. Integration Architecture

### 2.1 Prerequisite: ERPNext Installation
ERPNext must be installed and configured before any integration code is written.
- Install `erpnext` app: `bench get-app erpnext --branch version-15`
- Run `bench --site lavanya-dev.localhost install-app erpnext`
- Configure Company, Chart of Accounts, Fiscal Year, Warehouses.

### 2.2 Integration Modes

| Mode | Description | Trigger | Example |
|---|---|---|---|
| **Read-only lookup** | Look up ERP data for display only. No writes. | SPA page load | Show open invoices for customer. |
| **Draft creation** | Create ERPNext document in Draft status. | Manager action | Create Draft Purchase Invoice. |
| **Manager-approved posting** | Submit ERPNext document after manager approval. | Approval workflow | Submit Debit Note for penalty. |
| **Never auto-post** | Fully blocked. Must be manual. | N/A | Automatic Journal Entry. |

### 2.3 Layered Implementation Plan
```
Phase A: ERPNext installation + read-only lookups         [not started]
Phase B: master data sync (Customer, Supplier, Item)      [not started]
Phase C: draft creation with approval gates              [not started]
Phase D: manager-approved posting                        [not started]
```

---

## 3. Supplier Penalty Accounting Path

### 3.1 Current State (P2.1)
- `Supplier Penalty Rule` and `Supplier Penalty Computation` exist.
- Computation produces advisory amounts only: `final_penalty_amount`.
- Approval workflow: Draft → Manager Review → Approved/Waived/Rejected.
- No ledger mutation. No ERP posting.

### 3.2 Future Accounting Path (Design Only)

```
Supplier Penalty Computation (Approved)
    |
    |--- Manager clicks "Post to ERP"
    |       |
    |       v
    |   Create Draft Debit Note (Purchase Return) against Supplier
    |       |   - reference: Supplier Payment Block
    |       |   - amount: final_penalty_amount
    |       |   - narration: calculation_narration
    |       |
    |       v
    |   Manager Reviews Draft Debit Note
    |       |
    |       |--- If correct: Submit Debit Note → GL Impact
    |       |--- If incorrect: Cancel Debit Note, return to Manager Review
    |
    v
   Penalty Computation status → Applied
```

#### Debit Note Mapping

| Debit Note Field | Source |
|---|---|
| `supplier` | `Supplier Penalty Computation.brand` → lookup ERPNext `Supplier` |
| `company` | Site default company |
| `posting_date` | `Supplier Penalty Computation.approved_at` |
| `items[0].item_code` | "Penalty Service Item" (configurable default) |
| `items[0].qty` | 1 |
| `items[0].rate` | `Supplier Penalty Computation.final_penalty_amount` |
| `items[0].warehouse` | Default warehouse |
| `reference_doctype` | `Supplier Penalty Computation` |
| `reference_name` | `Supplier Penalty Computation.name` |

#### Safety Rules
- Only computable from **Approved** status.
- One Debit Note per computation (idempotency key: `computation.name`).
- Manager must confirm in a prompt: "Post Debit Note for Rs.{amount} against {supplier}?"
- Posting triggers audit log entry.
- Once posted, computation status → **Applied** (immutable).

---

## 4. Stock Complaint / Credit Note Path

### 4.1 Current State
- `Stock Complaint Record` tracks: supplier_notified_at, credit_note_received_at, credit_note_amount.
- `Supplier Payment Block` tracks: block_status, block_reason.
- No ERP posting.

### 4.2 Future Credit Note Path

```
Stock Complaint Record
    |--- credit_note_received_at is set
    |       |
    |       v
    |   Auto-create Draft Purchase Return (Credit Note)
    |       |   - supplier: complaint supplier
    |       |   - amount: credit_note_amount
    |       |   - reference: ticket.name
    |       |
    |       v
    |   Manager reviews and submits
    |
    v
   Supplier Payment Block → Released (if all complaints resolved)
```

---

## 5. Customer / Service Integration

### 5.1 Customer Mapping
```
Lavanya Customer Profile / HD Customer
    |
    |--- ERPNext Customer (create if not exists)
    |       |   - customer_name: profile.customer_name
    |       |   - customer_group: "Individual" (default)
    |       |   - territory: "All Territories" (default)
    |
    v
   Link HD Ticket.customer → ERPNext Customer
```

### 5.2 Product/Item Mapping
```
Lavanya Product Item
    |
    |--- ERPNext Item (create if not exists)
    |       |   - item_code: product_item.item_code
    |       |   - item_name: product_item.item_name
    |       |   - item_group: product_item.category → ERPNext Item Group
    |
    v
   Link HD Ticket.product_type → ERPNext Item (lookup only)
```

### 5.3 Invoice Lookup
- Customer provides invoice number during complaint registration.
- Look up `Sales Invoice` by `name` or by `customer` + `posting_date` range.
- Display invoice status, amount, item details in Ticket Detail.
- Read-only. No mutation.

---

## 6. Integration Boundaries Summary

| Action | Classification | Reason |
|---|---|---|
| Look up Customer by mobile | Read-only lookup | SPA display only |
| Look up open Sales Invoices | Read-only lookup | SPA display only |
| Look up Supplier by brand | Read-only lookup | Reference data |
| Create Draft Purchase Return | Draft creation | Manager action |
| Submit Debit Note for penalty | Manager-approved posting | Requires approval |
| Submit Purchase Return for credit note | Manager-approved posting | Requires approval |
| Create Customer in ERPNext | Draft creation | Auto-created from profile sync |
| Create Supplier in ERPNext | Draft creation | Auto-created from brand master |
| Create Item in ERPNext | Draft creation | Auto-created from product catalog |
| Auto-post Journal Entry | Never auto-post | High-risk accounting |
| Auto-submit any invoice | Never auto-post | Requires human review |

---

## 7. Implementation Prerequisites

Before any ERPNext integration code is written:
1. ERPNext app installed and configured.
2. Company, Chart of Accounts, Fiscal Year set up.
3. Default Warehouse, Item Group, Customer Group, Supplier Group defined.
4. "Penalty Service Item" and "Credit Note Service Item" default items created.
5. `Lavanya Manager` role granted ERPNext posting permissions.
6. Audit log Doctype (`Lavanya ERP Integration Log`) created.
7. Sandbox/test site for integration testing.
