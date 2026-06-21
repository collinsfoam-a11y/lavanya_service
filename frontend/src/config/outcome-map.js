/**
 * OUTCOME_MAP — Config-driven action mapping for the Outcome-Capture Console.
 *
 * Maps followup_stage values to their available outcome actions. Each stage
 * defines which actions are "primary" (most likely next step), "secondary"
 * (available but less likely), and "danger" (escalation/closure).
 *
 * This replaces the hardcoded nextActions computed property with a
 * deterministic, config-driven approach. The engine decides what actions
 * are available; the UI just renders them.
 *
 * Field mapping (no loop_type exists in this codebase):
 *   followup_stage → the actual post-brand follow-up sub-stage
 *   current_service_stage → the canonical workflow stage
 *   status → the HD Ticket status
 *
 * Each action entry references a key from the ACTIONS config in TicketDetail.vue,
 * or defines a custom action with endpoint + fields inline.
 */

// ── Stage → Action mapping ──────────────────────────────────────────────────
// Keys match FOLLOWUP_STAGE_OPTIONS from setup/followup_fields.py
// Values define which actions are available at each stage.

export const STAGE_ACTIONS = {
  // ── Pre-brand registration ────────────────────────────────────────────────
  registration_done: {
    description: 'Brand registered — awaiting service center follow-up',
    primary: ['record_sc_followup'],
    secondary: ['inform_customer', 'set_reverification_date'],
    danger: ['escalate_case'],
  },

  // ── Technician follow-up loop ─────────────────────────────────────────────
  technician_call_pending: {
    description: 'Verify if technician called the customer',
    primary: ['verify_tech_called'],
    secondary: ['record_sc_followup', 'inform_customer'],
    danger: ['escalate_case'],
  },

  technician_called: {
    description: 'Technician called — await visit or escalate',
    primary: ['confirm_appointment', 'record_sc_followup'],
    secondary: ['inform_customer', 'set_reverification_date'],
    danger: ['escalate_case', 'mark_no_update'],
  },

  technician_visit_pending: {
    description: 'Technician visit pending — confirm or mark missed',
    primary: ['mark_technician_visited', 'mark_appointment_missed'],
    secondary: ['record_sc_followup', 'inform_customer'],
    danger: ['escalate_case'],
  },

  technician_visited: {
    description: 'Technician visited — record outcome or verify customer',
    primary: ['verify_customer_after_visit', 'record_sc_followup'],
    secondary: ['inform_customer', 'record_part_required'],
    danger: ['escalate_case'],
  },

  no_technician_update: {
    description: 'No update from technician — escalate or follow up',
    primary: ['record_sc_followup', 'mark_no_update'],
    secondary: ['inform_customer'],
    danger: ['escalate_case'],
  },

  // ── Service center follow-up ──────────────────────────────────────────────
  sc_followup_done: {
    description: 'SC follow-up recorded — inform customer or set reverify',
    primary: ['inform_customer', 'set_reverification_date'],
    secondary: ['record_sc_followup'],
    danger: ['escalate_case'],
  },

  // ── Customer communication ────────────────────────────────────────────────
  customer_informed: {
    description: 'Customer informed — await response or close',
    primary: ['set_reverification_date'],
    secondary: ['record_sc_followup', 'inform_customer'],
    danger: ['escalate_case'],
  },

  // ── Part pending ──────────────────────────────────────────────────────────
  part_pending: {
    description: 'Part pending — update ETA or mark ready',
    primary: ['update_part_eta', 'mark_product_ready'],
    secondary: ['record_sc_followup', 'inform_customer'],
    danger: ['escalate_case'],
  },

  // ── Customer verification ─────────────────────────────────────────────────
  customer_confirmation_pending: {
    description: 'Awaiting customer confirmation after service',
    primary: ['verify_customer_after_visit', 'record_satisfaction'],
    secondary: ['inform_customer', 'set_reverification_date'],
    danger: ['escalate_case'],
  },

  customer_satisfied: {
    description: 'Customer satisfied — ready to close',
    primary: ['customer_confirmed', 'close_ticket'],
    secondary: ['inform_customer'],
    danger: [],
  },

  customer_not_satisfied: {
    description: 'Customer not satisfied — re-engage or escalate',
    primary: ['record_sc_followup', 'confirm_appointment'],
    secondary: ['inform_customer', 'set_reverification_date'],
    danger: ['escalate_case'],
  },
}

// ── Status-based action overrides ───────────────────────────────────────────
// When followup_stage is empty or the ticket is at a status-level decision point,
// these status-based rules determine available actions.

export const STATUS_ACTIONS = {
  New: {
    description: 'New complaint — register brand or request details',
    primary: ['brand_complaint'],
    secondary: ['inform_customer'],
    danger: [],
  },
  Open: {
    description: 'Open complaint — register brand or request details',
    primary: ['brand_complaint'],
    secondary: ['inform_customer'],
    danger: [],
  },
  'Brand Registered': {
    description: 'Brand registered — verify technician call',
    primary: ['verify_tech_called'],
    secondary: ['record_sc_followup', 'inform_customer'],
    danger: ['escalate_case'],
  },
  'In Progress': {
    description: 'In progress — follow up or inform customer',
    primary: ['record_sc_followup', 'inform_customer'],
    secondary: ['set_reverification_date'],
    danger: ['escalate_case'],
  },
  'Waiting on Customer': {
    description: 'Waiting on customer — follow up or resume',
    primary: ['resume_followup'],
    secondary: ['inform_customer', 'escalate_case'],
    danger: [],
  },
  'Waiting on Part / Approval': {
    description: 'Waiting on part — update ETA or mark ready',
    primary: ['update_part_eta', 'mark_product_ready'],
    secondary: ['record_sc_followup', 'inform_customer'],
    danger: ['escalate_case'],
  },
  'Ready for Pickup': {
    description: 'Product ready — record satisfaction or close',
    primary: ['record_satisfaction'],
    secondary: ['inform_customer'],
    danger: ['close_ticket'],
  },
  Resolved: {
    description: 'Resolved — confirm closure',
    primary: ['customer_confirmed'],
    secondary: ['close_ticket'],
    danger: [],
  },
  Closed: {
    description: 'Ticket closed',
    primary: [],
    secondary: [],
    danger: [],
  },
  Cancelled: {
    description: 'Ticket cancelled',
    primary: [],
    secondary: [],
    danger: [],
  },
}

// ── Action metadata ─────────────────────────────────────────────────────────
// Maps action keys to their display properties and backend endpoints.
// This is the single source of truth for action rendering.

export const ACTION_REGISTRY = {
  // ── Brand registration ────────────────────────────────────────────────────
  brand_complaint: {
    label: 'Register Brand Complaint',
    icon: 'verified',
    color: 'primary',
    endpoint: 'lavanya_service.api.workflow_actions.register_brand_complaint',
    fields: [
      { key: 'brand_ticket_number', label: 'Brand Ticket Number', type: 'text', required: true },
      { key: 'registration_date', label: 'Registration Date', type: 'date', required: true },
      { key: 'next_follow_up_date', label: 'Next Follow-up Date', type: 'date', required: true },
      { key: 'service_center', label: 'Service Center', type: 'text', required: false },
    ],
  },

  // ── Technician verification ───────────────────────────────────────────────
  verify_tech_called: {
    label: 'Verify Technician Called',
    icon: 'phone_in_talk',
    color: 'primary',
    endpoint: 'lavanya_service.api.workflow_actions.verify_technician_called',
    fields: [
      { key: 'technician_name', label: 'Technician Name', type: 'text', required: false },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },

  verify_tech_visit: {
    label: 'Verify Technician Visit',
    icon: 'handyman',
    color: 'primary',
    endpoint: 'lavanya_service.api.workflow_actions.verify_technician_visit',
    fields: [
      { key: 'technician_name', label: 'Technician Name', type: 'text', required: false },
      { key: 'visit_result', label: 'Visit Result', type: 'text', required: false },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },

  // ── Appointment handling ──────────────────────────────────────────────────
  confirm_appointment: {
    label: 'Confirm Appointment',
    icon: 'event_available',
    color: 'primary',
    endpoint: 'lavanya_service.api.workflow_actions.confirm_appointment',
    fields: [
      { key: 'appointment_datetime', label: 'Date & Time', type: 'datetime-local', required: false },
      { key: 'technician', label: 'Technician', type: 'text', required: false },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },

  mark_appointment_missed: {
    label: 'Mark Appointment Missed',
    icon: 'event_busy',
    color: 'warning',
    endpoint: 'lavanya_service.api.workflow_actions.mark_appointment_missed',
    fields: [
      { key: 'reason', label: 'Reason', type: 'textarea', required: true, placeholder: 'Why was the appointment missed?' },
      { key: 'reschedule_date', label: 'Reschedule Date', type: 'date', required: false },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },

  mark_technician_visited: {
    label: 'Record Technician Visit',
    icon: 'handyman',
    color: 'primary',
    endpoint: 'lavanya_service.api.workflow_actions.mark_technician_visited',
    fields: [
      { key: 'visit_result', label: 'Visit Result', type: 'text', required: false, placeholder: 'Repaired / PCBs required / Revisit needed' },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },

  // ── Service center follow-up ──────────────────────────────────────────────
  record_sc_followup: {
    label: 'Record SC Follow-up',
    icon: 'support_agent',
    color: 'secondary',
    endpoint: 'lavanya_service.api.workflow_actions.record_sc_followup',
    fields: [
      {
        key: 'follow_up_result',
        label: 'Follow-up Result',
        type: 'select',
        required: true,
        options: [
          'Service center contacted',
          'Technician assigned',
          'Customer not reachable',
          'Service completed',
          'Part pending',
          'Approval pending',
        ],
      },
      { key: 'next_follow_up_date', label: 'Next Follow-up Date', type: 'date', required: false },
      {
        key: 'customer_informed_status',
        label: 'Customer Informed',
        type: 'select',
        required: true,
        options: ['Informed by Call', 'Informed by WhatsApp', 'Informed by SMS', 'Pending', 'Customer Not Reachable', 'Not Required'],
      },
    ],
  },

  follow_up_sc: {
    label: 'Follow Up Service Center',
    icon: 'support_agent',
    color: 'secondary',
    endpoint: 'lavanya_service.api.workflow_actions.follow_up_service_center',
    fields: [
      {
        key: 'follow_up_result',
        label: 'Follow-up Result',
        type: 'select',
        required: true,
        options: [
          'Service center contacted',
          'Technician assigned',
          'Customer not reachable',
          'Service completed',
          'Part pending',
          'Approval pending',
        ],
      },
      {
        key: 'next_follow_up_date',
        label: 'Next Follow-up Date',
        type: 'date',
        required: (f) => f.follow_up_result !== 'Service completed',
        hint: 'Required unless the result is "Service completed".',
      },
    ],
  },

  // ── Customer communication ────────────────────────────────────────────────
  inform_customer: {
    label: 'Inform Customer',
    icon: 'campaign',
    color: 'success',
    endpoint: 'lavanya_service.api.workflow_actions.inform_customer',
    fields: [
      { key: 'channel', label: 'Channel', type: 'select', required: true, options: ['Phone', 'WhatsApp', 'Direct', 'SMS', 'Email'] },
      { key: 'message', label: 'Message', type: 'textarea', required: false },
    ],
  },

  // ── Escalation / no-update ────────────────────────────────────────────────
  mark_no_update: {
    label: 'Mark No Update',
    icon: 'warning',
    color: 'warning',
    endpoint: 'lavanya_service.api.workflow_actions.mark_no_update',
    fields: [
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },

  escalate_case: {
    label: 'Escalate Case',
    icon: 'escalator_warning',
    color: 'danger',
    endpoint: 'lavanya_service.api.workflow_actions.escalate_case',
    fields: [
      { key: 'reason', label: 'Reason', type: 'textarea', required: true, placeholder: 'Why is this being escalated?' },
    ],
  },

  // ── Customer verification / satisfaction ───────────────────────────────────
  verify_customer_after_visit: {
    label: 'Verify Customer After Visit',
    icon: 'contact_phone',
    color: 'primary',
    endpoint: 'lavanya_service.api.workflow_actions.verify_customer_after_appointment',
    fields: [
      { key: 'confirmed', label: 'Customer Confirms', type: 'select', required: true, options: ['Yes', 'Cleared', 'Satisfied', 'No', 'Not Cleared', 'Still Issue', 'Part Pending'] },
      { key: 'satisfaction', label: 'Satisfaction (optional)', type: 'select', required: false, options: ['Satisfied', 'Not Satisfied', 'Customer Not Reachable', 'Not Required'] },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },

  record_satisfaction: {
    label: 'Record Satisfaction',
    icon: 'sentiment_satisfied',
    color: 'success',
    endpoint: 'lavanya_service.api.workflow_actions.record_satisfaction',
    fields: [
      { key: 'satisfaction_status', label: 'Satisfaction Status', type: 'select', required: true, options: ['Satisfied', 'Not Satisfied', 'Customer Not Reachable', 'Not Required'] },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },

  // ── Part tracking ─────────────────────────────────────────────────────────
  record_part_required: {
    label: 'Record Part Required',
    icon: 'build',
    color: 'warning',
    endpoint: 'lavanya_service.api.workflow_actions.record_part_required',
    fields: [
      { key: 'part_name', label: 'Part Name', type: 'text', required: true, placeholder: 'e.g. PCB, Compressor' },
      { key: 'part_expected_date', label: 'Part ETA', type: 'date', required: true },
      { key: 'next_follow_up_date', label: 'Next Follow-up', type: 'date', required: true },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },

  update_part_eta: {
    label: 'Update Part ETA',
    icon: 'schedule',
    color: 'warning',
    endpoint: 'lavanya_service.api.workflow_actions.update_part_eta',
    fields: [
      { key: 'new_eta', label: 'New ETA Date', type: 'date', required: true },
      { key: 'delay_reason', label: 'Delay Reason', type: 'text', required: false, placeholder: 'Supplier delayed / Out of stock' },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },

  waiting_part: {
    label: 'Waiting for Part',
    icon: 'build',
    color: 'warning',
    endpoint: 'lavanya_service.api.workflow_actions.waiting_for_part',
    fields: [
      {
        key: 'pending_reason',
        label: 'Pending Reason',
        type: 'select',
        required: true,
        options: [
          'Invoice Proof Pending', 'Invoice Pending', 'Brand Registration Recommended',
          'Manufacturer Registration Pending', 'Service Follow-up Required', 'Brand Ticket Number Pending',
          'Customer Details Missing', 'Technician Not Visited', 'Service Center Delayed',
          'Service Center Out of Area', 'Customer Not Reachable', 'Customer Reappointed', 'Part Pending',
          'Part Warranty Pending', 'Replacement Approval Pending', 'Supplier Approval Pending',
          'Customer Pickup Pending', 'Manager Escalation Pending', 'Local Technician Pending',
          'Local Service Transfer Pending', 'Estimate Approval Pending', 'Brand Line Busy',
          'Service Center Unreachable', 'Other',
        ],
      },
      { key: 'next_follow_up_date', label: 'Next Follow-up Date', type: 'date', required: true },
    ],
  },

  // ── Product ready / pickup ────────────────────────────────────────────────
  mark_product_ready: {
    label: 'Mark Product Ready',
    icon: 'hail',
    color: 'success',
    endpoint: 'lavanya_service.api.workflow_actions.mark_product_ready',
    fields: [
      { key: 'next_follow_up_date', label: 'Ready Date', type: 'date', required: false },
    ],
  },

  // ── Reverification ────────────────────────────────────────────────────────
  set_reverification_date: {
    label: 'Set Reverification Date',
    icon: 'event_repeat',
    color: 'primary',
    endpoint: 'lavanya_service.api.workflow_actions.set_reverification_date',
    fields: [
      { key: 'reverify_at', label: 'Reverify Date', type: 'date', required: true },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },

  // ── Resume from parked ────────────────────────────────────────────────────
  resume_followup: {
    label: 'Resume Follow-up',
    icon: 'play_circle',
    color: 'primary',
    endpoint: 'lavanya_service.api.workflow_actions.resume_followup',
    fields: [
      { key: 'next_follow_up_date', label: 'Next Follow-up Date', type: 'date', required: false },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },

  // ── Customer approval ─────────────────────────────────────────────────────
  record_approval: {
    label: 'Record Customer Approval',
    icon: 'contract',
    color: 'secondary',
    endpoint: 'lavanya_service.api.workflow_actions.record_customer_approval',
    fields: [
      { key: 'approved_amount', label: 'Approved Amount', type: 'number', required: true },
      { key: 'payment_status', label: 'Payment Status', type: 'select', required: false, options: ['Not Applicable', 'Pending', 'Approved', 'Paid'] },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },

  // ── Closure ───────────────────────────────────────────────────────────────
  customer_confirmed: {
    label: 'Customer Confirmed',
    icon: 'how_to_reg',
    color: 'success',
    endpoint: 'lavanya_service.api.workflow_actions.customer_confirmed',
    fields: [
      { key: 'work_narration', label: 'Work Narration', type: 'textarea', required: true, placeholder: 'Summary of the work done...' },
      {
        key: 'closure_type',
        label: 'Closure Type',
        type: 'select',
        required: true,
        options: [
          'Resolved by Brand Service', 'Resolved by Local Technician', 'Replacement Completed',
          'Customer Collected Product', 'Customer Cancelled', 'Duplicate Ticket',
          'Not Purchased From Lavanya - Guided Only', 'Brand Denied Warranty', 'Customer Not Responding',
          'Closed After Manager Approval', 'Other',
        ],
      },
    ],
  },

  close_ticket: {
    label: 'Close Ticket',
    icon: 'task_alt',
    color: 'danger',
    endpoint: 'lavanya_service.api.workflow_actions.close_ticket',
    fields: [
      { key: 'work_narration', label: 'Work Narration', type: 'textarea', required: true, placeholder: 'Summary of the work done...' },
      {
        key: 'closure_type',
        label: 'Closure Type',
        type: 'select',
        required: true,
        options: [
          'Resolved by Brand Service', 'Resolved by Local Technician', 'Replacement Completed',
          'Customer Collected Product', 'Customer Cancelled', 'Duplicate Ticket',
          'Not Purchased From Lavanya - Guided Only', 'Brand Denied Warranty', 'Customer Not Responding',
          'Closed After Manager Approval', 'Other',
        ],
      },
      { key: 'customer_confirmation_received', label: 'Customer Confirmation Received', type: 'select', required: true, options: ['Yes', 'No'] },
    ],
  },

  // ── Schedule appointment (extended) ───────────────────────────────────────
  schedule_appointment: {
    label: 'Schedule Appointment',
    icon: 'event',
    color: 'primary',
    endpoint: 'lavanya_service.api.stitch_console.schedule_appointment',
    fields: [
      { key: 'appointment_datetime', label: 'Date & Time', type: 'datetime-local', required: true },
      { key: 'technician', label: 'Technician', type: 'text', required: false, placeholder: 'Name of the technician' },
      { key: 'notes', label: 'Notes', type: 'textarea', required: false },
    ],
  },

  set_promise: {
    label: 'Set Customer Promise',
    icon: 'schedule_send',
    color: 'secondary',
    endpoint: 'lavanya_service.api.stitch_console.set_customer_promise',
    fields: [
      { key: 'promised_at', label: 'Promised an update by', type: 'datetime-local', required: true },
    ],
  },
}

// ── Color mapping for action buttons ────────────────────────────────────────
export const ACTION_COLORS = {
  primary: {
    bg: 'bg-primary',
    text: 'text-on-primary',
    hover: 'hover:bg-primary-dark',
    border: 'border-primary',
    chip: (colorVar) => ({
      background: `color-mix(in srgb, ${colorVar} 12%, transparent)`,
      color: colorVar,
    }),
  },
  secondary: {
    bg: 'bg-surface-container',
    text: 'text-on-surface',
    hover: 'hover:bg-surface-container-low',
    border: 'border-outline-variant',
  },
  success: {
    bg: 'bg-success',
    text: 'text-on-success',
    hover: 'hover:opacity-90',
    border: 'border-success',
  },
  warning: {
    bg: 'bg-warning',
    text: 'text-on-warning',
    hover: 'hover:opacity-90',
    border: 'border-warning',
  },
  danger: {
    bg: 'bg-error',
    text: 'text-on-error',
    hover: 'hover:opacity-90',
    border: 'border-error',
  },
}

// ── Helper: resolve available actions for a ticket ──────────────────────────
/**
 * Given a ticket's state, return the available actions grouped by priority.
 *
 * @param {Object} ticket - The ticket object (with stage, status fields)
 * @returns {{ primary: Array, secondary: Array, danger: Array }}
 */
export function resolveActions(ticket) {
  if (!ticket) return { primary: [], secondary: [], danger: [] }

  const status = ticket.status || ''
  const stage = ticket.stage || {}
  const followupStage = stage.followup_stage || ticket.followup_stage || ''

  // Terminal states — no actions
  if (status === 'Closed' || status === 'Cancelled') {
    return { primary: [], secondary: [], danger: [] }
  }

  // Try followup_stage first (more specific)
  let mapping = STAGE_ACTIONS[followupStage]

  // Fall back to status-based mapping
  if (!mapping) {
    mapping = STATUS_ACTIONS[status]
  }

  // Default fallback
  if (!mapping) {
    mapping = {
      primary: ['record_sc_followup', 'inform_customer'],
      secondary: ['set_reverification_date'],
      danger: ['escalate_case'],
    }
  }

  // Resolve action definitions from ACTION_REGISTRY
  const resolve = (keys) =>
    (keys || [])
      .map((key) => {
        const def = ACTION_REGISTRY[key]
        if (!def) return null
        return { key, ...def }
      })
      .filter(Boolean)

  return {
    primary: resolve(mapping.primary),
    secondary: resolve(mapping.secondary),
    danger: resolve(mapping.danger),
  }
}

// ── Helper: get the single "Record Outcome" action for a ticket ─────────────
/**
 * Returns the single most important action for a ticket — the one that
 * should appear as the prominent "Record Outcome" button.
 *
 * @param {Object} ticket - The ticket object
 * @returns {Object|null} The action definition, or null if no action needed
 */
export function getPrimaryAction(ticket) {
  const actions = resolveActions(ticket)
  return actions.primary[0] || null
}

// ── Helper: check if ticket can be closed ───────────────────────────────────
/**
 * Determines if a ticket is eligible for closure based on its state.
 *
 * @param {Object} ticket - The ticket object
 * @returns {{ allowed: boolean, reason: string }}
 */
export function canCloseTicket(ticket) {
  if (!ticket) return { allowed: false, reason: 'No ticket data' }

  const status = ticket.status || ''
  const stage = ticket.stage || {}
  const satisfaction = stage.customer_satisfaction_status || ticket.customer_satisfaction_status
  const confirmed = stage.customer_confirmation_received || ticket.customer_confirmation_received

  if (status === 'Closed' || status === 'Cancelled') {
    return { allowed: true, reason: 'Already closed' }
  }

  if (confirmed === 'Yes' || satisfaction === 'Satisfied' || satisfaction === 'Not Required') {
    return { allowed: true, reason: 'Customer confirmed issue solved' }
  }

  if (satisfaction === 'Not Satisfied') {
    return { allowed: false, reason: 'Customer not satisfied — follow-up must continue' }
  }

  return { allowed: false, reason: 'Customer confirmation pending' }
}
