<!--
  Tickets — native SPA list view (replaces the external /helpdesk/tickets link).
  Free-text search + status filter, Stitch-styled rows that open the existing
  TicketDetail drawer. Data from lavanya_service.api.stitch_console.get_ticket_list
  (permission-scoped HD Ticket list, paginated).
-->
<template>
  <AppShell>
    <div class="mb-gutter flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 class="font-headline-lg text-headline-lg text-on-surface">Tickets</h2>
        <p class="font-body-md text-on-surface-variant">Service complaints &amp; their current state</p>
      </div>
      <a
        href="/helpdesk/tickets/new"
        target="_blank"
        class="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-on-primary font-label-md text-body-md"
      >
        <span class="material-symbols-outlined">add</span> New Ticket
      </a>
    </div>

    <!-- Search -->
    <div class="lav-search mb-3">
      <span class="material-symbols-outlined text-on-surface-variant">search</span>
      <input
        v-model="search"
        type="search"
        placeholder="Search ticket #, subject, customer or phone…"
        class="lav-search__input"
        @keyup.enter="reload"
      />
      <button v-if="search" class="lav-search__clear" @click="search = ''; reload()">
        <span class="material-symbols-outlined">close</span>
      </button>
    </div>

    <!-- Status filter chips -->
    <div class="lav-chips mb-gutter">
      <button
        v-for="s in STATUSES"
        :key="s"
        class="lav-chip"
        :class="status === s ? 'lav-chip--active' : ''"
        @click="status = s; reload()"
      >
        {{ s }}
      </button>
    </div>

    <!-- States -->
    <div v-if="loading && tickets.length === 0" class="text-on-surface-variant font-body-md py-12 text-center">
      Loading tickets…
    </div>
    <div v-else-if="error" class="text-error font-body-md py-12 text-center">
      Could not load tickets. Check your access or contact the manager.
    </div>
    <div v-else-if="tickets.length === 0" class="py-16 text-center">
      <div class="text-5xl mb-2">🔍</div>
      <div class="text-on-surface-variant font-body-lg">No tickets match this view.</div>
    </div>

    <!-- List -->
    <div v-else class="lav-queue">
      <ul>
        <li
          v-for="t in tickets"
          :key="t.name"
          class="lav-work-card cursor-pointer hover:bg-surface-container-low"
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
          <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="chip(t.status)">
            {{ t.status }}
          </span>
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
    </div>

    <!-- Load more -->
    <div v-if="hasMore && !error" class="text-center py-6">
      <button
        class="px-5 py-2 rounded-lg border border-outline-variant text-primary font-label-md text-body-md hover:bg-surface-container-low"
        :disabled="loading"
        @click="loadMore"
      >
        {{ loading ? 'Loading…' : 'Load more' }}
      </button>
    </div>

    <!-- Ticket Detail Drawer -->
    <TicketDetail :ticketId="selectedTicket" @close="selectedTicket = null" @refresh="reload" />
  </AppShell>
</template>

<script setup>
import { ref } from 'vue'
import { call } from '@/api'
import AppShell from '@/components/AppShell.vue'
import TicketDetail from '@/components/TicketDetail.vue'

const STATUSES = [
  'All',
  'New',
  'Registration Pending',
  'Brand Registered',
  'In Progress',
  'Waiting on Customer',
  'Waiting on Part / Approval',
  'Ready for Pickup',
  'Resolved',
  'Closed',
]

const PAGE_LENGTH = 30

const tickets = ref([])
const loading = ref(false)
const error = ref(false)
const hasMore = ref(false)
const search = ref('')
const status = ref('All')
const selectedTicket = ref(null)

async function fetchPage(start) {
  loading.value = true
  error.value = false
  try {
    const res =
      (await call('lavanya_service.api.stitch_console.get_ticket_list', {
        search: search.value || undefined,
        status: status.value,
        start,
        page_length: PAGE_LENGTH,
      })) || {}
    const batch = res.tickets || []
    tickets.value = start === 0 ? batch : tickets.value.concat(batch)
    hasMore.value = !!res.has_more
  } catch (e) {
    error.value = true
  } finally {
    loading.value = false
  }
}

function reload() {
  fetchPage(0)
}

function loadMore() {
  fetchPage(tickets.value.length)
}

reload()

// ── Stitch row helpers (shared with Today's Work) ──────────────────────────
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
function product(t) {
  return [t.brand, t.product_item].filter(Boolean).join(' / ')
}
function followText(value) {
  if (!value) return ''
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
