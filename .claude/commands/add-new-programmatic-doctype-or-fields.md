---
name: add-new-programmatic-doctype-or-fields
description: Workflow command scaffold for add-new-programmatic-doctype-or-fields in lavanya_service.
allowed_tools: ["Bash", "Read", "Write", "Grep", "Glob"]
---

# /add-new-programmatic-doctype-or-fields

Use this workflow when working on **add-new-programmatic-doctype-or-fields** in `lavanya_service`.

## Goal

Adds a new DocType or fields to the backend via programmatic setup (not via shared fixtures), typically for new workflow layers or config objects.

## Common Files

- `lavanya_service/setup/*.py`
- `lavanya_service/hooks.py`

## Suggested Sequence

1. Understand the current state and failure mode before editing.
2. Make the smallest coherent change that satisfies the workflow goal.
3. Run the most relevant verification for touched files.
4. Summarize what changed and what still needs review.

## Typical Commit Signals

- Create new setup/*.py file to define DocType or fields programmatically.
- Wire setup file into hooks.py via after_install/after_migrate.
- Verify creation and round-trip of the new DocType/fields.
- Update related business logic or APIs to use the new DocType/fields.

## Notes

- Treat this as a scaffold, not a hard-coded script.
- Update the command if the workflow evolves materially.