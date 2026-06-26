<template>
  <div class="ticket-card" :class="{ 'ticket-card--critical': isCritical }" @click="$emit('click', ticket)">
    <div class="tc-left">
      <div class="tc-avatar" :style="{ background: avatarBg, color: avatarColor }">{{ initials }}</div>
    </div>
    <div class="tc-body">
      <div class="tc-top">
        <span class="tc-name">{{ ticket.customer_name }}</span>
        <span class="mono tc-id">#{{ ticket.name }}</span>
        <StatusBadge :status="ticket.status" />
        <QualityBadge v-if="ticket.quality_badge" :badge="ticket.quality_badge" style="margin-left:4px;" />
      </div>
      <div class="tc-meta">{{ ticket.product }} · {{ ticket.brand }} · {{ ticket.phone }}</div>
      <div v-if="ticket.next_action" class="tc-action">
        <span class="ms" style="font-size:15px;color:#0D9488;">lightbulb</span>
        {{ ticket.next_action }}
      </div>
    </div>
    <div class="tc-right">
      <SLACountdown v-if="ticket.sla_deadline" :deadline-iso="ticket.sla_deadline" :total-seconds="ticket.sla_total_seconds || 172800" />
      <div v-if="ticket.escalation_level" class="tc-esc">
        <span class="ms" style="font-size:13px;">priority_high</span>
        {{ ticket.escalation_level }}
      </div>
    </div>
    <div class="tc-chevron"><span class="ms">chevron_right</span></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import SLACountdown from './SLACountdown.vue'
import QualityBadge from './QualityBadge.vue'
import StatusBadge from './StatusBadge.vue'

const props = defineProps({ ticket: { type: Object, required: true } })
defineEmits(['click'])

const AVATAR_COLORS = [
  ['#EEF2FF', '#4F46E5'], ['#EDE9FE', '#7C3AED'], ['#DCFCE7', '#059669'],
  ['#FEF9C3', '#D97706'], ['#CCFBF1', '#0D9488'], ['#FFE4E6', '#E11D48'],
]
const colorIdx = computed(() => (props.ticket.name || '').charCodeAt(0) % AVATAR_COLORS.length)
const avatarBg = computed(() => AVATAR_COLORS[colorIdx.value][0])
const avatarColor = computed(() => AVATAR_COLORS[colorIdx.value][1])
const initials = computed(() => (props.ticket.customer_name || '?').charAt(0).toUpperCase())
const isCritical = computed(() => props.ticket.quality_badge === 'critical' || props.ticket.escalation_level === 'L4')
</script>

<style scoped>
.ticket-card { display: flex; align-items: center; gap: 14px; padding: 14px 18px; background: #fff; border: 1px solid #ECECE8; border-radius: 13px; cursor: pointer; transition: box-shadow 0.15s, border-color 0.15s; }
.ticket-card:hover { box-shadow: 0 4px 16px -6px rgba(17,17,26,0.12); }
.ticket-card--critical { border-color: #FCE7EA; background: #FFFAFA; }
.tc-avatar { width: 36px; height: 36px; border-radius: 10px; font-size: 15px; font-weight: 700; display: flex; align-items: center; justify-content: center; flex: none; }
.tc-body { flex: 1; min-width: 0; }
.tc-top { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px; }
.tc-name { font-size: 13.5px; font-weight: 700; color: #1C1C1E; }
.tc-id { font-size: 11.5px; font-weight: 600; color: #0F766E; }
.tc-meta { font-size: 11.5px; color: #9A9A93; margin-bottom: 5px; }
.tc-action { display: flex; align-items: center; gap: 5px; font-size: 11.5px; font-weight: 700; color: #1C1C1E; background: #F0FDFA; border-radius: 7px; padding: 4px 9px; width: fit-content; }
.tc-right { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; }
.tc-esc { display: flex; align-items: center; gap: 4px; font-size: 10.5px; font-weight: 700; color: #E11D48; background: #FFF1F3; padding: 2px 8px; border-radius: 6px; }
.tc-chevron { color: #C4C4BD; }
.tc-chevron .ms { font-size: 20px; }
</style>
