<!--
  Tickets — native SPA list view (replaces the external /helpdesk/tickets link).
  Free-text search + status filter, Stitch-styled rows that open the existing
  TicketDetail drawer. Data from lavanya_service.api.stitch_console.get_ticket_list
  (permission-scoped HD Ticket list, paginated).
-->
<template>
  <AppShell>
    <div class="mb-gutter">
      <LavSectionHeader title="Tickets" icon="confirmation_number">
        <template #actions>
          <router-link
            to="/new-ticket"
            class="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-on-primary font-label-md text-body-md"
          >
            <span class="material-symbols-outlined">add</span> New Ticket
          </router-link>
        </template>
      </LavSectionHeader>
      <p class="font-body-md text-on-surface-variant -mt-2">Service complaints &amp; their current state</p>
    </div>

    <!-- Search -->
    <div class="lav-search mb-3">
      <span class="material-symbols-outlined text-on-surface-variant">search</span>
      <input
        v-model="search"
        type="search"
        placeholder="Search ticket #, subject, customer or phone…"
        class="lav-search__input"
      />
      <button v-if="search" class="lav-search__clear" @click="search = ''; reload()" aria-label="Clear search">
        <span class="material-symbols-outlined" aria-hidden="true">close</span>
      </button>
    </div>

    <!-- Status filter chips -->
    <div class="lav-chips mb-gutter">
      <LavChip
        v-for="s in STATUSES"
        :key="s"
        :active="status === s"
        @click="status = s; reload()"
      >{{ s }}</LavChip>
    </div>

    <!-- States -->
    <LavLoadingState v-if="loading && tickets.length === 0" :lines="8" />
    <LavEmptyState
      v-else-if="error"
      icon="error"
      title="Could not load tickets"
      message="Check your access or contact the manager."
      tone="error"
    />
    <LavEmptyState
      v-else-if="tickets.length === 0"
      icon="search_off"
      title="No tickets match this view"
    >
      <div class="mt-4 flex justify-center gap-3">
        <button v-if="search || status !== 'All'" @click="search = ''; status = 'All'; reload()" class="px-4 h-10 rounded-lg border border-outline-variant text-primary font-label-md hover:bg-surface-container-low">
          Clear filters
        </button>
        <router-link to="/new-ticket" class="px-4 h-10 rounded-lg bg-primary text-on-primary font-label-md inline-flex items-center gap-1.5">
          <span class="material-symbols-outlined" style="font-size:18px">add</span> New Ticket
        </router-link>
      </div>
    </LavEmptyState>

    <!-- List -->
    <LavCard v-else padding="none" class="lav-queue overflow-x-auto">
      <table class="w-full" style="border-collapse:collapse">
        <thead>
          <tr class="text-left font-label-md text-label-md text-on-surface-variant border-b border-outline-variant">
            <th class="px-4 py-3 cursor-pointer select-none hover:text-on-surface" @click="toggleSort('name')" :aria-label="'Sort by ticket number' + (sortKey==='name' ? ', currently ' + sortDir : ', not sorted')" role="columnheader" :aria-sort="sortKey==='name' ? (sortDir==='asc' ? 'ascending' : 'descending') : 'none'">
              Ticket# <template v-if="sortKey==='name'"><span aria-hidden="true">{{ sortDir==='asc' ? '▲' : '▼' }}</span></template>
            </th>
            <th class="px-4 py-3 cursor-pointer select-none hover:text-on-surface" @click="toggleSort('customer')" :aria-label="'Sort by customer' + (sortKey==='customer' ? ', currently ' + sortDir : ', not sorted')" role="columnheader" :aria-sort="sortKey==='customer' ? (sortDir==='asc' ? 'ascending' : 'descending') : 'none'">
              Customer <template v-if="sortKey==='customer'"><span aria-hidden="true">{{ sortDir==='asc' ? '▲' : '▼' }}</span></template>
            </th>
            <th class="px-4 py-3 cursor-pointer select-none hover:text-on-surface" @click="toggleSort('status')" :aria-label="'Sort by status' + (sortKey==='status' ? ', currently ' + sortDir : ', not sorted')" role="columnheader" :aria-sort="sortKey==='status' ? (sortDir==='asc' ? 'ascending' : 'descending') : 'none'">
              Status <template v-if="sortKey==='status'"><span aria-hidden="true">{{ sortDir==='asc' ? '▲' : '▼' }}</span></template>
            </th>
            <th class="px-4 py-3 cursor-pointer select-none hover:text-on-surface" @click="toggleSort('product')" :aria-label="'Sort by product' + (sortKey==='product' ? ', currently ' + sortDir : ', not sorted')" role="columnheader" :aria-sort="sortKey==='product' ? (sortDir==='asc' ? 'ascending' : 'descending') : 'none'">
              Product <template v-if="sortKey==='product'"><span aria-hidden="true">{{ sortDir==='asc' ? '▲' : '▼' }}</span></template>
            </th>
            <th class="px-4 py-3 cursor-pointer select-none hover:text-on-surface" @click="toggleSort('overdue')" :aria-label="'Sort by SLA' + (sortKey==='overdue' ? ', currently ' + sortDir : ', not sorted')" role="columnheader" :aria-sort="sortKey==='overdue' ? (sortDir==='asc' ? 'ascending' : 'descending') : 'none'">
              SLA <template v-if="sortKey==='overdue'"><span aria-hidden="true">{{ sortDir==='asc' ? '▲' : '▼' }}</span></template>
            </th>
            <th class="px-4 py-3 cursor-pointer select-none hover:text-on-surface" @click="toggleSort('followup')" :aria-label="'Sort by follow-up date' + (sortKey==='followup' ? ', currently ' + sortDir : ', not sorted')" role="columnheader" :aria-sort="sortKey==='followup' ? (sortDir==='asc' ? 'ascending' : 'descending') : 'none'">
              Follow-up <template v-if="sortKey==='followup'"><span aria-hidden="true">{{ sortDir==='asc' ? '▲' : '▼' }}</span></template>
            </th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="t in sortedTickets"
            :key="t.name"
            class="group cursor-pointer hover:bg-surface-container-low border-b border-outline-variant/40"
            @click="selectedTicket = t.name"
            tabindex="0"
            @keydown.enter="selectedTicket = t.name"
          >
            <td class="px-4 py-3">
              <span class="font-body-md font-semibold text-primary">{{ t.name }}</span>
              <div class="font-label-md text-label-md text-on-surface-variant">{{ t.subject || '(no subject)' }}</div>
            </td>
            <td class="px-4 py-3 font-body-md text-on-surface">
              {{ t.customer_name }}
              <div class="font-label-md text-label-md text-on-surface-variant">{{ t.phone_1 || '' }}</div>
            </td>
            <td class="px-4 py-3">
              <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md whitespace-nowrap" :style="chip(t.status)">{{ t.status }}</span>
              <span v-if="t.customer_promise_status === 'Breached'" class="ml-1 px-2 py-0.5 rounded-full font-label-md text-label-md" :style="promiseChip('Breached')">Promise breach</span>
            </td>
            <td class="px-4 py-3 font-body-md text-on-surface">
              <template v-if="product(t)">{{ product(t) }}</template>
              <span v-if="t.overdue_status && t.overdue_status !== 'Not Due'" class="ml-1 px-2 py-0.5 rounded-full font-label-md text-label-md" :style="dueChip(t.overdue_status)">{{ t.overdue_status }}</span>
              <div v-if="t.pending_reason" class="font-label-md text-label-md text-on-surface-variant">{{ t.pending_reason }}</div>
            </td>
            <td class="px-4 py-3">
              <SlaBadge :agreement-status="t.agreement_status" :response-by="t.response_by" :resolution-by="t.resolution_by" />
              <span v-if="escLevel(t) && escLevel(t) !== 'None'" class="ml-1 px-2 py-0.5 rounded-full font-label-md text-label-md" :style="escChip(escLevel(t))">{{ escLevel(t) }}</span>
            </td>
            <td class="px-4 py-3 font-label-md text-label-md" :style="followStyle(t.next_follow_up_date)">
              {{ followText(t.next_follow_up_date) }}
              <span v-if="t.customer_update_due" class="ml-1 px-2 py-0.5 rounded-full font-label-md text-label-md" :style="promiseChip('Pending')">Update due</span>
            </td>
            <td class="px-4 py-3">
              <button class="px-3 py-1 rounded border border-outline-variant text-primary font-label-md hover:bg-surface-container-low md:opacity-0 md:group-hover:opacity-100 md:group-focus-within:opacity-100 transition-opacity" :aria-label="'Open ticket ' + t.name">
                Open
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </LavCard>

    <!-- Infinite scroll sentinel -->
    <div v-if="hasMore && !error" ref="sentinel" class="text-center py-6">
      <span v-if="loading" class="text-on-surface-variant font-body-md">Loading tickets…</span>
    </div>

    <!-- Ticket Detail Drawer -->
    <TicketDetail :ticketId="selectedTicket" @close="selectedTicket = null" @refresh="reload" />
  </AppShell>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { call } from '@/api'
import AppShell from '@/components/AppShell.vue'
import TicketDetail from '@/components/TicketDetail.vue'
import SlaBadge from '@/components/SlaBadge.vue'
import LavSectionHeader from '@/components/LavSectionHeader.vue'
import LavCard from '@/components/LavCard.vue'
import LavChip from '@/components/LavChip.vue'
import LavEmptyState from '@/components/LavEmptyState.vue'
import LavLoadingState from '@/components/LavLoadingState.vue'
import { chip, dueChip, escChip, promiseChip, product, followText, followStyle } from '@/utils'

const route = useRoute()

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
const search = ref(route.query.search || '')
const status = ref('All')
const selectedTicket = ref(null)
const sentinel = ref(null)
const sortKey = ref('name')
const sortDir = ref('desc')

const sortedTickets = computed(() => {
  const arr = [...tickets.value]
  const k = sortKey.value
  const dir = sortDir.value === 'asc' ? 1 : -1
  arr.sort((a, b) => {
    let va, vb
    if (k === 'customer') { va = (a.customer_name || '').toLowerCase(); vb = (b.customer_name || '').toLowerCase() }
    else if (k === 'status') { va = (a.status || ''); vb = (b.status || '') }
    else if (k === 'product') { va = (product(a) || '').toLowerCase(); vb = (product(b) || '').toLowerCase() }
    else if (k === 'overdue') { va = overdueWeight(a); vb = overdueWeight(b) }
    else if (k === 'followup') { va = a.next_follow_up_date || ''; vb = b.next_follow_up_date || '' }
    else { va = (a.name || ''); vb = (b.name || '') }
    if (va < vb) return -1 * dir
    if (va > vb) return 1 * dir
    return 0
  })
  return arr
})

function toggleSort(key) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortKey.value = key
    sortDir.value = 'asc'
  }
}

function overdueWeight(t) {
  const s = (t.overdue_status || '').toLowerCase()
  if (s.includes('breach') || s === 'overdue') return 3
  if (s.includes('due')) return 2
  return 1
}
let observer = null

// Debounced auto-search — fires 300ms after the user stops typing.
let searchTimer
watch(search, (val) => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => reload(), 300)
})

// Sync from header search (?search= query param).
watch(
  () => route.query.search,
  (term) => {
    const next = term || ''
    if (next !== search.value) {
      search.value = next
    }
  },
)

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
  hasMore.value = true
  fetchPage(0)
}

function loadMore() {
  if (!loading.value && hasMore.value) fetchPage(tickets.value.length)
}

onMounted(() => {
  observer = new IntersectionObserver(([entry]) => {
    if (entry.isIntersecting) loadMore()
  }, { rootMargin: '200px' })
  nextTick(() => {
    if (sentinel.value) observer.observe(sentinel.value)
  })
})
onUnmounted(() => {
  if (observer) observer.disconnect()
})

reload()
function escLevel(t) {
  return t.computed_escalation_level || t.escalation_level || 'None'
}
</script>
