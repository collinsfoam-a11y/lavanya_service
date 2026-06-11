# Phase 1L-9 — Native Helpdesk Role Mapping Decision

Status: RECOMMENDED, pending business sign-off before first real user is onboarded.

## Verified Facts (lavanya-dev.localhost, frappe 15.110.0, helpdesk 1.25.1)

1. Helpdesk ships standard DocPerms on HD Ticket for `Agent`, `Agent Manager`,
   `System Manager`, and a broad `All` (read/write/create).
2. The Lavanya app defines Custom DocPerm rows for HD Ticket (5 Lavanya roles at
   permlevels 0/1/2 plus a restricted `All` read-only row). In Frappe, when Custom
   DocPerm rows exist for a DocType, they REPLACE the standard DocPerm set entirely.
3. Therefore native `Agent` / `Agent Manager` currently have NO document-level
   permission on HD Ticket. Doc-level access on HD Ticket is governed exclusively
   by the Lavanya Custom DocPerm set.
4. The Helpdesk agent portal additionally gates functionality on the existence of
   an `HD Agent` record for the user (independent of DocPerms).

## Decision (Option 1 — Compose native portal roles with Lavanya doc roles)

Each staff user gets:

| Purpose                          | What to assign                                  |
| -------------------------------- | ----------------------------------------------- |
| Agent portal access              | `HD Agent` record + native `Agent` role         |
| Manager portal features          | native `Agent Manager` role (managers only)     |
| Document-level permissions       | exactly ONE Lavanya role                        |

Mapping:

| Person type          | Native roles            | Lavanya role                  |
| -------------------- | ----------------------- | ----------------------------- |
| Store manager        | Agent, Agent Manager    | Lavanya Manager               |
| Helpdesk staff       | Agent                   | Lavanya Helpdesk Agent        |
| Front desk           | Agent                   | Lavanya Front Desk            |
| Service coordinator  | Agent                   | Lavanya Service Coordinator   |
| Read-only stakeholder| (none)                  | Lavanya Viewer                |

Rationale:
- Native `Agent` is required for the portal UX but grants no HD Ticket DocPerm
  (see fact 3), so the Lavanya permission model stays authoritative.
- Field-level restrictions (permlevels 1/2) continue to apply: only the Lavanya
  roles granted permlevel 1/2 write can edit restricted fields.
- No native role permissions need to be modified or restricted.

Rejected alternatives:
- Lavanya roles only (no native Agent): staff lose the Helpdesk portal.
- Native roles only: discards the field-level permission model.

## Mandatory verification before go-live (UAT items)

1. Create one test user per row of the mapping table; confirm portal login,
   ticket list visibility, ticket edit, and restricted-field behavior.
2. Confirm helpdesk's whitelisted API endpooints do not bypass Lavanya DocPerms
   for agents (spot-check status change, assignment, comment).
3. Confirm `Lavanya Viewer` (no HD Agent record) can read via desk UI only.
4. Re-run the permission behavior smoke test (Phase 1L-7 procedure) after the
   first real role assignments.
