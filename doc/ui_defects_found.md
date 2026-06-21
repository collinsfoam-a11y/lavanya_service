# UI Defects Found — Frontend Phase A

## Critical (Fixed)

1. **Native `confirm()` in TicketDetail.vue** — `submitAction()` used browser `confirm()` for danger actions. Replaced with `useConfirm()`/`LavConfirm`.

2. **4 inline modals missing focus traps** — Tab from last element (submit button) escaped modal into page background. All 4 converted to `<LavModal>` which implements a complete focus-trapping loop.

3. **"Open" buttons invisible to keyboard users** — `md:opacity-0 md:group-hover:opacity-100` on TodayWork.vue and Tickets.vue made buttons fully transparent on `md+` screens when not hovered. Keyboard tabbing never triggers `group-hover`. Fixed by adding `md:group-focus-within:opacity-100`.

4. **TodayWork `<li>` cards not keyboard-activatable** — Rows had `@click` but no `tabindex`, `role`, or keyboard handlers. Fixed with `tabindex="0"`, `role="button"`, `@keydown.enter/space.prevent`.

## Medium (Fixed)

5. **`aria-sort` hardcoded to "none"** — All 6 sortable `<th>` columns in Tickets.vue had `aria-sort="none"` regardless of actual sort state. Now dynamically reflects `ascending`/`descending`/`none`.

6. **Sort `aria-label` always reports current direction** — Headers always read "currently asc/desc" even when that column was not the active sort. Now reports "not sorted" for inactive columns.

7. **Sort arrows (▲/▼) not hidden from screen readers** — Unicode glyphs lacked `aria-hidden="true"`. Wrapped in `<span aria-hidden="true">`.

8. **Hardcoded color values** — ~15 locations across TicketDetail, TodayWork, Tickets used raw hex/rgba strings. Replaced with `COLORS.*` constants and `hexToRgba()` from `theme.js`.

9. **LavModal missing `aria-describedby`** — Dialog body not linked to modal. Added dynamic `bodyId` prop + auto-generated fallback ID.

10. **LavModal incomplete focus trap** — Tab escaped modal. Added `keydown` handler that wraps from first to last element and vice versa.

11. **AppShell missing keyboard shortcuts** — `g+t` and `?` not handled. Added global keydown listener.

12. **Search form missing `role="search"`** — Added `role="search"` landmark.

13. **Avatar icon missing `aria-hidden`** — Decorative person icon not hidden from screen readers. Added `aria-hidden="true"`.

## Low (Fixed)

14. **LavConfirm icon "warning" for danger actions** — Changed to `"warning"` icon for danger, `"help"` for normal (consistent with UX pattern).

15. **Empty state inline styles in TodayWork** — Hardcoded `color:#737686; font-size:14px` replaced with Tailwind classes.

16. **TicketDetail followupBanner raw hex** — 10 branches used inline hex/rgba. Converted to `hexToRgba(COLORS.*, alpha)` pattern.

17. **TicketDetail WhatsApp button hardcoded brand color** — `style="background:#25D366"` kept as-is (brand-specific color not suitable for theming).

## Not Fixed (Intentionally)

- **TicketDetail WhatsApp brand color (#25D366)** — Brand-specific color that should not be in the theme palette.
- **CSS hardcoded colors in `index.css`** — `.lav-shell`, `.lav-metric`, `.lav-queue`, `.lav-chip` classes use hardcoded hex values from the original Tailwind theme. These are framework-level and would require migrating to frappe-ui preset.

## Pre-existing (Not Caused by Phase A)

- No skip-to-main navigation link (needs AppShell restructuring)
- No `g+n` → New Ticket shortcut (mapped to `g+t` only)
- No axe-core or Playwright a11y test suite
