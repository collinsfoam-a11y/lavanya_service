# Agent rules — lavanya_service

These rules are **mandatory for any AI coding agent** working in this app
(Claude Code, Cursor, Copilot, Gemini/Antigravity, Aider, Codex, or any other).
They exist so the project stays self-documenting and every change is traceable.

This is the canonical rule file. Tool-specific files (`CLAUDE.md`, `.cursorrules`,
`.github/copilot-instructions.md`) just point here — edit *this* file.

## Rule 1 — Read the status doc FIRST

Before doing anything else in this app, **read
[`doc/lavanya-spa-status.md`](doc/lavanya-spa-status.md)** in full. It is the
single source of truth for:
- what is already built (and the commit that built it),
- what is pending (P1–Pn) and how to build each,
- the architecture/file map and the build/serve loop,
- the verification playbook (build grep → `bench execute` → serve `200` →
  authenticated screenshots).

Do not re-derive any of this from scratch or duplicate work already listed there.

## Rule 2 — Update the status doc after EVERY step

A "step" = a meaningful, self-contained change (a page, an endpoint, a fix, a
refactor). After each step — and before you move on — update
`doc/lavanya-spa-status.md` so it never goes stale:

1. **What you did** — move the item from "Pending" (§3) to "What we did" (§2) with
   its commit hash, or add a new row. One line, specific.
2. **How you did it** — note the key files touched and the approach (e.g. "reused
   `today_work.get_today_work`; new `pages/MyWork.vue` + `/my-work` route").
3. **Why you did it** — the reason/trade-off in one line (what gap it closes, why
   this approach over alternatives). If you deviated from the Stitch design or a
   plan, say so and why.
4. **Remaining to do** — update §3: remove what's done, add any new follow-ups you
   discovered, and note partial work explicitly (don't leave half-done items
   looking complete).

Keep edits surgical and honest. If a step failed or was skipped, record that too —
the doc must reflect reality, not intentions.

## Rule 3 — Verify before you claim done

Use the §5 playbook in the status doc. For any UI change, the authenticated
**screenshot** check (§5d) is the gold standard — build/serve `200` alone is not
proof the page renders or loads data (that's how the empty-Tickets bug slipped
through until a screenshot caught it). State plainly what you verified and how.

## Rule 4 — Commit discipline

- Commit **only your own files**. Never `git add -A`.
- Multiple agents write in this repo. Do **not** stage another agent's files; at
  time of writing these belong to a parallel (non-Claude) agent:
  `setup/helpdesk_config.py`, `setup/install.py`, `api/coordinator_dashboard.py`,
  `api/manager_dashboard.py`, `fixtures/client_script.json`,
  `lavanya_service/page/*dashboard/`, `utils/add_client_script.py`, `yarn.lock`.
  If you are that other agent, the inverse holds — leave the SPA/frontend files to
  their owner unless coordinating.
- Build the SPA on the **host** (`cd frontend && node node_modules/vite/bin/vite.js
  build`) — the container can't build (host-installed `node_modules`).
- Include the doc update in the same commit (or an adjacent one) as the change it
  describes.

## Rule 5 — Security

Never type the real password into a login form or POST it to `/api/method/login`
from automation. The passwordless `login_as` session mint in the status doc §5d is
the only sanctioned way to get an authenticated session for verification.
