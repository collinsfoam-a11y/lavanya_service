<!--
  Reports Center — ported from the Stitch "Reports Center" screen as a report
  *catalog*: each card opens a filtered ticket list (the drill-down). Catalog
  + rows come from lavanya_service.api.manager_reports (get_report_catalog /
  get_report), which reuse the same reports.manager_dashboard queries that feed
  the manager summary, so a card's count always matches the list it opens.
  Rows open the shared TicketDetail drawer.
-->
<template>
  <AppShell>
    <!-- Catalog view -->
    <template v-if="!active">
      <div class="mb-gutter">
        <h2 class="font-headline-lg text-headline-lg text-on-surface">Reports Center</h2>
        <p class="font-body-md text-on-surface-variant">Open a report to drill into its tickets</p>
      </div>

      <!-- Overview: trend + breakdowns (manager-only) -->
      <section v-if="overview.allowed" class="mb-6 flex flex-col gap-4">
        <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4">
          <div class="flex items-center justify-between mb-3">
            <h3 class="font-headline-md text-headline-md text-on-surface">Last {{ overview.days }} days</h3>
            <div class="flex items-center gap-4 font-label-md text-label-md text-on-surface-variant">
              <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full inline-block" style="background:#004ac6"></span> Created {{ overview.totals?.created ?? 0 }}</span>
              <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-full inline-block" style="background:#1a7f37"></span> Resolved {{ overview.totals?.resolved ?? 0 }}</span>
            </div>
          </div>
          <svg v-if="trend" :viewBox="`0 0 ${trend.W} ${trend.H}`" class="w-full" style="height: 130px" preserveAspectRatio="none">
            <path :d="trend.created" fill="none" stroke="#004ac6" stroke-width="2" vector-effect="non-scaling-stroke" />
            <path :d="trend.resolved" fill="none" stroke="#1a7f37" stroke-width="2" vector-effect="non-scaling-stroke" />
          </svg>
          <div v-if="trend" class="flex justify-between font-label-md text-label-md text-on-surface-variant mt-1">
            <span>{{ trend.first }}</span><span>{{ trend.last }}</span>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4">
            <h3 class="font-headline-md text-headline-md text-on-surface mb-3">By status</h3>
            <div v-for="b in overview.by_status" :key="b.label" class="flex items-center gap-2 mb-1.5">
              <span class="font-label-md text-label-md text-on-surface-variant w-36 truncate">{{ b.label }}</span>
              <div class="flex-1 h-3 bg-surface-container rounded-full overflow-hidden">
                <div class="h-full bg-primary rounded-full" :style="{ width: barPct(b.count, overview.by_status) }"></div>
              </div>
              <span class="font-label-md text-label-md w-7 text-right text-on-surface">{{ b.count }}</span>
            </div>
          </div>
          <div class="bg-surface-container-lowest border border-outline-variant rounded-xl p-4">
            <h3 class="font-headline-md text-headline-md text-on-surface mb-3">By closure type</h3>
            <div v-if="!overview.by_closure_type?.length" class="font-body-md text-on-surface-variant">No closed tickets yet.</div>
            <div v-for="b in overview.by_closure_type" :key="b.label" class="flex items-center gap-2 mb-1.5">
              <span class="font-label-md text-label-md text-on-surface-variant w-36 truncate" :title="b.label">{{ b.label }}</span>
              <div class="flex-1 h-3 bg-surface-container rounded-full overflow-hidden">
                <div class="h-full rounded-full" style="background:#1a7f37" :style="{ width: barPct(b.count, overview.by_closure_type) }"></div>
              </div>
              <span class="font-label-md text-label-md w-7 text-right text-on-surface">{{ b.count }}</span>
            </div>
          </div>
        </div>
      </section>

      <div v-if="loadingCatalog" class="text-on-surface-variant font-body-md py-12 text-center">
        Loading reports…
      </div>
      <div v-else-if="catalogError" class="text-error font-body-md py-12 text-center">
        Could not load reports. Check your access or contact the manager.
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <button
          v-for="r in catalog"
          :key="r.key"
          class="group text-left bg-surface-container-lowest border border-outline-variant rounded-xl p-4
                 transition hover:-translate-y-1 hover:border-primary hover:shadow-md flex flex-col gap-2"
          @click="openReport(r.key)"
        >
          <div class="flex items-start justify-between">
            <span class="material-symbols-outlined text-primary" style="font-size: 28px">{{ r.icon }}</span>
            <span
              class="min-w-[28px] h-7 px-2 inline-flex items-center justify-center rounded-full font-label-md text-label-md"
              :class="r.count ? 'bg-primary text-on-primary' : 'bg-surface-container-highest text-on-surface-variant'"
            >{{ r.count ?? '—' }}</span>
          </div>
          <div class="font-headline-md text-headline-md text-on-surface">{{ r.title }}</div>
          <div class="font-body-md text-on-surface-variant flex-1">{{ r.description }}</div>
          <div class="font-label-md text-label-md text-primary flex items-center gap-1 mt-1">
            Open report
            <span class="material-symbols-outlined transition-transform group-hover:translate-x-1" style="font-size: 16px">arrow_forward</span>
          </div>
        </button>
      </div>
    </template>

    <!-- Report drill-down view -->
    <template v-else>
      <button
        class="flex items-center gap-1 font-label-md text-body-md text-primary mb-3 hover:underline"
        @click="active = null"
      >
        <span class="material-symbols-outlined" style="font-size: 18px">arrow_back</span> Back to reports
      </button>

      <div class="mb-gutter flex items-center gap-3">
        <span class="material-symbols-outlined text-primary" style="font-size: 28px">{{ active.icon }}</span>
        <div class="flex-1">
          <h2 class="font-headline-lg text-headline-lg text-on-surface">
            {{ active.title }}
            <span class="font-body-md text-on-surface-variant">· {{ active.count }}</span>
          </h2>
          <p class="font-body-md text-on-surface-variant">{{ active.description }}</p>
        </div>
        <button
          v-if="active.count > 0"
          @click="exportCsv"
          class="flex items-center gap-1.5 px-4 h-9 rounded-lg border border-outline-variant text-primary font-label-md text-body-md hover:bg-surface-container-low"
        >
          <span class="material-symbols-outlined" style="font-size: 18px">download</span> Export CSV
        </button>
      </div>

      <div v-if="loadingReport" class="text-on-surface-variant font-body-md py-12 text-center">
        Loading…
      </div>
      <div v-else-if="active.count === 0" class="py-16 text-center">
        <div class="text-5xl mb-2">✅</div>
        <div class="text-on-surface-variant font-body-lg">Nothing in this report right now.</div>
      </div>

      <div v-else class="bg-surface-container-lowest border border-outline-variant rounded-xl overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-surface-container-low">
              <th
                v-for="c in active.columns"
                :key="c.key"
                class="font-label-md text-label-md uppercase tracking-wide text-on-surface-variant px-4 py-3 whitespace-nowrap"
              >{{ c.label }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, i) in active.rows"
              :key="i"
              class="border-t border-outline-variant cursor-pointer hover:bg-surface-container-low"
              @click="row.ticket && (selectedTicket = row.ticket)"
            >
              <td
                v-for="c in active.columns"
                :key="c.key"
                class="px-4 py-3 font-body-md whitespace-nowrap"
                :class="c.key === 'ticket' ? 'text-primary font-semibold' : 'text-on-surface'"
              >
                <span v-if="c.key === 'status'" class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="chip(row[c.key])">
                  {{ row[c.key] || '—' }}
                </span>
                <span v-else>{{ cell(row, c.key) }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <TicketDetail :ticketId="selectedTicket" @close="selectedTicket = null" @refresh="onRefresh" />
  </AppShell>
</template>

<script setup>
import { ref, computed } from 'vue'
import { call } from '@/api'
import AppShell from '@/components/AppShell.vue'
import TicketDetail from '@/components/TicketDetail.vue'

const catalog = ref([])
const loadingCatalog = ref(true)
const catalogError = ref(false)

const active = ref(null)
const loadingReport = ref(false)
const selectedTicket = ref(null)

// ── Overview: trend + breakdowns (manager-only; silently hidden otherwise) ──
const overview = ref({ allowed: false, series: [], by_status: [], by_closure_type: [], totals: {}, days: 30 })
async function loadOverview() {
  try {
    const [t, b] = await Promise.all([
      call('lavanya_service.api.manager_reports.get_report_trends'),
      call('lavanya_service.api.manager_reports.get_report_breakdowns'),
    ])
    overview.value = { ...(t || {}), ...(b || {}), allowed: !!(t && t.allowed) }
  } catch (e) {
    overview.value = { ...overview.value, allowed: false }
  }
}

const trend = computed(() => {
  const s = overview.value.series || []
  if (!s.length) return null
  const W = 700
  const H = 130
  const max = Math.max(1, ...s.map((p) => Math.max(p.created, p.resolved)))
  const x = (i) => (s.length === 1 ? W / 2 : (i / (s.length - 1)) * W)
  const y = (v) => H - 6 - (v / max) * (H - 12)
  const path = (k) => s.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i).toFixed(1)},${y(p[k]).toFixed(1)}`).join(' ')
  return { W, H, created: path('created'), resolved: path('resolved'), first: s[0].date, last: s[s.length - 1].date }
})

function barPct(count, list) {
  const max = Math.max(1, ...(list || []).map((x) => x.count))
  return `${Math.round((count / max) * 100)}%`
}

function exportCsv() {
  if (!active.value?.rows?.length) return
  const cols = active.value.columns
  const esc = (v) => {
    const s = v == null ? '' : String(v)
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  const raw = (row, key) => {
    const v = row[key]
    if (v == null || v === '') return ''
    return DATE_KEYS.test(key) ? String(v).slice(0, 10) : v
  }
  const lines = [cols.map((c) => esc(c.label)).join(',')]
  for (const row of active.value.rows) lines.push(cols.map((c) => esc(raw(row, c.key))).join(','))
  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${active.value.key}-${new Date().toISOString().slice(0, 10)}.csv`
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

async function loadCatalog() {
  loadingCatalog.value = true
  catalogError.value = false
  try {
    const res = (await call('lavanya_service.api.manager_reports.get_report_catalog')) || {}
    catalog.value = res.reports || []
  } catch (e) {
    catalogError.value = true
  } finally {
    loadingCatalog.value = false
  }
}

async function openReport(key) {
  loadingReport.value = true
  active.value = { columns: [], rows: [], count: 0, title: '', description: '', icon: 'assessment' }
  try {
    active.value = (await call('lavanya_service.api.manager_reports.get_report', { report: key })) || active.value
  } catch (e) {
    active.value = null
    catalogError.value = true
  } finally {
    loadingReport.value = false
  }
}

function onRefresh() {
  // Refresh the open report (counts may shift after an action) and catalog.
  if (active.value) openReport(active.value.key)
  loadCatalog()
}

loadCatalog()
loadOverview()

// ── cell formatting ────────────────────────────────────────────────────────
const DATE_KEYS = /(_date|_on|modified|closure_date|registration_date|receipt_date)$/
function cell(row, key) {
  const v = row[key]
  if (v == null || v === '') return '—'
  if (DATE_KEYS.test(key)) return String(v).slice(0, 10)
  return v
}

const STATUS_HUE = {
  New: '#004ac6',
  'Registration Pending': '#2563eb',
  'Brand Registered': '#0053db',
  'In Progress': '#004ac6',
  'Waiting on Customer': '#943700',
  'Waiting on Part / Approval': '#943700',
  'Ready for Pickup': '#1a7f37',
  Resolved: '#1a7f37',
  Closed: '#434655',
  Cancelled: '#ba1a1a',
}
function hexToRgba(hex, a) {
  const h = hex.replace('#', '')
  return `rgba(${parseInt(h.slice(0, 2), 16)}, ${parseInt(h.slice(2, 4), 16)}, ${parseInt(h.slice(4, 6), 16)}, ${a})`
}
function chip(s) {
  const hue = STATUS_HUE[s] || '#434655'
  return { color: hue, background: hexToRgba(hue, 0.12) }
}
</script>
