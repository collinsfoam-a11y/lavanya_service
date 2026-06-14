<template>
  <div v-if="ticketId" class="fixed inset-0 z-50 flex justify-end bg-on-surface/20" @click.self="close">
    <div class="w-full max-w-4xl bg-surface-container-lowest h-full shadow-xl flex flex-col md:flex-row overflow-hidden animate-slide-in">
      
      <!-- Main Detail Area -->
      <div class="flex-1 overflow-y-auto border-r border-outline-variant flex flex-col">
        <div v-if="loading" class="p-8 text-center text-on-surface-variant">Loading ticket...</div>
        <div v-else-if="error" class="p-8 text-center text-error">Failed to load ticket.</div>
        <div v-else-if="ticket" class="p-6 md:p-8 flex flex-col gap-8">
          
          <!-- Header -->
          <header class="flex flex-col gap-2 border-b border-outline-variant pb-4">
            <div class="flex items-start justify-between">
              <div>
                <h2 class="font-headline-lg text-headline-lg text-on-surface">{{ ticket.name }}</h2>
                <div class="flex gap-2 mt-2">
                  <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md" :style="chip(ticket.status)">{{ ticket.status }}</span>
                  <span class="px-2.5 py-0.5 rounded-full font-label-md text-label-md bg-surface-variant text-on-surface-variant">{{ ticket.priority }}</span>
                </div>
              </div>
              <button @click="close" class="p-2 rounded hover:bg-surface-container-low">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>
            <div class="mt-4 font-body-md text-on-surface-variant grid grid-cols-2 gap-y-2">
              <div>Customer: <span class="font-bold text-on-surface">{{ ticket.customer?.name || '—' }}</span></div>
              <div>Mobile: <span class="text-on-surface">{{ ticket.customer?.mobile || '—' }}</span></div>
              <div>Age: <span class="text-on-surface">{{ ticketAge(ticket.creation) }} days</span></div>
              <div>Assigned: <span class="text-on-surface">{{ ticket.assigned_to || 'Unassigned' }}</span></div>
            </div>
            <div class="mt-2">
              <a :href="'/helpdesk/tickets/' + ticket.name" target="_blank" class="text-primary hover:underline font-label-md">
                Open in Standard Helpdesk ↗
              </a>
            </div>
          </header>

          <!-- Customer Summary -->
          <section>
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Customer</h3>
            <div class="grid grid-cols-2 gap-4 font-body-md text-on-surface-variant bg-surface-container p-4 rounded-xl">
              <div><span class="block text-label-md text-outline">Name</span> {{ ticket.customer?.name || '—' }}</div>
              <div><span class="block text-label-md text-outline">Mobile</span> {{ ticket.customer?.mobile || '—' }}</div>
              <div class="col-span-2"><span class="block text-label-md text-outline">Address</span> {{ ticket.customer?.address || '—' }}</div>
              <div><span class="block text-label-md text-outline">Pincode</span> {{ ticket.customer?.pincode || '—' }}</div>
            </div>
          </section>

          <!-- Product Summary -->
          <section>
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Product</h3>
            <div class="grid grid-cols-2 gap-4 font-body-md text-on-surface-variant bg-surface-container p-4 rounded-xl">
              <div><span class="block text-label-md text-outline">Type</span> {{ ticket.product?.type || '—' }}</div>
              <div><span class="block text-label-md text-outline">Category/Item</span> {{ ticket.product?.item || '—' }}</div>
              <div><span class="block text-label-md text-outline">Brand</span> {{ ticket.product?.brand || '—' }}</div>
              <div><span class="block text-label-md text-outline">Model</span> {{ ticket.product?.model_number || '—' }}</div>
              <div><span class="block text-label-md text-outline">Serial Number</span> {{ ticket.product?.serial_number || '—' }}</div>
              <div><span class="block text-label-md text-outline">Warranty</span> {{ ticket.product?.warranty_status || '—' }}</div>
              <div><span class="block text-label-md text-outline">Invoice No.</span> {{ ticket.product?.invoice_number || '—' }}</div>
              <div><span class="block text-label-md text-outline">Purchase Date</span> {{ ticket.product?.purchase_date || '—' }}</div>
            </div>
          </section>

          <!-- Workflow Summary -->
          <section>
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Workflow</h3>
            <div class="grid grid-cols-2 gap-4 font-body-md text-on-surface-variant bg-surface-container p-4 rounded-xl">
              <div><span class="block text-label-md text-outline">Current Status</span> {{ ticket.workflow?.status || '—' }}</div>
              <div><span class="block text-label-md text-outline">Pending Reason</span> {{ ticket.workflow?.pending_reason || '—' }}</div>
              <div><span class="block text-label-md text-outline">Next Follow-up</span> {{ ticket.workflow?.next_follow_up_date || '—' }}</div>
              <div><span class="block text-label-md text-outline">Service Center</span> {{ ticket.workflow?.service_center || '—' }}</div>
              <div><span class="block text-label-md text-outline">Brand Ticket</span> {{ ticket.workflow?.brand_ticket_number || '—' }}</div>
              <div><span class="block text-label-md text-outline">Brand Reg Date</span> {{ ticket.workflow?.brand_registration_date || '—' }}</div>
            </div>
          </section>

          <!-- Product Receipt Summary -->
          <section>
            <h3 class="font-headline-md text-headline-md text-primary mb-3">Product Custody</h3>
            <div class="grid grid-cols-2 gap-4 font-body-md text-on-surface-variant bg-surface-container p-4 rounded-xl">
              <div><span class="block text-label-md text-outline">Receipt No.</span> {{ ticket.receipt?.number || '—' }}</div>
              <div><span class="block text-label-md text-outline">Custody Status</span> {{ ticket.receipt?.custody_status || '—' }}</div>
              <div><span class="block text-label-md text-outline">Last Movement</span> {{ ticket.receipt?.last_movement?.substring(0,10) || '—' }}</div>
              <div><span class="block text-label-md text-outline">Ready for Pickup</span> {{ ticket.receipt?.ready_for_pickup ? 'Yes' : 'No' }}</div>
            </div>
          </section>

          <!-- Timeline Placeholder -->
          <section class="border-t border-outline-variant pt-4 mt-4">
            <h3 class="font-headline-md text-headline-md text-on-surface mb-3">Timeline</h3>
            <div class="p-4 rounded-xl border border-dashed border-outline-variant text-center text-on-surface-variant text-body-md bg-surface-bright">
              Timeline events and communications will appear here.
            </div>
          </section>
        </div>
      </div>

      <!-- Quick Action Panel -->
      <div class="w-full md:w-80 bg-surface flex flex-col overflow-y-auto border-t md:border-t-0 md:border-l border-outline-variant">
        <div class="p-4 border-b border-outline-variant bg-surface-container-low sticky top-0 z-10">
          <h3 class="font-headline-md text-headline-md text-on-surface">Quick Actions</h3>
        </div>
        <div class="p-4 flex flex-col gap-3">
          
          <button disabled class="w-full px-4 py-3 bg-primary text-on-primary rounded-lg font-label-md text-left opacity-50 cursor-not-allowed group relative">
            Register Brand Complaint
            <span class="absolute hidden group-hover:block bottom-full left-0 mb-2 p-2 bg-inverse-surface text-inverse-on-surface text-xs rounded shadow w-full z-20">Available in Phase 2C after write-action wiring and role smoke.</span>
          </button>
          
          <button @click="openNeedInvoice" class="w-full px-4 py-3 bg-primary text-on-primary rounded-lg font-label-md text-left hover:opacity-90 active:scale-[0.98] transition-all group relative">
            Need Invoice
          </button>
          
          <button disabled class="w-full px-4 py-3 bg-primary-container text-on-primary-container rounded-lg font-label-md text-left opacity-50 cursor-not-allowed group relative">
            Follow Up Service Center
            <span class="absolute hidden group-hover:block bottom-full left-0 mb-2 p-2 bg-inverse-surface text-inverse-on-surface text-xs rounded shadow w-full z-20">Available in Phase 2C after write-action wiring and role smoke.</span>
          </button>

          <button disabled class="w-full px-4 py-3 bg-primary-container text-on-primary-container rounded-lg font-label-md text-left opacity-50 cursor-not-allowed group relative">
            Waiting for Part
            <span class="absolute hidden group-hover:block bottom-full left-0 mb-2 p-2 bg-inverse-surface text-inverse-on-surface text-xs rounded shadow w-full z-20">Available in Phase 2C after write-action wiring and role smoke.</span>
          </button>

          <button disabled class="w-full px-4 py-3 bg-secondary text-on-secondary rounded-lg font-label-md text-left opacity-50 cursor-not-allowed group relative">
            Create Product Receipt
            <span class="absolute hidden group-hover:block bottom-full left-0 mb-2 p-2 bg-inverse-surface text-inverse-on-surface text-xs rounded shadow w-full z-20">Available in Phase 2C after write-action wiring and role smoke.</span>
          </button>

          <button disabled class="w-full px-4 py-3 bg-secondary text-on-secondary rounded-lg font-label-md text-left opacity-50 cursor-not-allowed group relative">
            Mark Ready for Pickup
            <span class="absolute hidden group-hover:block bottom-full left-0 mb-2 p-2 bg-inverse-surface text-inverse-on-surface text-xs rounded shadow w-full z-20">Available in Phase 2C after write-action wiring and role smoke.</span>
          </button>

          <button disabled class="w-full px-4 py-3 bg-outline text-surface rounded-lg font-label-md text-left opacity-50 cursor-not-allowed group relative">
            Customer Confirmed
            <span class="absolute hidden group-hover:block bottom-full left-0 mb-2 p-2 bg-inverse-surface text-inverse-on-surface text-xs rounded shadow w-full z-20">Available in Phase 2C after write-action wiring and role smoke.</span>
          </button>
          
          <button disabled class="w-full px-4 py-3 bg-error text-on-error rounded-lg font-label-md text-left opacity-50 cursor-not-allowed group relative">
            Close Ticket
            <span class="absolute hidden group-hover:block bottom-full left-0 mb-2 p-2 bg-inverse-surface text-inverse-on-surface text-xs rounded shadow w-full z-20">Available in Phase 2C after write-action wiring and role smoke.</span>
          </button>

        </div>
        <div class="p-4 mt-auto text-xs text-on-surface-variant text-center bg-surface-container-low border-t border-outline-variant">
          Other actions disabled for read-only preview mode. Use Standard Helpdesk for real operations.
        </div>
      </div>
      
    </div>
  </div>

  <!-- Need Invoice Modal -->
  <div v-if="modals.needInvoice" class="fixed inset-0 bg-inverse-surface/40 backdrop-blur-sm flex items-center justify-center p-4 z-50" @click.self="modals.needInvoice = false">
    <div class="bg-surface-container-lowest rounded-xl w-full max-w-lg shadow-[0_10px_15px_-3px_rgba(0,0,0,0.1)] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200">
      <!-- Modal Header -->
      <div class="px-6 py-5 border-b border-outline-variant/30 flex justify-between items-center bg-surface-bright">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-full bg-error-container flex items-center justify-center text-error">
            <span class="material-symbols-outlined icon-fill">error</span>
          </div>
          <div>
            <h2 class="text-headline-md font-headline-md text-on-surface">Need Invoice</h2>
            <p class="text-body-md font-body-md text-on-surface-variant mt-1">Ticket #{{ ticketId }} - Status Update</p>
          </div>
        </div>
        <button @click="modals.needInvoice = false" class="text-on-surface-variant hover:text-on-surface transition-colors rounded-full p-1 hover:bg-surface-variant/50">
          <span class="material-symbols-outlined">close</span>
        </button>
      </div>
      <!-- Modal Body -->
      <div class="px-6 py-6 space-y-6 overflow-y-auto">
        <div v-if="actionError" class="p-3 bg-error-container text-on-error-container rounded font-body-sm mb-2">
          {{ actionError }}
        </div>
        <!-- Info Banner -->
        <div class="bg-surface-container p-4 rounded-lg flex items-start gap-3 border border-primary-fixed-dim/30">
          <span class="material-symbols-outlined text-primary mt-0.5">info</span>
          <div>
            <p class="text-body-md font-body-md text-on-surface font-medium">Customer document missing</p>
            <p class="text-body-md font-body-md text-on-surface-variant mt-1">This action will change the ticket status to <span class="font-semibold text-secondary">Waiting on Customer</span> and notify the assigned agent.</p>
          </div>
        </div>
        <form class="space-y-5" @submit.prevent="submitNeedInvoice">
          <!-- Pending Reason -->
          <div class="space-y-1.5">
            <label class="text-label-md font-label-md text-on-surface-variant block">Pending Reason</label>
            <div class="relative">
              <input class="w-full h-10 px-3 bg-surface-variant/30 border border-outline-variant/50 rounded-lg text-on-surface text-body-md font-body-md cursor-not-allowed focus:outline-none focus:ring-0" readonly type="text" :value="form.pending_reason" />
              <span class="material-symbols-outlined absolute right-3 top-2.5 text-on-surface-variant/50 text-[20px]">lock</span>
            </div>
          </div>
          <!-- Next Follow-up Date -->
          <div class="space-y-1.5">
            <label class="text-label-md font-label-md text-on-surface-variant block" for="followup">Next Follow-up Date <span class="text-error">*</span></label>
            <div class="relative">
              <input class="w-full h-10 px-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow" id="followup" required type="date" v-model="form.next_follow_up_date" :min="todayDate()"/>
            </div>
          </div>
          <!-- Note to Staff -->
          <div class="space-y-1.5">
            <label class="text-label-md font-label-md text-on-surface-variant block" for="staffNote">Note to Staff (Visible to internal team)</label>
            <textarea class="w-full p-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md font-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow resize-none" id="staffNote" placeholder="E.g., Customer promised to email it by tomorrow..." rows="3" v-model="form.note"></textarea>
          </div>
        </form>
      </div>
      <!-- Modal Footer -->
      <div class="px-6 py-4 bg-surface-bright border-t border-outline-variant/30 flex justify-end gap-3 rounded-b-xl">
        <button @click="modals.needInvoice = false" :disabled="submitting" class="px-5 h-10 rounded-lg text-body-md font-body-md font-medium text-on-surface-variant hover:bg-surface-variant/50 transition-colors border border-transparent disabled:opacity-50" type="button">
          Cancel
        </button>
        <button @click="submitNeedInvoice" :disabled="submitting || !form.next_follow_up_date" class="px-5 h-10 rounded-lg text-body-md font-body-md font-medium bg-primary text-on-primary hover:bg-on-primary-fixed-variant transition-colors shadow-sm flex items-center gap-2 disabled:opacity-50" type="button">
          <span v-if="submitting" class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
          <span v-else class="material-symbols-outlined text-[18px]">schedule_send</span>
          Mark Waiting on Customer
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, reactive } from 'vue'
import { call, post } from '@/api'

const props = defineProps({
  ticketId: { type: String, default: null }
})

const emit = defineEmits(['close', 'refresh'])

const ticket = ref(null)
const loading = ref(false)
const error = ref(false)

const loadTicket = async () => {
  if (props.ticketId) {
    loading.value = true
    error.value = false
    try {
      ticket.value = await call('lavanya_service.api.stitch_console.get_ticket_detail', { ticket_id: props.ticketId })
    } catch (e) {
      error.value = true
    } finally {
      loading.value = false
    }
  }
}

watch(() => props.ticketId, loadTicket)

function close() {
  emit('close')
}

// Action state
const modals = reactive({
  needInvoice: false
})
const form = reactive({
  pending_reason: 'Need Invoice',
  next_follow_up_date: '',
  note: ''
})
const submitting = ref(false)
const actionError = ref('')

function todayDate() {
  return new Date().toISOString().slice(0, 10)
}

function openNeedInvoice() {
  actionError.value = ''
  form.pending_reason = 'Need Invoice'
  form.next_follow_up_date = ''
  form.note = ''
  modals.needInvoice = true
}

async function submitNeedInvoice() {
  if (!form.next_follow_up_date) {
    actionError.value = "Next follow-up date is required."
    return
  }
  submitting.value = true
  actionError.value = ''
  try {
    await post('lavanya_service.api.workflow_actions.need_invoice_from_customer', {
      ticket_name: props.ticketId,
      next_follow_up_date: form.next_follow_up_date,
      note: form.note
    })
    modals.needInvoice = false
    emit('refresh')
    await loadTicket()
  } catch (err) {
    actionError.value = err.message || 'An error occurred while saving.'
  } finally {
    submitting.value = false
  }
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
function ticketAge(creationDate) {
  if (!creationDate) return 0
  const created = new Date(creationDate)
  const diffTime = Math.abs(new Date() - created)
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}
</script>

<style scoped>
.animate-slide-in {
  animation: slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}
</style>
