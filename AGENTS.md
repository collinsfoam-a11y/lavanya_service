# Agent rules — lavanya_service

These rules are **mandatory for any AI coding agent** working in this app
(Claude Code, Cursor, Copilot, Gemini/Antigravity, Aider, Codex, or any other).

## Canonical rule

This is the canonical rule file. Tool-specific files (`CLAUDE.md`, `.cursorrules`,
`.github/copilot-instructions.md`) just point here — edit *this* file.

---

## Rule 0 — You MUST read ALL docs before ANY change

Before writing ANY code, adding ANY field, or modifying ANY file in this app,
you **MUST** read:

1. **`doc/lavanya-app-reference.md`** — complete app reference: every DocType,
   every custom field, every API endpoint, every function signature, every test
   file, every config value. This is the single source of truth for what exists.
2. **`doc/lavanya-requirements.md`** — source-grounded requirements document.
   Every requirement here cites the file it came from. If you need something not
   stated here and not verifiable in code, it is an **open question** (§10).
3. **`doc/lavanya-spa-status.md`** — SPA frontend build log, pending work, and
   verification playbook.
4. **`doc/lavanya-changelog.md`** — complete change history. Read the latest
   entries to understand what changed recently and why.
5. **`doc/lavanya-expanded-design.md`** — proposed expansions (ERD, new entities,
   workflows). If you are implementing something from here, read it fully first.

**Do not re-derive** any of this from scratch. Do not duplicate work already
listed there. Do not assume requirements — see Rule 0 in lavanya-requirements.md.

> **Violation consequence:** If you edit the app without reading these docs first
> and your change breaks something, it will be caught by the next agent who reads
> the changelog. You will be wasting human time.

---

## Rule 1 — You MUST document every change in the changelog

Every time you make a change, you **MUST** append an entry to
`doc/lavanya-changelog.md` using this exact format:

```markdown
## YYYY-MM-DD HH:MM — Short title of change

### What changed
- `path/to/file.py` — specific description of what was modified/added/removed
- `path/to/another/file.py` — ...

### Previous state
What the code looked like / what existed before / what was missing

### Current state
What the code looks like now / what was added / what changed

### Why changed
Why this change was necessary (bug fix, feature request, refactor, etc.)

### What was obtained
The measurable outcome: fixed bug, new capability, performance gain, etc.

### Compatibility notes
- What existing code was checked for breakage
- What tests were run
- Any migration steps needed
```

---

## Rule 2 — You MUST verify backward compatibility

Before committing any change:

1. **Check all imports** — verify no existing file that imports your changed
   module will break. See `doc/lavanya-app-reference.md` §Imports for the full
   import map.
2. **Check API response shapes** — verify no SPA or external consumer expects
   fields you changed/removed. The SPA lives in `frontend/src/` and calls
   `lavanya_service/api/*.py` endpoints.
3. **Check all stage_rules references** — `stage_rules.py` is referenced by
   `today_work.py`, `stitch_console.py`, `overrides/hd_ticket.py`. Any change
   to option lists, stage names, or function signatures must be checked across
   all consumers.
4. **Check all custom field values** — HD Ticket custom fields are defined in
   `setup/hd_ticket_fields.py`, `setup/service_stages.py`, `setup/followup_fields.py`,
   `setup/intake_masters.py`. Changing a field name requires updating the fixture
   list in `hooks.py` and all references across the app.
5. **Check test modules** — run the relevant test module(s) after your change
   (see §Tests in app-reference.md).

---

## Rule 3 — Run tests after every change

After making ANY code change, run the affected test module(s) to verify nothing
broke:

```
printf 'from lavanya_service.tests import <module> as t\nt.run()\n' \
 | docker exec -i devcontainer-example-frappe-1 bash -lc \
   "cd /workspace/development/frappe-bench && bench --site lavanya-dev.localhost console"
```

The full list of test modules and their focus areas is in `doc/lavanya-app-reference.md`
§Tests (29 modules currently).

---

## Rule 4 — Update reference docs on structural changes

If you add/modify/remove any of the following, update `doc/lavanya-app-reference.md`
accordingly:

- A DocType (custom or via fixture)
- A custom field on HD Ticket (add/remove/rename)
- A whitelisted API endpoint
- A quick action function
- A scheduler job
- A test module
- A role or permission
- A stage rule, flow type, stage, or next action
- A custom field option list

This keeps the reference doc the single source of truth for the next agent.

---

## Rule 5 — Commit discipline

- Commit **only your own files**. Never `git add -A`.
- Multiple agents write in this repo. Do **not** stage another agent's files.
- Build the SPA on the **host** (`cd frontend && node node_modules/vite/bin/vite.js
  build`) — the container can't build (host-installed `node_modules`).
- Include the changelog update and reference doc update in the same commit (or
  an adjacent one) as the change it describes.

---

## Rule 6 — Security

- Never type the real password into a login form or POST it to `/api/method/login`
  from automation.
- The passwordless `login_as` session mint is the only sanctioned way to get an
  authenticated session for verification.
- Never commit secrets or keys.

---

## Reference file map

| File | What it contains |
|------|-----------------|
| `doc/lavanya-app-reference.md` | **Complete app reference** — read this first |
| `doc/lavanya-requirements.md` | **Source-grounded requirements** — never assume |
| `doc/lavanya-changelog.md` | **Change history** — update on every change |
| `doc/lavanya-spa-status.md` | **SPA build log & pending work** |
| `doc/lavanya-expanded-design.md` | **Proposed expansions & new entities** |
| `doc/lavanya-overview.md` | **High-level overview** for human readers |
