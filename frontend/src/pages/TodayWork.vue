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

    <!-- 6 work-priority metric cards (Stitch) -->
    <div class="lav-metric-grid">
      <div
        v-for="m in METRICS"
        :key="m.key"
        class="lav-metric"
        :style="{ '--lav-accent': accent(m.key) }"
        @click="scrollToBucket(m.key)"
        @keydown.enter="scrollToBucket(m.key)"
        @keydown.space.prevent="scrollToBucket(m.key)"
        tabindex="0"
        role="button"
      >
        <span class="material-symbols-outlined lav-metric__icon">{{ m.icon }}</span>
        <div class="lav-metric__label">{{ m.label }}</div>
        <div>
          <div class="lav-metric__num">{{ metricCount(m.key) }}</div>
          <div v-if="metricSub(m.key)" class="lav-metric__sub">{{ metricSub(m.key) }}</div>
        </div>
      </div>
    </div>

    <!-- Reminder Intelligence cards (Step 5) — click to filter the queue -->
    <div v-if="!loading && !error && summary.total > 0" class="flex flex-wrap gap-2 mb-gutter">
      <button
        v-for="c in intel"
        :key="c.key"
        class="lav-intel"
        :class="{ 'lav-intel--on': intelActive(c.key) }"
        :style="{ '--lav-accent': c.hue }"
        @click="intelActive(c.key) ? clearFilters() : applyIntel(c.key)"
      >
        <span class="material-symbols-outlined" style="font-size:18px">{{ c.icon }}</span>
        <span class="font-label-lg text-label-lg">{{ c.label }}</span>
        <span class="lav-intel__num">{{ c.count }}</span>
      </button>
    </div>

    <!-- States -->
    <div v-if="loading">
      <!-- Skeleton: metric grid -->
      <div class="lav-metric-grid mb-gutter">
        <div v-for="i in 6" :key="'m' + i" class="lav-metric" style="pointer-events:none">
          <div class="lav-skeleton" style="width:20px;height:20px;border-radius:999px"></div>
          <div style="display:flex;flex-direction:column;gap:4px">
            <div class="lav-skeleton" style="width:70px;height:12px"></div>
            <div class="lav-skeleton" style="width:30px;height:20px"></div>
          </div>
        </div>
      </div>
      <!-- Skeleton: queue rows -->
      <div class="flex flex-col gap-2">
        <div v-for="i in 5" :key="'r' + i" class="lav-skeleton" style="width:100%;height:52px;border-radius:8px"></div>
      </div>
    </div>
    <div v-else-if="error" class="text-error font-body-md py-12 text-center">
      Could not load Today’s Work. Check your access or contact the manager.
    </div>
    <div v-else-if="summary.total === 0" class="py-16 text-center">
      <div class="text-5xl mb-2">🎉</div>
      <div class="text-on-surface-variant font-body-lg">All clear — no pending work right now.</div>
    </div>

    <!-- Action Queue + stage/flow filters (delta Sprint 2) -->
    <template v-else>
      <div class="flex items-center gap-2 mb-gutter">
        <button @click="showFilters = !showFilters" class="lav-chip flex items-center gap-1">
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
          <span class="lav-badge" :style="{ background: group.count ? accent(group.key) : '#c3c6d7' }">{{ group.count }}</span>
          <h3 class="font-headline-md text-headline-md text-on-surface">{{ group.label }}</h3>
        </div>

        <div v-if="group.tickets.length === 0" style="padding: 12px 16px; color: #737686; font-size: 14px;">
          No {{ group.label.toLowerCase() }} tickets at the moment.
        </div>
        <ul v-else>
          <li
            v-for="t in group.tickets"
            :key="t.name"
            class="lav-work-card group cursor-pointer hover:bg-surface-container-low transition-all"
            :style="{ borderLeft: '4px solid ' + accent(group.key) }"
            @click="selectedTicket = t.name"
          >
            <div class="flex items-start gap-3 flex-1 min-w-0">
              <!-- Customer initial avatar -->
              <div class="w-9 h-9 rounded-full flex items-center justify-center shrink-0 font-label-md font-semibold text-on-primary"
                   :style="{ background: accent(group.key) }">
                {{ (t.customer_name || '?').charAt(0).toUpperCase() }}
              </div>
              <div class="min-w-0 flex-1">
                <div class="font-body-md font-semibold text-primary hover:underline truncate">
                  {{ t.subject || '(no subject)' }}
                </div>
                <div class="font-label-md text-label-md text-on-surface-variant mt-0.5 truncate">
                  <span class="text-on-surface font-medium">{{ t.name }}</span>
                  <template v-if="t.customer_name"> · {{ t.customer_name }}</template>
                  <template v-if="t.phone_1"> · {{ t.phone_1 }}</template>
                  <template v-if="product(t)"> · {{ product(t) }}</template>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-1.5 flex-wrap shrink-0">
              <span class="px-2 py-0.5 rounded-full font-label-md text-label-md"
                    :style="chip(t.status)">{{ t.status }}</span>
              <SlaBadge :agreement-status="t.agreement_status" :response-by="t.response_by" :resolution-by="t.resolution_by" />
              <span v-if="t.overdue_status && t.overdue_status !== 'Not Due'" class="px-2 py-0.5 rounded-full font-label-md text-label-md whitespace-nowrap" :style="dueChip(t.overdue_status)">{{ t.overdue_status }}</span>
              <span v-if="t.customer_promise_status === 'Breached'" class="px-2 py-0.5 rounded-full font-label-md text-label-md whitespace-nowrap" style="color:#ba1a1a;background:rgba(186,26,26,0.12)">Breach</span>
              <span v-if="escLevel(t) && escLevel(t) !== 'None'" class="px-2 py-0.5 rounded-full font-label-md text-label-md whitespace-nowrap" :style="escChip(escLevel(t))">{{ escLevel(t) }}</span>
              <span v-if="t.customer_update_due" class="px-2 py-0.5 rounded-full font-label-md text-label-md whitespace-nowrap" style="color:#0053db;background:rgba(0,83,219,0.12)">Update due</span>
            </div>
            <div class="flex items-center gap-3 shrink-0">
              <div v-if="t.pending_reason" class="font-label-md text-label-md text-on-surface-variant truncate max-w-[140px]" :title="t.pending_reason">
                {{ t.pending_reason }}
              </div>
              <div class="font-label-md text-label-md whitespace-nowrap" :style="followStyle(t.next_follow_up_date)">
                {{ followText(t.next_follow_up_date) }}
              </div>
            </div>
            <button class="px-3 py-1.5 rounded-lg border border-outline-variant text-primary font-label-md hover:bg-primary-container hover:text-on-primary hover:border-primary transition-all md:opacity-0 md:group-hover:opacity-100">
              Open
            </button>
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
import { chip, followText, followStyle, product, escChip, dueChip } from '@/utils'

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
    { key: 'promise_breach', label: 'Promise Breach', icon: 'gpp_bad', hue: '#ba1a1a',
      count: t.filter((x) => x.customer_promise_status === 'Breached').length },
    { key: 'escalated', label: 'Escalated', icon: 'priority_high', hue: '#943700',
      count: t.filter((x) => escLevel(x) !== 'None').length },
    { key: 'overdue', label: 'Overdue', icon: 'error', hue: '#ba1a1a',
      count: t.filter((x) => x.overdue_status === 'Overdue').length },
    { key: 'due_soon', label: 'Due Soon', icon: 'schedule', hue: '#943700',
      count: t.filter((x) => x.overdue_status === 'Due Soon').length },
    { key: 'update_due', label: 'Customer Update Due', icon: 'campaign', hue: '#0053db',
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

const ACCENT = {
  overdue_follow_up: '#ba1a1a',
  no_technician_update: '#ba1a1a',
  escalated_cases: '#ba1a1a',
  customer_not_informed: '#943700',
  technician_call_due: '#004ac6',
  technician_visit_due: '#2563eb',
  due_today: '#943700',
  registration_recommended: '#004ac6',
  registration_pending: '#2563eb',
  waiting_on_customer: '#0053db',
  waiting_on_part: '#943700',
  ready_for_pickup: '#1a7f37',
  customer_satisfaction_pending: '#712ae2',
  product_receipt_missing: '#712ae2',
  closure_pending: '#434655',
  new_complaints: '#004ac6',
  upcoming_work: '#434655',
}
function accent(key) {
  return ACCENT[key] || '#004ac6'
}

</script>
