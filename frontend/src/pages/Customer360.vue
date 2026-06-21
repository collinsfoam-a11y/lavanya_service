<!--
  H6C: Customer 360 — read-only operational view of a customer.
  Shows identity, products, tickets, CRM, and WhatsApp context.
  No CRM creation, no WhatsApp send, no ERP posting, no auto-close.
-->
<template>
  <AppShell>
    <div class="mb-gutter">
      <LavSectionHeader title="Customer 360" icon="person_search" />
      <p class="font-body-md text-on-surface-variant -mt-2">Read-only customer intelligence — service, product, CRM, and communication context</p>
    </div>

    <!-- Search -->
    <div class="lav-search mb-gutter" style="max-width: 480px">
      <span class="material-symbols-outlined text-on-surface-variant">search</span>
      <input
        v-model="searchMobile"
        type="search"
        inputmode="numeric"
        placeholder="Enter customer mobile number…"
        class="lav-search__input"
        @keydown.enter="lookup"
      />
      <button v-if="searchMobile" class="lav-search__clear" @click="searchMobile = ''" aria-label="Clear"><span class="material-symbols-outlined" aria-hidden="true">close</span></button>
    </div>
    <button @click="lookup" :disabled="!searchMobile || searching" class="px-5 h-10 rounded-lg bg-primary text-on-primary font-label-md hover:opacity-90 disabled:opacity-50 mb-gutter">
      {{ searching ? 'Loading...' : 'Look Up Customer' }}
    </button>

    <LavLoadingState v-if="searching" :lines="8" />
    <LavEmptyState v-else-if="!searched" icon="person_search" title="Look up a customer" message="Enter a mobile number to view customer context." />
    <LavEmptyState v-else-if="!data || !data.found" icon="person_off" :title="'No customer found for ' + searchMobile" message="This mobile number has no service tickets or customer profile." />

    <template v-else>
      <!-- Identity -->
      <LavCard class="mb-gutter">
        <LavSectionHeader title="Customer Identity" icon="person" />
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 font-body-md text-on-surface-variant">
          <div><span class="block text-label-md text-outline">Name</span><span class="text-on-surface font-semibold">{{ data.identity?.customer_name || '—' }}</span></div>
          <div><span class="block text-label-md text-outline">Mobile</span><span class="text-on-surface font-semibold">{{ data.mobile }}</span></div>
          <div><span class="block text-label-md text-outline">Address</span><span class="text-on-surface">{{ data.identity?.address || '—' }}</span></div>
          <div><span class="block text-label-md text-outline">Pincode</span><span class="text-on-surface">{{ data.identity?.pincode || '—' }}</span></div>
        </div>
        <div v-if="data.identity?.duplicate_warning" class="mt-3 p-2 rounded-lg bg-warning-container/20 text-on-surface-variant font-label-md text-label-md">
          <span class="material-symbols-outlined" style="font-size:14px" aria-hidden="true">warning</span> {{ data.identity.duplicate_warning }}
        </div>
      </LavCard>

      <!-- Ticket Summary -->
      <LavCard class="mb-gutter">
        <LavSectionHeader title="Service Tickets" icon="confirmation_number" :badge="data.tickets?.total" />
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          <LavStatCard label="Active" :value="data.tickets?.active || 0" icon="pending_actions" :accent="data.tickets?.active > 0 ? 'var(--lav-primary)' : 'var(--lav-border)'" :hover="false" />
          <LavStatCard label="Overdue" :value="data.tickets?.overdue || 0" icon="warning" :accent="data.tickets?.overdue > 0 ? 'var(--lav-danger)' : 'var(--lav-border)'" :hover="false" />
          <LavStatCard label="Escalated" :value="data.tickets?.escalated || 0" icon="escalator_warning" :accent="data.tickets?.escalated > 0 ? 'var(--lav-danger)' : 'var(--lav-border)'" :hover="false" />
          <LavStatCard label="Not Informed" :value="data.tickets?.not_informed || 0" icon="campaign" :accent="data.tickets?.not_informed > 0 ? 'var(--lav-warning)' : 'var(--lav-border)'" :hover="false" />
        </div>
        <!-- Active tickets -->
        <h4 class="font-headline-md text-headline-md text-on-surface mb-2" v-if="data.tickets?.active_tickets?.length">Active ({{ data.tickets.active_tickets.length }})</h4>
        <div v-if="data.tickets?.active_tickets?.length" class="flex flex-col gap-2 mb-4">
          <div v-for="t in data.tickets.active_tickets" :key="t.name" class="rounded-lg p-3 border border-outline-variant bg-surface-container-lowest hover:border-primary cursor-pointer" @click="selectedTicket = t.name">
            <div class="flex items-center gap-2">
              <span class="font-body-md font-semibold text-primary">{{ t.name }}</span>
              <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="chip(t.status)">{{ t.status }}</span>
              <span v-if="t.escalation_level && t.escalation_level !== 'None'" class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="{ background: 'color-mix(in srgb, var(--lav-danger) 12%, transparent)', color: 'var(--lav-danger)' }">{{ t.escalation_level }}</span>
            </div>
            <div class="font-label-md text-on-surface-variant mt-1">{{ t.subject }} · {{ t.brand }} {{ t.product_type }}</div>
          </div>
        </div>
        <!-- Closed tickets -->
        <h4 class="font-headline-md text-headline-md text-on-surface mb-2" v-if="data.tickets?.closed_tickets?.length">Closed ({{ data.tickets.closed_tickets.length }})</h4>
        <div v-if="data.tickets?.closed_tickets?.length" class="flex flex-col gap-2">
          <div v-for="t in data.tickets.closed_tickets.slice(0,5)" :key="t.name" class="rounded-lg p-3 border border-outline-variant bg-surface-container-lowest hover:border-primary cursor-pointer" @click="selectedTicket = t.name">
            <div class="flex items-center gap-2">
              <span class="font-body-md font-semibold text-primary">{{ t.name }}</span>
              <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="chip(t.status)">{{ t.status }}</span>
            </div>
            <div class="font-label-md text-on-surface-variant mt-1">{{ t.subject }} · {{ t.brand }} {{ t.product_type }}</div>
          </div>
        </div>
      </LavCard>

      <!-- Products -->
      <LavCard class="mb-gutter" v-if="data.products?.has_history">
        <LavSectionHeader title="Products & Warranty" icon="inventory_2" :badge="data.products?.count" />
        <div class="flex flex-col gap-2">
          <div v-for="p in data.products.products" :key="p.name" class="rounded-lg p-3 border border-outline-variant bg-surface-container-lowest">
            <div class="flex items-center justify-between gap-2">
              <span class="font-body-md font-semibold text-on-surface">{{ p.brand }} {{ p.product_type }} {{ p.model_no || '' }}</span>
              <span class="px-2 py-0.5 rounded-full font-label-md text-label-md" :style="chip(p.warranty_status)">{{ p.warranty_status || 'Unknown' }}</span>
            </div>
            <div class="font-label-md text-on-surface-variant mt-1">
              S/N: {{ p.serial_no || '—' }} · Purchase: {{ p.purchase_date || '—' }} · Warranty to: {{ p.warranty_end_date || '—' }}
              <span v-if="p.ticket_count > 1" class="ml-1" :style="{ color: 'var(--lav-warning)' }">· {{ p.ticket_count }} service tickets</span>
            </div>
          </div>
        </div>
      </LavCard>

      <!-- CRM -->
      <LavCard class="mb-gutter" v-if="data.crm?.available">
        <LavSectionHeader title="CRM Relationship" icon="handshake" />
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 font-body-md text-on-surface-variant">
          <div><span class="block text-label-md text-outline">Contact</span><span class="text-on-surface">{{ data.crm.contact_linked ? data.crm.contact_name : 'Not linked' }}</span></div>
          <div><span class="block text-label-md text-outline">Organization</span><span class="text-on-surface">{{ data.crm.organization || '—' }}</span></div>
          <div><span class="block text-label-md text-outline">Open Deals</span><span class="text-on-surface font-semibold">{{ data.crm.open_deals || 0 }}</span></div>
          <div><span class="block text-label-md text-outline">Mode</span><span class="text-on-surface">{{ data.crm.mode }}</span></div>
        </div>
        <div class="flex flex-wrap gap-2 mt-2">
          <span v-if="data.crm.service_to_sales_opportunity" class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="{ background: 'color-mix(in srgb, var(--lav-secondary) 12%, transparent)', color: 'var(--lav-secondary)' }">Sales opportunity</span>
          <span v-if="data.crm.service_risk" class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="{ background: 'color-mix(in srgb, var(--lav-danger) 12%, transparent)', color: 'var(--lav-danger)' }">Service risk</span>
        </div>
      </LavCard>

      <!-- WhatsApp -->
      <LavCard class="mb-gutter">
        <LavSectionHeader title="WhatsApp" icon="chat" />
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 font-body-md text-on-surface-variant">
          <div><span class="block text-label-md text-outline">Inbound</span><span class="text-on-surface font-semibold">{{ data.whatsapp?.inbound_count || 0 }}</span></div>
          <div><span class="block text-label-md text-outline">Pending Review</span><span class="text-on-surface" :class="data.whatsapp?.pending_review > 0 ? 'text-warning font-semibold' : ''">{{ data.whatsapp?.pending_review || 0 }}</span></div>
          <div><span class="block text-label-md text-outline">Drafts</span><span class="text-on-surface font-semibold">{{ data.whatsapp?.draft_count || 0 }}</span></div>
          <div><span class="block text-label-md text-outline">Approved</span><span class="text-on-surface">{{ data.whatsapp?.approved_drafts || 0 }}</span></div>
        </div>
        <div v-if="data.whatsapp?.last_message_text" class="mt-3 p-3 rounded-lg bg-surface-container text-on-surface-variant font-body-md max-h-[80px] overflow-y-auto">
          Last: {{ data.whatsapp.last_message_text }}
        </div>
      </LavCard>
    </template>

    <TicketDetail :ticketId="selectedTicket" @close="selectedTicket = null" @refresh="lookup" />
    <LavConfirm />
  </AppShell>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { call } from '@/api'
import AppShell from '@/components/AppShell.vue'
import TicketDetail from '@/components/TicketDetail.vue'
import LavCard from '@/components/LavCard.vue'
import LavSectionHeader from '@/components/LavSectionHeader.vue'
import LavStatCard from '@/components/LavStatCard.vue'
import LavEmptyState from '@/components/LavEmptyState.vue'
import LavLoadingState from '@/components/LavLoadingState.vue'
import LavConfirm from '@/components/LavConfirm.vue'
import { chip, STATUS_HUE } from '@/utils'

const route = useRoute()
const searchMobile = ref('')
const data = ref(null)
const searching = ref(false)
const searched = ref(false)
const selectedTicket = ref(null)

onMounted(() => {
  const q = route.query.mobile
  if (q) {
    searchMobile.value = q
    lookup()
  }
})

async function lookup() {
  const m = searchMobile.value.trim()
  if (!m) return
  searching.value = true
  searched.value = true
  try {
    data.value = await call('lavanya_service.api.customer_360.get_customer_360', { mobile: m })
  } catch (e) {
    data.value = null
  } finally {
    searching.value = false
  }
}
</script>
