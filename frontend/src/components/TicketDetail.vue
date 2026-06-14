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
          
          <button disabled class="w-full px-4 py-3 bg-primary text-on-primary rounded-lg font-label-md text-left opacity-50 cursor-not-allowed group relative">
            Need Invoice
            <span class="absolute hidden group-hover:block bottom-full left-0 mb-2 p-2 bg-inverse-surface text-inverse-on-surface text-xs rounded shadow w-full z-20">Available in Phase 2C after write-action wiring and role smoke.</span>
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
          Actions disabled for read-only preview mode. Use Standard Helpdesk for real operations.
        </div>
      </div>
      
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { call } from '@/api'

const props = defineProps({
  ticketId: { type: String, default: null }
})

const emit = defineEmits(['close'])

const ticket = ref(null)
const loading = ref(false)
const error = ref(false)

watch(() => props.ticketId, async (newVal) => {
  if (newVal) {
    loading.value = true
    error.value = false
    ticket.value = null
    try {
      ticket.value = await call('lavanya_service.api.stitch_console.get_ticket_detail', { ticket_id: newVal })
    } catch (e) {
      error.value = true
    } finally {
      loading.value = false
    }
  }
})

function close() {
  emit('close')
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
