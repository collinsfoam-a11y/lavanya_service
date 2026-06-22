<!--
  Field Mode — touch-first, counter/showroom staff view.
  Reuses existing endpoints (today_work, stitch_console) and opens the shared
  TicketDetail drawer. Designed for tablets/phones: large tap targets, compact
  cards, phone-first search. No live WhatsApp/SMS, ERP posting, or penalty
  application is triggered here — only read + drawer actions (which keep their
  own server-side safety gates).
-->
<template>
  <AppShell>
    <div class="mb-gutter">
      <LavSectionHeader title="Field Mode" icon="phone_iphone" />
      <p class="font-body-md text-on-surface-variant -mt-2">Counter &amp; showroom quick actions</p>
    </div>

    <!-- Primary action tiles -->
    <div class="grid grid-cols-2 gap-3 mb-gutter">
      <LavCard :interactive="true" padding="default" class="flex flex-col items-center gap-2 py-6 hover:border-primary" @click="goNewTicket">
        <span class="material-symbols-outlined text-primary" style="font-size:40px">add_box</span>
        <span class="font-headline-md text-headline-md text-on-surface">New Ticket</span>
        <span class="font-label-md text-label-md text-on-surface-variant">Register a complaint</span>
      </LavCard>
      <LavCard :interactive="true" padding="default" class="flex flex-col items-center gap-2 py-6 hover:border-primary" @click="focusSearch">
        <span class="material-symbols-outlined text-primary" style="font-size:40px">contact_phone</span>
        <span class="font-headline-md text-headline-md text-on-surface">Find Customer</span>
        <span class="font-label-md text-label-md text-on-surface-variant">Search by phone / ticket</span>
      </LavCard>
    </div>

    <!-- Phone / ticket search -->
    <LavCard padding="default" class="mb-gutter">
      <div class="lav-search lav-search--lg">
        <span class="material-symbols-outlined text-on-surface-variant">search</span>
        <input
          ref="searchInput"
          v-model="search"
          type="search"
          inputmode="numeric"
          placeholder="Enter phone or ticket #…"
          class="lav-search__input"
          @keydown.enter="runSearch"
        />
        <button v-if="search" class="lav-search__clear" @click="search = ''; results = []" aria-label="Clear">
          <span class="material-symbols-outlined" aria-hidden="true">close</span>
        </button>
      </div>
      <button
        class="mt-3 w-full py-3 rounded-lg bg-primary text-on-primary font-label-lg text-label-lg"
        @click="runSearch"
      >Search</button>

      <LavLoadingState v-if="searching" :lines="4" />
      <div v-else-if="searched && results.length === 0" class="mt-3">
        <LavEmptyState icon="search_off" title="No tickets found" :message="'No matches for ' + search + '.'" />
      </div>
      <ul v-else-if="results.length" class="mt-3 flex flex-col gap-2" role="list">
        <li v-for="t in results" :key="t.name">
          <LavTicketCard :ticket="t" :compact="true" @open="selectedTicket = $event" />
        </li>
      </ul>
    </LavCard>

    <!-- Critical work snapshot -->
    <div class="mb-gutter">
      <LavSectionHeader title="Critical Work" icon="priority_high" :badge="criticalTotal" :accent="'var(--lav-danger)'" />
      <LavLoadingState v-if="loadingWork" layout="card-list" />
      <template v-else>
        <div class="grid grid-cols-2 gap-3">
          <LavStatCard label="Overdue" :value="counts.overdue" icon="warning" :accent="'var(--lav-danger)'" @click="goTodayWork" />
          <LavStatCard label="Due Today" :value="counts.due_today" icon="event" :accent="'var(--lav-warning)'" @click="goTodayWork" />
          <LavStatCard label="Ready Pickup" :value="counts.ready_for_pickup" icon="inventory_2" :accent="'var(--lav-success)'" @click="goTodayWork" />
          <LavStatCard label="New" :value="counts.new" icon="fiber_new" :accent="'var(--lav-primary)'" @click="goTodayWork" />
        </div>
      </template>
    </div>

    <div class="mb-gutter">
      <LavSectionHeader title="Recently Opened Work" icon="history" :badge="recentTickets.length" />
      <LavEmptyState v-if="!loadingWork && recentTickets.length === 0" icon="task_alt" title="No recent ticket work" message="Search by phone or open Today’s Work to begin." />
      <div v-else class="flex flex-col gap-3">
        <LavTicketCard v-for="t in recentTickets" :key="t.name" :ticket="t" :compact="true" @open="selectedTicket = $event" />
      </div>
    </div>

    <LavCard class="sticky bottom-20 md:bottom-4 z-20 shadow-lg" padding="compact">
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-2">
        <button type="button" class="field-action" @click="goNewTicket">
          <span class="material-symbols-outlined" aria-hidden="true">add_box</span>
          New Ticket
        </button>
        <button type="button" class="field-action opacity-50 cursor-not-allowed" disabled
          title="Not enabled in pilot. Open a ticket and use Call from the ticket drawer" aria-label="Call Customer — Not enabled in pilot">
          <span class="material-symbols-outlined" aria-hidden="true">phone_in_talk</span>
          Call Customer
        </button>
        <button type="button" class="field-action opacity-50 cursor-not-allowed" disabled
          title="Not enabled in pilot. Open a ticket and use Verify Technician Visit from the ticket drawer" aria-label="Verify Visit — Not enabled in pilot">
          <span class="material-symbols-outlined" aria-hidden="true">fact_check</span>
          Verify Visit
        </button>
        <button type="button" class="field-action opacity-50 cursor-not-allowed" disabled
          title="Not enabled in pilot. Open a ticket and use WhatsApp Draft from the ticket drawer" aria-label="WhatsApp Draft — Not enabled in pilot">
          <span class="material-symbols-outlined" aria-hidden="true">chat</span>
          WhatsApp Draft
        </button>
      </div>
      <p class="mt-2 font-label-md text-label-md text-on-surface-variant text-center">Open a ticket below to call, verify a visit, or draft WhatsApp — those run inside the ticket drawer with their safety gates. Live WhatsApp/SMS/ERP/payment actions remain disabled.</p>
    </LavCard>

    <TicketDetail :ticketId="selectedTicket" @close="selectedTicket = null" @refresh="loadWork" />
  </AppShell>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call } from '@/api'
import { useToast } from '@/utils/toast'
import AppShell from '@/components/AppShell.vue'
import TicketDetail from '@/components/TicketDetail.vue'
import LavCard from '@/components/LavCard.vue'
import LavSectionHeader from '@/components/LavSectionHeader.vue'
import LavStatCard from '@/components/LavStatCard.vue'
import LavEmptyState from '@/components/LavEmptyState.vue'
import LavLoadingState from '@/components/LavLoadingState.vue'
import LavTicketCard from '@/components/LavTicketCard.vue'
// Colors now use CSS custom properties (e.g. 'var(--lav-danger)') for theme responsiveness

const router = useRouter()
const { show: showToast } = useToast()
const search = ref('')
const results = ref([])
const searched = ref(false)
const searching = ref(false)
const selectedTicket = ref(null)
const searchInput = ref(null)
const work = ref({})
const loadingWork = ref(true)

const counts = computed(() => {
  const groups = work.value.groups || []
  const pick = (key) => {
    const g = groups.find((x) => x.key === key)
    return g ? (g.count != null ? g.count : (g.tickets || []).length) : 0
  }
  return {
    overdue: pick('overdue_follow_up'),
    due_today: pick('due_today'),
    ready_for_pickup: pick('ready_for_pickup'),
    new: pick('new_complaints'),
  }
})

const criticalTotal = computed(() => counts.value.overdue + counts.value.due_today)
const recentTickets = computed(() => {
  const seen = new Set()
  const out = []
  for (const group of work.value.groups || []) {
    for (const ticket of group.tickets || []) {
      if (!ticket?.name || seen.has(ticket.name)) continue
      seen.add(ticket.name)
      out.push(ticket)
      if (out.length >= 5) return out
    }
  }
  return out
})

function focusSearch() {
  if (searchInput.value) searchInput.value.focus()
}

function goNewTicket() {
  router.push('/new-ticket')
}

function openFirstResult() {
  if (results.value.length > 0) {
    selectedTicket.value = results.value[0].name
    return
  }
  focusSearch()
}

function callCustomer() {
  if (selectedTicket.value) {
    const t = results.value.find((x) => x.name === selectedTicket.value)
    if (t?.phone_1) {
      window.location.href = `tel:${t.phone_1}`
      return
    }
  }
  focusSearch()
}

function verifyVisit() {
  if (selectedTicket.value) return
  focusSearch()
}


async function runSearch() {
  const term = search.value.trim()
  if (!term) { results.value = []; searched.value = false; return }
  searching.value = true
  searched.value = true
  try {
    const res = await call('lavanya_service.api.stitch_console.get_ticket_list', {
      search: term,
      status: 'All',
      start: 0,
      page_length: 20,
    })
    results.value = res?.tickets || []
  } catch (e) {
    results.value = []
  } finally {
    searching.value = false
  }
}

async function loadWork() {
  loadingWork.value = true
  try {
    work.value = (await call('lavanya_service.api.today_work.get_today_work', { include_counts: 1 })) || {}
  } catch (e) {
    work.value = {}
  } finally {
    loadingWork.value = false
  }
}

onMounted(async () => {
  // Role guard: Field Mode is manager/coordinator-only in pilot (also hidden from
  // nav for staff). Block direct-URL access by non-admins.
  let canManage = false
  try {
    canManage = !!(await call('lavanya_service.api.ui_settings.can_manage_lavanya_settings'))
  } catch {
    canManage = false
  }
  if (!canManage) {
    showToast('Field Mode is not available for your role.', 'error')
    router.replace('/')
    return
  }
  loadWork()
})
</script>
