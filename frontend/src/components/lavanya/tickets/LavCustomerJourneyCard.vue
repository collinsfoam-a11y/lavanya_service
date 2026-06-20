<template>
  <div class="rounded-xl border bg-surface p-4">
    <div class="flex items-center gap-2 mb-4">
      <span class="material-symbols-outlined text-primary" aria-hidden="true">route</span>
      <h3 class="font-headline-md text-headline-md text-on-surface">Customer Journey</h3>
      <LavFollowupQualityBadge v-if="ticket" :ticket="ticket" class="ml-auto" />
    </div>

    <div class="grid grid-cols-2 sm:grid-cols-3 gap-4">
      <div>
        <div class="font-label-md text-label-md text-on-surface-variant">Days Open</div>
        <div class="font-body-md text-on-surface font-semibold" :class="daysOpenClass">{{ daysOpen }} days</div>
      </div>
      <div>
        <div class="font-label-md text-label-md text-on-surface-variant">Current Stage</div>
        <div class="font-body-md text-on-surface font-semibold">{{ currentStage }}</div>
      </div>
      <div>
        <div class="font-label-md text-label-md text-on-surface-variant">Next Follow-up</div>
        <div class="font-body-md font-semibold" :class="nextFollowUp.class">{{ nextFollowUp.label }}</div>
      </div>
      <div>
        <div class="font-label-md text-label-md text-on-surface-variant">Last Customer Update</div>
        <div class="font-body-md text-on-surface">{{ lastCustomerUpdate }}</div>
      </div>
      <div>
        <div class="font-label-md text-label-md text-on-surface-variant">Last Technician Update</div>
        <div class="font-body-md text-on-surface">{{ lastTechnicianUpdate }}</div>
      </div>
      <div>
        <div class="font-label-md text-label-md text-on-surface-variant">Last SC Update</div>
        <div class="font-body-md text-on-surface">{{ lastSCUpdate }}</div>
      </div>
      <div>
        <div class="font-label-md text-label-md text-on-surface-variant">Satisfaction</div>
        <div class="font-body-md text-on-surface">{{ satisfaction }}</div>
      </div>
      <div>
        <div class="font-label-md text-label-md text-on-surface-variant">Escalation Level</div>
        <div class="font-body-md text-on-surface">{{ escalation }}</div>
      </div>
      <div>
        <div class="font-label-md text-label-md text-on-surface-variant">Closure Eligibility</div>
        <div class="font-body-md font-semibold" :class="closure.class">{{ closure.label }}</div>
      </div>
    </div>

    <div v-if="reason" class="mt-4 p-3 rounded-lg bg-surface-container-low border border-outline-variant">
      <div class="font-label-md text-label-md text-on-surface-variant mb-1">Why this quality?</div>
      <div class="font-body-md text-on-surface">{{ reason }}</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import LavFollowupQualityBadge from './LavFollowupQualityBadge.vue'
import { computeFollowupQuality, qualityReason } from '@/utils/followup-quality.js'
import { ticketAge, followText, followStyle } from '@/utils/index.js'

const props = defineProps({
  ticket: { type: Object, required: true },
})

const s = computed(() => props.ticket?.stage || props.ticket || {})
const daysOpen = computed(() => ticketAge(props.ticket?.creation))
const daysOpenClass = computed(() => daysOpen.value > 7 ? 'text-danger' : 'text-on-surface')
const currentStage = computed(() => s.value.current_service_stage || s.value.followup_stage || props.ticket?.status || 'Unknown')
const nextFollowUp = computed(() => followStyleObj(s.value.next_follow_up_date || s.value.computed_next_follow_up))
const lastCustomerUpdate = computed(() => datetime(s.value.customer_informed_at || s.value.last_followup_at) || 'No update yet')
const lastTechnicianUpdate = computed(() => {
  const fs = s.value.followup_stage || ''
  if (fs === 'technician_visited' || fs === 'technician_called') return datetime(s.value.last_followup_at) || 'Pending'
  return '—'
})
const lastSCUpdate = computed(() => datetime(s.value.last_service_center_followup) || '—')
const satisfaction = computed(() => s.value.customer_satisfaction_status || 'Pending')
const escalation = computed(() => {
  const esc = s.value.computed_escalation_level || s.value.escalation_level
  return esc && esc !== 'None' ? esc : 'None'
})
const closure = computed(() => {
  const sat = s.value.customer_satisfaction_status
  const status = props.ticket?.status
  if (status === 'Closed' || status === 'Resolved') return { label: 'Closed', class: 'text-success' }
  if (sat === 'Satisfied' || sat === 'Not Required') return { label: 'Allowed', class: 'text-success' }
  if (sat === 'Not Satisfied') return { label: 'Not Allowed', class: 'text-danger' }
  return { label: 'Not Allowed', class: 'text-on-surface-variant' }
})
const reason = computed(() => qualityReason(props.ticket))

function datetime(v) {
  if (!v) return ''
  const s = String(v)
  return s.length >= 16 ? s.substring(0, 16) : s
}

function followStyleObj(dateStr) {
  const style = followStyle(dateStr)
  if (style.color) {
    return { label: followText(dateStr), class: 'font-semibold', style }
  }
  return { label: followText(dateStr), class: 'text-on-surface', style: {} }
}
</script>
