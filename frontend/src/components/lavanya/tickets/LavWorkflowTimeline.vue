<template>
  <div class="w-full flex flex-col gap-3">
    <div
      v-for="(step, idx) in steps"
      :key="step.key"
      class="flex items-start gap-3"
    >
      <div class="flex flex-col items-center">
        <div
          class="w-8 h-8 rounded-full flex items-center justify-center border-2 transition-colors"
          :class="stateClass(step.state)"
          :aria-label="step.label + ': ' + step.state"
        >
          <span class="material-symbols-outlined" style="font-size:16px">{{ step.icon }}</span>
        </div>
        <div
          v-if="idx < steps.length - 1"
          class="w-0.5 flex-1 min-h-[24px] mt-1"
          :class="connectorClass(step.state, steps[idx + 1].state)"
          aria-hidden="true"
        ></div>
      </div>
      <div class="flex-1 pb-3">
        <div class="flex items-center gap-2">
          <div class="font-label-md text-label-md font-semibold" :class="textClass(step.state)">
            {{ step.label }}
          </div>
          <span v-if="step.state === 'complete'" class="material-symbols-outlined text-success" style="font-size:16px">check_circle</span>
          <span v-if="step.reEntryCount > 1" class="text-xs px-1.5 py-0.5 rounded-full bg-warning/20 text-warning font-medium">
            ×{{ step.reEntryCount }}
          </span>
        </div>
        <div v-if="step.sub" class="font-label-md text-label-md text-on-surface-variant mt-0.5">{{ step.sub }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  ticket: { type: Object, required: true },
})

const STEP_ORDER = [
  { key: 'registration_done', label: 'Complaint Registered', icon: 'inbox', stages: ['registration_done'] },
  { key: 'technician_called', label: 'Technician Called', icon: 'phone_in_talk', stages: ['technician_called'] },
  { key: 'technician_visited', label: 'Technician Visited', icon: 'handyman', stages: ['technician_visited'] },
  { key: 'sc_followup_done', label: 'SC Follow-up', icon: 'support_agent', stages: ['sc_followup_done'] },
  { key: 'part_pending', label: 'Part Tracking', icon: 'build', stages: ['part_pending'] },
  { key: 'customer_informed', label: 'Customer Informed', icon: 'campaign', stages: ['customer_informed'] },
  { key: 'customer_confirmation', label: 'Customer Confirmation', icon: 'fact_check', stages: ['customer_confirmation_pending', 'customer_satisfied', 'customer_not_satisfied'] },
  { key: 'closed', label: 'Closed', icon: 'task_alt', stages: [] },
]

const log = computed(() => props.ticket?.followup_log || [])
const currentStage = computed(() => props.ticket?.followup_stage || '')
const status = computed(() => props.ticket?.status || '')

function logHasStage(stages) {
  return log.value.some(entry => stages.includes(entry.stage))
}

function logCount(stages) {
  return log.value.filter(entry => stages.includes(entry.stage)).length
}

function lastLogEntry(stages) {
  const entries = log.value.filter(entry => stages.includes(entry.stage))
  return entries.length > 0 ? entries[entries.length - 1] : null
}

function resolveState(key) {
  const step = STEP_ORDER.find(s => s.key === key)
  if (!step) return 'future'

  const isClosed = status.value === 'Closed' || status.value === 'Resolved' || status.value === 'Cancelled'

  // Closed step
  if (key === 'closed') {
    if (isClosed) return 'complete'
    if (currentStage.value === 'customer_satisfied' || currentStage.value === 'customer_confirmation_pending') return 'current'
    return 'future'
  }

  // Check if stage exists in log → complete
  if (logHasStage(step.stages)) return 'complete'

  // Check if this is the current active stage
  if (step.stages.includes(currentStage.value)) {
    return 'current'
  }

  // Check waiting states
  if (key === 'part_pending' && currentStage.value === 'technician_visited') return 'waiting'
  if (key === 'customer_informed' && currentStage.value === 'part_pending') return 'waiting'
  if (key === 'customer_confirmation' && currentStage.value === 'customer_informed') return 'waiting'

  return 'future'
}

const steps = computed(() =>
  STEP_ORDER.map((step) => ({
    ...step,
    state: resolveState(step.key),
    reEntryCount: logCount(step.stages),
    sub: subtext(step),
  }))
)

function subtext(step) {
  const entry = lastLogEntry(step.stages)
  if (!entry) {
    if (step.key === 'closed') return `${props.ticket?.ticketAge || 0} days open`
    return ''
  }
  const date = entry.completed_at ? entry.completed_at.substring(0, 16) : ''
  const user = entry.user ? entry.user.split('@')[0] : ''
  if (entry.is_re_entry) return `Re-entry · ${date}`
  if (date) return `${date}`
  return ''
}

function stateClass(state) {
  switch (state) {
    case 'complete': return 'bg-success text-on-success border-success'
    case 'current': return 'bg-primary text-on-primary border-primary ring-2 ring-primary/30'
    case 'waiting': return 'bg-warning text-on-warning border-warning'
    case 'overdue': return 'bg-danger text-on-danger border-danger animate-pulse'
    case 'blocked': return 'bg-surface text-danger border-danger border-dashed'
    default: return 'bg-surface text-on-surface-variant border-outline-variant'
  }
}

function textClass(state) {
  switch (state) {
    case 'complete': return 'text-success'
    case 'current': return 'text-primary'
    case 'waiting': return 'text-warning'
    case 'overdue': return 'text-danger'
    case 'blocked': return 'text-danger'
    default: return 'text-on-surface-variant'
  }
}

function connectorClass(prevState, nextState) {
  if (prevState === 'complete' && (nextState === 'complete' || nextState === 'current')) return 'bg-success'
  if (prevState === 'overdue' || nextState === 'overdue') return 'bg-danger'
  if (prevState === 'waiting' || nextState === 'waiting') return 'bg-warning'
  return 'bg-outline-variant'
}
</script>
