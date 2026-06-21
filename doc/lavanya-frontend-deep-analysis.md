# Lavanya Service Console — Deep Frontend Analysis

## 0. Executive Summary

The SPA is a functional, well-structured Vue 3 Composition API app that works reliably.
It has **0 imports from frappe-ui components** (only the Tailwind preset for tokens),
meaning ~3,000 lines of UI are hand-built. This buys full control but misses out on
battle-tested components (dropdowns, dialogs, form fields, date pickers, comboboxes).

The app is at a **pivot point**: adding a component library now will pay back 5x as
more modals, forms, and complex interactions are added with the expanded service flows.

---

## 1. Modern Design Pattern Comparison

### 1.1 Current Architecture vs Modern Standards

| Aspect | Current | Modern Pattern | Gap |
|--------|---------|----------------|-----|
| **Component library** | Hand-built HTML/CSS | Radix Vue / shadcn-vue / PrimeVue | No accessible primitives for modals, selects |
| **State management** | Component-local `ref()` | Pinia stores + composables | SelectedTicket duplicated in 3 pages |
| **API layer** | Hand-written `fetch()` | TanStack Query / vue-query | No caching, dedup, retry, stale management |
| **Form validation** | Manual computed checks | VeeValidate / Zod + vue-use-forms | No declarative validation rules |
| **DateTime picker** | Native `<input type="date">` | frappe-ui DatePicker / vue-datepicker | No timezone-aware, localized picker |
| **Type safety** | None (vanilla JS) | TypeScript 5.x | Runtime errors instead of compile-time catches |
| **Toast system** | Custom 20-line composable | vue-sonner (in node_modules) | Re-inventing the wheel |
| **CSS approach** | Tailwind + hand-written `lav-*` | Tailwind + CSS variables + `@apply` | Token duplication, no design system linking |
| **Table rendering** | Native `<table>` | TanStack Table / AG Grid | Columns, sorting, filtering, pagination all hand-rolled |

### 1.2 Component Library Comparison

**frappe-ui** (already installed, NOT used):
- Provides: Button, FormControl, Input, Select, Dialog, Dropdown, DatePicker, Tabs, Card, Badge, Avatar, Alert, Breadcrumbs
- The Tailwind preset is used but no Vue components are imported
- **Why it matters**: frappe-ui components are Frappe-aware (CSRF, session, frappe.call),
  follow Frappe UX patterns, and are already in `package.json`

**shadcn-vue / Radix Vue**:
- Headless, unstyled primitives with full a11y
- Would require significant theming work
- Better for fully custom branded apps

**PrimeVue 4**:
- 90+ components, Material Design themes
- Heavy bundle size, opinionated styling
- Overkill for this app's scope

**Recommended**: **Use frappe-ui components** (already installed). They provide:
- `frappe-ui/src/components/Select/Select.vue` — auto-complete with search
- `frappe-ui/src/components/Dialog/Dialog.vue` — accessible modal with focus trap
- `frappe-ui/src/components/DatePicker/DatePicker.vue` — date/time range
- `frappe-ui/src/components/Table/Table.vue` — virtual scrolling, sort, filter
- `frappe-ui/src/components/Badge/Badge.vue` — status badges (replaces `chip()` utils)

### 1.3 Current 7 Modal Implementations in TicketDetail.vue

| Modal | Lines | Unique Structure | Could Use frappe-ui |
|-------|-------|------------------|---------------------|
| Need Invoice | ~65 | Full custom | Dialog + FormControl |
| Create Product Receipt | ~78 | Full custom | Dialog + FormControl |
| Ready for Pickup | ~59 | Full custom | Dialog + FormControl |
| Generic Action | ~76 | Full custom | Dialog + FormControl |
| Repeat banner | inline | Custom inline | Alert component |
| AI Advisory | inline | Custom inline | Alert + Badge |
| Follow-up stepper | inline | Custom timeline | Stepper component |

---

## 2. Anti-Pattern Catalog (What to Avoid)

### 2.1 Structural Anti-Patterns

**AP-1: Component Bloat** — TicketDetail.vue at 1,552 lines violates the single-responsibility principle.
- **Avoid**: Letting any component exceed ~400 lines
- **Fix**: Extract into 6-8 sub-components (TicketHeader, TicketSections, QuickActionPanel, FollowupTimeline, ActivityTimeline, ActionModal, ProductReceiptModal, FollowupStepper)

**AP-2: Modal Duplication** — 3 modals with near-identical overlay + header + body + footer structure.
- **Avoid**: Copy-pasting modal structure
- **Fix**: Create a reusable `LavModal` component with props for title, icon, size, submit/cancel labels

**AP-3: Color Token Scattering** — `STATUS_HUE` defined in 3 places (utils/index.js, TicketDetail.vue FOLLOWUP_ACTION_STYLES, Reports.vue).
- **Avoid**: Defining the same color map in multiple files
- **Fix**: Single source in `utils/theme.js` exported to all consumers

**AP-4: Utility Code Duplication** — `hexToRgba()` and `chip()` implemented in both `utils/index.js` and `Reports.vue`.
- **Avoid**: Re-implementing shared utilities
- **Fix**: Import from `@/utils` in Reports.vue (remove local copies)

### 2.2 UX Anti-Patterns

**AP-5: `confirm()` Dialogs** — Used in AppShell (logout), TicketDetail (dangerous actions), NewTicket (clear form).
- **Avoid**: Native `confirm()` — blocks UI, not mobile-friendly, unstyled
- **Fix**: Custom confirmation dialog component with promise-based API

**AP-6: Icon-Only Buttons** — Close buttons, clear search buttons with no aria-label.
- **Avoid**: `<button><span class="material-symbols-outlined">close</span></button>`
- **Fix**: Always add `aria-label` or `title` and a `.sr-only` text fallback

**AP-7: Inline Styles for Dynamic Colors** — Heavy use of `:style="chip(t.status)"` patterns throughout.
- **Avoid**: 50+ inline style bindings for status colors
- **Fix**: CSS custom properties set via class binding, or computed color classes

**AP-8: Table Rows as Click Target** — Tables use `@click="selectTicket"` on `<tr>`.
- **Avoid**: Clickable table rows (breaks accessibility — screen readers expect `<tr>` to be structural)
- **Fix**: Use an explicit "Open" button/action in each row

### 2.3 Performance Anti-Patterns

**AP-9: Unbounded Infinite Scroll** — Tickets.vue loads pages of 30 rows with no virtual scrolling.
- **Avoid**: Loading thousands of DOM nodes
- **Fix**: frappe-ui Table has virtual scrolling built in, or use `vue-virtual-scroller`

**AP-10: No Request Deduplication** — Rapid filter changes each trigger a separate API call.
- **Avoid**: Parallel requests for the same endpoint
- **Fix**: Use `AbortController` to cancel in-flight requests, or `debounce` the filter watcher

**AP-11: `watch` with API Call on Every Change** — Tickets.vue watches `search` with a 300ms debounce but no cancellation.
- **Avoid**: Stale responses from overlapping requests
- **Fix**: Add `AbortController` or check a generation counter

---

## 3. Responsive Behavior Matrix

| Screen | Width | Sidebar | Header | Content Layout | Metric Grid | Table | Modals | Notes |
|--------|-------|---------|--------|---------------|-------------|-------|--------|-------|
| **Mobile S** | 320px | Hidden | Simplified (logo only) | Single column, max 320px | 2-col (too tight) | Horizontal scroll (broken) | Full-width with 16px padding | **Most problematic** — metric cards show 1 word, tables overflow |
| **Mobile M** | 375px | Hidden | Simplified | Single column | 2-col (tight) | Horizontal scroll | Full-width with 16px padding | Text truncation starts at ~15 chars |
| **Mobile L** | 425px | Hidden | Simplified | Single column | 2-col | Horizontal scroll | Full-width | Acceptable but tables need scroll |
| **Tablet** | 768px | **Visible** | Full (with search) | 2-column grid | 3-col | Full-width table | Max-width modal | **First good breakpoint** — sidebar appears, search bar visible |
| **Tablet L** | 1024px | Visible | Full | 2-3 column | 3-col | Full with hover actions | Comfortable | Most fields visible without scrolling |
| **Desktop** | 1280px | Visible | Full | 3-4 column | 6-col | Full with row actions | Max-width 4xl | Full capability |
| **Desktop L** | 1440px | Visible | Full | Max-content 1440px | 6-col | Full | Max-width | Wrapped by max-content-width |
| **Desktop XL** | 1920px | Visible | Full | Centered max 1440px | 6-col (stretched) | Full | Max-width | Content is centered, not full-width |

### 3.1 Critical Breakpoint Issues

**320px-480px (small mobile):**
- `.lav-metric-grid` is 2 columns — each card is ~140px wide, label text wraps awkwardly
- Today's Work action queue: status chips wrap to 3-4 lines per ticket
- `.lav-chip` filter buttons wrap to multiple rows, taking too much vertical space
- Ticket tables overflow — no horizontal scroll wrapper on some tables
- `font-headline-lg` (28px) is too large for page titles on 320px screens

**480px-640px (medium mobile):**
- NewTicket form 2-column grid collapses to 1 column — good
- Filter panel with 8 select dropdowns fills the screen
- Reports card grid is 2 columns — acceptable

**640px-768px (phablet/tablet transition):**
- No specific breakpoint — 2-col metric grid when 3-col would fit
- Search bar in header is hidden until 768px — gap at 640px

### 3.2 Recommended Breakpoint Additions

```css
/* Add to index.css or tailwind config */
@media (min-width: 480px) {
  .lav-metric-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .lav-header h2 { display: block; } /* show simplified header */
}

@media (min-width: 640px) and (max-width: 767px) {
  .lav-metric-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  /* Show condensed search in header */
}

@media (max-width: 480px) {
  .lav-metric { height: 100px; } /* shorter cards */
  .lav-metric__num { font-size: 28px; line-height: 32px; }
  .lav-metric__label { font-size: 10px; }
  h2 { font-size: 22px !important; } /* smaller page titles */
}
```

---

## 4. Feature Gap Analysis (Backend Capabilities Not in Frontend)

The backend has many features the SPA doesn't expose:

| Backend Feature | Frontend Coverage | Gap |
|----------------|-------------------|-----|
| 11 service flow types | Only ticket creation uses flow types | No flow-specific UI anywhere |
| 46 service stages | Read-only display in TicketDetail | No stage selector/advancer in UI |
| 27 next actions | Action buttons in TicketDetail (partial — ~15 of 27) | 12 actions not accessible from SPA |
| 5 custom roles | No role-based UI | TicketDetail shows same buttons for all roles |
| SLA computed fields | SlaBadge renders helpdesk SLA | No stage SLA display |
| Reminder engine (dry-run) | Reminder Intelligence section | Read-only — no way to configure rules |
| AI Advisory engine | AI Advisory section with accept/ignore | Read-only — no way to configure |
| Product Receipt movements | 3 custody buttons in Quick Actions | No custody timeline/history view |
| Manager reports (4 endpoints) | Reports Center with drill-down | Missing: supplier_performance, area_performance, payment_block_status, brand_delay_summary |
| Follow-up journey flow | AI-powered stepper in TicketDetail | Limited to current ticket — no aggregate view |
| Repeat complaints | Detection + linking in drawer | No "all repeats for this customer" view |
| 3 scheduler jobs (reminders) | No frontend visibility | No "next run" or status display |
| Customer profile lookup | Mobile autofill on NewTicket | No full profile view or ticket history |
| Brand service masters | Brand list in NewTicket select | No brand detail view or performance |

### 4.1 Missing Frontend Pages/Features

| Feature | Priority | Why |
|---------|----------|-----|
| **Supplier SLA configuration UI** | P0 | Currently only via backend — managers need to configure SLAs |
| **Supplier Payment Block dashboard** | P0 | Need UI to view/review/release blocks |
| **Brand performance dashboard** | P0 | Per-brand metrics from backend APIs |
| **Area performance dashboard** | P0 | Area-wise metrics |
| **Stage advancement UI** | P0 | Currently only via follow-up actions — need explicit stage changer |
| **Role-based UI adapt** | P1 | Different roles should see different actions (currently all-or-nothing) |
| **Filter presets / saved views** | P1 | Save filter combinations for quick access |
| **Mass/bulk ticket operations** | P1 | Select multiple tickets → update stage, assign, escalate |
| **QR-code intake page** | P2 | Standalone page for customer self-service intake (backend exists) |
| **Notifications / real-time updates** | P2 | Frappe events via socket.io for live ticket changes |
| **Print-friendly report views** | P2 | Printable ticket summary, invoice, receipt |

---

## 5. Comprehensive Improvement Roadmap

### Phase A: Foundation (Next 2 weeks)
| # | Improvement | Effort | Impact | Files Affected |
|---|-------------|--------|--------|----------------|
| A1 | Extract frappe-ui Dialog for all modals | 2d | High | TicketDetail.vue, new LavModal.vue |
| A2 | Consolidate color tokens into `utils/theme.js` | 0.5d | High | utils/index.js, Reports.vue, TicketDetail.vue |
| A3 | Remove `hexToRgba`/`chip` duplication from Reports.vue | 0.25d | Medium | Reports.vue |
| A4 | Add `aria-label` to all icon-only buttons | 0.5d | Medium | AppShell, TodayWork, Tickets, TicketDetail |
| A5 | Replace `confirm()` with a custom dialog | 1d | High | AppShell, TicketDetail, NewTicket |

### Phase B: Component Modernization (Week 3-4)
| # | Improvement | Effort | Impact | Files Affected |
|---|-------------|--------|--------|----------------|
| B1 | Extract TicketDetail sub-components (6-8 files) | 3d | High | New: TicketHeader, QuickActions, FollowupTimeline, etc. |
| B2 | Build generic `LavModal` component | 1d | High | New component |
| B3 | Add `AbortController` to API calls | 1d | Medium | api.js, TodayWork, Tickets, Reports |
| B4 | Add form validation with VeeValidate or manual composable | 2d | Medium | NewTicket, TicketDetail forms |
| B5 | Add 480px breakpoint for better mobile | 0.5d | Medium | index.css |

### Phase C: Feature Completion (Week 5-6)
| # | Improvement | Effort | Impact | Files Affected |
|---|-------------|--------|--------|----------------|
| C1 | Supplier Payment Block dashboard page | 2d | High | New page + API integration |
| C2 | Brand/Area performance dashboards | 2d | High | New page + API integration |
| C3 | Stage advancement UI for coordinators | 1.5d | High | TicketDetail new section |
| C4 | Role-based action gating in UI | 1d | Medium | TicketDetail, AppShell |
| C5 | Filter presets / saved views | 2d | Medium | TodayWork, Tickets |

### Phase D: Advanced (Weeks 7-8)
| # | Improvement | Effort | Impact | Files Affected |
|---|-------------|--------|--------|----------------|
| D1 | TypeScript migration (start with API types + utils) | 3d | Medium | All files incrementally |
| D2 | vue-query / TanStack Query for API caching | 2d | Medium | api.js + data-fetching composables |
| D3 | Real-time updates via Frappe socket.io events | 3d | High | New composable + integration |
| D4 | Bulk ticket operations page | 2d | Medium | New page |
| D5 | Print styles for tickets and reports | 1d | Low | index.css + print media queries |

---

## 6. Documentation Gaps in Frontend Code

| Gap | Current State | Needed |
|-----|---------------|--------|
| **Component props** | No JSDoc on any `.vue` component | `@param` docs for props and emits |
| **API response shapes** | Assumed by consumer — no documentation | Types/interfaces or JSDoc for each endpoint |
| **Color token semantics** | `STATUS_HUE` maps status codes to hex — no comment on why | Document each color choice semantics |
| **Mobile breakpoints** | Scattered across CSS | Centralized breakpoint documentation in index.css |
| **Routing** | No route meta documentation | Document auth requirements, roles per route |
| **Build/deploy** | Minimal README (frappe-ui template default) | Document build process, Frappe integration, `syncServePage()`
| **Keybindings** | Hidden in App.vue with no external documentation | Add to README or a docs file |

---

## 7. What to Avoid (Decision Guide)

### Do NOT:
1. **Add a heavy UI library** (PrimeVue, Element Plus, Vuetify) — frappe-ui is already installed and Frappe-aware
2. **Switch to a meta-framework** (Nuxt) — Frappe handles SSR, no benefit
3. **Over-abstract** — Don't create 20 tiny single-use components. Extract only when a pattern repeats 3+ times
4. **Use inline styles for theming** — CSS variables or Tailwind classes only
5. **Remove `cache: 'no-store'`** — It's there for a critical reason (stale data on refresh)
6. **Share `TicketDetail` via route** — Currently a drawer overlay; a dedicated route would complicate the UX
7. **Add Pinia before the app has cross-component state** — Only 3 pieces of shared state exist (selectedTicket, toasts, csrf_token)
8. **Rewrite the CSS from scratch** — `lav-*` classes work well; just consolidate and document

### Do:
1. **Use frappe-ui components** where they exist (Dialog, Select, DatePicker, Table, Badge, Alert)
2. **Extract TicketDetail.vue** — it's the single biggest maintainability risk
3. **Consolidate colors** into `utils/theme.js` with a single STATUS_HUE export
4. **Add TypeScript** — start small with `utils/theme.js`, then API response types, then components
5. **Add 480px and 360px breakpoints** — the biggest responsive gap is small mobile
6. **Add print CSS** — Staff need to print ticket summaries for customers
7. **Version the API** — As more SPA endpoints are added, avoid breaking existing consumers

---

## 8. Browser Compatibility (Detailed)

| Feature | Chrome | Firefox | Safari | Edge | Samsung | Opera | Notes |
|---------|--------|---------|--------|------|---------|-------|-------|
| **Vite build (es2015)** | 49+ | 52+ | 10+ | 79+ | 5+ | 36+ | No IE11 |
| **CSS Grid** | 57+ | 52+ | 10.1+ | 16+ | 6.2+ | 44+ | OK on all modern |
| **CSS `color-mix()`** | 111+ | 113+ | 16.2+ | 111+ | 22+ | 97+ | **NOT on Firefox ESR or Safari 15** |
| **backdrop-blur** | 76+ | 103+ | 15+ | 79+ | 12+ | 63+ | Firefox 103+ (late 2022) |
| **IntersectionObserver** | 51+ | 55+ | 12.1+ | 16+ | 7.2+ | 38+ | Universal |
| **Material Symbols variable font** | 94+ | 100+ | 16+ | 94+ | 16+ | 80+ | Safari 16+ required |
| **CSS `:focus-visible`** | 86+ | 85+ | 15.4+ | 86+ | 14+ | 72+ | Safari 15.4+ |
| **prefers-reduced-motion** | 74+ | 63+ | 10.1+ | 79+ | 10+ | 62+ | Universal |
| **CSS Scroll-behavior** | 61+ | 36+ | 15.4+ | 79+ | 8+ | 48+ | Safari 15.4+ |
| **fetch()** | 42+ | 39+ | 10.1+ | 14+ | 5+ | 29+ | Universal |
| **ES modules** | 61+ | 60+ | 10.1+ | 16+ | 8.5+ | 48+ | Universal |

### 8.1 Identified Compatibility Risks

1. **`color-mix()` in `.lav-intel`** (index.css lines 345-351): NOT supported in Safari <16.2, Firefox <113, Chrome <111. Falls back to no background color (transparent) — chips appear without their accent tint. **Fix**: Use pre-computed RGBA values instead.

2. **`backdrop-blur`** in modal overlays (TicketDetail.vue): Works in all modern browsers but noticeably slower on older mobile devices. **Mitigation**: Already acceptable — graceful degradation to solid background.

3. **Material Symbols fill axis** (`FILL` variation setting): `font-variation-settings: 'FILL' 1` works in all modern browsers. The `fill` CSS class depends on the variable font having the wght axis. **Fine.**

### 8.2 Testing Matrix

| Device Class | Examples | Expected | Issues |
|-------------|----------|----------|--------|
| Desktop Chrome | Chrome 125+ on Win/Mac | ✅ Full | None |
| Desktop Firefox | FF 130+ on Win/Mac | ✅ Full | None |
| Desktop Safari | Safari 17+ on macOS | ⚠️ Minor | `color-mix()` may not tint intel chips |
| Mobile Chrome | Chrome 125+ on Android | ⚠️ Usable | Tables scroll, metric grid tight at <360px |
| Mobile Safari | Safari 17+ on iOS | ⚠️ Usable | Same + Modal backdrop-blur perf hit |
| Tablet Safari | Safari on iPadOS | ✅ Full | Sidebar width (260px) leaves ~500px for content |
| Edge | Edge on Win | ✅ Full | Same as Chrome |
| Samsung Internet | Samsung Browser 22+ | ⚠️ Usable | Same as mobile Chrome |

---

## 9. What's Missing (Feature Completeness Check)

### 9.1 Backend Features Without Frontend

- ⬜ Supplier SLA config UI (CRUD for `Supplier SLA Definition` records)
- ⬜ Supplier Payment Block dashboard (list active blocks, review, release)
- ⬜ Brand performance dashboard (rolling 90-day metrics)
- ⬜ Area performance dashboard (area-based breakdowns)
- ⬜ Brand delay summary (per-brand delay statistics)
- ⬜ QR-based customer self-service intake page (backend exists)
- ⬜ Stage advancement panel (explicit stage changer — currently only implicit via actions)
- ⬜ Role-appropriate quick actions (backend gates by role, frontend shows all buttons)
- ⬜ Scheduler job status display (reminder engine, performance computation)
- ⬜ Full customer profile view (ticket history, product history)

### 9.2 Missing UX Polish

- ⬜ Page transition animations (route transitions)
- ⬜ Loading states for data-dependent sections (not just full-page skeleton)
- ⬜ Empty state illustrations (svg illustrations instead of emoji)
- ⬜ Undo for non-destructive actions (e.g., "Ticket created" with undo)
- ⬜ Avatar/initials fallback with colors derived from name
- ⬜ Contextual help tooltips (ℹ️ icons explaining SLA/escalation/status)
- ⬜ Keyboard shortcut cheat sheet (available but not discoverable — no "?" hint on UI)
- ⬜ Copy-to-clipboard for ticket numbers
- ⬜ Auto-refresh toggle (keep dashboard data fresh without manual reload)
- ⬜ URL-based state for filter persistence (shareable filtered views)

### 9.3 Missing Developer Experience

- ⬜ ESLint configuration (no `.eslintrc` — only .prettierrc)
- ⬜ Pre-commit hooks for lint + format
- ⬜ Component unit tests (Vitest)
- ⬜ Storybook or similar component explorer
- ⬜ API mock service for isolated frontend development
- ⬜ Environment-based config (dev/staging/prod API URLs)
- ⬜ Changelog within the frontend directory

---

## 10. Architectural Decision Records (Suggested)

| ADR | Decision | Rationale |
|-----|----------|-----------|
| ADR-FE-001 | Use frappe-ui components | Already installed, Frappe-aware, follows existing patterns |
| ADR-FE-002 | Composition API + `<script setup>` | Already adopted — maintain consistency |
| ADR-FE-003 | No Pinia until cross-component state > 3 items | Current state is manageable |
| ADR-FE-004 | CSS custom properties for dynamic colors | Replace inline `:style` bindings |
| ADR-FE-005 | Progressive TypeScript adoption | Start with types, then utils, then components |
| ADR-FE-006 | Route-level code splitting | Already implemented — maintain |
| ADR-FE-007 | Modal composition pattern | Single LavModal wrapper with slots |
| ADR-FE-008 | Server-state only via API (no Pinia ORM) | Frappe is the single source of truth |

---

## 11. Code Organization Recommendations

```
frontend/src/
  main.js                      — App bootstrap (keep)
  router.js                    — Routes (keep, could split if >20 routes)
  api.js                       — Frappe API helper (enhance: abort, retry, types)
  
  assets/
    Inter/                     — Font files (keep)
    icons/                     — SVG icons for empty states, illustrations
  
  utils/
    theme.js                   — SINGLE source for all color tokens
    index.js                   — Formatting helpers (keep, add types)
    toast.js                   — Toast composable (keep, or use vue-sonner)
    api.types.d.ts             — TypeScript type definitions for API responses
  
  composables/                 — NEW: shared logic
    useTicket.js               — Ticket CRUD operations
    useFilters.js              — Filter state + persistence
    useKeyboard.js             — Keyboard shortcut registration
  
  components/
    common/                    — Shared reusable components
      LavShell.vue             — (extracted from AppShell — keep shell)
      LavModal.vue             — Generic modal wrapper
      LavConfirm.vue           — Confirmation dialog
      LavBadge.vue             — Status badge (wraps SlaBadge + status colors)
      LavEmptyState.vue        — Empty state with illustration
    tickets/                   — Ticket-related components
      TicketHeader.vue         — (extracted from TicketDetail)
      TicketSections.vue       — (extracted from TicketDetail)
      QuickActionPanel.vue     — (extracted from TicketDetail)
      FollowupTimeline.vue     — (extracted from TicketDetail)
      ActivityTimeline.vue     — (extracted from TicketDetail)
      ActionModal.vue          — (extracted from TicketDetail)
      SlaBadge.vue             — (kept as is)
  
  pages/
    TodayWork.vue              — Metric grid + Action Queue (keep, thin)
    Tickets.vue                — Ticket list (keep, add virtual scroll)
    NewTicket.vue              — Intake form (keep, add validation)
    Reports.vue                — Reports catalog (keep, add missing reports)
    PaymentBlocks.vue          — NEW: Supplier Payment Block dashboard
    BrandPerformance.vue       — NEW: Brand performance page
    AreaPerformance.vue        — NEW: Area performance page
    SupplierSla.vue            — NEW: SLA configuration
    NotFound.vue               — 404 (keep)
```

---

## 12. Technology Radar

| Technology | Status | Recommendation |
|-----------|--------|---------------|
| Vue 3.2.25 | CURRENT | Stay — upgrade to Vue 3.4+ for `defineModel`, better hydration |
| Vite 5 | CURRENT | Stay — upgrade to 6.x when stable |
| vue-router 4.0 | CURRENT | Stay — upgrade to 4.3+ for route-level suspense |
| Tailwind 3.4 | CURRENT | Stay — upgrade to 4.x only when frappe-ui supports it |
| frappe-ui (git HEAD) | CURRENT | **USE IT** — import Dialog, Select, DatePicker, Badge |
| Material Symbols | ADOPT | Good — continue, consider self-hosting icon font |
| TypeScript | ASSESS | Start with `@/utils/theme.js` → `theme.ts` |
| Pinia | ASSESS | Only when TicketDetail is extracted and shared state grows |
| TanStack Query | ASSESS | Add only if API call count triple or caching needs grow |
| vitest | ASSESS | Add for component tests |
| Playwright | ASSESS | Add for E2E testing of critical flows |
