```markdown
# lavanya_service Development Patterns

> Auto-generated skill from repository analysis

## Overview

This skill teaches you how to contribute to the `lavanya_service` Python backend and its associated frontend. You'll learn the repository's coding conventions, commit patterns, and the main workflows for adding features, programmatic DocTypes, reminder engine enhancements, and documentation. The guide also covers how to write and structure tests, and provides handy `/commands` for common tasks.

---

## Coding Conventions

**File Naming:**  
- Use `snake_case` for Python files and modules.
  - Example: `reminder_engine.py`, `stage_rules.py`

**Import Style:**  
- Use **relative imports** within the package.
  - Example:
    ```python
    from .stage_rules import get_stage_rules
    from .workflow import WorkflowEngine
    ```

**Export Style:**  
- Use **named exports** (explicitly define what is exported).
  - Example:
    ```python
    def send_reminder(...):
        ...

    __all__ = ["send_reminder"]
    ```

**Commit Patterns:**  
- Use [Conventional Commits](https://www.conventionalcommits.org/).
- Prefixes: `feat`, `docs`, `ui`
- Example commit messages:
  - `feat: add support for custom reminder intervals`
  - `docs: update workflow documentation`
  - `ui: improve ticket detail component layout`

---

## Workflows

### Add New Programmatic DocType or Fields
**Trigger:** When you need to add a new entity/config to the backend without conflicting with shared fixtures.  
**Command:** `/new-programmatic-doctype`

1. **Create a new setup file:**  
   Add a Python file in `lavanya_service/setup/` to define the new DocType or fields programmatically.
   ```python
   # lavanya_service/setup/new_entity.py
   import frappe

   def execute():
       if not frappe.db.exists("DocType", "MyNewEntity"):
           # define DocType here
           ...
   ```
2. **Wire into hooks:**  
   Reference your setup file in `lavanya_service/hooks.py` under `after_install` or `after_migrate`.
   ```python
   after_install = "lavanya_service.setup.new_entity.execute"
   ```
3. **Verify creation:**  
   Ensure the new DocType/fields are created and function as expected.
4. **Update business logic:**  
   Modify related APIs or logic to use the new DocType/fields.

---

### Feature Development: API, Frontend, and Tests
**Trigger:** When adding a new workflow or user-facing feature.  
**Command:** `/new-feature`

1. **Backend logic:**  
   Implement or update Python modules (e.g., `api/*.py`, `workflow/*.py`).
   ```python
   # lavanya_service/api/new_feature.py
   def get_new_feature(...):
       ...
   ```
2. **Frontend components/pages:**  
   Update or create Vue components/pages.
   ```vue
   <!-- frontend/src/components/NewFeature.vue -->
   <template>
     <div>New Feature UI</div>
   </template>
   ```
3. **SPA integration:**  
   Update `index.html` or `frontend.html` for new routes or components.
4. **Automated tests:**  
   Add or update tests in `lavanya_service/tests/` or frontend test files.
5. **Documentation:**  
   Update or add relevant docs as needed.

---

### Document Feature or Release
**Trigger:** When recording a new feature, workflow, or sprint milestone.  
**Command:** `/document-feature`

1. **Write or update markdown docs:**  
   Add to `doc/*.md` or `docs/*.md` describing the new feature/release.
   ```markdown
   # New Feature: Smart Reminders
   - Overview: ...
   - Usage: ...
   ```
2. **Include guides, changelogs, or design docs** as needed.
3. **Commit with `docs:` prefix.**

---

### Add or Enhance Reminder Engine Step
**Trigger:** When adding a new capability or layer to the reminder engine.  
**Command:** `/reminder-step`

1. **Backend logic:**  
   Update `reminder_engine.py`, `tasks/reminder_refresh.py`, etc.
   ```python
   # lavanya_service/reminder_engine.py
   def compute_smart_reminders(...):
       ...
   ```
2. **Tests:**  
   Add or update tests for the new reminder logic.
   ```python
   # lavanya_service/tests/reminder_engine.py
   def test_smart_reminders():
       ...
   ```
3. **Frontend updates:**  
   Update `TodayWork.vue`, `TicketDetail.vue`, etc.
4. **Documentation:**  
   Document the new step in `doc/lavanya-spa-status.md` or similar.

---

## Testing Patterns

- **Testing Framework:** Not explicitly detected; likely uses Python's built-in `unittest` or `pytest` for backend.
- **File Naming:** Test files are in `lavanya_service/tests/` and named after the module tested, e.g., `reminder_engine.py`, `reminder_refresh.py`.
- **Frontend Tests:** Pattern `*.test.ts` suggests TypeScript-based tests for Vue components.

**Example Backend Test:**
```python
# lavanya_service/tests/reminder_engine.py
import unittest
from lavanya_service.reminder_engine import compute_smart_reminders

class TestReminderEngine(unittest.TestCase):
    def test_reminders(self):
        result = compute_smart_reminders(...)
        self.assertTrue(result)
```

---

## Commands

| Command                    | Purpose                                                        |
|----------------------------|----------------------------------------------------------------|
| /new-programmatic-doctype  | Add a new backend DocType or fields programmatically           |
| /new-feature               | Start a new feature: backend, frontend, and tests              |
| /document-feature          | Document a new feature, workflow, or release                   |
| /reminder-step             | Add or enhance a step in the reminder engine                   |
```
