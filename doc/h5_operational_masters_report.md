# H5 Operational Masters + Service Data Foundation Report

## Scope

H5 adds the backend data foundation for customer-owned products, warranty history,
master-data lookup, controlled proof categories, and richer service appointments.
It extends existing Lavanya DocTypes instead of introducing a parallel master-data
architecture.

## What Changed

- `lavanya_service/setup/operational_masters.py` creates and upgrades H5 DocTypes and fields idempotently.
- `lavanya_service/api/operational_masters.py` exposes customer product sync/history, master suggestions, service-center/technician lookups, proof validation, and appointment status APIs.
- `lavanya_service/setup/install.py` wires H5 setup into the existing install/migrate path.
- `lavanya_service/api/stitch_console.py` delegates appointment creation to the H5 API while preserving free-text technician compatibility.
- `lavanya_service/tests/h5_operational_masters.py` adds rollback-safe coverage for H5 behavior and safety boundaries.

## Safety Boundaries

- No live WhatsApp/SMS.
- No ERP posting or ERP draft posting.
- No stock posting, accounting entries, payment entries, or penalty application.
- No automatic ticket closure.
- No automatic repeat-complaint linking.
- H5 APIs do not create `Communication`, `Email Queue`, or `Notification Log` rows.

## Verification

- `python -m py_compile lavanya_service/setup/operational_masters.py lavanya_service/api/operational_masters.py lavanya_service/tests/h5_operational_masters.py lavanya_service/setup/install.py lavanya_service/api/stitch_console.py`: PASS.
- `lavanya_service.tests.h5_operational_masters.run`: 13 pass / 0 fail.
- `lavanya_service.tests.theme_settings.run`: 29 pass / 0 fail.
- `lavanya_service.tests.stitch_console_spa.run`: PASS.
- `lavanya_service.tests.p2_tests.run`: 18 pass / 0 fail.
- `lavanya_service.tests.today_work.run`: 23 pass / 1 fail; TW-015 group-order mismatch remains pre-existing.
- `node node_modules/vite/bin/vite.js build`: PASS; existing Browserslist data warning only.

Broader regression commands are also tracked in `doc/lavanya-spa-status.md`.
