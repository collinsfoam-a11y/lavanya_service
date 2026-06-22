<!--
  H6A: WhatsApp Inbox — read-only inbound + draft-only outbound.
  No live WhatsApp/SMS sending. Drafts must be approved by manager.
  Safety locks remain: no ERP posting, no penalty, no auto-close.
-->
<template>
  <AppShell>
    <div class="mb-gutter">
      <LavSectionHeader title="WhatsApp Drafts" icon="chat" />
      <p class="font-body-md text-on-surface-variant -mt-2">Draft-only outbound queue. Live WhatsApp sending is disabled in pilot.</p>
    </div>

    <!-- Safety Banner -->
    <LavCard class="mb-6 border-warning" padding="compact">
      <div class="flex items-start gap-3">
        <span class="material-symbols-outlined text-warning" aria-hidden="true">notifications_paused</span>
        <div>
          <div class="font-body-md font-semibold text-on-surface">Draft-only system</div>
          <p class="font-label-md text-label-md text-on-surface-variant">No live WhatsApp messages are sent. All outbound messages are drafts requiring manager review. Inbound messages are captured read-only.</p>
        </div>
      </div>
    </LavCard>

    <!-- Tab bar -->
    <div class="flex items-center gap-1 mb-gutter overflow-x-auto pb-1" role="tablist">
      <button v-for="tab in TABS" :key="tab.key" role="tab" :aria-selected="activeTab === tab.key"
        class="px-4 py-2 rounded-lg font-label-md text-body-md whitespace-nowrap transition-colors"
        :class="activeTab === tab.key ? 'bg-primary text-on-primary' : 'text-on-surface-variant hover:bg-surface-container-low'"
        @click="activeTab = tab.key">{{ tab.label }}</button>
    </div>

    <!-- INBOUND TAB -->
    <template v-if="activeTab === 'inbound'">
      <div v-if="!hasInboxDoctype" class="mb-6 rounded-xl bg-surface-container border border-outline-variant p-6 text-center">
        <span class="material-symbols-outlined text-5xl text-on-surface-variant mb-3" aria-hidden="true">inbox</span>
        <h3 class="font-headline-md text-headline-md text-on-surface mb-1">WhatsApp Inbox not yet installed</h3>
        <p class="font-body-md text-on-surface-variant">Run bench migrate to create the WhatsApp Inbound Message DocType.</p>
      </div>

      <LavLoadingState v-else-if="loadingInbound" :lines="6" />
      <LavEmptyState v-else-if="inboundError" icon="error" title="Could not load messages" tone="error" />
      <LavEmptyState v-else-if="inboundMessages.length === 0" icon="inbox" title="No inbound messages yet" message="WhatsApp messages from customers will appear here once captured." />

      <div v-else class="flex flex-col gap-3">
        <div v-for="msg in inboundMessages" :key="msg.name"
          class="rounded-xl p-4 bg-surface border border-outline-variant hover:border-primary transition-colors">
          <div class="flex items-start justify-between gap-3 mb-2">
            <div>
              <div class="font-body-md font-semibold text-on-surface">{{ msg.sender_name || msg.sender_mobile }}</div>
              <div class="font-label-md text-on-surface-variant">{{ msg.sender_mobile }} · {{ relTime(msg.received_at) }}</div>
            </div>
            <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md shrink-0" :style="inboundStatusChip(msg.review_status)">{{ msg.review_status }}</span>
          </div>
          <p class="font-body-md text-on-surface mb-3 whitespace-pre-wrap">{{ msg.message_text }}</p>
          <div class="flex flex-wrap items-center gap-2">
            <button v-if="!msg.linked_ticket" @click="selectedInbound = msg" class="px-3 py-1.5 rounded-lg bg-primary text-on-primary font-label-md text-label-md hover:opacity-90">Link to Ticket</button>
            <span v-else class="px-3 py-1.5 rounded-lg border border-outline-variant text-on-surface-variant font-label-md text-label-md cursor-pointer hover:bg-surface-container-low" @click="selectedTicket = msg.linked_ticket">Ticket {{ msg.linked_ticket }}</span>
            <button v-if="msg.review_status === 'New'" @click="reviewInbound(msg.name, 'reviewed')" class="px-3 py-1.5 rounded-lg border border-outline-variant text-on-surface-variant font-label-md text-label-md hover:bg-surface-container-low">Mark Reviewed</button>
            <button v-if="msg.review_status === 'New'" @click="reviewInbound(msg.name, 'spam')" class="px-3 py-1.5 rounded-lg text-error font-label-md text-label-md">Ignore / Spam</button>
          </div>
        </div>
        <div v-if="hasMoreInbound" class="text-center py-4">
          <button @click="loadMoreInbound" :disabled="loadingInbound" class="px-4 py-2 rounded-lg border border-outline-variant text-primary font-label-md hover:bg-surface-container-low">Load more</button>
        </div>
      </div>
    </template>

    <!-- DRAFT OUTBOUND TAB -->
    <template v-if="activeTab === 'draft'">
      <div v-if="!hasDraftDoctype" class="mb-6 rounded-xl bg-surface-container border border-outline-variant p-6 text-center">
        <span class="material-symbols-outlined text-5xl text-on-surface-variant mb-3" aria-hidden="true">drafts</span>
        <h3 class="font-headline-md text-headline-md text-on-surface mb-1">Draft Outbound not yet installed</h3>
        <p class="font-body-md text-on-surface-variant">Run bench migrate to create the WhatsApp Draft Outbound DocType.</p>
      </div>

      <LavLoadingState v-else-if="loadingDraft" :lines="6" />
      <LavEmptyState v-else-if="draftError" icon="error" title="Could not load drafts" tone="error" />
      <LavEmptyState v-else-if="draftMessages.length === 0" icon="drafts" title="No drafts yet" message="Create drafts from the Ticket Detail communication section." />

      <div v-else class="flex flex-col gap-3">
        <div v-for="d in draftMessages" :key="d.name"
          class="rounded-xl p-4 bg-surface border border-outline-variant hover:border-primary transition-colors">
          <div class="flex items-start justify-between gap-3 mb-2">
            <div>
              <div class="font-body-md font-semibold text-on-surface">{{ d.recipient_name || d.recipient_mobile }}</div>
              <div class="font-label-md text-on-surface-variant">{{ d.recipient_mobile }} · {{ d.created_by_user }} · {{ relTime(d.created_at) }}</div>
            </div>
            <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md shrink-0" :style="draftStatusChip(d.review_status)">{{ d.review_status }}</span>
          </div>
          <p class="font-body-md text-on-surface mb-3 whitespace-pre-wrap bg-surface-container-low p-3 rounded-lg">{{ d.draft_message }}</p>
          <div class="flex flex-wrap items-center gap-2">
            <span @click="selectedTicket = d.ticket" class="px-3 py-1.5 rounded-lg border border-outline-variant text-primary font-label-md text-label-md cursor-pointer hover:bg-surface-container-low">Ticket {{ d.ticket }}</span>
            <button v-if="d.review_status === 'Draft'" @click="reviewDraft(d.name, 'approve')" class="px-3 py-1.5 rounded-lg bg-primary-container text-on-primary font-label-md text-label-md hover:opacity-90">Manager Review</button>
            <button v-if="d.review_status === 'Manager Reviewed'" @click="reviewDraft(d.name, 'ready')" class="px-3 py-1.5 rounded-lg bg-success text-on-success font-label-md text-label-md hover:opacity-90">Approve (Ready)</button>
            <button v-if="d.review_status !== 'Rejected' && d.review_status !== 'Sent (External)'" @click="rejectDraft(d.name)" class="px-3 py-1.5 rounded-lg text-error font-label-md text-label-md hover:bg-surface-container-low">Reject</button>
          </div>
        </div>
        <div v-if="hasMoreDraft" class="text-center py-4">
          <button @click="loadMoreDraft" :disabled="loadingDraft" class="px-4 py-2 rounded-lg border border-outline-variant text-primary font-label-md hover:bg-surface-container-low">Load more</button>
        </div>
      </div>
    </template>

    <!-- Link Inbound Modal -->
    <LavModal :show="!!selectedInbound" title="Link Message to Ticket" subtitle="Select a ticket to link this message" icon="link" maxWidth="lg" :submit-disabled="!linkTicketId" submitLabel="Link" submitIcon="link" @close="selectedInbound = null" @submit="linkToTicket">
      <div class="space-y-4">
        <div class="rounded-lg bg-surface-container p-3 font-body-md text-on-surface-variant max-h-[120px] overflow-y-auto">{{ selectedInbound?.message_text }}</div>
        <label class="block">
          <span class="font-label-md text-label-md text-on-surface">Ticket ID <span class="text-error">*</span></span>
          <input v-model="linkTicketId" type="text" class="lav-input mt-1" placeholder="e.g. HD-TKT-2024-00001" />
        </label>
      </div>
    </LavModal>

    <LavConfirm />
    <TicketDetail :ticketId="selectedTicket" @close="selectedTicket = null" @refresh="loadAll" />
  </AppShell>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { call, post } from '@/api'
import AppShell from '@/components/AppShell.vue'
import TicketDetail from '@/components/TicketDetail.vue'
import LavCard from '@/components/LavCard.vue'
import LavSectionHeader from '@/components/LavSectionHeader.vue'
import LavEmptyState from '@/components/LavEmptyState.vue'
import LavLoadingState from '@/components/LavLoadingState.vue'
import LavModal from '@/components/LavModal.vue'
import LavConfirm from '@/components/LavConfirm.vue'
import { useConfirm } from '@/utils/confirm'
import { useToast } from '@/utils/toast'
import { relTime } from '@/utils'

const { confirm } = useConfirm()
const { show: showToast } = useToast()

const TABS = [
  { key: 'inbound', label: 'Inbound Messages' },
  { key: 'draft', label: 'Draft Outbound' },
]
const activeTab = ref('inbound')
const selectedTicket = ref(null)
const selectedInbound = ref(null)
const linkTicketId = ref('')

const inboundMessages = ref([])
const draftMessages = ref([])
const loadingInbound = ref(true)
const loadingDraft = ref(true)
const inboundError = ref(false)
const draftError = ref(false)
const hasMoreInbound = ref(false)
const hasMoreDraft = ref(false)
const hasInboxDoctype = ref(true)
const hasDraftDoctype = ref(true)

async function loadInbound() {
  loadingInbound.value = true
  inboundError.value = false
  try {
    const res = await call('lavanya_service.api.whatsapp_inbox.list_inbound_messages', { status: 'All' })
    inboundMessages.value = res?.messages || []
    hasMoreInbound.value = !!res?.has_more
  } catch (e) {
    if (e.message?.includes('DocType')) { hasInboxDoctype.value = false; inboundMessages.value = [] }
    else inboundError.value = true
  } finally {
    loadingInbound.value = false
  }
}

async function loadMoreInbound() {
  loadingInbound.value = true
  try {
    const res = await call('lavanya_service.api.whatsapp_inbox.list_inbound_messages', { start: inboundMessages.value.length })
    inboundMessages.value = inboundMessages.value.concat(res?.messages || [])
    hasMoreInbound.value = !!res?.has_more
  } finally {
    loadingInbound.value = false
  }
}

async function loadDraft() {
  loadingDraft.value = true
  draftError.value = false
  try {
    const res = await call('lavanya_service.api.whatsapp_inbox.list_draft_outbound', { status: 'All' })
    draftMessages.value = res?.drafts || []
    hasMoreDraft.value = !!res?.has_more
  } catch (e) {
    if (e.message?.includes('DocType')) { hasDraftDoctype.value = false; draftMessages.value = [] }
    else draftError.value = true
  } finally {
    loadingDraft.value = false
  }
}

async function loadMoreDraft() {
  loadingDraft.value = true
  try {
    const res = await call('lavanya_service.api.whatsapp_inbox.list_draft_outbound', { start: draftMessages.value.length })
    draftMessages.value = draftMessages.value.concat(res?.drafts || [])
    hasMoreDraft.value = !!res?.has_more
  } finally {
    loadingDraft.value = false
  }
}

function loadAll() { loadInbound(); loadDraft() }

async function reviewInbound(name, action) {
  try {
    if (action === 'reviewed') {
      await post('lavanya_service.api.whatsapp_inbox.review_inbound', { message_name: name, action: 'review' })
    } else {
      await post('lavanya_service.api.whatsapp_inbox.review_inbound', { message_name: name, action: 'ignore' })
    }
    await loadInbound()
    showToast('Message reviewed')
  } catch (e) {
    showToast(e.message || 'Could not update message.', 'error')
  }
}

async function linkToTicket() {
  if (!selectedInbound.value || !linkTicketId.value.trim()) return
  try {
    await post('lavanya_service.api.whatsapp_inbox.link_inbound_to_ticket', { message_name: selectedInbound.value.name, ticket_name: linkTicketId.value.trim() })
    selectedInbound.value = null
    linkTicketId.value = ''
    showToast('Message linked')
    await loadInbound()
  } catch (e) {
    showToast(e.message || 'Could not link message.', 'error')
  }
}

async function reviewDraft(name, action) {
  try {
    await post('lavanya_service.api.whatsapp_inbox.review_draft', { draft_name: name, action })
    await loadDraft()
    showToast(`Draft ${action === 'ready' ? 'approved' : 'reviewed'}`)
  } catch (e) {
    showToast(e.message || 'Could not update draft.', 'error')
  }
}

async function rejectDraft(name) {
  const ok = await confirm('Reject this draft? It will be marked as rejected.', 'Reject Draft', true)
  if (!ok) return
  try {
    await post('lavanya_service.api.whatsapp_inbox.review_draft', { draft_name: name, action: 'reject' })
    await loadDraft()
    showToast('Draft rejected')
  } catch (e) {
    showToast(e.message || 'Could not reject draft.', 'error')
  }
}

function inboundStatusChip(status) {
  const map = { New: 'var(--lav-primary)', Reviewed: 'var(--lav-success)', 'Linked to Ticket': 'var(--lav-secondary)', Ignored: 'var(--lav-muted)', Spam: 'var(--lav-danger)' }
  const c = map[status] || 'var(--lav-muted)'
  return { background: `color-mix(in srgb, ${c} 13%, transparent)`, color: c }
}

function draftStatusChip(status) {
  const map = { Draft: 'var(--lav-primary)', 'Manager Reviewed': 'var(--lav-warning)', 'Approved (Ready)': 'var(--lav-success)', Rejected: 'var(--lav-danger)', 'Sent (External)': 'var(--lav-info)' }
  const c = map[status] || 'var(--lav-muted)'
  return { background: `color-mix(in srgb, ${c} 13%, transparent)`, color: c }
}

onMounted(loadAll)
</script>
