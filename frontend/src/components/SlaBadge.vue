<!--
  SLA badge — renders Helpdesk's SLA state (agreement_status + response_by /
  resolution_by deadlines) as a compact due/breach pill. Shared across the
  Tickets list, Today's Work queue, and the ticket detail drawer.
    Failed     -> red "Breached"
    Fulfilled  -> green "Met"
    Paused     -> gray "Paused"
    *Due       -> blue/amber/red "Resp|Resln due|overdue Xh/Xd"
  Renders nothing when there's no SLA on the ticket.
-->
<template>
  <span
    v-if="info"
    class="px-2 py-0.5 rounded-full font-label-md text-label-md inline-flex items-center gap-1 whitespace-nowrap"
    :style="{ color: info.color, background: tint(info.color) }"
    :title="info.title"
  >
    <span class="material-symbols-outlined" style="font-size: 13px">{{ info.icon }}</span>
    {{ info.label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { COLORS } from '@/utils'

const props = defineProps({
  agreementStatus: { type: String, default: null },
  responseBy: { type: String, default: null },
  resolutionBy: { type: String, default: null },
})

function tint(hex, a = 0.12) {
  const h = hex.replace('#', '')
  return `rgba(${parseInt(h.slice(0, 2), 16)}, ${parseInt(h.slice(2, 4), 16)}, ${parseInt(h.slice(4, 6), 16)}, ${a})`
}

function rel(deadline) {
  if (!deadline) return null
  const d = new Date(String(deadline).replace(' ', 'T'))
  const ms = d.getTime() - Date.now()
  const abs = Math.abs(ms)
  const mins = Math.round(abs / 60000)
  const hrs = Math.round(abs / 3600000)
  const days = Math.round(abs / 86400000)
  const text = mins < 60 ? `${mins}m` : hrs < 24 ? `${hrs}h` : `${days}d`
  return { overdue: ms < 0, soon: ms >= 0 && ms < 86400000, text, when: d.toLocaleString() }
}

const info = computed(() => {
  const s = props.agreementStatus
  if (!s) return null
  if (s === 'Fulfilled') return { label: 'SLA met', color: COLORS.success, icon: 'check_circle', title: 'SLA fulfilled' }
  if (s === 'Failed') return { label: 'SLA breached', color: COLORS.error, icon: 'error', title: 'SLA failed' }
  if (s === 'Paused') return { label: 'SLA paused', color: COLORS.neutral, icon: 'pause_circle', title: 'SLA paused' }

  const isResp = s === 'First Response Due'
  const who = isResp ? 'Resp' : 'Resln'
  const r = rel(isResp ? props.responseBy : props.resolutionBy)
  const title = `${isResp ? 'First response' : 'Resolution'} by ${r ? r.when : '—'}`
  if (!r) return { label: `${who} due`, color: COLORS.secondary, icon: 'schedule', title }
  if (r.overdue) return { label: `${who} overdue ${r.text}`, color: COLORS.error, icon: 'error', title }
  if (r.soon) return { label: `${who} due ${r.text}`, color: COLORS.warning, icon: 'hourglass_top', title }
  return { label: `${who} due ${r.text}`, color: COLORS.secondary, icon: 'schedule', title }
})
</script>
