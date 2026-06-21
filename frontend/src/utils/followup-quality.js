/**
 * Follow-up Quality Badge computation.
 *
 * The badge is always computed from ticket state; it is never manually editable.
 */

export const QUALITY_LEVELS = ['Good', 'Needs Update', 'At Risk', 'Critical']

/**
 * Compute the quality badge for a ticket.
 *
 * @param {Object} ticket - ticket object from the SPA API (may include `stage` sub-object)
 * @returns {string} one of Good | Needs Update | At Risk | Critical
 */
export function computeFollowupQuality(ticket) {
  if (!ticket) return 'Good'
  const s = ticket.stage || ticket
  const esc = (s.escalation_level || s.computed_escalation_level || '').toString()
  const noUpdate = Number(s.no_update_count || 0)
  const informed = (s.customer_informed_status || s.customer_informed || '').toString()
  const overdue = (s.overdue_status || ticket.overdue_status || '').toString()
  const promise = (s.customer_promise_status || ticket.customer_promise_status || '').toString()
  const satisfaction = (s.customer_satisfaction_status || '').toString()
  const nextFollowUp = s.next_follow_up_date || s.computed_next_follow_up || null
  const partExpected = s.part_expected_date || null
  const partRequired = s.part_required || 0

  // Critical
  if (satisfaction === 'Not Satisfied') return 'Critical'
  if (overdue === 'Overdue' || promise === 'Breached') return 'Critical'
  if (esc && esc !== 'None' && noUpdate > 0) return 'Critical'
  if (partRequired && partExpected && new Date(partExpected) < new Date()) return 'Critical'
  if (s.closure_attempted_without_confirmation) return 'Critical'

  // At Risk
  if (esc && esc !== 'None') return 'At Risk'
  if (!informed || informed === 'Pending') return 'At Risk'
  if (overdue === 'Due Soon') return 'At Risk'

  // Needs Update
  if (!nextFollowUp) return 'Needs Update'
  if (noUpdate > 0) return 'Needs Update'
  if (partRequired && partExpected) {
    const daysUntil = Math.round((new Date(partExpected) - new Date()) / 86400000)
    if (daysUntil >= 0 && daysUntil <= 2) return 'Needs Update'
  }

  return 'Good'
}

/**
 * Return a human-readable reason for the quality level.
 */
export function qualityReason(ticket) {
  const level = computeFollowupQuality(ticket)
  const s = ticket?.stage || ticket || {}
  const esc = (s.escalation_level || s.computed_escalation_level || '').toString()
  const noUpdate = Number(s.no_update_count || 0)
  const informed = (s.customer_informed_status || s.customer_informed || '').toString()
  const overdue = (s.overdue_status || ticket?.overdue_status || '').toString()
  const promise = (s.customer_promise_status || ticket?.customer_promise_status || '').toString()
  const satisfaction = (s.customer_satisfaction_status || '').toString()

  if (level === 'Good') return 'Follow-up is on track.'
  if (satisfaction === 'Not Satisfied') return 'Customer is not satisfied.'
  if (overdue === 'Overdue') return 'Follow-up is overdue.'
  if (promise === 'Breached') return 'Customer promise breached.'
  if (esc && esc !== 'None' && noUpdate > 0) return 'Escalated with no recent update.'
  if (esc && esc !== 'None') return 'Case is escalated.'
  if (!informed || informed === 'Pending') return 'Customer has not been informed.'
  if (noUpdate > 0) return 'No update recorded.'
  if (overdue === 'Due Soon') return 'Follow-up is due soon.'
  if (!s.next_follow_up_date && !s.computed_next_follow_up) return 'Next follow-up date missing.'
  return 'Requires attention.'
}

export const QUALITY_COLORS = {
  Good: 'var(--lav-quality-good)',
  'Needs Update': 'var(--lav-quality-needs-update)',
  'At Risk': 'var(--lav-quality-at-risk)',
  Critical: 'var(--lav-quality-critical)',
}

export function qualityColor(level) {
  return QUALITY_COLORS[level] || QUALITY_COLORS.Good
}
