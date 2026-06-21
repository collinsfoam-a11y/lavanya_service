# Lavanya Service Console — Frontend Audit

## 1. Architecture Overview

Single-page application (SPA) built with **Vue 3 Composition API** + **Vite** + **vue-router** + **Tailwind CSS (frappe-ui preset)**. Served from `/frontend` via Frappe's static file routing. Not a Frappe Desk extension — fully standalone SPA that communicates with the Frappe backend via REST API calls.

**File map:**

```
frontend/src/
  main.js               — Bootstrap (createApp, errorHandler)
  App.vue               — Root: keyboard shortcuts, error boundary, help overlay
  router.js             — 5 routes (lazy-loaded), base: /frontend
  api.js                — Frappe API helper (call GET, post POST)
  index.css             — Tailwind base + lav-* layout component classes
  pages/
    TodayWork.vue       — Today's Work dashboard (metric grid + action queue)
    Tickets.vue         — Ticket list (search, filters, sort, infinite scroll)
    NewTicket.vue       — Staff intake form (customer lookup, brand/product selects)
    Reports.vue         — Reports catalog + trend chart + drill-down + CSV export
    NotFound.vue        — 404 fallback
  components/
    AppShell.vue        — Layout: sidebar, header, mobile bottom nav, slot
    TicketDetail.vue    — Full ticket detail drawer (~1552 lines)
    SlaBadge.vue        — SLA status pill
  utils/
    index.js            — Chip generators, color maps, formatting helpers
    toast.js            — Global toast notification state
  assets/
    Inter/inter.css     — Inter font (no local files — Google Fonts URL)
```

## 2. Component Tree

```
App.vue
├── AppShell.vue (layout wrapper via slot)
│   ├── sidebar (260px, fixed, nav items)
│   ├── header (sticky, search bar, user avatar)
│   ├── <router-view> (page content)
│   └── mobile-bottom-nav (fixed bottom bar — 4 items)
│
├── [TodayWork.vue]        — Metric grid (6 columns) + Action Queue bucket list
│   ├── SlaBadge.vue (per row)
│   └── TicketDetail.vue (drawer on click)
│
├── [Tickets.vue]          — Search bar + status chips + sortable table + infinite scroll
│   ├── SlaBadge.vue (per row)
│   └── TicketDetail.vue (drawer on click)
│
├── [NewTicket.vue]        — Full-page form with customer lookup
│
├── [Reports.vue]          — Catalog grid → drill-down table + inline trend SVG
│   └── TicketDetail.vue (drawer on click)
│
└── [NotFound.vue]         — Static 404 page
```

**TicketDetail.vue** sub-component tree:

```
TicketDetail.vue (drawer overlay)
├── Main detail panel (scrollable)
│   ├── Header (status, priority, SLA, WhatsApp, Helpdesk link)
│   ├── Sticky section nav (10 sections)
│   ├── Repeat complaint banner (candidates / linked)
│   ├── Service Stage section
│   ├── Reminder Intelligence section
│   ├── AI Advisory section (accept/ignore buttons)
│   ├── Follow-up Tracking section (stepper, banner, part/financial cards)
│   ├── Customer section
│   ├── Product section
│   ├── Workflow section
│   ├── Product Custody section
│   ├── Follow-up history timeline
│   └── Activity timeline + add note
├── Quick Action panel (fixed width, scrollable)
│   ├── 5 primary action buttons
│   ├── Follow-up Journey stepper (from AI engine)
│   ├── Alternative actions
│   ├── Product Receipt / Ready for Pickup / Customer Confirmed / Close
│   └── Product custody movements (conditional)
├── Need Invoice modal
├── Create Product Receipt modal
├── Mark Ready for Pickup modal
└── Generic Action modal (dynamic form fields per action type)
```

## 3. Routing

| Path | Component | Lazy-loaded |
|------|-----------|-------------|
| `/` | TodayWork.vue | Yes |
| `/tickets` | Tickets.vue | Yes |
| `/new-ticket` | NewTicket.vue | Yes |
| `/reports` | Reports.vue | Yes |
| `/:pathMatch(.*)*` | NotFound.vue | Yes |

Base: `createWebHistory('/frontend')`. Query params used for search (`?search=`) in Tickets page.

**Gaps:** No route guards (auth assumed by Frappe session), no navigation guards, no route meta for roles/permissions.

## 4. State Management

No Pinia/Vuex. State is contained per-component via `ref()` and `reactive()`:

- **TodayWork.vue**: `raw`, `loading`, `error`, `selectedTicket`, `showFilters`, `filters` (reactive)
- **Tickets.vue**: `tickets[]`, `loading`, `error`, `hasMore`, `search`, `status`, `sortKey`, `sortDir`
- **NewTicket.vue**: `opts`, `loadingOptions`, `submitting`, `error`, `created`, `lookupHint`, `form` (reactive)
- **Reports.vue**: `catalog[]`, `loadingCatalog`, `active`, `overview`, `selectedTicket`
- **TicketDetail.vue**: `ticket`, `loading`, `activity[]`, `noteText`, `modals`, `actionForm` (reactive)

**Global state:** Only toast notifications via composable (`useToast()` — singleton `ref`).

**Gaps:** No centralized state management — drawer open state is duplicated in every page that opens tickets. No cached API responses. Refreshing a page re-fetches all data.

## 5. API Layer

`api.js` provides two functions:

- **`call(method, params)`** — GET requests via `fetch()`, unwraps `data.message`. Cleans null/undefined params. Uses `cache: 'no-store'`.
- **`post(method, body)`** — POST with CSRF token (`window.csrf_token`), JSON body. Handles 400 errors (stale CSRF) with actionable messages.

Both throw on non-OK responses. Server messages parsed from `_server_messages` JSON structure.

**Endpoints called (14 unique methods):**
- `today_work.get_today_work`
- `stitch_console.get_ticket_list`
- `stitch_console.get_ticket_detail`
- `stitch_console.get_ticket_activity`
- `stitch_console.get_new_ticket_options`
- `stitch_console.create_ticket`
- `stitch_console.schedule_appointment`
- `stitch_console.set_customer_promise`
- `stitch_console.add_ticket_note`
- `workflow_actions.*` (7 endpoints)
- `product_receipt_actions.*` (4 endpoints)
- `customer_intake.lookup_customer_by_mobile`
- `repeat_complaints.*` (3 endpoints)
- `ai_advisory.*` (3 endpoints)
- `manager_reports.*` (4 endpoints)

**Gaps:** No retry logic, no request cancellation, no caching layer, no TypeScript types for API responses.

## 6. Design System Compliance

**Tailwind frappe-ui preset** provides colors: `primary`, `secondary`, `tertiary`, `error`, `surface-container-*`, `on-surface`, etc.

**Custom CSS classes (`index.css` — ~400 lines):**
- `.lav-shell`, `.lav-sidebar`, `.lav-main`, `.lav-header` — layout
- `.lav-metric-grid`, `.lav-metric` — Today's Work cards
- `.lav-queue`, `.lav-bucket`, `.lav-badge` — action queue
- `.lav-search`, `.lav-chips`, `.lav-chip` — search/filters
- `.lav-intel` — reminder intelligence pill
- `.lav-input` — form inputs
- `.lav-skeleton` — shimmer loading
- `.lav-work-card` — work list rows
- `.lav-mobile-nav` — bottom navigation

**Typography:** Inter font via Google Fonts (`@import`), sizes via `font-body-md`, `font-headline-lg` classes from frappe-ui.

**Icons:** Google Material Symbols Outlined (variable font, `@import`).

**SLA color tokens duplicated** in `utils/index.js` (STATUS_HUE, DUE_HUE, PROMISE_HUE, ESC_HUE) and in `TicketDetail.vue` (FOLLOWUP_ACTION_STYLES, followupBanner).

**Gaps:** 
- Color token duplication between utils/ and TicketDetail.vue (FOLLOWUP_ACTION_STYLES hardcodes 8 actions)
- No design token system — colors hardcoded in CSS and JS
- Tailwind theme `extend.colors` not fully utilized for custom Lavanya colors
- Material Symbols import uses `http://fonts.googleapis.com` (no HTTPS) — mixed content risk on HTTPS sites

## 7. Responsiveness

| Breakpoint | Behavior |
|------------|----------|
| `< 640px` | Single column, mobile bottom nav visible, sidebar hidden |
| `640px+` | Metric grid 2-col, card grids 2-col |
| `768px+` | Sidebar visible (260px), mobile nav hidden, desktop header with search |
| `1200px+` | Metric grid 6-col |

**Ticket detail drawer:** Full width on mobile, `max-w-4xl` + side panel (320px) on desktop.

**Gaps:**
- No `<meta name="viewport">` considerations beyond default
- No tablet-specific breakpoints (640-768 gap for some layouts)
- `.lav-card-grid` uses 2-col below 640px — may be tight on very small screens
- Modals use `max-w-lg` / `max-w-2xl` with `mx-4` — ok on mobile but no full-screen modal option

## 8. Accessibility

**Present:**
- `tabindex="0"` on interactive cards (TodayWork, Tickets)
- `role="button"` on clickable metric cards
- `aria-label="Search tickets"` on search input (AppShell)
- `prefers-reduced-motion` media query in CSS
- `focus-visible` outline styles in base layer
- `@keydown.enter` on some interactive elements
- Keyboard shortcut system in App.vue (g+h, g+t, g+n, g+r, ?, Esc)

**Missing:**
- No `aria-live` regions for dynamic content (queue loading, search results)
- No `aria-expanded` on filter toggles
- No focus trap in modals or the TicketDetail drawer
- No `role="dialog"` / `aria-modal` on drawer/modals
- No skip-to-content link
- No heading hierarchy validation (multiple `<h2>` with no `<h1>` — sidebar h1 is hidden in mobile)
- Color contrast not verified (some light backgrounds with lighter text)
- No ARIA labels on icon-only buttons (close, clear search)
- No loading announcements for screen readers (skeleton visible but not announced)

## 9. Performance

**Strengths:**
- Lazy-loaded routes (code splitting per page)
- `cache: 'no-store'` on API calls prevents stale data
- Debounced search (300ms) in Tickets.vue
- Infinite scroll with IntersectionObserver
- SVG trend chart instead of canvas/library (lightweight)
- `v-for` with `:key` on all lists

**Concerns:**
- **No virtual scrolling** — TicketDetail's activity/follow-up lists render all items
- Ticket list can grow unbounded (infinite scroll with no virtualization)
- `color-mix()` CSS function in `.lav-intel` — not supported in older browsers (CSS Color Level 5)
- No request deduplication (rapid filter changes trigger parallel API calls)
- No image optimization (none used, but worth noting)

## 10. Code Quality Observations

**Strengths:**
- Consistent Composition API with `<script setup>`
- Clear component separation (AppShell wraps pages via slot)
- Well-commented file headers explaining origin/purpose
- Clean error handling with user-facing messages
- Consistent naming convention (PascalCase components, camelCase variables)
- API helper handles common edge cases (null params, stale CSRF, server messages)
- Toast system is simple and effective

**Issues:**
1. **TicketDetail.vue is 1552 lines** — the largest component by far. Should be split into: `TicketDetailHeader`, `TicketSections` (accordion/tabs), `QuickActionPanel`, `ActionModal`, `FollowupTimeline`, `ActivityTimeline`
2. **Color token duplication** — `STATUS_HUE` in repo`utils/index.js` vs `FOLLOWUP_ACTION_STYLES` in TicketDetail.vue vs `STATUS_HUE` in Reports.vue. Three copies of similar status color maps
3. **No shared types** — API response shapes are inferred, not defined. No TypeScript despite Vue 3 having excellent TS support
4. **Inline styles** — heavy use of `:style` bindings for dynamic colors throughout. A `computed` or CSS variable approach would be cleaner
5. **Modal duplication** — Three separate modal implementations (NeedInvoice, CreateReceipt, ReadyPickup) with near-identical structure. Could use a generic modal component
6. **Direct `window` access** in AppShell.confirmLogout (`window.location.href = '/api/method/logout'`) — fragile
7. **`@click.prevent` on anchors** in TicketDetail section nav — should use `<button>` for interactive elements
8. **`confirm()` calls** in modals — blocks UI, not mobile-friendly. Should use custom confirm dialog
9. **Utility duplication** — `chip()`, `hexToRgba()` defined in both `utils/index.js` and `Reports.vue`
10. **No unit tests** for any frontend component

## 11. Browser Compatibility

- Material Symbols variable font (`opsz,wght,FILL,GRAD`) requires Chromium 94+/Firefox 100+/Safari 16+
- `color-mix()` requires Chromium 111+/Firefox 113+/Safari 16.2+
- `backdrop-blur` requires Chromium 76+/Firefox 103+/Safari 15+
- IntersectionObserver requires Chromium 51+/Firefox 55+/Safari 12.1+
- CSS Grid requires Chromium 57+/Firefox 52+/Safari 10.1+
- `prefers-reduced-motion` requires Chromium 74+/Firefox 63+/Safari 10.1+
- **No support for IE11** — acceptable for modern SPA
- **Potential issue:** `color-mix()` may not render correctly in all browsers (used in `.lav-intel` hover/active states)

## 12. Upgrade Suggestions

### High Priority
1. **Split TicketDetail.vue** (~1552 lines) into focused sub-components
2. **Consolidate color tokens** into a single source (theme config or utils)
3. **Eliminate utility duplication** — remove `chip()`/`hexToRgba()` from Reports.vue, use utils import
4. **Add TypeScript** — start with API response types, then component props
5. **Replace `color-mix()`** with pre-computed RGBA fallback for wider browser support

### Medium Priority
6. **Generic modal component** — extract shared modal layout (overlay, header, body, footer, transitions)
7. **Focus trap** in modals and drawer for keyboard accessibility
8. **ARIA attributes** — `aria-live`, `aria-expanded`, `role="dialog"`, `aria-modal`
9. **Heading hierarchy** — ensure one `<h1>` per page
10. **Custom confirm dialog** — replace `confirm()` calls with SPA-native dialog

### Low Priority
11. **Virtual scrolling** for activity/follow-up lists if they grow large
12. **Pinia store** for shared state (selected ticket, filters, user session)
13. **Route guards** for role-based access
14. **ESLint + Prettier** configuration
15. **Component unit tests** with Vitest + Vue Test Utils
16. **HTTPS** for Google Fonts import (`https://` protocol)

## 13. Comparison to Modern Vue 3 Standards

| Criteria | Status | Notes |
|----------|--------|-------|
| Composition API | ✅ | `<script setup>` throughout |
| TypeScript | ❌ | All JS — no `.ts` files |
| Pinia state | ❌ | Component-local state only |
| Route guards | ❌ | No `beforeEach` / `beforeResolve` |
| Component tests | ❌ | None |
| E2E tests | ❌ | None |
| Code splitting | ✅ | Route-level dynamic imports |
| Tree-shaking | ✅ | Vite + ES modules |
| SSR/SSG | ❌ | Not applicable (Frappe SPA) |
| Accessible | ⚠️ | Partial — missing ARIA + focus management |
| Responsive | ✅ | 3 breakpoints, mobile-first |
| Design tokens | ❌ | Colors duplicated across files |
| Form validation | ⚠️ | Manual in-component — no library |
| Loading states | ✅ | Skeletons, spinners, disabled buttons |
| Error boundaries | ✅ | App-level `onErrorCaptured` + per-page catch |
