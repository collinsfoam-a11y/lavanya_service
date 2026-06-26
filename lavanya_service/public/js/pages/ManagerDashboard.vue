<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Manager Dashboard</h1>
        <p class="page-sub">{{ todayLabel }} · Real-time service quality</p>
      </div>
      <div class="header-actions">
        <select v-model="period" class="select-ctrl" @change="fetch">
          <option>Today</option><option>This Week</option><option>This Month</option>
        </select>
        <button class="btn btn--outline" @click="fetch"><span class="ms">refresh</span></button>
        <button class="btn btn--dark" @click="exportReport"><span class="ms">download</span> Export</button>
      </div>
    </div>

    <div v-if="loading" class="loading-state"><span class="ms spin">sync</span> Loading dashboard…</div>
    <div v-else-if="error" class="error-state"><span class="ms">error</span> {{ error }} <button class="btn btn--outline" @click="fetch">Retry</button></div>

    <template v-else-if="data">
      <!-- KPI strip -->
      <div class="kpi-strip">
        <div class="kpi-card kpi--neutral">
          <div class="ki ki--gray"><span class="ms">confirmation_number</span></div>
          <div><div class="kv mono">{{ data.kpis.open_tickets }}</div><div class="kl">Open Tickets</div></div>
        </div>
        <div class="kpi-card kpi--red">
          <div class="ki ki--red"><span class="ms">schedule</span></div>
          <div><div class="kv mono text--red">{{ data.kpis.overdue_followups }}</div><div class="kl">Overdue Follow-ups</div></div>
        </div>
        <div class="kpi-card kpi--amber">
          <div class="ki ki--amber"><span class="ms">notifications_off</span></div>
          <div><div class="kv mono text--amber">{{ data.kpis.customer_not_informed }}</div><div class="kl">Not Informed</div></div>
        </div>
        <div class="kpi-card kpi--teal">
          <div class="ki ki--teal"><span class="ms">task_alt</span></div>
          <div><div class="kv mono text--teal">{{ data.kpis.closed_today }}</div><div class="kl">Closed Today</div></div>
        </div>
        <div class="kpi-card kpi--teal">
          <div class="ki ki--teal"><span class="ms">sentiment_satisfied</span></div>
          <div><div class="kv mono text--teal">{{ data.kpis.satisfaction_rate }}%</div><div class="kl">CSAT</div></div>
        </div>
        <div class="kpi-card kpi--red">
          <div class="ki ki--red"><span class="ms">priority_high</span></div>
          <div><div class="kv mono text--red">{{ data.kpis.escalated }}</div><div class="kl">Escalated</div></div>
        </div>
      </div>

      <div class="dash-grid">
        <!-- Escalation aging -->
        <div class="card card--wide">
          <div class="card-title"><span class="ms">priority_high</span> Escalation Aging</div>
          <div class="data-table">
            <div class="dt-header">
              <span>Ticket</span><span>Customer</span><span>Product</span>
              <span>Level</span><span>Days</span><span>Quality</span><span></span>
            </div>
            <div v-for="t in data.escalations" :key="t.name" class="dt-row"
              @click="navigate('lavanya-ticket-detail','name='+t.name)">
              <span class="mono text--teal">#{{ t.name }}</span>
              <span>{{ t.customer_name }}</span>
              <span class="text-muted">{{ t.product_model }}</span>
              <span><span class="badge badge--dark">{{ t.escalation_level }}</span></span>
              <span class="mono" :class="(t.days_open||0)>5?'text--red':'text--amber'">{{ t.days_open }}d</span>
              <span><QualityBadge :badge="t.quality_badge" /></span>
              <span><button class="btn btn--teal btn--sm">Open</button></span>
            </div>
            <div v-if="!data.escalations?.length" class="dt-empty">No escalated tickets 🎉</div>
          </div>
        </div>

        <!-- Brand delay -->
        <div class="card">
          <div class="card-title"><span class="ms">business</span> Brand Delay Scorecard</div>
          <div class="brand-scores">
            <div v-for="b in data.brand_scores" :key="b.name" class="bs-row">
              <div class="bs-name">{{ b.name }}</div>
              <div class="bs-bar-wrap">
                <div class="bs-bar" :style="{ width: Math.min(100, (b.open/Math.max(...data.brand_scores.map(x=>x.open),1))*100)+'%',
                  background: b.overdue > 5 ? '#E11D48' : b.overdue > 2 ? '#D97706' : '#0D9488' }"></div>
              </div>
              <div class="bs-meta">
                <span>{{ b.open }} open</span>
                <span v-if="b.overdue" class="text--red">{{ b.overdue }} overdue</span>
              </div>
            </div>
            <div v-if="!data.brand_scores?.length" class="dt-empty">No brand data</div>
          </div>
        </div>

        <!-- Staff performance -->
        <div class="card">
          <div class="card-title"><span class="ms">groups</span> Staff Performance</div>
          <div class="staff-list">
            <div v-for="s in data.staff_perf" :key="s.name" class="staff-row">
              <div class="sa">{{ initials(s.name) }}</div>
              <div class="si-info">
                <div class="si-name">{{ s.name }}</div>
                <div class="si-meta">{{ s.logs }} follow-ups</div>
              </div>
              <div class="sm-metrics">
                <div class="sm-item">
                  <div class="sm-n" :class="s.compliance>=90?'text--teal':s.compliance>=70?'text--amber':'text--red'">{{ s.compliance }}%</div>
                  <div class="sm-l">Compliance</div>
                </div>
                <div class="sm-item">
                  <div class="sm-n text--red">{{ s.overdue }}</div>
                  <div class="sm-l">Overdue</div>
                </div>
              </div>
            </div>
            <div v-if="!data.staff_perf?.length" class="dt-empty">No staff data</div>
          </div>
        </div>

        <!-- Part pending -->
        <div class="card">
          <div class="card-title"><span class="ms">build</span> Part Pending Aging</div>
          <div class="part-list">
            <div v-for="p in data.part_pending" :key="p.name" class="part-row">
              <div class="pa-age" :class="(p.days_open||0)>14?'pa--crit':(p.days_open||0)>7?'pa--risk':'pa--ok'">
                {{ p.days_open }}d
              </div>
              <div class="pa-info">
                <div class="pa-name">{{ p.part_name || 'Part pending' }}</div>
                <div class="pa-meta">#{{ p.name }} · {{ p.customer_name }}</div>
              </div>
              <span class="badge" :class="p.part_received ? 'badge--teal':'badge--amber'">
                {{ p.part_received ? 'Received' : 'Pending' }}
              </span>
            </div>
            <div v-if="!data.part_pending?.length" class="dt-empty">No parts pending</div>
          </div>
        </div>

        <!-- Safety locks -->
        <div class="card">
          <div class="card-title"><span class="ms">shield</span> Safety Locks</div>
          <div class="lock-list">
            <div v-for="(val, key) in data.safety_locks" :key="key" class="lock-row">
              <div class="lock-dot" :class="isLockSafe(key,val) ? 'ld--safe' : 'ld--risk'"></div>
              <div class="lock-name">{{ lockLabel(key) }}</div>
              <span class="lock-badge" :class="val ? 'lb--on':'lb--off'">
                {{ typeof val === 'string' ? val.toUpperCase() : (val ? 'ON' : 'OFF') }}
              </span>
            </div>
          </div>
          <button class="btn btn--outline full mt-10" @click="navigate('lavanya-settings')">
            <span class="ms">settings</span> Manage Settings
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import QualityBadge from '../components/QualityBadge.vue'
import { useManagerDashboard } from '../composables/useDashboard.js'
import { navigate } from '../composables/frappe.js'
import { frappeCall } from '../composables/frappe.js'

const props = defineProps({ frappePage: Object })
const { data, loading, error, period, setPeriod, refresh: fetch } = useManagerDashboard()

const todayLabel = new Date().toLocaleDateString('en-IN',{weekday:'long',day:'numeric',month:'long'})

const LOCK_LABELS = { closure_guard:'Closure Guard', customer_confirm:'Customer Confirmation', live_whatsapp:'Live WhatsApp', erp_posting:'ERP Posting', penalty:'Penalty Apply', whatsapp_bot_mode:'Bot Mode' }
const SAFE_WHEN_ON  = new Set(['closure_guard','customer_confirm'])
const SAFE_WHEN_OFF = new Set(['live_whatsapp','erp_posting','penalty','auto_closure'])

function lockLabel(k) { return LOCK_LABELS[k] || k.replace(/_/g,' ') }
function isLockSafe(k, v) {
  if (SAFE_WHEN_ON.has(k))  return !!v
  if (SAFE_WHEN_OFF.has(k)) return !v
  return true
}
function initials(n) { return (n||'?').split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase() }

async function exportReport() {
  const url = await frappeCall('lavanya_service.api.dashboard.export_report')
  if (url) window.open(url)
}

defineExpose({ setPeriod, refresh: fetch })
</script>

<style scoped>
.page{padding:28px 32px;max-width:1600px}.page-header{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:22px}.page-title{font-size:24px;font-weight:800;color:#1C1C1E;letter-spacing:-0.02em;margin:0}.page-sub{font-size:13px;color:#8B8B85;margin:4px 0 0}.header-actions{display:flex;gap:8px;align-items:center}
.kpi-strip{display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:18px}.kpi-card{background:#fff;border:1px solid #ECECE8;border-radius:14px;padding:16px;display:flex;align-items:center;gap:12px}.ki{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;flex:none}.ki--gray{background:#F4F4F1}.ki--gray .ms{color:#6B6B66;font-variation-settings:'FILL' 1}.ki--red{background:#FFF1F3}.ki--red .ms{color:#E11D48;font-variation-settings:'FILL' 1}.ki--amber{background:#FFF7ED}.ki--amber .ms{color:#D97706;font-variation-settings:'FILL' 1}.ki--teal{background:#F0FDFA}.ki--teal .ms{color:#0D9488;font-variation-settings:'FILL' 1}.kv{font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:700;color:#1C1C1E}.kl{font-size:10px;font-weight:700;color:#8B8B85;margin-top:2px}
.dash-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}.card{background:#fff;border:1px solid #ECECE8;border-radius:16px;padding:20px}.card--wide{grid-column:1/-1}.card-title{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:800;color:#1C1C1E;margin-bottom:16px}.card-title .ms{font-size:17px;color:#0D9488;font-variation-settings:'FILL' 1}
.data-table{display:flex;flex-direction:column}.dt-header{display:grid;grid-template-columns:80px 120px 1fr 70px 60px 120px 70px;gap:8px;padding:8px 12px;background:#F4F4F1;border-radius:9px;font-size:10.5px;font-weight:700;color:#9A9A93;text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px}.dt-row{display:grid;grid-template-columns:80px 120px 1fr 70px 60px 120px 70px;gap:8px;padding:11px 12px;border-bottom:1px solid #F4F4F1;align-items:center;cursor:pointer;font-size:13px;transition:background .1s}.dt-row:hover{background:#FAFAF8}.dt-row:last-child{border-bottom:none}.dt-empty{padding:24px;text-align:center;color:#A1A19B;font-size:13px}
.brand-scores{display:flex;flex-direction:column;gap:12px}.bs-row{display:flex;align-items:center;gap:12px}.bs-name{font-size:12.5px;font-weight:700;color:#1C1C1E;width:80px;flex:none}.bs-bar-wrap{flex:1;height:8px;background:#F0F0EC;border-radius:4px;overflow:hidden}.bs-bar{height:100%;border-radius:4px;transition:width .4s}.bs-meta{display:flex;flex-direction:column;gap:2px;min-width:80px;text-align:right;font-size:11px;color:#8B8B85}
.staff-list{display:flex;flex-direction:column;gap:10px}.staff-row{display:flex;align-items:center;gap:12px;padding:10px 12px;border-radius:11px;background:#FAFAF8}.sa{width:36px;height:36px;border-radius:50%;background:linear-gradient(140deg,#0D9488,#15B8A6);color:#fff;font-size:12px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}.si-name{font-size:13px;font-weight:700;color:#1C1C1E}.si-meta{font-size:11px;color:#8B8B85}.sm-metrics{margin-left:auto;display:flex;gap:20px}.sm-item{text-align:center}.sm-n{font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:700;color:#1C1C1E}.sm-l{font-size:9.5px;color:#A1A19B;font-weight:600;margin-top:1px}
.part-list{display:flex;flex-direction:column;gap:9px}.part-row{display:flex;align-items:center;gap:12px;padding:10px;border-radius:11px;background:#FAFAF8;border:1px solid #F0F0EC}.pa-age{font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:700;width:38px;text-align:center}.pa--crit{color:#E11D48}.pa--risk{color:#D97706}.pa--ok{color:#0D9488}.pa-name{font-size:13px;font-weight:700;color:#1C1C1E}.pa-meta{font-size:11px;color:#8B8B85}
.lock-list{display:flex;flex-direction:column;gap:8px}.lock-row{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:10px;background:#FAFAF8;font-size:12.5px}.lock-dot{width:8px;height:8px;border-radius:50%;flex:none}.ld--safe{background:#0D9488}.ld--risk{background:#E11D48}.lock-name{flex:1;color:#3F3F46;font-weight:600}.lock-badge{font-size:10.5px;font-weight:700;padding:2px 8px;border-radius:6px}.lb--on{background:#F0FDFA;color:#0D9488}.lb--off{background:#F4F4F1;color:#9A9A93}
.badge{padding:3px 9px;border-radius:7px;font-size:10.5px;font-weight:700}.badge--teal{background:#F0FDFA;color:#0D9488}.badge--amber{background:#FFF7ED;color:#D97706}.badge--dark{background:#FEF2F2;color:#B91C1C}
.mono{font-family:'JetBrains Mono',monospace}.text--teal{color:#0D9488;font-weight:700}.text--red{color:#E11D48;font-weight:700}.text--amber{color:#D97706;font-weight:700}.text-muted{color:#9A9A93}.full{width:100%;justify-content:center}.mt-10{margin-top:10px}
.select-ctrl{height:40px;padding:0 14px;border-radius:11px;border:1px solid #ECECE8;font-size:13px;font-family:inherit;background:#fff}
.loading-state,.error-state{padding:60px;text-align:center;display:flex;align-items:center;justify-content:center;gap:10px;color:#9A9A93;font-weight:600}
.btn{display:inline-flex;align-items:center;gap:6px;padding:9px 16px;border-radius:10px;font-size:13px;font-weight:700;border:none;cursor:pointer}.btn--dark{background:#1C1C1E;color:#fff}.btn--teal{background:#0D9488;color:#fff}.btn--outline{background:#fff;border:1px solid #ECECE8;color:#52525B}.btn--sm{padding:6px 12px;font-size:12px}
@keyframes spin{to{transform:rotate(360deg)}}.spin{display:inline-block;animation:spin 1s linear infinite}
.ms{font-family:'Material Symbols Rounded';font-weight:normal;font-style:normal;line-height:1;font-size:18px}
</style>
