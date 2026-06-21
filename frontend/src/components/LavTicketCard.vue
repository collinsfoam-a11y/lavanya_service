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
    <div class="lav-ticket-card__top flex items-center gap-3">
      <div class="lav-ticket-card__avatar" aria-hidden="true">{{ initial }}</div>
      <div class="min-w-0 flex-1">
        <div class="flex items-center justify-between gap-2">
          <span class="font-body-md font-semibold text-primary truncate">{{ ticket.name }}</span>
          <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="chip(ticket.status)">{{ ticket.status || 'Open' }}</span>
        </div>
        <h3 class="mt-1 font-body-md text-on-surface font-semibold truncate">{{ ticket.subject || '(no subject)' }}</h3>
      </div>
    </div>

    <div class="my-3 p-2 rounded-lg bg-surface-container border-l-4" :style="{ borderLeftColor: accent }">
      <div class="flex items-center gap-2 text-primary">
        <span class="material-symbols-outlined" style="font-size:16px">bolt</span>
        <span class="font-label-md font-bold uppercase tracking-wider">Next Action</span>
      </div>
      <div class="font-body-md text-on-surface font-semibold mt-1">{{ nextAction }}</div>
    </div>

    <div class="flex flex-wrap gap-1.5 mb-3">
      <span v-if="ticket.overdue_status === 'Overdue'" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="followStyle(ticket.next_follow_up_date)">Overdue</span>
      <span v-if="informedState !== 'Pending' && informedState !== 'Due now'" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="informedChip(informedState)">Informed</span>
      <span v-if="ticket.stage?.part_required" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="{ background: 'color-mix(in srgb, var(--lav-warning) 12%, transparent)', color: 'var(--lav-warning)' }">Part Pending</span>
      <span v-if="escalation && escalation !== 'None'" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="escChip(escalation)">{{ escalation }}</span>
    </div>

    <div class="lav-ticket-card__footer flex items-center justify-between">
      <div class="font-label-md text-label-md text-on-surface-variant truncate max-w-[60%]">
        {{ ticket.customer_name || '—' }}
      </div>
      <span class="inline-flex items-center gap-1 font-label-md text-label-md text-primary font-bold">
        Open
        <span class="material-symbols-outlined" style="font-size:16px" aria-hidden="true">chevron_right</span>
      </span>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'
import { chip, escChip, followStyle, followText, informedChip, product, promiseChip, qualityBadge, qualityChip } from '@/utils'

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
