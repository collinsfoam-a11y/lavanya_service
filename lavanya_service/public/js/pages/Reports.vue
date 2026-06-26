<template>
  <div class="page">
    <div class="page-header">
      <div><h1 class="page-title">Reports</h1><p class="page-sub">Service quality analytics · {{ period }}</p></div>
      <div class="header-actions">
        <select v-model="activeReport" class="select-ctrl" @change="fetch">
          <optgroup label="Service Reports">
            <option v-for="r in serviceReports" :key="r.key" :value="r.key">{{ r.label }}</option>
          </optgroup>
          <optgroup label="CRM">
            <option v-for="r in crmReports" :key="r.key" :value="r.key">{{ r.label }}</option>
          </optgroup>
        </select>
        <select v-model="period" class="select-ctrl" @change="fetch">
          <option>Today</option><option>This Week</option><option selected>This Month</option><option>Last 3 Months</option>
        </select>
        <button class="btn btn--outline" @click="fetch" :disabled="loading"><span class="ms">refresh</span></button>
        <button class="btn btn--dark" @click="exportCSV"><span class="ms">download</span> Export</button>
      </div>
    </div>

    <!-- KPI strip -->
    <div class="kpi-strip">
      <div class="kpi-card kpi--neutral"><div class="ki ki--gray"><span class="ms">table_rows</span></div><div><div class="kv mono">{{ rows.length }}</div><div class="kl">Total Records</div></div></div>
      <div class="kpi-card kpi--red"><div class="ki ki--red"><span class="ms">error</span></div><div><div class="kv mono text--red">{{ rows.filter(r=>r.quality_badge==='Critical').length }}</div><div class="kl">Critical</div></div></div>
      <div class="kpi-card kpi--amber"><div class="ki ki--amber"><span class="ms">warning</span></div><div><div class="kv mono text--amber">{{ rows.filter(r=>r.quality_badge==='At Risk').length }}</div><div class="kl">At Risk</div></div></div>
      <div class="kpi-card kpi--teal"><div class="ki ki--teal"><span class="ms">check_circle</span></div><div><div class="kv mono text--teal">{{ rows.filter(r=>r.quality_badge==='Good').length }}</div><div class="kl">Good</div></div></div>
    </div>

    <!-- Bar chart -->
    <div class="chart-card" v-if="chartData.length && !loading">
      <div class="chart-title">{{ currentReport.label }}</div>
      <svg :viewBox="'0 0 '+cW+' '+cH" :width="cW" :height="cH">
        <g v-for="(bar,i) in chartData" :key="i">
          <rect :x="bX(i)" :y="cH-bar.h-40" :width="bW-8" :height="bar.h" :fill="bar.color" rx="5"/>
          <text :x="bX(i)+(bW-8)/2" :y="cH-20" text-anchor="middle" font-size="11" fill="#9A9A93">{{ bar.label }}</text>
          <text :x="bX(i)+(bW-8)/2" :y="cH-bar.h-46" text-anchor="middle" font-size="12" font-weight="700" fill="#1C1C1E">{{ bar.value }}</text>
        </g>
      </svg>
    </div>

    <!-- Table -->
    <div class="table-card">
      <div v-if="loading" class="loading-state"><span class="ms spin">sync</span> Loading report…</div>
      <template v-else>
        <div class="table-header">
          <span v-for="col in currentReport.columns" :key="col.key" class="th">{{ col.label }}</span>
        </div>
        <div v-for="row in rows" :key="row.name || row.brand"
          class="table-row" :class="{ 'tr--link': !!row.name }"
          @click="row.name && navigate('lavanya-ticket-detail','name='+row.name)">
          <span v-for="col in currentReport.columns" :key="col.key" class="td" :class="col.cls">
            <QualityBadge v-if="col.key==='quality_badge'" :badge="row[col.key]" />
            <span v-else-if="col.key==='status'" class="s-pill">{{ row[col.key] }}</span>
            <span v-else>{{ row[col.key] || '—' }}</span>
          </span>
        </div>
        <div v-if="!rows.length" class="empty-state"><span class="ms">assessment</span><div>No data for selected period</div></div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import QualityBadge from '../components/QualityBadge.vue'
import { useReports } from '../composables/useDashboard.js'
import { navigate } from '../composables/frappe.js'

const props = defineProps({ frappePage: Object })
const { rows, loading, report: activeReport, period, setReport, setPeriod, refresh: fetch } = useReports()

const serviceReports = [
  { key:'overdue_followups', label:'Overdue Follow-ups' },
  { key:'open_by_stage',     label:'Open Tickets by Stage' },
  { key:'brand_delay',       label:'Brand-wise Delay' },
  { key:'not_informed',      label:'Customer Not Informed' },
  { key:'part_aging',        label:'Part Pending Aging' },
  { key:'satisfaction',      label:'Satisfaction Summary' },
  { key:'repeat_complaints', label:'Repeat Complaints' },
]
const crmReports = [
  { key:'crm_opportunities', label:'Service-to-CRM Opportunities' },
]

const REPORT_DEFS = {
  overdue_followups: { label:'Overdue Follow-ups', columns:[
    {key:'name',label:'Ticket',cls:'mono text--teal'},{key:'customer_name',label:'Customer'},{key:'brand',label:'Brand'},{key:'days_open',label:'Days',cls:'mono'},{key:'escalation_level',label:'Level'},{key:'quality_badge',label:'Quality'},{key:'next_action',label:'Next Action'},
  ]},
  open_by_stage: { label:'Open by Stage', columns:[
    {key:'name',label:'Ticket',cls:'mono text--teal'},{key:'customer_name',label:'Customer'},{key:'status',label:'Status'},{key:'follow_up_stage',label:'Stage'},{key:'brand',label:'Brand'},{key:'days_open',label:'Days',cls:'mono'},{key:'quality_badge',label:'Quality'},
  ]},
  brand_delay: { label:'Brand Delay', columns:[
    {key:'brand',label:'Brand'},{key:'open_tickets',label:'Open',cls:'mono'},{key:'sla_breached',label:'SLA Breached',cls:'mono text--red'},
  ]},
  not_informed: { label:'Customer Not Informed', columns:[
    {key:'name',label:'Ticket',cls:'mono text--teal'},{key:'customer_name',label:'Customer'},{key:'brand',label:'Brand'},{key:'days_open',label:'Days',cls:'mono'},{key:'follow_up_stage',label:'Stage'},
  ]},
  satisfaction: { label:'Satisfaction', columns:[
    {key:'name',label:'Ticket',cls:'mono text--teal'},{key:'customer_name',label:'Customer'},{key:'brand',label:'Brand'},{key:'customer_satisfaction',label:'CSAT'},{key:'days_open',label:'Days',cls:'mono'},
  ]},
  crm_opportunities: { label:'CRM Opportunities', columns:[
    {key:'name',label:'Ticket',cls:'mono text--teal'},{key:'customer_name',label:'Customer'},{key:'brand',label:'Brand'},{key:'days_open',label:'Days',cls:'mono'},{key:'escalation_level',label:'Level'},
  ]},
}
const currentReport = computed(() => REPORT_DEFS[activeReport.value] || REPORT_DEFS.overdue_followups)

const cW = 700, cH = 220
const bW = computed(() => Math.max(20, Math.floor(cW / Math.max(rows.value.length, 1))))
const COLORS = ['#0D9488','#4F46E5','#D97706','#E11D48','#7C3AED','#059669']
const chartData = computed(() => {
  const numKey = currentReport.value.columns.find(c => c.cls?.includes('mono') && c.key !== 'name')?.key || 'days_open'
  const maxV = Math.max(...rows.value.map(r => Number(r[numKey])||0), 1)
  return rows.value.slice(0,12).map((r,i) => ({
    label: (r.brand || r.customer_name || r.name || '').slice(0,8),
    value: Number(r[numKey])||0,
    h: Math.max(6, Math.floor((Number(r[numKey])||0)/maxV*140)),
    color: COLORS[i%COLORS.length],
  }))
})
function bX(i) { return i * bW.value + 20 }

function exportCSV() {
  const cols = currentReport.value.columns
  const header = cols.map(c=>c.label).join(',')
  const body = rows.value.map(r=>cols.map(c=>JSON.stringify(r[c.key]||'')).join(',')).join('\n')
  const blob = new Blob([header+'\n'+body],{type:'text/csv'})
  const a = document.createElement('a'); a.href=URL.createObjectURL(blob)
  a.download = activeReport.value+'_'+period.value.replace(/s/g,'_')+'.csv'; a.click()
}

defineExpose({ setReport, setPeriod, exportCSV, refresh: fetch })
</script>

<style scoped>
.page{padding:28px 32px;max-width:1400px}.page-header{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:22px;flex-wrap:wrap;gap:12px}.page-title{font-size:24px;font-weight:800;color:#1C1C1E;letter-spacing:-0.02em;margin:0}.page-sub{font-size:13px;color:#8B8B85;margin:4px 0 0}.header-actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.select-ctrl{height:40px;padding:0 14px;border-radius:11px;border:1px solid #ECECE8;font-size:13px;font-family:inherit;background:#fff}
.kpi-strip{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px}.kpi-card{background:#fff;border:1px solid #ECECE8;border-radius:14px;padding:16px;display:flex;align-items:center;gap:12px}.ki{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;flex:none}.ki--gray{background:#F4F4F1}.ki--gray .ms{color:#6B6B66;font-variation-settings:'FILL' 1}.ki--red{background:#FFF1F3}.ki--red .ms{color:#E11D48;font-variation-settings:'FILL' 1}.ki--amber{background:#FFF7ED}.ki--amber .ms{color:#D97706;font-variation-settings:'FILL' 1}.ki--teal{background:#F0FDFA}.ki--teal .ms{color:#0D9488;font-variation-settings:'FILL' 1}.kv{font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:700;color:#1C1C1E}.kl{font-size:10px;font-weight:700;color:#8B8B85;margin-top:2px}
.chart-card{background:#fff;border:1px solid #ECECE8;border-radius:16px;padding:20px;margin-bottom:14px;overflow-x:auto}.chart-title{font-size:15px;font-weight:800;color:#1C1C1E;margin-bottom:16px}
.table-card{background:#fff;border:1px solid #ECECE8;border-radius:16px;overflow:hidden}.table-header{display:flex;gap:0;padding:10px 18px;background:#F4F4F1}.th{flex:1;font-size:10.5px;font-weight:700;color:#9A9A93;text-transform:uppercase;letter-spacing:.04em}.table-row{display:flex;gap:0;padding:13px 18px;border-bottom:1px solid #F4F4F1;align-items:center;font-size:13px;transition:background .1s}.table-row:last-child{border-bottom:none}.tr--link{cursor:pointer}.tr--link:hover{background:#FAFAF8}.td{flex:1;color:#1C1C1E}.s-pill{padding:2px 8px;border-radius:6px;font-size:11px;font-weight:700;background:#F4F4F1;color:#52525B}
.empty-state{padding:48px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:8px;color:#A1A19B}.empty-state .ms{font-size:36px;color:#C4C4BD;font-variation-settings:'FILL' 1}
.loading-state{padding:48px;text-align:center;display:flex;align-items:center;justify-content:center;gap:10px;color:#9A9A93;font-weight:600}
.mono{font-family:'JetBrains Mono',monospace}.text--teal{color:#0D9488;font-weight:700}.text--red{color:#E11D48;font-weight:700}.text--amber{color:#D97706;font-weight:700}
.btn{display:inline-flex;align-items:center;gap:6px;padding:9px 16px;border-radius:10px;font-size:13px;font-weight:700;border:none;cursor:pointer}.btn--dark{background:#1C1C1E;color:#fff}.btn--outline{background:#fff;border:1px solid #ECECE8;color:#52525B}.btn:disabled{opacity:.5;cursor:not-allowed}
@keyframes spin{to{transform:rotate(360deg)}}.spin{display:inline-block;animation:spin 1s linear infinite}
.ms{font-family:'Material Symbols Rounded';font-weight:normal;font-style:normal;line-height:1;font-size:18px}
</style>
