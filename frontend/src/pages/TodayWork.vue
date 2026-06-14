<!--
  Today's Work dashboard — ported from the Stitch "Today's Work Dashboard"
  screen. Data comes from the live backend:
  lavanya_service.api.today_work.get_today_work (role-aware grouping +
  priority order are decided server-side; this page only renders).
-->
<template>
  <AppShell>
    <div class="mb-gutter">
      <h2 class="font-headline-lg text-headline-lg text-on-surface">Today’s Work</h2>
      <p class="font-body-md text-on-surface-variant">{{ data?.date || '' }}</p>
    </div>

    <!-- Summary metrics -->
    <div class="lav-card-grid">
      <div class="rounded-xl border-2 border-primary bg-surface-container-low p-gutter">
        <div class="font-display text-display text-primary">{{ summary.total }}</div>
        <div class="font-label-md text-label-md uppercase tracking-wide text-on-surface-variant">Total Pending</div>
      </div>
      <div class="rounded-xl border border-outline-variant bg-surface-container-lowest p-gutter">
        <div class="font-display text-display text-error">{{ summary.overdue }}</div>
        <div class="font-label-md text-label-md uppercase tracking-wide text-on-surface-variant">Overdue</div>
      </div>
      <div class="rounded-xl border border-outline-variant bg-surface-container-lowest p-gutter">
        <div class="font-display text-display text-tertiary">{{ summary.due_today }}</div>
        <div class="font-label-md text-label-md uppercase tracking-wide text-on-surface-variant">Due Today</div>
      </div>
    </div>

    <!-- States -->
    <div v-if="loading" class="text-on-surface-variant font-body-md py-12 text-center">
      Loading Today’s Work…
    </div>
    <div v-else-if="error" class="text-error font-body-md py-12 text-center">
      Could not load Today’s Work. Check your access or contact the manager.
    </div>
    <div v-else-if="summary.total === 0" class="py-16 text-center">
      <div class="text-5xl mb-2">🎉</div>
      <div class="text-on-surface-variant font-body-lg">All clear — no pending work right now.</div>
    </div>

    <!-- Buckets -->
    <div v-else class="flex flex-col gap-gutter">
      <section
        v-for="group in groups"
        :key="group.key"
        class="rounded-xl border border-outline-variant bg-surface-container-lowest overflow-hidden"
        :style="{ borderLeft: '4px solid ' + accent(group.key) }"
      >
        <header class="flex items-center gap-3 px-gutter py-3 border-b border-outline-variant">
          <span
            class="min-w-[28px] h-7 px-2 rounded-full text-on-primary font-label-md text-label-md flex items-center justify-center"
            :style="{ background: group.count ? accent(group.key) : '#c3c6d7' }"
          >{{ group.count }}</span>
          <h3 class="font-headline-md text-headline-md text-on-surface">{{ group.label }}</h3>
        </header>

        <div v-if="group.tickets.length === 0" class="px-gutter py-3 font-body-md text-on-surface-variant">
          Nothing here.
        </div>
        <ul v-else>
          <li
            v-for="t in group.tickets"
            :key="t.name"
            class="lav-work-card cursor-pointer hover:bg-surface-container"
            @click="selectedTicket = t.name"
          >
            <div class="flex-[2_1_220px] min-w-[200px]">
              <span class="font-body-md font-semibold text-primary hover:underline">
                {{ t.name }} · {{ t.subject || '(no subject)' }}
              </span>
              <div class="font-label-md text-label-md text-on-surface-variant mt-0.5">
                {{ t.customer_name }}<template v-if="t.phone_1"> · {{ t.phone_1 }}</template>
                <template v-if="product(t)"> · {{ product(t) }}</template>
              </div>
            </div>
            <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md"
                  :style="chip(t.status)">{{ t.status }}</span>
            <div class="flex-1 min-w-[130px] font-label-md text-label-md text-on-surface-variant">
              {{ t.pending_reason || '' }}
            </div>
            <div class="font-label-md text-label-md" :style="followStyle(t.next_follow_up_date)">
              {{ followText(t.next_follow_up_date) }}
            </div>
            <button class="px-3 py-1 rounded border border-outline-variant text-primary font-label-md hover:bg-surface-container-low">
              Open
            </button>
          </li>
        </ul>
      </section>
    </div>

    <!-- Ticket Detail Drawer -->
    <TicketDetail :ticketId="selectedTicket" @close="selectedTicket = null" />
  </AppShell>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { call } from '@/api'
import AppShell from '@/components/AppShell.vue'
import TicketDetail from '@/components/TicketDetail.vue'

const raw = ref({})
const loading = ref(true)
const error = ref(false)
const selectedTicket = ref(null)

onMounted(async () => {
  try {
    raw.value = (await call('lavanya_service.api.today_work.get_today_work', { include_counts: 1 })) || {}
  } catch (e) {
    error.value = true
  } finally {
    loading.value = false
  }
})

const data = computed(() => raw.value || {})
const groups = computed(() => data.value.groups || [])
const summary = computed(() => data.value.summary || { total: 0, overdue: 0, due_today: 0 })

const ACCENT = {
  overdue_follow_up: '#ba1a1a',
  due_today: '#943700',
  registration_recommended: '#004ac6',
  registration_pending: '#2563eb',
  waiting_on_customer: '#0053db',
  waiting_on_part: '#943700',
  ready_for_pickup: '#1a7f37',
  product_receipt_missing: '#712ae2',
  closure_pending: '#434655',
  new_complaints: '#004ac6',
}
function accent(key) {
  return ACCENT[key] || '#004ac6'
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
  const r = parseInt(h.slice(0, 2), 16)
  const g = parseInt(h.slice(2, 4), 16)
  const b = parseInt(h.slice(4, 6), 16)
  return `rgba(${r}, ${g}, ${b}, ${a})`
}
function chip(status) {
  const hue = STATUS_HUE[status] || '#434655'
  return { color: hue, background: hexToRgba(hue, 0.12) }
}

function product(t) {
  return [t.brand, t.product_item || t.product_type].filter(Boolean).join(' / ')
}

function followText(value) {
  if (!value) return 'No follow-up date'
  const d = new Date(String(value).slice(0, 10))
  const today = new Date(new Date().toISOString().slice(0, 10))
  const disp = d.toLocaleDateString()
  if (d < today) return 'Overdue: ' + disp
  if (d.getTime() === today.getTime()) return 'Due today: ' + disp
  return disp
}
function followStyle(value) {
  if (!value) return { color: '#737686' }
  const d = new Date(String(value).slice(0, 10))
  const today = new Date(new Date().toISOString().slice(0, 10))
  if (d < today) return { color: '#ba1a1a', fontWeight: '700' }
  if (d.getTime() === today.getTime()) return { color: '#943700', fontWeight: '700' }
  return {}
}
</script>
