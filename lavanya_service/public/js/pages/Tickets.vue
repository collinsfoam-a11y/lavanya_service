<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Tickets</h1>
        <p class="page-sub">{{ total }} complaints across all stages</p>
      </div>
      <button class="btn btn--dark" @click="navigate('lavanya-new-ticket')">
        <span class="ms">add</span> New Ticket
      </button>
    </div>

    <!-- search + sort -->
    <div class="toolbar">
      <div class="search-box">
        <span class="ms">search</span>
        <input v-model="searchInput" class="search-input" placeholder="Search ticket #, subject, customer or phone…"
          @input="onSearch" />
        <span v-if="searchInput" class="ms clear-btn" @click="searchInput=''; setSearch('')">close</span>
      </div>
      <div class="sort-ctrl" @click="cycleSort">
        <span class="ms">swap_vert</span>{{ sortLabel }}
      </div>
    </div>

    <!-- status chips -->
    <div class="status-chips">
      <span v-for="s in STATUS_FILTERS" :key="s.key"
        class="status-chip" :class="{ 'status-chip--active': activeStatus === s.key }"
        @click="setStatusFilter(s.key)">
        {{ s.label }}
        <span v-if="s.key === 'all'" class="sc-count">{{ total }}</span>
      </span>
    </div>

    <div v-if="loading" class="loading-state"><span class="ms spin">sync</span> Loading…</div>
    <div v-else-if="error" class="error-state">
      <span class="ms">error</span> {{ error }}
      <button class="btn btn--outline" @click="fetch">Retry</button>
    </div>

    <div v-else class="ticket-list">
      <div v-if="!tickets.length" class="empty-state">
        <span class="ms">inbox</span>
        <div>No tickets found</div>
        <button class="btn btn--teal" @click="navigate('lavanya-new-ticket')">
          <span class="ms">add</span> Create First Ticket
        </button>
      </div>

      <div v-for="t in tickets" :key="t.name"
        class="ticket-card" @click="navigate('lavanya-ticket-detail', 'name=' + t.name)">
        <div class="tc-avatar" :style="avatarStyle(t)">{{ initials(t.customer_name) }}</div>
        <div class="tc-main">
          <div class="tc-subject">{{ t.subject }}</div>
          <div class="tc-meta">
            <span class="tc-id">#{{ t.name }}</span> · {{ t.customer_name }}
            <span v-if="t.customer_phone"> · {{ t.customer_phone }}</span>
          </div>
        </div>
        <div class="tc-status"><StatusBadge :status="t.status" /></div>
        <div class="tc-context">
          <div class="tc-brand-line">{{ t.brand || '—' }} · <span class="tc-hint">{{ nextActionHint(t) }}</span></div>
          <div class="tc-chips">
            <span v-if="t.sla_breached" class="lav-mini-chip" style="background:#FFF1F3;color:#E11D48"><span class="ms">timer_off</span>SLA breached</span>
            <span v-else-if="t.sla_due_date" class="lav-mini-chip" style="background:#FFF7ED;color:#D97706"><span class="ms">timer</span>{{ slaLabel(t.sla_due_date) }}</span>
            <span v-else-if="t.status === 'Replied'" class="lav-mini-chip" style="background:#F4F4F1;color:#71717A"><span class="ms">pause_circle</span>SLA paused</span>
            <span v-if="t.escalation_level && t.escalation_level !== 'L1'" class="lav-mini-chip" style="background:#FEF2F2;color:#B91C1C">{{ escLabel(t.escalation_level) }}</span>
            <QualityBadge v-if="t.quality_badge" :badge="t.quality_badge" />
            <span v-if="t.service_path" class="lav-mini-chip" style="background:#F4F4F1;color:#6B6B66"><span class="ms">event_repeat</span>{{ cadenceLabel(t) }}</span>
          </div>
        </div>
        <div class="tc-followup">
          <div class="tc-fu-label">Follow-up</div>
          <div class="tc-fu-date" :class="fuClass(t.next_followup_date)">
            {{ t.next_followup_date ? fmtDate(t.next_followup_date) : '—' }}
          </div>
        </div>
        <span class="ms tc-chevron">chevron_right</span>
      </div>
    </div>

    <div class="pagination" v-if="totalPages > 1">
      <span class="pg-info">Showing {{ pageStart }}–{{ pageEnd }} of {{ total }}</span>
      <div class="pg-controls">
        <button class="pg-btn" :disabled="page === 1" @click="setPage(page - 1)">
          <span class="ms">chevron_left</span>
        </button>
        <button v-for="p in pageRange" :key="p"
          class="pg-btn" :class="{ 'pg-btn--active': p === page }" @click="setPage(p)">{{ p }}</button>
        <button class="pg-btn" :disabled="page === totalPages" @click="setPage(page + 1)">
          <span class="ms">chevron_right</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import StatusBadge from '../components/StatusBadge.vue'
import QualityBadge from '../components/QualityBadge.vue'
import { useTicketList } from '../composables/useTickets.js'
import { navigate } from '../composables/frappe.js'

const props = defineProps({ frappePage: Object })
const { tickets, total, totalPages, loading, error, page, pageSize, filters, setStatus, setSearch, setPage, refresh: fetch } = useTicketList()

const searchInput = ref('')
const activeStatus = ref('all')
const sortBy = ref('creation desc')
const SORT_CYCLE = [
  { v: 'creation desc',  label: 'Newest' },
  { v: 'creation asc',   label: 'Oldest' },
  { v: 'days_open desc', label: 'Most Overdue' },
]
const sortLabel = computed(() => SORT_CYCLE.find(s => s.v === sortBy.value)?.label || 'Newest')
function cycleSort() {
  const idx = SORT_CYCLE.findIndex(s => s.v === sortBy.value)
  sortBy.value = SORT_CYCLE[(idx + 1) % SORT_CYCLE.length].v
  fetch()
}

let searchTimer = null
function onSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => setSearch(searchInput.value), 400)
}

function setStatusFilter(key) {
  activeStatus.value = key
  setStatus(key === 'all' ? '' : key)
}

const STATUS_FILTERS = [
  { key: 'all',                           label: 'All' },
  { key: 'New',                           label: 'New' },
  { key: 'Registered',                    label: 'Registration Pending' },
  { key: 'In Follow-up',                  label: 'In Progress' },
  { key: 'Waiting',                       label: 'Waiting on Customer' },
  { key: 'Resolved by Brand',             label: 'Ready for Pickup' },
  { key: 'Customer Confirmation Pending', label: 'Confirmation Pending' },
  { key: 'Closed',                        label: 'Closed' },
  { key: 'Reopened',                      label: 'Reopened' },
]

const pageStart = computed(() => (page.value - 1) * pageSize + 1)
const pageEnd   = computed(() => Math.min(page.value * pageSize, total.value))
const pageRange = computed(() => Array.from({ length: Math.min(5, totalPages.value) }, (_, i) => i + 1))

const COLORS = [['#EEF2FF','#4F46E5'],['#EDE9FE','#7C3AED'],['#DCFCE7','#059669'],['#FFF1F3','#E11D48'],['#CCFBF1','#0D9488'],['#FFF7ED','#D97706']]
function avatarStyle(t) {
  const idx = (t.customer_name?.charCodeAt(0)||0) % COLORS.length
  return { background: COLORS[idx][0], color: COLORS[idx][1] }
}
function initials(n) { return (n||'?').split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase() }

function nextActionHint(t) {
  if (!t.next_action) return 'Review required'
  const a = t.next_action
  if (a.length > 40) return a.slice(0, 38) + '…'
  return a
}
function escLabel(l) {
  const map = { L1: 'L1', L2: 'L2 Manager', L3: 'L3 Manager', L4: 'L4 Owner' }
  return map[l] || l
}
function cadenceLabel(t) {
  if (t.service_path && t.service_path.includes('Brand')) return 'Brand · 2d'
  if (t.service_path === 'Local Paid Service') return 'Confirm · next-day'
  return t.service_path || ''
}
function fmtDate(d) {
  if (!d) return '—'
  const dt = new Date(d), now = new Date()
  const diff = Math.round((dt - now) / 86400000)
  if (diff === 0) return 'Today'
  if (diff === -1) return 'Yesterday'
  if (diff < 0) return Math.abs(diff) + 'd overdue'
  if (diff === 1) return 'Tomorrow'
  return dt.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}
function fuClass(d) {
  if (!d) return ''
  const diff = Math.round((new Date(d) - new Date()) / 86400000)
  if (diff < 0) return 'fu--overdue'
  if (diff === 0) return 'fu--today'
  return ''
}
function slaLabel(d) {
  if (!d) return ''
  const h = Math.round((new Date(d) - new Date()) / 3600000)
  if (h < 0) return 'Breached'
  if (h < 24) return 'Resp ' + h + 'h'
  return Math.round(h/24) + 'd left'
}

defineExpose({ refresh: fetch, setFilter: (k, v) => { if (k === 'status') setStatusFilter(v) } })
</script>

<style scoped>
.page{padding:24px 28px;max-width:1400px}
.page-header{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:18px}
.page-title{font-size:21px;font-weight:800;color:#1C1C1E;letter-spacing:-0.02em;margin:0}
.page-sub{font-size:13px;color:#8B8B85;margin:2px 0 0}

.toolbar{display:flex;gap:8px;margin-bottom:14px}
.search-box{flex:1;display:flex;align-items:center;gap:8px;height:40px;padding:0 16px;border-radius:12px;background:#fff;border:1px solid #ECECE8}
.search-input{flex:1;border:none;outline:none;font-size:13px;background:transparent;font-family:inherit}
.clear-btn{cursor:pointer;color:#A1A19B;font-size:18px}
.sort-ctrl{display:flex;align-items:center;gap:6px;height:40px;padding:0 14px;border-radius:12px;background:#fff;border:1px solid #ECECE8;font-size:12.5px;font-weight:700;color:#52525B;cursor:pointer}
.sort-ctrl .ms{font-size:17px;color:#A1A19B}

.status-chips{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:18px}
.status-chip{padding:7px 14px;border-radius:10px;background:#fff;border:1px solid #ECECE8;color:#52525B;font-size:12px;font-weight:600;cursor:pointer;transition:all .15s}
.status-chip--active{background:#1C1C1E;color:#fff;border-color:#1C1C1E}
.sc-count{opacity:.5;margin-left:4px}

.ticket-list{display:flex;flex-direction:column;gap:9px}
.ticket-card{background:#fff;border:1px solid #ECECE8;border-radius:14px;padding:15px 18px;display:flex;align-items:center;gap:16px;cursor:pointer;box-shadow:0 1px 2px rgba(17,17,26,0.04);transition:box-shadow .15s,transform .1s}
.ticket-card:hover{box-shadow:0 4px 20px -6px rgba(17,17,26,.12);transform:translateY(-1px)}
.tc-avatar{width:38px;height:38px;border-radius:11px;font-size:15px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}
.tc-main{width:230px;flex:none}
.tc-subject{font-size:13.5px;font-weight:700;color:#1C1C1E;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tc-meta{font-size:11.5px;color:#9A9A93;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tc-id{font-family:'JetBrains Mono',monospace;color:#0F766E;font-weight:600}
.tc-status{flex:none;width:118px}
.tc-context{flex:1;min-width:0}
.tc-brand-line{font-size:12.5px;font-weight:600;color:#1C1C1E;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tc-hint{color:#8B8B85;font-weight:500}
.tc-chips{display:flex;gap:5px;margin-top:5px;flex-wrap:wrap}
.tc-followup{flex:none;width:120px;text-align:right}
.tc-fu-label{font-size:10px;font-weight:700;color:#A1A19B;text-transform:uppercase;letter-spacing:.04em}
.tc-fu-date{font-family:'JetBrains Mono',monospace;font-size:12px;font-weight:600;margin-top:2px}
.fu--today{color:#D97706}.fu--overdue{color:#E11D48}
.tc-chevron{color:#C4C4BD;font-size:20px;flex:none}

.pagination{display:flex;align-items:center;justify-content:space-between;margin-top:20px}
.pg-info{font-size:12px;color:#9A9A93;font-weight:600}
.pg-controls{display:flex;gap:5px}
.pg-btn{min-width:32px;height:32px;border-radius:9px;border:1px solid #ECECE8;background:#fff;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:600;color:#52525B;cursor:pointer}
.pg-btn--active{background:#1C1C1E;color:#fff;border-color:#1C1C1E}
.pg-btn:disabled{opacity:.4;cursor:not-allowed}

.empty-state{padding:60px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:12px;color:#A1A19B}
.empty-state .ms{font-size:36px;color:#C4C4BD;font-variation-settings:'FILL' 1}
.loading-state,.error-state{padding:48px;text-align:center;display:flex;align-items:center;justify-content:center;gap:10px;color:#9A9A93;font-weight:600}

.btn{display:inline-flex;align-items:center;gap:6px;padding:9px 16px;border-radius:11px;font-size:13px;font-weight:700;border:none;cursor:pointer;font-family:inherit}
.btn--dark{background:#1C1C1E;color:#fff}.btn--teal{background:#0D9488;color:#fff}.btn--outline{background:#fff;border:1px solid #ECECE8;color:#52525B}
@keyframes spin{to{transform:rotate(360deg)}}.spin{display:inline-block;animation:spin 1s linear infinite}
.ms{font-family:'Material Symbols Rounded';font-weight:normal;font-style:normal;line-height:1;font-size:18px}
.lav-mini-chip{display:inline-flex;align-items:center;gap:3px;padding:2px 7px;border-radius:6px;font-size:10px;font-weight:700}
.lav-mini-chip .ms{font-size:11px}
</style>
