<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Good morning, {{ staffName }}</h1>
        <p class="page-sub">{{ todayLabel }} ·
          <span class="highlight" v-if="counts.critical">{{ counts.critical }} tickets need action</span>
          <span v-else class="text--teal">All caught up</span>
        </p>
      </div>
      <button class="btn btn--dark" @click="navigate('lavanya-new-ticket')">
        <span class="ms">add</span> New Ticket
      </button>
    </div>

    <div v-if="loading" class="loading-state"><span class="ms spin">sync</span> Loading today's work…</div>

    <div v-else-if="error" class="error-state">
      <span class="ms">error</span> {{ error }}
      <button class="btn btn--outline" @click="refresh">Retry</button>
    </div>

    <template v-else>
      <!-- 3 Priority Lanes -->
      <div class="lanes">
        <div class="lane">
          <div class="lane-head">
            <div class="lane-icon"><span class="ms">warning</span></div>
            <div><div class="lane-title">Needs you now</div><div class="lane-sub">Overdue & escalated</div></div>
            <div class="lane-count lc--red">{{ buckets.counts?.critical || 0 }}</div>
          </div>
          <div class="lane-chips">
            <div class="chip chip--red">
              <span class="chip-n">{{ chipCount.critOverdue }}</span>Overdue follow-up
            </div>
            <div class="chip chip--red">
              <span class="chip-n">{{ chipCount.critEscalated }}</span>Escalated
            </div>
          </div>
        </div>
        <div class="lane">
          <div class="lane-head">
            <div class="lane-icon lane-icon--amber"><span class="ms">hourglass_top</span></div>
            <div><div class="lane-title">Waiting on us</div><div class="lane-sub">Customer expects update</div></div>
            <div class="lane-count lc--amber">{{ buckets.counts?.important || 0 }}</div>
          </div>
          <div class="lane-chips">
            <div class="chip chip--amber">
              <span class="chip-n">{{ chipCount.impNotInformed }}</span>Not informed
            </div>
            <div class="chip chip--amber">
              <span class="chip-n">{{ chipCount.impDueToday }}</span>Due today
            </div>
          </div>
        </div>
        <div class="lane">
          <div class="lane-head">
            <div class="lane-icon lane-icon--teal"><span class="ms">trending_up</span></div>
            <div><div class="lane-title">In motion</div><div class="lane-sub">Moving through pipeline</div></div>
            <div class="lane-count lc--teal">{{ buckets.counts?.normal || 0 }}</div>
          </div>
          <div class="lane-chips">
            <div class="chip chip--teal">
              <span class="chip-n">{{ chipCount.normNew }}</span>New complaints
            </div>
            <div class="chip chip--teal">
              <span class="chip-n">{{ chipCount.normSatisfaction }}</span>Satisfaction pending
            </div>
          </div>
        </div>
      </div>

      <!-- Compact stat strip -->
      <div class="stat-strip">
        <div class="ss-cell">
          <div class="ss-icon ss-icon--green"><span class="ms">inventory_2</span></div>
          <div><div class="ss-val">{{ statStrip.readyPickup }}</div><div class="ss-lbl">Ready pickup</div></div>
        </div>
        <div class="ss-div"></div>
        <div class="ss-cell">
          <div class="ss-icon ss-icon--amber"><span class="ms">build</span></div>
          <div><div class="ss-val">{{ statStrip.waitingPart }}</div><div class="ss-lbl">Waiting part</div></div>
        </div>
        <div class="ss-div"></div>
        <div class="ss-cell">
          <div class="ss-icon ss-icon--indigo"><span class="ms">hourglass_empty</span></div>
          <div><div class="ss-val">{{ statStrip.waitCustomer }}</div><div class="ss-lbl">Wait customer</div></div>
        </div>
        <div class="ss-div"></div>
        <div class="ss-cell">
          <div class="ss-icon ss-icon--violet"><span class="ms">receipt_long</span></div>
          <div><div class="ss-val">{{ statStrip.missingReceipt }}</div><div class="ss-lbl">Missing receipt</div></div>
        </div>
        <div class="ss-div"></div>
        <div class="ss-cell">
          <div class="ss-icon ss-icon--gray"><span class="ms">task_alt</span></div>
          <div><div class="ss-val">{{ statStrip.closurePending }}</div><div class="ss-lbl">Closure pending</div></div>
        </div>
      </div>

      <!-- Action Queue header -->
      <div class="section-header">
        <div class="sh-left">
          <span class="section-title">Action Queue</span>
          <span class="sh-pill">prioritised for you</span>
        </div>
        <div class="filters">
          <span v-for="f in qFilters" :key="f.key"
            class="filter-chip" :class="{ 'filter-chip--active': activeFilter === f.key }"
            @click="activeFilter = f.key">
            <span class="filter-dot" :style="{ background: f.color }"></span>{{ f.label }}
            <span class="filter-count">{{ f.count }}</span>
          </span>
        </div>
      </div>

      <!-- Ticket table -->
      <div class="ticket-table">
        <template v-for="group in visibleGroups" :key="group.key">
          <div class="group-header" :class="'group--' + group.type">
            <span class="group-dot" :style="{ background: group.color }"></span>
            <span class="group-label">{{ group.label }}</span>
            <span class="group-badge">{{ group.tickets.length }}</span>
          </div>
          <div v-for="t in group.tickets" :key="t.name"
            class="ticket-row" @click="navigate('lavanya-ticket-detail', 'name=' + t.name)">
            <div class="tr-avatar" :style="avatarStyle(t)">{{ initials(t.customer_name) }}</div>
            <div class="tr-info">
              <div class="tr-subject">{{ t.subject }}</div>
              <div class="tr-meta">
                <span class="tr-id">#{{ t.name }}</span> · {{ t.customer_name }} · {{ t.days_open }}d open
              </div>
              <div class="tr-quality-row">
                <QualityBadge :badge="t.quality_badge" />
              </div>
            </div>
            <div class="tr-badges">
              <StatusBadge :status="t.status" />
              <span v-if="t.sla_breached" class="lav-mini-chip" style="background:#FFF1F3;color:#E11D48">SLA breached</span>
              <span v-if="t.followup_overdue && !t.sla_breached" class="lav-mini-chip" style="background:#FFF1F3;color:#E11D48">Overdue</span>
              <span v-if="t.escalation_level && t.escalation_level !== 'L1'" class="lav-mini-chip" style="background:#FEF2F2;color:#B91C1C">{{ t.escalation_level }}</span>
            </div>
            <div class="tr-action">
              <span class="ms tr-ai">lightbulb</span>
              <div>
                <div class="tr-action-label">Recommended</div>
                <div class="tr-action-text">{{ t.next_action || 'Review ticket' }}</div>
              </div>
            </div>
            <button class="btn btn--teal" @click.stop="navigate('lavanya-ticket-detail', 'name=' + t.name)">
              Resolve <span class="ms">arrow_forward</span>
            </button>
          </div>
        </template>
        <div v-if="!visibleGroups.length" class="empty-state">
          <span class="ms">check_circle</span>
          <div>No tickets in this queue. Great work!</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import StatusBadge from '../components/StatusBadge.vue'
import QualityBadge from '../components/QualityBadge.vue'
import { useTodaysWork } from '../composables/useTickets.js'
import { navigate, currentUserName } from '../composables/frappe.js'

const props = defineProps({ frappePage: Object })
const { buckets, loading, error, refresh } = useTodaysWork()

const staffName = computed(() => currentUserName().split(' ')[0])
const todayLabel = new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' })
const activeFilter = ref('all')

const counts = computed(() => buckets.value.counts || {})

const all = computed(() => [...(buckets.value.critical||[]), ...(buckets.value.important||[]), ...(buckets.value.normal||[])])

const chipCount = computed(() => {
  const c = buckets.value.critical || [], i = buckets.value.important || [], n = buckets.value.normal || []
  return {
    critOverdue: c.filter(t => t.followup_overdue).length,
    critEscalated: c.filter(t => ['L3','L4'].includes(t.escalation_level)).length,
    impNotInformed: i.filter(t => !t.customer_informed).length,
    impDueToday: i.filter(t => t.bucket_label === 'Due Today').length,
    normNew: n.filter(t => t.status === 'New').length,
    normSatisfaction: n.filter(t => t.status === 'Customer Confirmation Pending').length,
  }
})

const statStrip = computed(() => {
  const a = all.value
  return {
    readyPickup: a.filter(t => t.status === 'Resolved by Brand').length,
    waitingPart: a.filter(t => t.part_pending).length,
    waitCustomer: a.filter(t => t.status === 'Waiting').length,
    missingReceipt: a.filter(t => !t.invoice_number).length,
    closurePending: a.filter(t => t.status === 'Customer Confirmation Pending').length,
  }
})

const GROUPS = [
  { key: 'overdue',      label: 'Overdue follow-up',     type: 'red',   color: '#E11D48', bucket: 'critical',  match: t => t.followup_overdue },
  { key: 'escalated',    label: 'Escalated',             type: 'red',   color: '#E11D48', bucket: 'critical',  match: t => ['L3','L4'].includes(t.escalation_level) && !t.followup_overdue },
  { key: 'not_informed', label: 'Customer not informed',type: 'amber', color: '#D97706', bucket: 'critical',  match: t => !t.customer_informed && !t.followup_overdue && !['L3','L4'].includes(t.escalation_level) },
  { key: 'due_today',    label: 'Due today',             type: 'blue',  color: '#4F46E5', bucket: 'important', match: t => t.bucket_label === 'Due Today' },
  { key: 'tech_pend',    label: 'Tech call/visit pending',type: 'blue', color: '#4F46E5', bucket: 'important', match: t => !t.technician_called || !t.technician_visited },
]

const qFilters = computed(() => [
  { key: 'all',       label: 'All',       color: '#9A9A93', count: (buckets.value.critical?.length||0)+(buckets.value.important?.length||0) },
  { key: 'overdue',   label: 'Overdue',   color: '#E11D48', count: (buckets.value.critical||[]).filter(t=>t.followup_overdue).length },
  { key: 'escalated', label: 'Escalated', color: '#D97706', count: (buckets.value.critical||[]).filter(t=>['L3','L4'].includes(t.escalation_level)).length },
])

const visibleGroups = computed(() => {
  const pool = [...(buckets.value.critical||[]), ...(buckets.value.important||[])]
  return GROUPS.map(g => ({
    ...g,
    tickets: pool.filter(t => {
      if (activeFilter.value !== 'all') {
        if (activeFilter.value === 'overdue'   && !t.followup_overdue) return false
        if (activeFilter.value === 'escalated' && !['L3','L4'].includes(t.escalation_level)) return false
      }
      return g.match(t)
    })
  })).filter(g => g.tickets.length)
})

const COLORS = [['#EEF2FF','#4F46E5'],['#EDE9FE','#7C3AED'],['#DCFCE7','#059669'],['#FFF1F3','#E11D48'],['#CCFBF1','#0D9488'],['#FFF7ED','#D97706']]
function avatarStyle(t) {
  const idx = (t.customer_name?.charCodeAt(0) || 0) % COLORS.length
  return { background: COLORS[idx][0], color: COLORS[idx][1] }
}
function initials(name) { return (name||'?').split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase() }

defineExpose({ refresh })
</script>

<style scoped>
.page{padding:26px 30px;max-width:1400px}
.page-header{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:22px}
.page-title{font-size:23px;font-weight:800;color:#1C1C1E;letter-spacing:-0.02em;margin:0}
.page-sub{font-size:13.5px;color:#8B8B85;margin:3px 0 0}.highlight{color:#E11D48;font-weight:700}.text--teal{color:#0D9488;font-weight:700}

.lanes{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:14px}
.lane{background:#fff;border:1px solid #ECECE8;border-radius:16px;padding:20px;box-shadow:0 1px 2px rgba(17,17,26,0.04)}
.lane-head{display:flex;align-items:center;gap:10px;margin-bottom:16px}
.lane-icon{width:38px;height:38px;border-radius:11px;background:#FFF1F3;display:flex;align-items:center;justify-content:center;flex:none}
.lane-icon .ms{color:#E11D48;font-size:21px;font-variation-settings:'FILL' 1}
.lane-icon--amber{background:#FFF7ED}.lane-icon--amber .ms{color:#D97706}
.lane-icon--teal{background:#F0FDFA}.lane-icon--teal .ms{color:#0D9488}
.lane-title{font-size:13px;font-weight:800;color:#1C1C1E}.lane-sub{font-size:11px;color:#A1A19B}
.lane-count{font-family:'JetBrains Mono',monospace;font-size:30px;font-weight:700;margin-left:auto;letter-spacing:-0.03em}
.lc--red{color:#E11D48}.lc--amber{color:#D97706}.lc--teal{color:#0D9488}
.lane-chips{display:flex;gap:7px}
.chip{flex:1;border-radius:10px;padding:9px 11px;font-size:10.5px;font-weight:600}
.chip--red{background:#FFF1F3;color:#9F1239}.chip--amber{background:#FFF7ED;color:#9A3412}.chip--teal{background:#F0FDFA;color:#115E59}
.chip-n{font-family:'JetBrains Mono',monospace;font-size:17px;font-weight:700;display:block;margin-bottom:2px}
.chip--red .chip-n{color:#E11D48}.chip--amber .chip-n{color:#D97706}.chip--teal .chip-n{color:#0D9488}

.stat-strip{background:#fff;border:1px solid #ECECE8;border-radius:14px;padding:4px;display:flex;align-items:stretch;margin-bottom:24px;box-shadow:0 1px 2px rgba(17,17,26,0.04)}
.ss-cell{flex:1;padding:11px 16px;display:flex;align-items:center;gap:11px}
.ss-icon{width:30px;height:30px;border-radius:8px;display:flex;align-items:center;justify-content:center;flex:none}
.ss-icon .ms{font-size:17px}
.ss-icon--green{background:#ECFDF5}.ss-icon--green .ms{color:#059669}
.ss-icon--amber{background:#FFF7ED}.ss-icon--amber .ms{color:#D97706}
.ss-icon--indigo{background:#EEF2FF}.ss-icon--indigo .ms{color:#4F46E5}
.ss-icon--violet{background:#F5F3FF}.ss-icon--violet .ms{color:#7C3AED}
.ss-icon--gray{background:#F4F4F1}.ss-icon--gray .ms{color:#71717A}
.ss-val{font-family:'JetBrains Mono',monospace;font-size:15px;font-weight:700;color:#1C1C1E}
.ss-lbl{font-size:10.5px;color:#8B8B85;font-weight:600}
.ss-div{width:1px;background:#F0F0EC;margin:8px 0}

.section-header{display:flex;align-items:center;justify-content:space-between;margin:22px 0 12px;flex-wrap:wrap;gap:10px}
.sh-left{display:flex;align-items:center;gap:10px}
.section-title{font-size:17px;font-weight:800;color:#1C1C1E;letter-spacing:-0.01em}
.sh-pill{font-size:12px;font-weight:600;color:#8B8B85;background:#fff;border:1px solid #ECECE8;padding:3px 10px;border-radius:20px}
.filters{display:flex;gap:7px;flex-wrap:wrap}
.filter-chip{display:inline-flex;align-items:center;gap:5px;padding:6px 12px;border-radius:9px;background:#fff;border:1px solid #ECECE8;font-size:12px;font-weight:600;color:#6B6B66;cursor:pointer}
.filter-chip--active{background:#1C1C1E;color:#fff;border-color:#1C1C1E}
.filter-dot{width:7px;height:7px;border-radius:50%;flex:none}
.filter-count{font-size:10.5px;opacity:.7}

.ticket-table{background:#fff;border:1px solid #ECECE8;border-radius:16px;overflow:hidden;box-shadow:0 1px 2px rgba(17,17,26,0.04)}
.group-header{padding:11px 20px;display:flex;align-items:center;gap:9px;border-bottom:1px solid #F4F4F1}
.group--red{background:#FFF8F8;border-bottom-color:#FCE7EA}
.group--amber{background:#FFFBF4;border-bottom-color:#FCEFD6}
.group--blue{background:#F5F6FF;border-bottom-color:#DDE1FC}
.group-dot{width:7px;height:7px;border-radius:50%;flex:none}
.group-label{font-size:12px;font-weight:800}
.group--red .group-label{color:#9F1239}.group--amber .group-label{color:#9A3412}.group--blue .group-label{color:#3730A3}
.group-badge{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:700;padding:1px 8px;border-radius:6px}
.group--red .group-badge{background:#FFF1F3;color:#E11D48}
.group--amber .group-badge{background:#FFF7ED;color:#D97706}
.group--blue .group-badge{background:#EEF2FF;color:#4F46E5}

.ticket-row{display:grid;grid-template-columns:42px 1fr 200px 250px 130px;align-items:center;padding:15px 20px;gap:12px;border-bottom:1px solid #F4F4F1;cursor:pointer;transition:background .15s}
.ticket-row:hover{background:#FAFAF8}
.tr-avatar{width:34px;height:34px;border-radius:10px;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}
.tr-info{min-width:0;padding-right:10px}
.tr-subject{font-size:13.5px;font-weight:700;color:#1C1C1E;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tr-meta{font-size:11.5px;color:#9A9A93;margin-top:2px}
.tr-id{font-family:'JetBrains Mono',monospace;color:#0F766E;font-weight:600}
.tr-quality-row{margin-top:6px}
.tr-badges{display:flex;flex-wrap:wrap;gap:4px}
.tr-action{display:flex;align-items:center;gap:8px;background:#FAFAF8;border:1px solid #F0F0EC;border-radius:10px;padding:8px 11px;min-width:0}
.tr-ai{font-size:17px;color:#0D9488;font-variation-settings:'FILL' 1;flex:none}
.tr-action-label{font-size:9.5px;font-weight:700;color:#A1A19B;text-transform:uppercase;letter-spacing:.04em}
.tr-action-text{font-size:12px;font-weight:700;color:#1C1C1E;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

.empty-state{padding:48px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:10px;color:#A1A19B}
.empty-state .ms{font-size:36px;color:#0D9488;font-variation-settings:'FILL' 1}
.loading-state,.error-state{padding:48px;text-align:center;display:flex;align-items:center;justify-content:center;gap:10px;color:#9A9A93;font-weight:600}

.btn{display:inline-flex;align-items:center;gap:6px;padding:8px 14px;border-radius:9px;font-size:12.5px;font-weight:700;border:none;cursor:pointer;font-family:inherit}
.btn--dark{background:#1C1C1E;color:#fff}
.btn--teal{background:#0D9488;color:#fff;box-shadow:0 2px 8px -2px rgba(13,148,136,.5)}
.btn--outline{background:#fff;border:1px solid #ECECE8;color:#52525B}
@keyframes spin{to{transform:rotate(360deg)}}.spin{display:inline-block;animation:spin 1s linear infinite}
.ms{font-family:'Material Symbols Rounded';font-weight:normal;font-style:normal;line-height:1;font-size:18px}
</style>
