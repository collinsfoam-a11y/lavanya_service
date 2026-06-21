# UX-R1 — UI/UX Study Report

## Executive Summary

The Lavanya Service SPA is functionally complete and pilot-ready. However, from a staff usability perspective, several areas need refinement for real showroom use. This report identifies usability gaps ranked by severity and provides concrete fixes.

**Biggest UX risks for pilot:**
1. Ticket Detail has 19 sections in a single long scroll — staff will miss critical info
2. Mobile bottom nav hides WhatsApp, Customer 360, and New Ticket — key pages are buried
3. Closure guard reason is low-contrast text — could be missed during closure attempts
4. Field Mode action buttons lead to wrong pages (Call Customer → Today's Work)

**Recommended fix priority:** P0 → P1 → P2, implement in this order.

---

## Page-by-Page Findings

### Today's Work (Dashboard)

| Finding | Severity | Detail |
|---|---|---|
| 15 metric groups is data-rich but functional | P2 | Staff understand the Critical/Important/Normal tiers |
| Filter bar is always visible, takes vertical space on mobile | P2 | Consider collapsible by default on mobile |
| Reminder intel chips are useful click-to-filter shortcuts | OK | No change needed |
| Bucket grouping is clear | OK | No change needed |
| Mobile cards are readable | OK | `LavTicketCard` compact variant works |

### Tickets List

| Finding | Severity | Detail |
|---|---|---|
| Desktop table columns are sortable with clear headers | OK | No change needed |
| Mobile card view works well | OK | `LavTicketCard` with Next Action + Quality |
| 8 saved filters cover common queries | OK | No change needed |
| "Open" button hidden on desktop until hover | P3 | Minor — staff hover naturally |

### New Ticket

| Finding | Severity | Detail |
|---|---|---|
| Customer lookup with auto-fill is fast | OK | No change needed |
| Previous product chips are excellent for speed | OK | No change needed |
| Brand metadata below select is useful | OK | No change needed |
| Mobile form is single-column, scrollable | P2 | Could benefit from stepper/wizard on mobile |
| Duplicate product warning missing | P2 | Same product+brand+model should warn before submit |

### Ticket Detail — CRITICAL

| # | Finding | Severity | Detail |
|---|---|---|---|
| 1 | **19 sections in one scroll** | **P0** | Staff must scroll through 19 sections to find what they need. Critical info (Next Action, Closure Guard) gets lost. |
| 2 | **Closure guard reason is low-contrast text** | **P1** | Red/green background but reason is small body text. Staff might miss why closure is blocked. |
| 3 | **No section status indicators** | P1 | Sections have no visual hint about their state — staff must open each to find issues. |
| 4 | **Sticky nav is horizontal scroll** | P2 | On mobile, the section nav bar requires horizontal scrolling — hard to use. |
| 5 | **No collapse/expand** | P2 | All 19 sections are always open. No way to hide resolved/irrelevant sections. |
| 6 | **Customer Informed status buried** | P2 | The customer-informed field is in the Stage section, not prominent. |
| 7 | **No "scroll to top" on mobile** | P3 | After scrolling 19 sections, returning to top requires manual scroll. |
| 8 | **Quick Actions panel at bottom** | P2 | On mobile, the actions panel is at the very bottom — staff must scroll past everything to act. |

### Customer 360

| Finding | Severity | Detail |
|---|---|---|
| Identity + ticket summary layout is clean | OK | Good first impression |
| Product/warranty cards are concise | OK | No change needed |
| CRM card shows useful context | OK | No change needed |
| WhatsApp summary is compact | OK | No change needed |
| No "Open in Ticket Detail" shortcut for active tickets | P2 | Clicking an active ticket opens drawer but label says "Open" not clear |

### WhatsApp Inbox

| Finding | Severity | Detail |
|---|---|---|
| Draft-only safety banner is visible | OK | Good |
| Inbound message list is scannable | OK | No change needed |
| Draft review workflow is clear | OK | No change needed |
| Empty state when DocTypes missing is handled | OK | Good defensive coding |

### Reports

| Finding | Severity | Detail |
|---|---|---|
| 8 tabs cover needed views | OK | No change needed |
| Safety banners on Penalty/Notifications are visible | OK | Good |
| Executive summary cards are scannable | OK | No change needed |
| Tab bar scrolls horizontally — mobile OK | P2 | Acceptable |

### Settings

| Finding | Severity | Detail |
|---|---|---|
| Manager/read-only mode is clearly indicated | OK | Good |
| Safety locks panel is prominent | OK | Good |
| CRM safety state card is clear | OK | Good |
| Save/reset bar is sticky | OK | Good |

### Field Mode

| # | Finding | Severity | Detail |
|---|---|---|---|
| 1 | **"Call Customer" routes to Today's Work** | **P1** | Button label says "Call Customer" but navigates to `/`. Misleading for counter staff. |
| 2 | **"Verify Visit" routes to Today's Work** | **P1** | Same problem — button implies an action but just navigates. |
| 3 | **"WhatsApp Draft" opens first search result** | P2 | Useful if results exist, but does nothing if no search was done. |
| 4 | **Critical work grid is useful** | OK | 4 stat cards show overdue, due today, ready pickup, new |
| 5 | **Recent work cards are good** | OK | Shows latest 5 tickets |

### Mobile Layout

| # | Finding | Severity | Detail |
|---|---|---|---|
| 1 | **Bottom nav only 4 items** | **P1** | WhatsApp, Customer 360, New Ticket hidden. Staff must use sidebar to access. |
| 2 | Sidebar hidden, bottom nav visible — correct | OK | Good responsive behavior |
| 3 | Ticket Detail becomes full-width on mobile — correct | OK | Good |
| 4 | Compact Counter Mode reduces spacing — works | OK | Good for counter screens |

### High Contrast Theme

| Finding | Severity | Detail |
|---|---|---|
| Black bg, white text, yellow primary — good contrast | OK | Accessible |
| Color-only indicators have text labels alongside | OK | Good |
| Inline styles using `color-mix` inherit theme vars | OK | Verified in code |

### Accessibility

| Finding | Severity | Detail |
|---|---|---|
| Focus-visible ring on all interactive elements | OK | `*:focus-visible { outline: 2px solid var(--lav-primary) }` |
| Modal focus trap in LavModal | OK | Tab cycles within modal |
| TicketDetail drawer no focus trap | P3 | Tab can escape to background — low risk |
| Icon buttons have aria-labels | OK | Verified in AppShell, TicketDetail, etc. |
| Keyboard shortcuts (g+h, g+t, etc.) | OK | Documented in App.vue help overlay |
| Reduced motion media query respected | OK | `prefers-reduced-motion: reduce` in index.css |

---

## Prioritized Fix List

### P0 — Blocks pilot usage
1. Add collapsible section groups to Ticket Detail
2. Make closure guard reason prominent (larger text, icon, persistent)

### P1 — Slows staff significantly
3. Make Customer Informed status visible at ticket header level
4. Fix Field Mode action buttons (Call Customer → tel: link, Verify Visit → open ticket)
5. Expand mobile bottom nav to 5 items (add WhatsApp)
6. Add section status chips (Missing Info / Needs Action / Safe / Blocked)

### P2 — Improves usability
7. Collapse lower-priority sections by default
8. Move Quick Actions panel closer to top on mobile
9. Add "scroll to top" button in Ticket Detail
10. Warn on duplicate product in New Ticket

### P3 — Future enhancement
11. Ticket Detail drawer focus trap
12. Mobile stepper/wizard for New Ticket
13. "Open in Ticket Detail" clearer label in Customer 360

---

## Safety Confirmation

All fixes in this pass are UI-only. No business rules, closure guards, safety locks, or backend logic will be changed.

Prepared: 2026-06-21
