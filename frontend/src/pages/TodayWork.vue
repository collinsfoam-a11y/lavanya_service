<!--
  Today's Work dashboard — ported from the Stitch "Today's Work Dashboard"
  screen (6-metric grid + single Action Queue). Data comes from the live
  backend: lavanya_service.api.today_work.get_today_work (role-aware grouping +
  priority order are decided server-side; this page only renders).
-->
<template>
  <AppShell>
    <div class="mb-gutter">
      <h2 class="font-headline-lg text-headline-lg text-on-surface">Today’s Work</h2>
      <p class="font-body-md text-on-surface-variant">{{ data?.date || '' }}</p>
    </div>

    <!-- Service Command Center — Critical / Important / Normal tiers -->
    <div v-for="tier in METRIC_TIERS" :key="tier.key" class="mb-gutter">
      <LavSectionHeader
        :title="tier.label"
        :icon="tier.icon"
        :badge="tierCount(tier)"
        :accent="tier.color"
      />
      <div class="lav-metric-grid">
        <LavStatCard
          v-for="m in tierMetrics(tier)"
          :key="m.key"
          :icon="m.icon"
          :label="m.label"
          :value="metricCount(m.key)"
          :caption="metricSub(m.key)"
          :accent="accent(m.key)"
          tabindex="0"
          role="button"
          :aria-label="'View ' + m.label + ' tickets'"
          @click="scrollToBucket(m.key)"
          @keydown.enter="scrollToBucket(m.key)"
          @keydown.space.prevent="scrollToBucket(m.key)"
        />
      </div>
    </div>

    <!-- Reminder Intelligence cards (Step 5) — click to filter the queue -->
      <div v-if="!loading && !error && summary.total > 0" class="flex flex-wrap gap-2 mb-gutter" role="group" aria-label="Filter shortcuts">
        <button
          v-for="c in intel"
          :key="c.key"
          class="lav-intel"
          :class="{ 'lav-intel--on': intelActive(c.key) }"
          :style="{ '--lav-accent': c.hue }"
          :aria-label="'Filter by ' + c.label + ': ' + c.count + ' tickets'"
          @click="intelActive(c.key) ? clearFilters() : applyIntel(c.key)"
        >
        <span class="material-symbols-outlined" style="font-size:18px">{{ c.icon }}</span>
        <span class="font-label-lg text-label-lg">{{ c.label }}</span>
        <span class="lav-intel__num">{{ c.count }}</span>
      </button>
    </div>

    <!-- States -->
    <LavLoadingState v-if="loading" layout="card-list" />
    <LavEmptyState
      v-else-if="error"
      icon="error"
      title="Could not load Today’s Work"
      message="Check your access or contact the manager."
      tone="error"
    />
    <LavEmptyState
      v-else-if="summary.total === 0"
      icon="celebration"
      title="All clear"
      message="No pending work right now."
    />

    <!-- Action Queue + stage/flow filters (delta Sprint 2) -->
    <template v-else>
      <div class="flex items-center gap-2 mb-gutter">
        <button @click="showFilters = !showFilters" class="lav-chip flex items-center gap-1" :aria-label="(showFilters ? 'Hide' : 'Show') + ' filters'">
          <span class="material-symbols-outlined" style="font-size:16px">{{ showFilters ? 'expand_less' : 'expand_more' }}</span>
          Filters
        </button>
        <button v-if="anyFilter" @click="clearFilters" class="lav-chip">Clear filters</button>
        <span class="font-label-md text-label-md text-on-surface-variant ml-auto">{{ filteredCount }} shown</span>
      </div>
      <div v-show="showFilters" class="flex flex-wrap items-center gap-2 mb-gutter">
        <select v-model="filters.flow" class="lav-input" style="width:auto;min-width:150px;height:36px">
          <option value="">All flows</option>
          <option v-for="o in filterOptions.flow" :key="o" :value="o">{{ o }}</option>
        </select>
        <select v-model="filters.stage" class="lav-input" style="width:auto;min-width:160px;height:36px">
          <option value="">All stages</option>
          <option v-for="o in filterOptions.stage" :key="o" :value="o">{{ o }}</option>
        </select>
        <select v-model="filters.due" class="lav-input" style="width:auto;min-width:130px;height:36px">
          <option value="">Any due status</option>
          <option v-for="o in DUE_OPTIONS" :key="o" :value="o">{{ o }}</option>
        </select>
        <select v-model="filters.escalation" class="lav-input" style="width:auto;min-width:140px;height:36px">
          <option value="">Any escalation</option>
          <option v-for="o in ESC_OPTIONS" :key="o" :value="o">{{ o }}</option>
        </select>
        <select v-model="filters.promise" class="lav-input" style="width:auto;min-width:140px;height:36px">
          <option value="">Any promise</option>
          <option v-for="o in PROMISE_OPTIONS" :key="o" :value="o">{{ o }}</option>
        </select>
        <select v-if="filterOptions.brand.length" v-model="filters.brand" class="lav-input" style="width:auto;min-width:120px;height:36px">
          <option value="">All brands</option>
          <option v-for="o in filterOptions.brand" :key="o" :value="o">{{ o }}</option>
        </select>
        <select v-if="filterOptions.productType.length" v-model="filters.productType" class="lav-input" style="width:auto;min-width:130px;height:36px">
          <option value="">All products</option>
          <option v-for="o in filterOptions.productType" :key="o" :value="o">{{ o }}</option>
        </select>
        <select v-if="filterOptions.nextAction.length" v-model="filters.nextAction" class="lav-input" style="width:auto;min-width:150px;height:36px">
          <option value="">Any next action</option>
          <option v-for="o in filterOptions.nextAction" :key="o" :value="o">{{ o }}</option>
        </select>
        <label class="lav-chip" style="cursor:pointer;display:inline-flex;align-items:center;gap:6px">
          <input type="checkbox" v-model="filters.updateDue" style="margin:0" /> Update due
        </label>
      </div>

      <div class="lav-queue">
      <div class="lav-queue__title">
        <span class="material-symbols-outlined">checklist</span> Action Queue
      </div>
      <div
        v-for="group in filteredGroups"
        :key="group.key"
        :id="'bucket-' + group.key"
        class="lav-bucket"
      >
        <div class="lav-bucket__head" :style="{ borderLeft: '4px solid ' + accent(group.key) }">
          <span class="lav-badge" :style="{ background: group.count ? accent(group.key) : COLORS.outline }">{{ group.count }}</span>
          <h3 class="font-headline-md text-headline-md text-on-surface">{{ group.label }}</h3>
        </div>

        <div v-if="group.tickets.length === 0" class="px-4 py-3 font-body-md text-on-surface-variant">
          No {{ group.label.toLowerCase() }} tickets at the moment.
        </div>
        <ul v-else role="list" :aria-label="'Tickets in ' + group.label">
          <li v-for="t in group.tickets" :key="t.name" class="p-3 border-b border-outline-variant last:border-b-0">
            <LavTicketCard :ticket="t" :accent="accent(group.key)" @open="selectedTicket = $event" />
          </li>
        </ul>
      </div>
      </div>
    </template>

    <!-- Ticket Detail Drawer -->
    <TicketDetail :ticketId="selectedTicket" @close="selectedTicket = null" @refresh="loadTodayWork" />
  </AppShell>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { call } from '@/api'
import AppShell from '@/components/AppShell.vue'
import TicketDetail from '@/components/TicketDetail.vue'
import SlaBadge from '@/components/SlaBadge.vue'
import LavCard from '@/components/LavCard.vue'
import LavSectionHeader from '@/components/LavSectionHeader.vue'
import LavStatCard from '@/components/LavStatCard.vue'
import LavChip from '@/components/LavChip.vue'
import LavEmptyState from '@/components/LavEmptyState.vue'
import LavLoadingState from '@/components/LavLoadingState.vue'
import LavTicketCard from '@/components/LavTicketCard.vue'
import { accentMetric, COLORS } from '@/utils/index.js'

const raw = ref({})
const loading = ref(true)
const error = ref(false)
const selectedTicket = ref(null)
const showFilters = ref(false)

async function loadTodayWork() {
  loading.value = true
  error.value = false
  try {
    raw.value = (await call('lavanya_service.api.today_work.get_today_work', { include_counts: 1 })) || {}
  } catch (e) {
    error.value = true
  } finally {
    loading.value = false
  }
}

onMounted(loadTodayWork)

const data = computed(() => raw.value || {})
const groups = computed(() => data.value.groups || [])
const summary = computed(() => data.value.summary || { total: 0, overdue: 0, due_today: 0 })

// ── Reminder Intelligence filtering (Sprint 2 + Step 5) ────────────────────────
// Prefer the Step-3 richer escalation (promise/repeat bumps) with Sprint-2 fallback.
function escLevel(t) {
  return t.computed_escalation_level || t.escalation_level || 'None'
}
const filters = reactive({
  flow: '', stage: '', due: '', escalation: '', promise: '',
  brand: '', productType: '', nextAction: '', updateDue: false,
})
const DUE_OPTIONS = ['Due Soon', 'Overdue', 'Not Due']
const ESC_OPTIONS = ['L1 - Agent Follow-up', 'L2 - Coordinator Escalation', 'L3 - Manager Escalation', 'L4 - Owner / Brand Manager Escalation']
const PROMISE_OPTIONS = ['Breached', 'Pending', 'Kept']
const allTickets = computed(() => groups.value.flatMap((g) => g.tickets || []))
const uniq = (vals) => [...new Set(vals.filter(Boolean))].sort()
const filterOptions = computed(() => ({
  flow: uniq(allTickets.value.map((t) => t.service_flow_type)),
  stage: uniq(allTickets.value.map((t) => t.current_service_stage)),
  brand: uniq(allTickets.value.map((t) => t.brand)),
  productType: uniq(allTickets.value.map((t) => t.product_type)),
  nextAction: uniq(allTickets.value.map((t) => t.next_action)),
}))
const anyFilter = computed(() =>
  !!(filters.flow || filters.stage || filters.due || filters.escalation || filters.promise ||
     filters.brand || filters.productType || filters.nextAction || filters.updateDue))
function matchesFilters(t) {
  if (filters.flow && t.service_flow_type !== filters.flow) return false
  if (filters.stage && t.current_service_stage !== filters.stage) return false
  if (filters.due && t.overdue_status !== filters.due) return false
  if (filters.escalation) {
    const lvl = escLevel(t)
    if (filters.escalation === 'Escalated') { if (lvl === 'None') return false }
    else if (lvl !== filters.escalation) return false
  }
  if (filters.promise && t.customer_promise_status !== filters.promise) return false
  if (filters.brand && t.brand !== filters.brand) return false
  if (filters.productType && t.product_type !== filters.productType) return false
  if (filters.nextAction && t.next_action !== filters.nextAction) return false
  if (filters.updateDue && !t.customer_update_due) return false
  return true
}
// Urgency-first ordering within each bucket (Step 5):
// Promise Breach → Owner → Manager → Overdue → Due Soon → rest.
function reminderRank(t) {
  if (t.customer_promise_status === 'Breached') return 6
  const e = escLevel(t)
  if (e === 'Owner' || e === 'L4 - Owner / Brand Manager Escalation') return 5
  if (e === 'Manager' || e === 'L3 - Manager Escalation') return 4
  if (t.overdue_status === 'Overdue') return 3
  if (t.overdue_status === 'Due Soon') return 2
  return 0
}
function sortByUrgency(tickets) {
  return [...tickets].sort((a, b) => reminderRank(b) - reminderRank(a))
}
const filteredGroups = computed(() =>
  groups.value.map((g) => {
    const tickets = sortByUrgency((g.tickets || []).filter(matchesFilters))
    return { ...g, tickets, count: tickets.length }
  })
)
const filteredCount = computed(() => filteredGroups.value.reduce((n, g) => n + (g.tickets?.length || 0), 0))
function clearFilters() {
  Object.assign(filters, { flow: '', stage: '', due: '', escalation: '', promise: '', brand: '', productType: '', nextAction: '', updateDue: false })
}

// Reminder Intelligence summary cards (Step 5) — derived client-side; click filters.
const intel = computed(() => {
  const t = allTickets.value
  return [
    { key: 'promise_breach', label: 'Promise Breach', icon: 'gpp_bad', hue: COLORS.error,
      count: t.filter((x) => x.customer_promise_status === 'Breached').length },
    { key: 'escalated', label: 'Escalated', icon: 'priority_high', hue: COLORS.warning,
      count: t.filter((x) => escLevel(x) !== 'None').length },
    { key: 'overdue', label: 'Overdue', icon: 'error', hue: COLORS.error,
      count: t.filter((x) => x.overdue_status === 'Overdue').length },
    { key: 'due_soon', label: 'Due Soon', icon: 'schedule', hue: COLORS.warning,
      count: t.filter((x) => x.overdue_status === 'Due Soon').length },
    { key: 'update_due', label: 'Customer Update Due', icon: 'campaign', hue: COLORS.secondary,
      count: t.filter((x) => x.customer_update_due).length },
  ]
})
function applyIntel(key) {
  clearFilters()
  if (key === 'promise_breach') filters.promise = 'Breached'
  else if (key === 'escalated') filters.escalation = 'Escalated'
  else if (key === 'overdue') filters.due = 'Overdue'
  else if (key === 'due_soon') filters.due = 'Due Soon'
  else if (key === 'update_due') filters.updateDue = true
}
function intelActive(key) {
  if (key === 'promise_breach') return filters.promise === 'Breached'
  if (key === 'escalated') return filters.escalation === 'Escalated'
  if (key === 'overdue') return filters.due === 'Overdue'
  if (key === 'due_soon') return filters.due === 'Due Soon'
  if (key === 'update_due') return filters.updateDue === true
  return false
}


// 6 priority metric cards (Stitch "Today's Work Dashboard").
const METRICS = [
  { key: 'overdue_follow_up', label: 'Overdue Follow-up', icon: 'warning' },
  { key: 'no_technician_update', label: 'No Tech Update', icon: 'cell_tower' },
  { key: 'escalated_cases', label: 'Escalated', icon: 'escalator_warning' },
  { key: 'customer_not_informed', label: 'Not Informed', icon: 'campaign' },
  { key: 'technician_call_due', label: 'Tech Call Due', icon: 'phone_in_talk' },
  { key: 'technician_visit_due', label: 'Tech Visit Due', icon: 'handyman' },
  { key: 'due_today', label: 'Due Today', icon: 'event' },
  { key: 'customer_satisfaction_pending', label: 'Satis. Pending', icon: 'feedback' },
  { key: 'registration_pending', label: 'Registration Pending', icon: 'app_registration' },
  { key: 'waiting_on_customer', label: 'Wait Customer', icon: 'hourglass_top' },
  { key: 'waiting_on_part', label: 'Wait Part', icon: 'build' },
  { key: 'ready_for_pickup', label: 'Ready Pickup', icon: 'inventory_2' },
  { key: 'product_receipt_missing', label: 'Missing Receipt', icon: 'receipt_long' },
  { key: 'closure_pending', label: 'Closure Pending', icon: 'task_alt' },
  { key: 'new_complaints', label: 'New Complaint', icon: 'fiber_new' },
]

const METRIC_TIERS = [
  { key: 'critical', label: 'Critical', color: COLORS.error, icon: 'warning',
    keys: ['overdue_follow_up', 'no_technician_update', 'escalated_cases', 'customer_not_informed'] },
  { key: 'important', label: 'Important', color: COLORS.warning, icon: 'priority_high',
    keys: ['technician_call_due', 'technician_visit_due', 'due_today', 'customer_satisfaction_pending'] },
  { key: 'normal', label: 'Normal', color: COLORS.primary, icon: 'check_circle',
    keys: ['registration_pending', 'waiting_on_customer', 'waiting_on_part', 'ready_for_pickup',
           'product_receipt_missing', 'closure_pending', 'new_complaints'] },
]

function tierMetrics(tier) {
  return tier.keys.map(k => METRICS.find(m => m.key === k)).filter(Boolean)
}

function tierCount(tier) {
  return tier.keys.reduce((sum, k) => sum + metricCount(k), 0)
}
function metricGroup(key) {
  return groups.value.find((g) => g.key === key)
}
function metricCount(key) {
  const g = metricGroup(key)
  return g ? (g.count != null ? g.count : g.tickets.length) : 0
}

// Honest sub-detail lines derived from each group's loaded tickets (matches the
// Stitch metric cards' second line). Computed client-side — no extra API call.
function daysSince(value) {
  if (!value) return null
  const d = new Date(String(value).slice(0, 10))
  const today = new Date(new Date().toISOString().slice(0, 10))
  return Math.round((today - d) / 86400000)
}
function oldestFollowUpDays(g) {
  const dates = (g?.tickets || []).map((t) => t.next_follow_up_date).filter(Boolean)
  if (!dates.length) return null
  return daysSince(dates.reduce((a, b) => (a < b ? a : b)))
}
function highPriorityCount(g) {
  return (g?.tickets || []).filter((t) => t.priority === 'High' || t.priority === 'Urgent').length
}
function metricSub(key) {
  const g = metricGroup(key)
  if (!g || !metricCount(key)) return ''
  if (key === 'overdue_follow_up' || key === 'no_technician_update') {
    const n = oldestFollowUpDays(g)
    return n != null ? `Oldest: ${n}d overdue` : 'Needs attention'
  }
  if (key === 'escalated_cases') return 'Requires escalation handling'
  if (key === 'customer_not_informed') return 'Customer needs contact'
  if (key === 'technician_call_due' || key === 'technician_visit_due') {
    const n = oldestFollowUpDays(g)
    return n != null ? `Oldest: ${n}d` : 'Pending verification'
  }
  if (key === 'due_today') {
    const n = highPriorityCount(g)
    return n ? `${n} high priority` : 'On schedule'
  }
  if (key === 'customer_satisfaction_pending') return 'Awaiting feedback'
  if (key === 'waiting_on_customer') {
    const n = oldestFollowUpDays(g)
    return n != null ? `Oldest: ${n}d` : 'Awaiting reply'
  }
  if (key === 'waiting_on_part') return 'Waiting for parts'
  if (key === 'registration_pending') return 'Action required'
  if (key === 'ready_for_pickup') return 'Ready to hand over'
  if (key === 'product_receipt_missing') return 'Receipt not created'
  if (key === 'closure_pending') return 'Pending closure'
  if (key === 'new_complaints') return 'Needs triage'
  return ''
}
function scrollToBucket(key) {
  const el = document.getElementById('bucket-' + key)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function accent(key) {
  return accentMetric(key)
}

</script>
