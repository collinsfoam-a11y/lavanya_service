# H2 Theme System Report

> Part of H2 — UI/UX Wiring, Settings, Modernisation + Theme System.
> Extended by H3/H3B/H4 — shared components modernized and polished across workflow pages.

---

## Summary

Implemented a runtime theme engine for the Lavanya Service SPA that supports
six themes, persists user choice, and applies instantly without a page reload.

---

## Files added / changed

| File | Change |
|------|--------|
| `frontend/src/utils/theme-engine.js` | New — theme definitions, CSS-variable application, localStorage persistence, invalid-theme fallback. |
| `frontend/src/utils/theme.js` | Extended — re-exports theme engine while keeping legacy `COLORS` / chip helpers for backward compatibility. |
| `frontend/src/index.css` | Updated — all `lav-*` classes and base styles now reference CSS custom properties; default values match Lavanya Light. |
| `frontend/tailwind.config.mjs` | Updated — color tokens now point to CSS variables so Tailwind utilities respond to theme changes. |
| `frontend/src/composables/useTheme.js` | New — reactive Vue composable wrapping the theme engine. |
| `frontend/src/components/LavThemeToggle.vue` | New — accessible theme selector dropdown. |
| `frontend/src/components/AppShell.vue` | Updated — theme toggle added to header. |
| `frontend/src/App.vue` | Updated — initializes theme on mount; added `g+s` shortcut for Settings. |
| `frontend/src/pages/Settings.vue` | New — settings page showing theme selector, safety locks, UI feature flags; **H3**: editable for managers with save/reset. |
| `frontend/src/pages/TodayWork.vue` | Updated — uses `LavSectionHeader`, `LavStatCard`, `LavLoadingState`, `LavEmptyState`. |
| `frontend/src/pages/Tickets.vue` | Updated — uses `LavSectionHeader`, `LavChip`, `LavLoadingState`, `LavEmptyState`, `LavCard`. |
| `frontend/src/pages/Reports.vue` | Updated — 8 tabs modernized with `LavSectionHeader`, `LavStatCard`, `LavCard`, `LavLoadingState`, `LavEmptyState`. |
| `frontend/src/pages/FieldMode.vue` | New — mobile field mode using shared components. |
| `frontend/src/components/LavTicketCard.vue` | New in H4 — shared ticket card using theme tokens for workflow scanning. |
| `frontend/src/pages/Tickets.vue` | H4 — saved filters, mobile cards, Next Action and Quality columns. |
| `frontend/src/pages/Settings.vue` | H4 — dirty-state indicator, manager/read-only state, sticky save/reset bar. |
| `frontend/src/router.js` | Updated — added `/settings` and `/field` routes. |
| `lavanya_service/setup/ui_settings.py` | New — `Lavanya Service Settings` Single DocType with theme/UI/safety fields. |
| `lavanya_service/api/ui_settings.py` | New — whitelisted `get_lavanya_service_settings`, `can_manage_lavanya_settings`, `save_lavanya_service_settings`, `reset_lavanya_service_settings` APIs. |
| `lavanya_service/hooks.py` | Updated — wired `ui_settings.create_lavanya_settings` to install/migrate. |
| `lavanya_service/tests/theme_settings.py` | Extended from 15 to 23 tests in H3, then to 29 checks in H4 (static UI wiring and native-dialog guard). |

---

## Theme list

| Theme id | Label | Purpose |
|----------|-------|---------|
| `lavanya-light` | Lavanya Light | Default clean light theme. |
| `lavanya-dark` | Lavanya Dark | Dark theme for low-light use. |
| `lavanya-blue` | Lavanya Blue | Blue-tinted brand variant. |
| `lavanya-green` | Lavanya Green | Green-tinted calmer variant. |
| `high-contrast` | High Contrast | WCAG-friendly maximum contrast. |
| `compact-counter` | Compact Counter Mode | Reduced spacing for service counters. |

---

## How it works

1. `utils/theme-engine.js` defines every theme as a token map plus spacing/typography metadata.
2. On app start, `useTheme()` calls `initTheme()`, which reads `localStorage.getItem('lavanya-theme')`, validates it, and applies the default on invalid values.
3. `applyTheme(name)` writes CSS custom properties to `:root` and sets `data-theme` and `data-compact` attributes on `<html>`.
4. Tailwind (`tailwind.config.mjs`) and the `lav-*` CSS classes consume those variables, so the entire UI updates instantly.
5. `LavThemeToggle.vue` lets staff preview/switch themes; the choice is saved to localStorage.

---

## Verification

- `node node_modules/vite/bin/vite.js build` — PASS.
- `lavanya_service.tests.theme_settings.run` — 29/29 PASS after H4 static UI checks.
- `lavanya_service.tests.stitch_console_spa.run` — PASS.
- `lavanya_service.tests.p2_tests.run` — 18/18 PASS.
- `lavanya_service.tests.today_work.run` — 23/24 PASS (TW-015 group-order mismatch is pre-existing and unrelated to theme work).

Static checks:
- No new hardcoded component colors.
- No native `confirm()` usage.

---

## Safety

- Theme system is purely client-side; no backend workflow behavior changed.
- `Lavanya Service Settings` defaults are safe (theme = Light, safety locks = on, ERP panel = off).
