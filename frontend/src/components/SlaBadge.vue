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
    :style="{ color: info.color, background: `color-mix(in srgb, ${info.color} 13%, transparent)` }"
    :title="info.title"
  >
    <span class="material-symbols-outlined" style="font-size: 13px">{{ info.icon }}</span>
    {{ info.label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  agreementStatus: { type: String, default: null },
  responseBy: { type: String, default: null },
  resolutionBy: { type: String, default: null },
})

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
  if (s === 'Fulfilled') return { label: 'SLA met', color: 'var(--lav-success)', icon: 'check_circle', title: 'SLA fulfilled' }
  if (s === 'Failed') return { label: 'SLA breached', color: 'var(--lav-danger)', icon: 'error', title: 'SLA failed' }
  if (s === 'Paused') return { label: 'SLA paused', color: 'var(--lav-muted)', icon: 'pause_circle', title: 'SLA paused' }

  const isResp = s === 'First Response Due'
  const who = isResp ? 'Resp' : 'Resln'
  const r = rel(isResp ? props.responseBy : props.resolutionBy)
  const title = `${isResp ? 'First response' : 'Resolution'} by ${r ? r.when : '—'}`
  if (!r) return { label: `${who} due`, color: 'var(--lav-secondary)', icon: 'schedule', title }
  if (r.overdue) return { label: `${who} overdue ${r.text}`, color: 'var(--lav-danger)', icon: 'error', title }
  if (r.soon) return { label: `${who} due ${r.text}`, color: 'var(--lav-warning)', icon: 'hourglass_top', title }
  return { label: `${who} due ${r.text}`, color: 'var(--lav-secondary)', icon: 'schedule', title }
})
</script>
