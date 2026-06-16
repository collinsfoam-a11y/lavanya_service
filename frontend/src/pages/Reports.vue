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
        <div>
          <h2 class="font-headline-lg text-headline-lg text-on-surface">
            {{ active.title }}
            <span class="font-body-md text-on-surface-variant">· {{ active.count }}</span>
          </h2>
          <p class="font-body-md text-on-surface-variant">{{ active.description }}</p>
        </div>
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
import { ref } from 'vue'
import { call } from '@/api'
import AppShell from '@/components/AppShell.vue'
import TicketDetail from '@/components/TicketDetail.vue'

const catalog = ref([])
const loadingCatalog = ref(true)
const catalogError = ref(false)

const active = ref(null)
const loadingReport = ref(false)
const selectedTicket = ref(null)

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
