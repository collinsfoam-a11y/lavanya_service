<!--
  New Ticket — staff-side ticket intake inside the console (replaces the external
  /helpdesk/tickets/new link). Posts to stitch_console.create_ticket (permission-
  scoped, created as the real staff user, complaint_source 'Staff Entered').
  Option lists come from get_new_ticket_options (reuses the QR intake safe lists).
-->
<template>
  <AppShell>
    <div class="mb-gutter">
      <h2 class="font-headline-lg text-headline-lg text-on-surface">New Ticket</h2>
      <p class="font-body-md text-on-surface-variant">Log a customer complaint</p>
    </div>

    <!-- Success state -->
    <div v-if="created" class="bg-surface-container-lowest border border-outline-variant rounded-xl p-6 max-w-2xl">
      <div class="flex items-center gap-3 mb-4">
        <span class="material-symbols-outlined text-3xl" style="color:#1a7f37">check_circle</span>
        <div>
          <div class="font-headline-md text-headline-md text-on-surface">Ticket {{ created }} created</div>
          <div class="font-body-md text-on-surface-variant">{{ form.customer_name }} · {{ form.brand }} {{ form.product_type }}</div>
        </div>
      </div>
      <div class="flex gap-3">
        <button class="px-4 h-10 rounded-lg bg-primary text-on-primary font-label-md text-body-md" @click="openCreated">Open ticket</button>
        <button class="px-4 h-10 rounded-lg border border-outline-variant text-primary font-label-md text-body-md hover:bg-surface-container-low" @click="reset">Create another</button>
      </div>
    </div>

    <!-- Form -->
    <form v-else class="bg-surface-container-lowest border border-outline-variant rounded-xl p-6 max-w-2xl flex flex-col gap-5" @submit.prevent="submit">
      <div v-if="error" class="p-3 bg-error-container text-on-error-container rounded-lg font-body-md">{{ error }}</div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <label class="flex flex-col gap-1">
          <span class="font-label-md text-label-md text-on-surface-variant">Customer Name <span class="text-error">*</span></span>
          <input v-model="form.customer_name" type="text" class="lav-input" placeholder="Full name" />
        </label>
        <label class="flex flex-col gap-1">
          <span class="font-label-md text-label-md text-on-surface-variant">Mobile <span class="text-error">*</span></span>
          <input v-model="form.mobile" type="tel" class="lav-input" placeholder="10-digit mobile" @blur="lookupCustomer" />
          <span v-if="lookupHint" class="font-label-md text-label-md" style="color:#1a7f37">{{ lookupHint }}</span>
        </label>
        <label class="flex flex-col gap-1">
          <span class="font-label-md text-label-md text-on-surface-variant">Brand <span class="text-error">*</span></span>
          <select v-model="form.brand" class="lav-input">
            <option value="" disabled>Select brand…</option>
            <option v-for="b in opts.brands" :key="b" :value="b">{{ b }}</option>
          </select>
        </label>
        <label class="flex flex-col gap-1">
          <span class="font-label-md text-label-md text-on-surface-variant">Product Type <span class="text-error">*</span></span>
          <select v-model="form.product_type" class="lav-input">
            <option value="" disabled>Select product…</option>
            <option v-for="p in opts.product_types" :key="p" :value="p">{{ p }}</option>
          </select>
        </label>
        <label class="flex flex-col gap-1">
          <span class="font-label-md text-label-md text-on-surface-variant">Ticket Type</span>
          <select v-model="form.ticket_type" class="lav-input">
            <option v-for="t in opts.ticket_types" :key="t" :value="t">{{ t }}</option>
          </select>
        </label>
        <label class="flex flex-col gap-1">
          <span class="font-label-md text-label-md text-on-surface-variant">Warranty</span>
          <select v-model="form.warranty_status" class="lav-input">
            <option v-for="w in opts.warranty_statuses" :key="w" :value="w">{{ w }}</option>
          </select>
        </label>
        <label class="flex flex-col gap-1">
          <span class="font-label-md text-label-md text-on-surface-variant">Model No.</span>
          <input v-model="form.model_no" type="text" class="lav-input" />
        </label>
        <label class="flex flex-col gap-1">
          <span class="font-label-md text-label-md text-on-surface-variant">Serial No.</span>
          <input v-model="form.serial_no" type="text" class="lav-input" />
        </label>
        <label class="flex flex-col gap-1">
          <span class="font-label-md text-label-md text-on-surface-variant">Source</span>
          <select v-model="form.complaint_source" class="lav-input">
            <option v-for="s in opts.complaint_sources" :key="s" :value="s">{{ s }}</option>
          </select>
        </label>
        <label class="flex flex-col gap-1">
          <span class="font-label-md text-label-md text-on-surface-variant">Pincode</span>
          <input v-model="form.pincode" type="text" class="lav-input" />
        </label>
      </div>

      <label class="flex flex-col gap-1">
        <span class="font-label-md text-label-md text-on-surface-variant">Address</span>
        <input v-model="form.address" type="text" class="lav-input" />
      </label>

      <label class="flex flex-col gap-1">
        <span class="font-label-md text-label-md text-on-surface-variant">Complaint Details <span class="text-error">*</span></span>
        <textarea v-model="form.complaint_details" rows="3" class="lav-input resize-none" placeholder="Describe the issue…"></textarea>
      </label>

      <div class="flex justify-end gap-3">
        <button type="button" class="px-5 h-10 rounded-lg border border-outline-variant text-on-surface-variant font-label-md text-body-md hover:bg-surface-container-low" @click="reset">Clear</button>
        <button
          type="submit"
          :disabled="!canSubmit || submitting"
          class="px-5 h-10 rounded-lg bg-primary text-on-primary font-label-md text-body-md flex items-center gap-2 hover:opacity-90 disabled:opacity-50"
        >
          <span v-if="submitting" class="material-symbols-outlined animate-spin" style="font-size:18px">progress_activity</span>
          <span v-else class="material-symbols-outlined" style="font-size:18px">add</span>
          Create Ticket
        </button>
      </div>
    </form>
  </AppShell>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { call, post } from '@/api'
import AppShell from '@/components/AppShell.vue'

const router = useRouter()

const opts = ref({ brands: [], product_types: [], ticket_types: [], complaint_sources: [], warranty_statuses: [] })
const submitting = ref(false)
const error = ref('')
const created = ref(null)
const lookupHint = ref('')

async function lookupCustomer() {
  const m = (form.mobile || '').replace(/\D/g, '')
  if (m.length < 10) {
    lookupHint.value = ''
    return
  }
  try {
    const res = await call('lavanya_service.api.customer_intake.lookup_customer_by_mobile', { mobile: form.mobile })
    if (res && res.found) {
      // Prefill empty fields only — never overwrite what staff already typed.
      if (!form.customer_name) form.customer_name = res.customer_name || ''
      if (!form.address) form.address = res.address || ''
      if (!form.pincode) form.pincode = res.pincode || ''
      if (!form.brand && res.last_brand && opts.value.brands?.includes(res.last_brand)) form.brand = res.last_brand
      if ((!form.product_type || form.product_type === '') && res.last_product_type && opts.value.product_types?.includes(res.last_product_type)) form.product_type = res.last_product_type
      const n = res.ticket_count || 0
      lookupHint.value = `Returning customer${n ? ` · ${n} previous ticket${n > 1 ? 's' : ''}` : ''} — details prefilled`
    } else {
      lookupHint.value = ''
    }
  } catch (e) {
    lookupHint.value = ''
  }
}

const blank = () => ({
  customer_name: '', mobile: '', brand: '', product_type: '', ticket_type: '',
  warranty_status: 'Unknown', model_no: '', serial_no: '', complaint_source: 'Staff Entered',
  address: '', pincode: '', complaint_details: '',
})
const form = reactive(blank())

const canSubmit = computed(() =>
  form.customer_name.trim() && form.mobile.trim() && form.brand && form.product_type && form.complaint_details.trim(),
)

async function loadOptions() {
  try {
    const res = (await call('lavanya_service.api.stitch_console.get_new_ticket_options')) || {}
    opts.value = { ...opts.value, ...res }
    if (!form.ticket_type && res.ticket_types?.length) form.ticket_type = res.ticket_types[0]
  } catch (e) {
    error.value = 'Could not load options. Check your access.'
  }
}
loadOptions()

async function submit() {
  if (!canSubmit.value) return
  submitting.value = true
  error.value = ''
  try {
    const res = await post('lavanya_service.api.stitch_console.create_ticket', { ...form })
    created.value = res?.ticket
  } catch (e) {
    error.value = e.message || 'Could not create the ticket.'
  } finally {
    submitting.value = false
  }
}

function reset() {
  Object.assign(form, blank())
  if (opts.value.ticket_types?.length) form.ticket_type = opts.value.ticket_types[0]
  created.value = null
  error.value = ''
  lookupHint.value = ''
}

function openCreated() {
  router.push({ path: '/tickets', query: { search: created.value } })
}
</script>
