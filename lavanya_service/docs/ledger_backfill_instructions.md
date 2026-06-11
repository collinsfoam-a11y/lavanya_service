# Ledger Backfill — Instructions (Template Only, No Import Performed)

Use `ledger_backfill_template.csv` to collect legacy/open complaints from the
physical register or old ERP before going live. Import happens via the Frappe
Data Import tool against **HD Ticket** — only after UAT sign-off.

## Rules for filling the CSV

1. One row per open complaint. Do NOT backfill already-closed history in
   Phase 1 (closed history stays in the old register).
2. `phone_1` must be a 10-digit number (no +91, no spaces). The system
   normalizes and then REJECTS anything that is not 10 digits.
3. `product_type` must be one of: AC, Refrigerator, Washing Machine, Mixer,
   Induction Cooker, Chimney, Hob, Gas Stove, TV, Water Purifier, Other.
4. `brand` must exactly match a Brand Service Master name
   (LG, Samsung, Whirlpool, Voltas, Preethi, Bajaj, Prestige, Crompton, Kent, Faber).
5. `ticket_type` must be one of the 7 Lavanya ticket types.
6. `status` rules (validation will enforce these on import):
   - `Brand Registered` rows MUST have `brand_ticket_number` and `registration_date`.
   - Rows in Registration Pending / Brand Registered / In Progress / Waiting on
     Customer / Waiting on Part / Approval / Ready for Pickup MUST have
     `pending_reason` and `next_follow_up_date`.
   - Do not import rows with status `Closed` (closure evidence fields would be
     required); land legacy nearly-done items as `Resolved` instead.
7. `serial_no` is mandatory for Replacement / DOA and Customer Product at Store rows.
8. Dates use YYYY-MM-DD format.

## Import procedure (when approved)

1. Desk > Data Import > New: Document Type = HD Ticket, Import Type = Insert.
2. Upload the CSV; map columns 1:1 (fieldnames already match).
3. Run with a 5-row pilot file first; verify tickets, then run the full file.
4. After import, spot-check the saved views and the reminder scan output.
