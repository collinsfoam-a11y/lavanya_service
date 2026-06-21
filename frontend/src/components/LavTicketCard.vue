<template>
  <article
    class="lav-ticket-card"
    :class="compact ? 'lav-ticket-card--compact' : ''"
    :style="{ '--lav-ticket-accent': accent }"
    tabindex="0"
    role="button"
    :aria-label="ariaLabel"
    @click="emit('open', ticket.name)"
    @keydown.enter.prevent="emit('open', ticket.name)"
    @keydown.space.prevent="emit('open', ticket.name)"
  >
    <div class="lav-ticket-card__top">
      <div class="lav-ticket-card__avatar" aria-hidden="true">{{ initial }}</div>
      <div class="min-w-0 flex-1">
        <div class="flex flex-wrap items-center gap-2">
          <span class="font-body-md font-semibold text-primary truncate">{{ ticket.name }}</span>
          <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="chip(ticket.status)">{{ ticket.status || 'Open' }}</span>
          <span v-if="quality && quality !== 'Good'" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="qualityChip(quality)">{{ quality }}</span>
        </div>
        <h3 class="mt-1 font-body-md text-on-surface font-semibold truncate">{{ ticket.subject || '(no subject)' }}</h3>
        <p class="font-label-md text-label-md text-on-surface-variant truncate">
          <template v-if="ticket.customer_name">{{ ticket.customer_name }}</template>
          <template v-if="ticket.phone_1"> · {{ ticket.phone_1 }}</template>
          <template v-if="product(ticket)"> · {{ product(ticket) }}</template>
        </p>
      </div>
    </div>

    <div class="lav-ticket-card__meta">
      <div>
        <span class="lav-ticket-card__label">Next Action</span>
        <span class="lav-ticket-card__value">{{ nextAction }}</span>
      </div>
      <div>
        <span class="lav-ticket-card__label">Due</span>
        <span class="lav-ticket-card__value" :style="followStyle(ticket.next_follow_up_date)">{{ followText(ticket.next_follow_up_date) }}</span>
      </div>
      <div>
        <span class="lav-ticket-card__label">Customer Informed</span>
        <span class="lav-ticket-card__value">{{ informedState }}</span>
      </div>
      <div v-if="escalation && escalation !== 'None'">
        <span class="lav-ticket-card__label">Escalation</span>
        <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="escChip(escalation)">{{ escalation }}</span>
      </div>
    </div>

    <div class="lav-ticket-card__footer">
      <span v-if="ticket.pending_reason" class="font-label-md text-label-md text-on-surface-variant truncate">{{ ticket.pending_reason }}</span>
      <span v-if="ticket.customer_update_due" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="promiseChip('Pending')">Customer update due</span>
      <span v-if="ticket.customer_promise_status === 'Breached'" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="promiseChip('Breached')">Promise breached</span>
      <span class="ml-auto inline-flex items-center gap-1 font-label-md text-label-md text-primary">
        Open
        <span class="material-symbols-outlined" style="font-size:16px" aria-hidden="true">chevron_right</span>
      </span>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { chip, escChip, followStyle, followText, product, promiseChip, qualityBadge, qualityChip } from '@/utils'

const props = defineProps({
  ticket: { type: Object, required: true },
  accent: { type: String, default: 'var(--lav-primary)' },
  compact: { type: Boolean, default: false },
})

const emit = defineEmits(['open'])

const initial = computed(() => (props.ticket.customer_name || props.ticket.subject || '?').charAt(0).toUpperCase())
const quality = computed(() => qualityBadge(props.ticket))
const escalation = computed(() => props.ticket.computed_escalation_level || props.ticket.escalation_level || 'None')
const nextAction = computed(() => props.ticket.next_action || props.ticket.current_service_stage || props.ticket.followup_stage || 'Review ticket')
const informedState = computed(() => props.ticket.customer_informed_status || props.ticket.customer_informed || (props.ticket.customer_update_due ? 'Due now' : 'Pending'))
const ariaLabel = computed(() => `Open ticket ${props.ticket.name || ''}: ${nextAction.value}`)
</script>
