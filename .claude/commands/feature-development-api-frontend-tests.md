---
name: feature-development-api-frontend-tests
description: Workflow command scaffold for feature-development-api-frontend-tests in lavanya_service.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /feature-development-api-frontend-tests

Use this workflow when working on **feature-development-api-frontend-tests** in `lavanya_service`.

## Goal

Implements a new feature by updating backend APIs, frontend components, and adding/expanding tests.

## Common Files

- `lavanya_service/api/*.py`
- `lavanya_service/workflow/*.py`
- `lavanya_service/stage_rules.py`
- `lavanya_service/reminder_engine.py`
- `frontend/src/components/*.vue`
- `frontend/src/pages/*.vue`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Implement backend logic and/or API endpoint (api/*.py, workflow/*.py, stage_rules.py, reminder_engine.py, etc).
- Update or create frontend Vue components/pages to surface the new feature.
- Update index.html/www/frontend.html for SPA integration.
- Add or update automated tests for backend and/or frontend.
- Update documentation if needed.

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.