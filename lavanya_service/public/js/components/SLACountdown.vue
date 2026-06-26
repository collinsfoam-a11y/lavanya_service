<template>
  <div class="sla-badge" :class="stateClass">
    <div class="sla-label">{{ label }}</div>
    <div class="sla-time" :class="{ 'sla-pulse': state === 'critical', 'sla-tick': state === 'breached' }">
      {{ displayTime }}
    </div>
    <div class="sla-sub">{{ subLabel }}</div>
    <!-- Progress bar (only for non-breached) -->
    <div v-if="state !== 'breached' && totalSeconds > 0" class="sla-bar-track">
      <div class="sla-bar-fill" :style="{ width: progressPct + '%', background: barColor }"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  deadlineIso: { type: String, required: true },
  totalSeconds: { type: Number, default: 172800 }, // 2 days default SLA
})

const now = ref(Date.now())
let timer = null

onMounted(() => { timer = setInterval(() => { now.value = Date.now() }, 30000) })
onUnmounted(() => clearInterval(timer))

const diffSeconds = computed(() => {
  const deadline = new Date(props.deadlineIso).getTime()
  return Math.floor((deadline - now.value) / 1000)
})

const state = computed(() => {
  const s = diffSeconds.value
  if (s < 0) return 'breached'
  if (s < 7200) return 'critical'
  if (s < props.totalSeconds * 0.25) return 'warning'
  return 'good'
})

const progressPct = computed(() => {
  const used = props.totalSeconds - diffSeconds.value
  return Math.min(100, Math.max(0, (used / props.totalSeconds) * 100))
})

const formatTime = (secs) => {
  const abs = Math.abs(secs)
  const d = Math.floor(abs / 86400)
  const h = Math.floor((abs % 86400) / 3600)
  const m = Math.floor((abs % 3600) / 60)
  if (d > 0) return `${secs < 0 ? '+' : ''}${d}d ${h}h`
  return `${h}h ${String(m).padStart(2, '0')}m`
}

const displayTime = computed(() => formatTime(diffSeconds.value))
const barColor = computed(() => ({ good: '#0D9488', warning: '#F59E0B', critical: '#EF4444' }[state.value] || '#EF4444'))
const label = computed(() => state.value === 'breached' ? 'SLA breach' : state.value === 'critical' ? 'SLA breach in' : state.value === 'warning' ? 'Follow-up due in' : 'SLA remaining')
const subLabel = computed(() => ({ good: 'On track', warning: 'Act today', critical: '⚡ Act now', breached: 'Overdue' }[state.value]))
const stateClass = computed(() => `sla-${state.value}`)
</script>

<style scoped>
.sla-badge { border-radius: 10px; padding: 8px 13px; text-align: center; min-width: 110px; }
.sla-label { font-size: 9.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
.sla-time { font-family: 'JetBrains Mono', monospace; font-size: 19px; font-weight: 700; line-height: 1.1; margin-top: 2px; }
.sla-sub { font-size: 9px; margin-top: 1px; }
.sla-bar-track { height: 4px; border-radius: 2px; background: rgba(0,0,0,0.08); margin-top: 5px; overflow: hidden; }
.sla-bar-fill { height: 100%; border-radius: 2px; transition: width 0.5s; }

.sla-good { background: #F0FDFA; border: 1px solid #CCFBF1; }
.sla-good .sla-label { color: #0F766E; }
.sla-good .sla-time { color: #0D9488; }
.sla-good .sla-sub { color: #0D9488; }

.sla-warning { background: #FFFBEB; border: 1px solid #FDE68A; }
.sla-warning .sla-label { color: #92400E; }
.sla-warning .sla-time { color: #D97706; }
.sla-warning .sla-sub { color: #D97706; }

.sla-critical { background: #FFF1F3; border: 1px solid #FCE7EA; }
.sla-critical .sla-label { color: #9F1239; }
.sla-critical .sla-time { color: #E11D48; }
.sla-critical .sla-sub { color: #E11D48; }

.sla-breached { background: #FFF1F3; border: 1px solid #FCE7EA; }
.sla-breached .sla-label { color: #9F1239; }
.sla-breached .sla-time { color: #E11D48; }
.sla-breached .sla-sub { color: #FCA5A5; }

@keyframes sla-pulse { 0%,100%{box-shadow:0 0 0 0 rgba(225,29,72,0.4);} 50%{box-shadow:0 0 0 6px rgba(225,29,72,0);} }
.sla-critical { animation: sla-pulse 2s infinite; }
@keyframes sla-tick { 0%,100%{opacity:1;} 50%{opacity:0.45;} }
.sla-tick { animation: sla-tick 1s infinite; }
</style>
