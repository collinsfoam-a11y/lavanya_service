# P2.1 Supplier Penalty Rules

## Operational Boundary
- Penalty is advisory/operational only.
- No ERP posting happens in P2.1.
- No accounting entry is created in P2.1.
- No WhatsApp/SMS is sent in P2.1.
- Manager approval/waiver/rejection requires narration or reason.
- ERPNext/accounting application is a future phase and must not be inferred from an approved penalty computation.

## Rule Selection
- Only active `Supplier Penalty Rule` records are considered.
- Optional filters narrow applicability by brand, supplier, service flow type, and validity dates.
- More specific matches score higher than generic rules.
- If no applicable rule exists, computation creates a Manager Review record with zero penalty.

## Grace Period
- `grace_days` are subtracted from total breach days.
- If chargeable days are zero or negative, no computation record is created.
- This prevents noise from cases still within supplier grace.

## Penalty Types
- `Fixed Amount`: applies fixed amount after grace.
- `Per Day`: `per_day_amount * chargeable_days`.
- `Percentage of Claim`: `base_amount * percentage_rate / 100`.
- `Percentage of Invoice`: `base_amount * percentage_rate / 100`.
- `Manual Review Only`: zero amount with manager-review flag.

## Caps
- `max_penalty_amount` caps the computed amount when greater than zero.
- Final amount is rounded to two decimals.

## Statuses
- `Computed`: normal advisory computation pending manager action.
- `Manager Review`: no rule or manual review path.
- `Approved`: manager accepted the advisory amount.
- `Waived`: manager waived the amount; final amount is set to zero.
- `Rejected`: manager rejected the advisory computation.
- `Applied` remains reserved; P2.1 does not post accounting entries.

## Controls
- Existing active computations prevent duplicate active records for the same ticket and breach type.
- Approved, waived, rejected, cancelled, and applied records are not considered active duplicates.
- Approval, waiver, and rejection require a narration/reason for auditability.
- Approval, waiver, and rejection are management decisions on the advisory computation only; they do not create payment deductions, supplier ledger entries, invoices, journal entries, WhatsApp messages, or SMS messages.
