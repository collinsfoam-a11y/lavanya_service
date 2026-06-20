import { COLORS } from './theme.js'

export {
  COLORS,
  STATUS_HUE, DUE_HUE, PROMISE_HUE, ESC_HUE,
  FOLLOWUP_STAGE_HUE, SATISFACTION_HUE, INFORMED_HUE,
  chip, dueChip, promiseChip, escChip,
  stageChip, satisfactionChip, informedChip,
  hexToRgba, accentMetric, qualityChip, TIMELINE_STATE_COLORS,
  THEMES, DEFAULT_THEME, isValidTheme, getThemeNames, getThemeMeta,
  getAllThemeMeta, resolveTheme, readSavedTheme, saveTheme, applyTheme,
  initTheme, THEME_STORAGE_KEY,
} from './theme.js'

export {
  computeFollowupQuality,
  qualityReason,
  qualityColor,
  QUALITY_LEVELS,
} from './followup-quality.js'

export function product(t) {
  return [t.brand, t.product_item || t.product_type].filter(Boolean).join(' / ')
}

export function followText(value) {
  if (!value) return 'No follow-up date'
  const d = new Date(String(value).slice(0, 10))
  const today = new Date(new Date().toISOString().slice(0, 10))
  const opts = { day: 'numeric', month: 'short', year: 'numeric' }
  const disp = d.toLocaleDateString('en-GB', opts).replace(/ /g, '-')
  if (d < today) return 'Overdue: ' + disp
  if (d.getTime() === today.getTime()) return 'Due today: ' + disp
  return disp
}

export function followStyle(value) {
  if (!value) return { color: COLORS.onSurfaceVariant }
  const d = new Date(String(value).slice(0, 10))
  const today = new Date(new Date().toISOString().slice(0, 10))
  if (d < today) return { color: COLORS.error, fontWeight: '700' }
  if (d.getTime() === today.getTime()) return { color: COLORS.warning, fontWeight: '700' }
  return {}
}

export function fmtDT(value) {
  if (!value) return '—'
  const s = String(value).replace('T', ' ')
  return s.length >= 16 ? s.substring(0, 16) : s
}

export function ticketAge(creationDate) {
  if (!creationDate) return 0
  const created = new Date(creationDate)
  const diffTime = Math.abs(new Date() - created)
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}

export function relTime(value) {
  if (!value) return ''
  const d = new Date(String(value).replace(' ', 'T'))
  const secs = Math.round((Date.now() - d.getTime()) / 1000)
  if (secs < 60) return 'just now'
  const mins = Math.round(secs / 60)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.round(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.round(hrs / 24)
  if (days < 30) return `${days}d ago`
  return d.toLocaleDateString()
}


export function qualityBadge(ticket) {
  const s = ticket.stage || ticket
  const esc = s.escalation_level || ''
  const noUpdate = s.no_update_count || 0
  const informed = s.customer_informed_status || s.customer_informed
  const overdue = s.overdue_status || ticket.overdue_status
  const promise = s.customer_promise_status || ticket.customer_promise_status
  const satisfaction = s.customer_satisfaction_status

  if (satisfaction === 'Satisfied' || satisfaction === 'Not Required') return 'Good'
  if (esc && esc !== 'None' && noUpdate > 0) return 'Critical'
  if (esc && esc !== 'None') return 'At Risk'
  if (overdue === 'Overdue' || promise === 'Breached') return 'Critical'
  if (noUpdate > 0) return 'Needs Update'
  if (!informed || informed === 'Pending') return 'At Risk'
  if (overdue === 'Due Soon') return 'Needs Update'
  return 'Good'
}

export const FRIENDLY_LABELS = {
  followup_stage: 'Follow-up Stage',
  customer_informed_status: 'Customer Updated?',
  current_service_stage: 'Current Service Step',
  no_update_count: 'No-update Count',
  escalation_level: 'Escalation Level',
  service_path: 'Service Path',
  service_flow_type: 'Service Flow',
  customer_satisfaction_status: 'Satisfaction',
  customer_informed: 'Customer Informed',
  pending_reason: 'Pending Reason',
  next_follow_up_date: 'Next Follow-up',
  stage_due_at: 'Stage Due',
  overdue_status: 'Due Status',
  customer_promise_status: 'Promise Status',
  brand_ticket_number: 'Brand Ticket',
  registration_date: 'Registration Date',
  work_narration: 'Work Summary',
  closure_type: 'Closure Type',
  customer_confirmation_received: 'Customer Confirmed',
}

export function friendlyLabel(fieldname) {
  return FRIENDLY_LABELS[fieldname] || fieldname
}
