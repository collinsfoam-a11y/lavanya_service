<template>
  <div class="w-full">
    <!-- Desktop horizontal -->
    <div class="hidden md:flex items-start justify-between gap-2">
      <div
        v-for="(step, idx) in steps"
        :key="step.key"
        class="flex-1 flex flex-col items-center text-center"
      >
        <div
          class="w-9 h-9 rounded-full flex items-center justify-center mb-2 border-2 transition-colors"
          :class="stateClass(step.state)"
          :aria-label="step.label + ': ' + step.state"
        >
          <span class="material-symbols-outlined" style="font-size:18px">{{ step.icon }}</span>
        </div>
        <div class="font-label-md text-label-md font-semibold" :class="textClass(step.state)">
          {{ step.label }}
        </div>
        <div v-if="step.sub" class="font-label-md text-label-md text-on-surface-variant">
          {{ step.sub }}
        </div>
        <div
          v-if="idx < steps.length - 1"
          class="hidden lg:block h-0.5 w-full mt-5"
          :class="connectorClass(step.state, steps[idx + 1].state)"
          aria-hidden="true"
        ></div>
      </div>
    </div>

    <!-- Mobile vertical -->
    <div class="md:hidden flex flex-col gap-3">
      <div
        v-for="(step, idx) in steps"
        :key="step.key"
        class="flex items-start gap-3"
      >
        <div class="flex flex-col items-center">
          <div
            class="w-8 h-8 rounded-full flex items-center justify-center border-2"
            :class="stateClass(step.state)"
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
          <div class="font-label-md text-label-md font-semibold" :class="textClass(step.state)">
            {{ step.label }}
          </div>
          <div v-if="step.sub" class="font-label-md text-label-md text-on-surface-variant">
            {{ step.sub }}
          </div>
        </div>
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
  { key: 'complaint_received', label: 'Complaint Received', icon: 'inbox' },
  { key: 'brand_registered', label: 'Brand Registered', icon: 'verified' },
  { key: 'technician_called', label: 'Technician Called', icon: 'phone_in_talk' },
  { key: 'technician_visited', label: 'Technician Visited', icon: 'handyman' },
  { key: 'part_pending', label: 'Part / Work Pending', icon: 'build' },
  { key: 'customer_informed', label: 'Customer Informed', icon: 'campaign' },
  { key: 'customer_confirmation', label: 'Customer Confirmation', icon: 'fact_check' },
  { key: 'closed', label: 'Closed / Reopened', icon: 'task_alt' },
]

function resolveState(key) {
  const t = props.ticket
  const s = t?.stage || t || {}
  const status = (t?.status || '').toString()
  const fs = (s.followup_stage || '').toString()
  const overdue = (s.overdue_status || t?.overdue_status || '').toString()
  const promise = (s.customer_promise_status || t?.customer_promise_status || '').toString()
  const satisfaction = (s.customer_satisfaction_status || '').toString()
  const informed = (s.customer_informed_status || s.customer_informed || '').toString()

  const isClosed = status === 'Closed' || status === 'Resolved' || status === 'Cancelled'

  const completed = {
    complaint_received: true,
    brand_registered: status === 'Brand Registered' || status === 'In Progress' || status === 'Waiting on Part / Approval' || status === 'Waiting on Customer' || status === 'Ready for Pickup' || isClosed || fs !== '',
    technician_called: fs === 'technician_called' || fs === 'technician_visited' || fs === 'sc_followup_done' || fs === 'customer_informed' || fs === 'customer_confirmation_pending' || fs === 'customer_not_satisfied' || isClosed,
    technician_visited: fs === 'technician_visited' || fs === 'sc_followup_done' || fs === 'customer_informed' || fs === 'customer_confirmation_pending' || fs === 'customer_not_satisfied' || isClosed,
    part_pending: fs === 'part_pending' || status === 'Waiting on Part / Approval' || (status === 'Ready for Pickup' && fs !== 'part_pending') || isClosed,
    customer_informed: (informed && informed !== 'Pending') || fs === 'customer_informed' || fs === 'customer_confirmation_pending' || fs === 'customer_not_satisfied' || isClosed,
    customer_confirmation: satisfaction === 'Satisfied' || satisfaction === 'Not Required' || (satisfaction === 'Not Satisfied' && !isClosed) || isClosed,
    closed: isClosed,
  }

  if (completed[key]) return 'complete'

  const current = {
    brand_registered: status === 'New' || status === 'Open',
    technician_called: status === 'Brand Registered' && fs !== 'technician_called',
    technician_visited: fs === 'technician_called',
    part_pending: fs === 'technician_visited' && status !== 'Waiting on Part / Approval',
    customer_informed: status === 'Waiting on Part / Approval' || (fs === 'part_pending' && informed === 'Pending'),
    customer_confirmation: (status === 'Ready for Pickup' || fs === 'customer_informed') && !satisfaction,
    closed: satisfaction === 'Satisfied' || satisfaction === 'Not Required',
  }

  if (current[key]) {
    if (overdue === 'Overdue' || promise === 'Breached') return 'overdue'
    return 'current'
  }

  const waiting = {
    part_pending: fs === 'part_pending' || status === 'Waiting on Part / Approval',
    customer_informed: informed === 'Pending',
    customer_confirmation: status === 'Ready for Pickup' && !satisfaction,
  }
  if (waiting[key]) return 'waiting'

  const blocked = {
    customer_confirmation: satisfaction === 'Not Satisfied',
  }
  if (blocked[key]) return 'blocked'

  return 'future'
}

const steps = computed(() =>
  STEP_ORDER.map((step) => ({
    ...step,
    state: resolveState(step.key),
    sub: subtext(step.key),
  }))
)

function subtext(key) {
  const t = props.ticket
  const s = t?.stage || t || {}
  if (key === 'complaint_received') return `${(t?.ticketAge || 0)} days open`
  if (key === 'technician_called' && s.technician_called_at) return s.technician_called_at.substring(0, 16)
  if (key === 'technician_visited' && s.technician_visited_at) return s.technician_visited_at.substring(0, 16)
  if (key === 'part_pending' && s.part_expected_date) return 'Expected ' + s.part_expected_date.substring(0, 10)
  if (key === 'customer_informed' && s.customer_informed_at) return s.customer_informed_at.substring(0, 16)
  if (key === 'customer_confirmation' && s.customer_satisfaction_status) return s.customer_satisfaction_status
  if (key === 'closed' && t?.closure_date) return t.closure_date.substring(0, 16)
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
