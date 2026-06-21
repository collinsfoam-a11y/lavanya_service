import {
  THEMES,
  DEFAULT_THEME,
  isValidTheme,
  getThemeNames,
  getThemeMeta,
  getAllThemeMeta,
  resolveTheme,
  readSavedTheme,
  saveTheme,
  applyTheme,
  initTheme,
  THEME_STORAGE_KEY,
} from './theme-engine.js'

export {
  THEMES,
  DEFAULT_THEME,
  isValidTheme,
  getThemeNames,
  getThemeMeta,
  getAllThemeMeta,
  resolveTheme,
  readSavedTheme,
  saveTheme,
  applyTheme,
  initTheme,
  THEME_STORAGE_KEY,
}

/**
 * Default light-theme color palette.
 *
 * These static tokens remain for backward compatibility with components that
 * import COLORS directly. New code should prefer the CSS custom properties
 * applied by the theme engine (e.g. `var(--lav-primary)`) or the reactive
 * `useTheme()` composable so the UI responds to theme changes.
 */
export const COLORS = {
  primary: '#004ac6',
  secondary: '#0053db',
  tertiary: '#712ae2',
  error: '#ba1a1a',
  warning: '#943700',
  success: '#1a7f37',
  neutral: '#434655',
  surface: '#f8f9ff',
  surfaceContainer: '#ffffff',
  outline: '#c3c6d7',
  outlineVariant: '#c3c6d7',
  onSurface: '#121c28',
  onSurfaceVariant: '#434655',
  info: '#2563eb',
}

export function hexToRgba(hex, a = 0.12) {
  const h = hex.replace('#', '')
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${a})`
}

function chipFn(hueMap) {
  return function (value) {
    const hue = hueMap[value] || COLORS.neutral
    return { color: hue, background: hexToRgba(hue, 0.12) }
  }
}

export const STATUS_HUE = {
  New: COLORS.primary,
  'Registration Pending': '#2563eb',
  'Brand Registered': COLORS.secondary,
  'In Progress': COLORS.primary,
  'Waiting on Customer': COLORS.warning,
  'Waiting on Part / Approval': COLORS.warning,
  'Ready for Pickup': COLORS.success,
  Resolved: COLORS.success,
  Closed: COLORS.neutral,
  Cancelled: COLORS.error,
}

export const DUE_HUE = { 'Due Soon': COLORS.warning, Overdue: COLORS.error, Breached: COLORS.error, 'Not Due': COLORS.success }
export const PROMISE_HUE = { Breached: COLORS.error, Pending: COLORS.secondary, Kept: COLORS.success }
export const ESC_HUE = { Coordinator: COLORS.secondary, Manager: COLORS.warning, Owner: COLORS.error, 'L1 - Agent Follow-up': COLORS.secondary, 'L2 - Coordinator Escalation': COLORS.info, 'L3 - Manager Escalation': COLORS.warning, 'L4 - Owner / Brand Manager Escalation': COLORS.error }

export const FOLLOWUP_STAGE_HUE = {
  technician_called: COLORS.primary, technician_visited: COLORS.info,
  sc_followup_done: COLORS.secondary, customer_informed: COLORS.success,
  no_technician_update: COLORS.error, part_pending: COLORS.warning,
  customer_confirmation_pending: COLORS.tertiary, customer_not_satisfied: COLORS.error,
  registration_done: COLORS.success,
}

export const SATISFACTION_HUE = { Satisfied: COLORS.success, 'Not Satisfied': COLORS.error, 'Customer Not Reachable': COLORS.warning, 'Not Required': COLORS.neutral }
export const INFORMED_HUE = { 'Informed by Call': COLORS.success, 'Informed by WhatsApp': COLORS.success, 'Informed by SMS': COLORS.success, Pending: COLORS.warning, 'Customer Not Reachable': COLORS.error, 'Not Required': COLORS.neutral, Informed: COLORS.success }

export const chip = chipFn(STATUS_HUE)
export const dueChip = chipFn(DUE_HUE)
export const promiseChip = chipFn(PROMISE_HUE)
export const escChip = chipFn(ESC_HUE)
export const stageChip = chipFn(FOLLOWUP_STAGE_HUE)
export const satisfactionChip = chipFn(SATISFACTION_HUE)
export const informedChip = chipFn(INFORMED_HUE)

export const ACCENT_METRICS = {
  overdue_follow_up: COLORS.error,
  no_technician_update: COLORS.error,
  escalated_cases: COLORS.error,
  customer_not_informed: COLORS.warning,
  technician_call_due: COLORS.primary,
  technician_visit_due: COLORS.info,
  due_today: COLORS.warning,
  registration_recommended: COLORS.primary,
  registration_pending: COLORS.info,
  waiting_on_customer: COLORS.secondary,
  waiting_on_part: COLORS.warning,
  ready_for_pickup: COLORS.success,
  customer_satisfaction_pending: COLORS.tertiary,
  product_receipt_missing: COLORS.tertiary,
  closure_pending: COLORS.neutral,
  new_complaints: COLORS.primary,
  upcoming_work: COLORS.neutral,
}

export function accentMetric(key) {
  return ACCENT_METRICS[key] || COLORS.primary
}

export const PAYMENT_HUE = {
  'Pending Review': COLORS.warning,
  Active: COLORS.error,
  Released: COLORS.success,
}

export const EXPANSION_HUE = {
  store_service: COLORS.primary,
  replacement: COLORS.secondary,
  return: COLORS.warning,
}

export const DARK_MODE_OVERRIDES = {
  surface: '#1a1c2e',
  surfaceContainer: '#232538',
  surfaceVariant: '#2a2d40',
  outline: '#434655',
  outlineVariant: '#3a3d52',
  onSurface: '#e3e2e7',
  onSurfaceVariant: '#c3c6d7',
}

export function darkModeColor(key) {
  return DARK_MODE_OVERRIDES[key] || COLORS[key] || COLORS.onSurface
}

export const BLOCK_HUE = { blocked: COLORS.error, unblocked: COLORS.success }
export const warrantyHue = chipFn({ 'In Warranty': COLORS.success, 'Out of Warranty': COLORS.warning })
export const paymentChip = chipFn(PAYMENT_HUE)
export const expansionChip = chipFn(EXPANSION_HUE)
export const blockChip = chipFn(BLOCK_HUE)

export const QUALITY_HUE = {
  Good: COLORS.success,
  'Needs Update': COLORS.warning,
  'At Risk': '#f59e0b',
  Critical: COLORS.error,
}

export const TIMELINE_STATE_COLORS = {
  completed: COLORS.success,
  current: COLORS.primary,
  waiting: COLORS.warning,
  blocked: COLORS.error,
  pending: COLORS.outline,
}

export function qualityChip(value) {
  const hue = QUALITY_HUE[value] || COLORS.neutral
  return { color: hue, background: hexToRgba(hue, 0.12) }
}
