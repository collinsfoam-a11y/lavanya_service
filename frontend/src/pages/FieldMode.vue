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
        <LavEmptyState icon="search_off" title="No tickets found" :message="'No matches for &ldquo;' + search + '&rdquo;.'" />
      </div>
      <ul v-else-if="results.length" class="mt-3 flex flex-col gap-2" role="list">
        <li
          v-for="t in results"
          :key="t.name"
          class="rounded-xl border border-outline-variant bg-surface-container-low p-3 flex items-center gap-3 cursor-pointer hover:border-primary active:scale-[0.99] transition"
          @click="selectedTicket = t.name"
        >
          <div class="w-10 h-10 rounded-full bg-primary text-on-primary flex items-center justify-center shrink-0 font-label-md font-semibold">
            {{ (t.customer_name || '?').charAt(0).toUpperCase() }}
          </div>
          <div class="min-w-0 flex-1">
            <div class="font-body-md font-semibold text-primary truncate">{{ t.subject || '(no subject)' }}</div>
            <div class="font-label-md text-label-md text-on-surface-variant truncate">
              <span class="text-on-surface font-medium">{{ t.name }}</span>
              <template v-if="t.customer_name"> · {{ t.customer_name }}</template>
              <template v-if="t.phone_1"> · {{ t.phone_1 }}</template>
            </div>
          </div>
          <span class="px-2 py-0.5 rounded-full font-label-md text-label-md whitespace-nowrap" :style="chip(t.status)">{{ t.status }}</span>
        </li>
      </ul>
    </LavCard>

    <!-- Critical work snapshot -->
    <div class="mb-gutter">
      <LavSectionHeader title="Critical Work" icon="priority_high" :badge="criticalTotal" :accent="COLORS.error" />
      <LavLoadingState v-if="loadingWork" layout="card-list" />
      <template v-else>
        <div class="grid grid-cols-2 gap-3">
          <LavStatCard label="Overdue" :value="counts.overdue" icon="warning" :accent="COLORS.error" @click="goTodayWork" />
          <LavStatCard label="Due Today" :value="counts.due_today" icon="event" :accent="COLORS.warning" @click="goTodayWork" />
          <LavStatCard label="Ready Pickup" :value="counts.ready_for_pickup" icon="inventory_2" :accent="COLORS.success" @click="goTodayWork" />
          <LavStatCard label="New" :value="counts.new" icon="fiber_new" :accent="COLORS.primary" @click="goTodayWork" />
        </div>
      </template>
    </div>

    <TicketDetail :ticketId="selectedTicket" @close="selectedTicket = null" @refresh="loadWork" />
  </AppShell>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { call } from '@/api'
import AppShell from '@/components/AppShell.vue'
import TicketDetail from '@/components/TicketDetail.vue'
import LavCard from '@/components/LavCard.vue'
import LavSectionHeader from '@/components/LavSectionHeader.vue'
import LavStatCard from '@/components/LavStatCard.vue'
import LavEmptyState from '@/components/LavEmptyState.vue'
import LavLoadingState from '@/components/LavLoadingState.vue'
import { chip, COLORS } from '@/utils'

const router = useRouter()
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

function focusSearch() {
  if (searchInput.value) searchInput.value.focus()
}

function goNewTicket() {
  router.push('/new-ticket')
}

function goTodayWork() {
  router.push('/')
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

onMounted(loadWork)
</script>
