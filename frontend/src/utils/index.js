export const STATUS_HUE = {
  New: '#004ac6',
  'Registration Pending': '#2563eb',
  'Brand Registered': '#0053db',
  'In Progress': '#004ac6',
  'Waiting on Customer': '#943700',
  'Waiting on Part / Approval': '#943700',
  'Ready for Pickup': '#1a7f37',
  Resolved: '#1a7f37',
  Closed: '#434655',
  Cancelled: '#ba1a1a',
}

export const DUE_HUE = { 'Due Soon': '#943700', Overdue: '#ba1a1a', Breached: '#ba1a1a', 'Not Due': '#1a7f37' }

export const PROMISE_HUE = { Breached: '#ba1a1a', Pending: '#0053db', Kept: '#1a7f37' }

export const ESC_HUE = { Coordinator: '#0053db', Manager: '#943700', Owner: '#ba1a1a', 'L1 - Agent Follow-up': '#0053db', 'L2 - Coordinator Escalation': '#2563eb', 'L3 - Manager Escalation': '#943700', 'L4 - Owner / Brand Manager Escalation': '#ba1a1a' }

export function hexToRgba(hex, a) {
  const h = hex.replace('#', '')
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${a})`
}

export function chip(status) {
  const hue = STATUS_HUE[status] || '#434655'
  return { color: hue, background: hexToRgba(hue, 0.12) }
}

export function escChip(level) {
  const hue = ESC_HUE[level] || '#434655'
  return { color: hue, background: hexToRgba(hue, 0.12) }
}

export function dueChip(status) {
  const hue = DUE_HUE[status] || '#434655'
  return { color: hue, background: hexToRgba(hue, 0.12) }
}

export function promiseChip(status) {
  const hue = PROMISE_HUE[status] || '#434655'
  return { color: hue, background: hexToRgba(hue, 0.12) }
}

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
  if (!value) return { color: '#737686' }
  const d = new Date(String(value).slice(0, 10))
  const today = new Date(new Date().toISOString().slice(0, 10))
  if (d < today) return { color: '#ba1a1a', fontWeight: '700' }
  if (d.getTime() === today.getTime()) return { color: '#943700', fontWeight: '700' }
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

// Follow-up tracking chip helpers (Phase 1N-6B)
const FOLLOWUP_STAGE_HUE = {
	technician_called: '#004ac6', technician_visited: '#2563eb',
	sc_followup_done: '#0053db', customer_informed: '#1a7f37',
	no_technician_update: '#ba1a1a', part_pending: '#943700',
	customer_confirmation_pending: '#712ae2', customer_not_satisfied: '#ba1a1a',
	registration_done: '#1a7f37',
}
export function stageChip(value) {
	const hue = FOLLOWUP_STAGE_HUE[value] || '#434655'
	return { color: hue, background: hexToRgba(hue, 0.12) }
}

const SATISFACTION_HUE = { Satisfied: '#1a7f37', 'Not Satisfied': '#ba1a1a', 'Customer Not Reachable': '#943700', 'Not Required': '#434655' }
export function satisfactionChip(value) {
	const hue = SATISFACTION_HUE[value] || '#434655'
	return { color: hue, background: hexToRgba(hue, 0.12) }
}

const INFORMED_HUE = { 'Informed by Call': '#1a7f37', 'Informed by WhatsApp': '#1a7f37', 'Informed by SMS': '#1a7f37', Pending: '#943700', 'Customer Not Reachable': '#ba1a1a', 'Not Required': '#434655', 'Informed': '#1a7f37' }
export function informedChip(value) {
	const hue = INFORMED_HUE[value] || '#434655'
	return { color: hue, background: hexToRgba(hue, 0.12) }
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
