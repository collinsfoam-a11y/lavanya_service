<template>
  <div class="page">
    <div class="breadcrumb" @click="navigate('lavanya-tickets')">
      <span class="ms">arrow_back</span> Tickets
    </div>
    <h1 class="page-title">New Ticket</h1>

    <!-- Step indicator -->
    <div class="step-indicator">
      <template v-for="(s, i) in STEPS" :key="s.key">
        <div class="si-step" :class="{ 'si--done': step > i+1, 'si--active': step === i+1 }">
          <div class="si-dot">
            <span class="ms" v-if="step > i+1">check</span>
            <span v-else>{{ i+1 }}</span>
          </div>
          <div class="si-label">{{ s.label }}</div>
        </div>
        <div v-if="i < STEPS.length-1" class="si-line" :class="{ 'si-line--done': step > i+1 }"></div>
      </template>
    </div>

    <div class="wizard-body">
      <!-- STEP 1: Customer -->
      <div v-if="step === 1" class="step-card">
        <div class="step-title"><span class="ms">person</span> Customer Details</div>
        <div class="form-grid">
          <div class="field field--full">
            <label>Phone Number <span class="req">*</span></label>
            <div class="phone-wrap">
              <input v-model="form.phone" type="tel" class="input" placeholder="Enter phone number to search…"
                @input="onPhoneInput" />
              <button class="btn btn--teal btn--sm"><span class="ms">qr_code_scanner</span></button>
            </div>
            <div v-if="customerLoading" class="lookup-status"><span class="ms spin">sync</span> Searching…</div>
            <div v-if="existingCustomer" class="suggestion-card">
              <div class="sc-avatar">{{ initials(existingCustomer.customer_name) }}</div>
              <div class="sc-info">
                <div class="sc-name">{{ existingCustomer.customer_name }}</div>
                <div class="sc-meta">{{ existingCustomer.customer_phone }} · {{ existingCustomer.ticket_count }} previous tickets · {{ existingCustomer.open_tickets }} open</div>
              </div>
              <button class="btn btn--teal btn--sm" @click="useExisting">Use Existing</button>
              <button class="btn btn--secondary btn--sm" @click="existingCustomer=null">Create New</button>
            </div>
          </div>
          <div class="field"><label>Customer Name <span class="req">*</span></label><input v-model="form.customer_name" class="input" placeholder="Full name" /></div>
          <div class="field"><label>Alternate Phone</label><input v-model="form.alt_phone" type="tel" class="input" /></div>
          <div class="field field--full"><label>Address</label><input v-model="form.address" class="input" /></div>
          <div class="field">
            <label>Customer Type</label>
            <select v-model="form.customer_type" class="select">
              <option value="">Select…</option><option>Regular</option><option>VIP</option><option>B2B</option>
            </select>
          </div>
          <div class="field">
            <label>Preferred Language</label>
            <select v-model="form.language" class="select">
              <option>Malayalam</option><option>English</option><option>Hindi</option><option>Tamil</option>
            </select>
          </div>
          <div class="field">
            <label>Communication Channel</label>
            <select v-model="form.comm_channel" class="select">
              <option>WhatsApp</option><option>Call</option><option>SMS</option>
            </select>
          </div>
          <div class="field">
            <label>WhatsApp Opt-in</label>
            <div class="toggle-btn" :class="{ 'tb--on': form.whatsapp_optin }" @click="form.whatsapp_optin = !form.whatsapp_optin">
              <span class="ms">{{ form.whatsapp_optin ? 'check_circle' : 'cancel' }}</span>
              {{ form.whatsapp_optin ? 'Opted In' : 'Not opted in' }}
            </div>
          </div>
        </div>
      </div>

      <!-- STEP 2: Product -->
      <div v-if="step === 2" class="step-card">
        <div class="step-title"><span class="ms">devices</span> Product Details</div>
        <div class="form-grid">
          <div class="field field--full">
            <label>Brand <span class="req">*</span></label>
            <div class="brand-grid">
              <div v-for="b in brands" :key="b.name"
                class="brand-chip" :class="{ 'bc--active': form.brand === b.name }"
                @click="form.brand = b.name; loadCategories()">
                {{ b.logo }} {{ b.name }}
              </div>
              <div class="brand-chip bc--add" @click="showBrandModal=true">
                <span class="ms">add</span> Add New
              </div>
            </div>
          </div>
          <div class="field field--full" v-if="form.brand">
            <label>Product Category <span class="req">*</span></label>
            <div class="cat-grid">
              <div v-for="c in categories" :key="c"
                class="cat-chip" :class="{ 'cc--active': form.category === c }"
                @click="form.category = c">{{ c }}</div>
            </div>
          </div>
          <div class="field"><label>Model <span class="req">*</span></label><input v-model="form.model" class="input" /></div>
          <div class="field">
            <label>Serial Number</label>
            <div class="serial-wrap">
              <input v-model="form.serial" class="input" />
              <button class="btn btn--outline btn--sm"><span class="ms">qr_code_scanner</span></button>
            </div>
          </div>
          <div class="field"><label>Invoice Number</label><input v-model="form.invoice" class="input" /></div>
          <div class="field"><label>Purchase Date</label><input v-model="form.purchase_date" type="date" class="input" /></div>
          <div class="field field--full">
            <label>Warranty Status</label>
            <div class="warranty-row">
              <div v-for="w in ['In Warranty','Out of Warranty','Extended Warranty','AMC']" :key="w"
                class="wc" :class="{ 'wc--active': form.warranty_status === w }"
                @click="form.warranty_status = w">{{ w }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- STEP 3: Complaint -->
      <div v-if="step === 3" class="step-card">
        <div class="step-title"><span class="ms">report_problem</span> Complaint Details</div>
        <div class="form-grid">
          <div class="field field--full">
            <label>Service Path <span class="req">*</span></label>
            <div class="sp-grid">
              <div v-for="sp in SERVICE_PATHS" :key="sp.key"
                class="sp-card" :class="{ 'sp--active': form.service_path === sp.key }"
                @click="form.service_path = sp.key">
                <span class="ms sp-icon">{{ sp.icon }}</span>
                <div class="sp-name">{{ sp.label }}</div>
                <div class="sp-desc">{{ sp.desc }}</div>
              </div>
            </div>
          </div>
          <div class="field">
            <label>Complaint Type <span class="req">*</span></label>
            <select v-model="form.complaint_type" class="select">
              <option value="">Select…</option>
              <option>Not working</option><option>Intermittent issue</option>
              <option>Physical damage</option><option>Installation issue</option>
              <option>No sound/display</option><option>Cooling not working</option><option>Other</option>
            </select>
          </div>
          <div class="field">
            <label>Priority</label>
            <div class="priority-row">
              <div v-for="p in ['Low','Medium','High','Urgent']" :key="p"
                class="pc" :class="['pc--'+p.toLowerCase(), form.priority===p ? 'pc--active':'']"
                @click="form.priority=p">{{ p }}</div>
            </div>
          </div>
          <div class="field field--full">
            <label>Issue Description <span class="req">*</span></label>
            <textarea v-model="form.description" rows="4" class="textarea" placeholder="Describe the issue…"></textarea>
          </div>
        </div>
      </div>

      <!-- STEP 4: Registration -->
      <div v-if="step === 4" class="step-card">
        <div class="step-title"><span class="ms">app_registration</span> Registration</div>

        <!-- Brand warranty/paid -->
        <div v-if="['brand_warranty','brand_paid'].includes(form.service_path)" class="form-grid">
          <div class="path-banner">
            <span class="ms">verified</span>
            <div><div class="pb-name">Brand Registration</div>
              <div class="pb-note">{{ autoRegSupported ? 'Auto-registration supported for ' + form.brand : 'Manual registration required' }}</div>
            </div>
            <div v-if="autoRegSupported" class="auto-badge"><span class="ms">auto_awesome</span> Auto-reg</div>
          </div>
          <div class="field"><label>Brand Complaint Number</label><input v-model="form.brand_ticket" class="input" placeholder="Filled after registration" /></div>
          <div class="field">
            <label>Service Center <span class="req">*</span></label>
            <select v-model="form.service_center" class="select" @change="loadSCInfo">
              <option value="">Select…</option>
              <option v-for="sc in serviceCenters" :key="sc.name" :value="sc.name">
                {{ sc.service_center_name }} · {{ sc.area_coverage }} · SLA {{ sc.sla_days }}d
              </option>
            </select>
          </div>
          <div class="field"><label>Expected Technician Call Date</label><input v-model="form.expected_call_date" type="date" class="input" /></div>
          <div class="field"><label>Next Follow-up Date <span class="req">*</span></label><input v-model="form.next_followup" type="date" class="input" /></div>
          <div v-if="autoRegSupported" class="field field--full">
            <div class="auto-reg-panel">
              <div class="arp-header"><span class="ms">auto_awesome</span> Auto-register via Email/WhatsApp for {{ form.brand }}</div>
              <div class="arp-row">
                <span class="ms arp-mail">mail</span>
                <span class="arp-label">Email Registration (dry-run)</span>
                <button class="btn btn--outline btn--sm" @click="triggerAutoReg('email')">Send Draft</button>
              </div>
              <div class="arp-row">
                <span class="ms arp-wa">chat</span>
                <span class="arp-label">WhatsApp Registration (dry-run)</span>
                <button class="btn btn--outline btn--sm" @click="triggerAutoReg('whatsapp')">Generate Draft</button>
              </div>
              <div class="arp-note"><span class="ms">info</span> Dry-run mode — no live messages sent</div>
            </div>
          </div>
        </div>

        <!-- Local service -->
        <div v-else-if="['local_paid','goodwill'].includes(form.service_path)" class="form-grid">
          <div class="field field--full">
            <label>Assign Technician</label>
            <div class="tech-list">
              <div v-for="t in technicians" :key="t.name"
                class="tech-card" :class="{ 'tc--active': form.technician === t.name }"
                @click="form.technician = t.name">
                <div class="tc-avatar">{{ initials(t.technician_name) }}</div>
                <div class="tc-info">
                  <div class="tc-name">{{ t.technician_name }}</div>
                  <div class="tc-meta">{{ t.skill_categories }} · {{ t.area_coverage }} · ★{{ t.rating }}</div>
                </div>
                <span class="tc-jobs" :class="t.open_jobs > 4 ? 'text--amber':''">{{ t.open_jobs }} jobs</span>
              </div>
            </div>
          </div>
          <div class="field"><label>Visit Date</label><input v-model="form.visit_date" type="date" class="input" /></div>
          <div class="field">
            <label>Charge Type</label>
            <select v-model="form.charge_type" class="select">
              <option value="">Select…</option><option>Free (Goodwill)</option><option>Fixed Rate</option><option>Estimate Required</option>
            </select>
          </div>
        </div>

        <!-- Showroom receiving -->
        <div v-else-if="form.service_path === 'showroom'" class="form-grid">
          <div class="field">
            <label>Product Condition on Receipt</label>
            <select v-model="form.received_condition" class="select">
              <option value="">Select…</option><option>Good condition</option><option>Minor damage noted</option><option>Major damage noted</option>
            </select>
          </div>
          <div class="field"><label>Accessories Received</label><input v-model="form.accessories" class="input" placeholder="Remote, power cord…" /></div>
          <div class="field"><label>Rack / Bin Location</label><input v-model="form.rack_bin" class="input" placeholder="e.g. A-3 Shelf 2" /></div>
          <div class="field field--full"><label>Physical Damage Notes</label><textarea v-model="form.damage_notes" rows="2" class="textarea"></textarea></div>
        </div>

        <!-- Summary -->
        <div class="summary-card">
          <div class="sum-row"><span>Customer</span><span>{{ form.customer_name || '—' }}</span></div>
          <div class="sum-row"><span>Product</span><span>{{ form.brand }} {{ form.model || '—' }}</span></div>
          <div class="sum-row"><span>Service Path</span><span>{{ SERVICE_PATHS.find(s=>s.key===form.service_path)?.label || '—' }}</span></div>
          <div class="sum-row"><span>Priority</span><span>{{ form.priority }}</span></div>
        </div>
      </div>

      <!-- Nav -->
      <div class="wizard-nav">
        <button v-if="step > 1" class="btn btn--outline" @click="step--">
          <span class="ms">arrow_back</span> Back
        </button>
        <div style="flex:1"></div>
        <button v-if="step < 4" class="btn btn--dark" @click="nextStep" :disabled="!canProceed">
          Continue <span class="ms">arrow_forward</span>
        </button>
        <button v-else class="btn btn--teal" @click="submitTicket" :disabled="submitting || !canProceed">
          <span v-if="submitting" class="ms spin">sync</span>
          <span v-else class="ms">check_circle</span>
          {{ submitting ? 'Creating…' : 'Create Ticket' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { navigate, showAlert, showError } from '../composables/frappe.js'
import { frappeCall } from '../composables/frappe.js'
import { searchCustomer, createTicket } from '../composables/useTickets.js'

const props = defineProps({ frappePage: Object, prefillPhone: String, prefillCustomer: String, onSuccess: Function })

const step       = ref(1)
const submitting = ref(false)
const customerLoading = ref(false)
const existingCustomer= ref(null)
const brands     = ref([])
const categories = ref([])
const serviceCenters = ref([])
const technicians    = ref([])
const showBrandModal = ref(false)

const STEPS = [
  { key:'customer', label:'Customer' },
  { key:'product',  label:'Product' },
  { key:'complaint',label:'Complaint' },
  { key:'registration',label:'Registration' },
]

const SERVICE_PATHS = [
  { key:'brand_warranty', icon:'verified',          label:'Brand Warranty',      desc:'Register with brand service center' },
  { key:'brand_paid',     icon:'paid',              label:'Brand Paid Service',  desc:'Brand service, customer pays' },
  { key:'local_paid',     icon:'engineering',       label:'Local Paid Service',  desc:'Our technician' },
  { key:'goodwill',       icon:'volunteer_activism',label:'Goodwill',            desc:'Lavanya bears cost' },
  { key:'demo',           icon:'play_lesson',       label:'Demo / Installation', desc:'New product setup' },
  { key:'showroom',       icon:'store',             label:'In-Showroom',         desc:'Product received at store' },
  { key:'stock',          icon:'inventory',         label:'Stock Complaint',     desc:'Supplier issue' },
]

const form = ref({
  phone:'', customer_name:'', alt_phone:'', address:'', customer_type:'', language:'Malayalam', comm_channel:'WhatsApp', whatsapp_optin:true,
  brand:'', category:'', model:'', serial:'', invoice:'', purchase_date:'', warranty_status:'In Warranty',
  service_path:'', complaint_type:'', priority:'Medium', description:'',
  brand_ticket:'', service_center:'', expected_call_date:'', next_followup:'',
  technician:'', visit_date:'', charge_type:'',
  received_condition:'', accessories:'', rack_bin:'', damage_notes:'',
})

const autoRegSupported = computed(() => ['LG','Samsung','Whirlpool'].includes(form.value.brand))

const canProceed = computed(() => {
  if (step.value === 1) return form.value.phone && form.value.customer_name
  if (step.value === 2) return form.value.brand && form.value.category && form.value.model
  if (step.value === 3) return form.value.service_path && form.value.complaint_type && form.value.description
  return true
})

onMounted(async () => {
  if (props.prefillPhone) { form.value.phone = props.prefillPhone; await lookupCustomer() }

  // Load brands from Frappe
  const br = await frappeCall('frappe.client.get_list', {
    doctype: 'Lavanya Brand Master', fields: ['name as name','brand_name as display','logo_emoji as logo'], filters: [['is_active','=',1]]
  })
  if (br) brands.value = (br).map(b => ({ name: b.name, logo: b.logo||'🏷️' }))

  // Load technicians
  const tech = await frappeCall('frappe.client.get_list', {
    doctype: 'Lavanya Technician', fields: ['name','technician_name','skill_categories','area_coverage','rating','open_jobs','is_available'], filters:[['is_active','=',1]]
  })
  if (tech) technicians.value = tech
})

let phoneTimer = null
function onPhoneInput() {
  existingCustomer.value = null
  clearTimeout(phoneTimer)
  if (form.value.phone.length >= 8) phoneTimer = setTimeout(lookupCustomer, 600)
}

async function lookupCustomer() {
  customerLoading.value = true
  try {
    const r = await searchCustomer(form.value.phone)
    if (r) existingCustomer.value = r
  } finally { customerLoading.value = false }
}

function useExisting() {
  form.value.customer_name = existingCustomer.value.customer_name
  form.value.address       = existingCustomer.value.address || ''
  existingCustomer.value   = null
}

async function loadCategories() {
  const sc = await frappeCall('frappe.client.get_list', {
    doctype: 'Lavanya Service Center',
    fields: ['name','service_center_name','area_coverage','sla_days'],
    filters: [['brand','=',form.value.brand],['is_active','=',1]]
  })
  if (sc) serviceCenters.value = sc

  // derive categories from brand
  const b = await frappeCall('frappe.client.get_value', {
    doctype: 'Lavanya Brand Master', fieldname: 'product_categories', filters: { name: form.value.brand }
  })
  if (b?.product_categories) {
    categories.value = b.product_categories.split('\n').filter(Boolean)
  } else {
    categories.value = ['LED TV','Refrigerator','Washing Machine','AC','Microwave','Other']
  }
}

function loadSCInfo() {}

function triggerAutoReg(channel) {
  showAlert('Dry-run: Auto-registration draft via ' + channel + ' generated for review', 'blue')
}

function nextStep() { if (canProceed.value) step.value++ }

async function submitTicket() {
  submitting.value = true
  try {
    const ticketName = await createTicket(form.value)
    showAlert('Ticket ' + ticketName + ' created successfully')
    if (props.onSuccess) props.onSuccess(ticketName)
    else navigate('lavanya-ticket-detail', 'name=' + ticketName)
  } catch(e) { showError(e.message || 'Failed to create ticket') }
  finally { submitting.value = false }
}

function initials(n) { return (n||'?').split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase() }
</script>

<style scoped>
.page{padding:28px 32px;max-width:900px}.breadcrumb{display:flex;align-items:center;gap:6px;font-size:12px;color:#9A9A93;cursor:pointer;font-weight:600;margin-bottom:8px}.page-title{font-size:24px;font-weight:800;color:#1C1C1E;letter-spacing:-0.02em;margin:0 0 22px}
.step-indicator{display:flex;align-items:center;background:#fff;border:1px solid #ECECE8;border-radius:16px;padding:20px 28px;margin-bottom:22px}.si-step{display:flex;align-items:center;gap:10px}.si-dot{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;flex:none;background:#F4F4F1;color:#9A9A93;border:2px solid #ECECE8}.si--done .si-dot{background:#0D9488;color:#fff;border-color:#0D9488}.si--active .si-dot{background:#fff;border-color:#0D9488;color:#0F766E}.si-label{font-size:12.5px;font-weight:700;white-space:nowrap}.si--done .si-label,.si--active .si-label{color:#1C1C1E}.si-label:not(.si--done .si-label):not(.si--active .si-label){color:#9A9A93}.si-line{flex:1;height:2px;background:#ECECE8;margin:0 12px;min-width:40px}.si-line--done{background:#0D9488}
.wizard-body{display:flex;flex-direction:column;gap:16px}.step-card{background:#fff;border:1px solid #ECECE8;border-radius:18px;padding:28px}.step-title{display:flex;align-items:center;gap:9px;font-size:16px;font-weight:800;color:#1C1C1E;margin-bottom:24px}.step-title .ms{font-size:20px;color:#0D9488;font-variation-settings:'FILL' 1}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.field{display:flex;flex-direction:column;gap:6px}.field--full{grid-column:1/-1}
label{font-size:12px;font-weight:700;color:#52525B}.req{color:#E11D48}.input{height:40px;border-radius:11px;border:1px solid #ECECE8;padding:0 14px;font-size:13px;font-family:inherit;outline:none;background:#FAFAF8}.input:focus{border-color:#0D9488;background:#fff}.select{height:40px;border-radius:11px;border:1px solid #ECECE8;padding:0 14px;font-size:13px;font-family:inherit;background:#FAFAF8}.textarea{border-radius:11px;border:1px solid #ECECE8;padding:12px 14px;font-size:13px;font-family:inherit;outline:none;background:#FAFAF8;resize:vertical}
.phone-wrap,.serial-wrap{display:flex;gap:8px}.phone-wrap .input,.serial-wrap .input{flex:1}
.lookup-status{font-size:12px;color:#A1A19B;display:flex;align-items:center;gap:6px}
.suggestion-card{display:flex;align-items:center;gap:10px;background:#F0FDFA;border:1px solid #CCFBF1;border-radius:11px;padding:10px 14px}.sc-avatar{width:36px;height:36px;border-radius:10px;background:#0D9488;color:#fff;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}.sc-name{font-size:13px;font-weight:700;color:#1C1C1E}.sc-meta{font-size:11px;color:#8B8B85}
.brand-grid{display:flex;flex-wrap:wrap;gap:7px}.brand-chip{display:flex;align-items:center;gap:7px;padding:8px 14px;border-radius:10px;background:#F4F4F1;border:1.5px solid transparent;font-size:13px;font-weight:600;cursor:pointer;color:#3F3F46;transition:all .15s}.brand-chip:hover{border-color:#0D9488}.bc--active{background:#F0FDFA;border-color:#0D9488;color:#0F766E;font-weight:800}.bc--add{color:#0D9488;border-color:#CCFBF1;background:#F0FDFA}
.cat-grid{display:flex;flex-wrap:wrap;gap:7px}.cat-chip{padding:7px 13px;border-radius:9px;background:#F4F4F1;font-size:12.5px;font-weight:600;cursor:pointer;border:1.5px solid transparent}.cc--active{background:#F0FDFA;border-color:#0D9488;color:#0F766E}
.warranty-row,.priority-row{display:flex;flex-wrap:wrap;gap:7px}.wc,.pc{padding:7px 14px;border-radius:9px;background:#F4F4F1;font-size:12.5px;font-weight:600;cursor:pointer;border:1.5px solid transparent}.wc--active,.pc--active{background:#F0FDFA;border-color:#0D9488;color:#0F766E}.pc--urgent.pc--active{background:#FFF1F3;border-color:#E11D48;color:#E11D48}.pc--high.pc--active{background:#FFF7ED;border-color:#D97706;color:#D97706}
.sp-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:10px}.sp-card{padding:14px;border-radius:12px;background:#F4F4F1;border:1.5px solid transparent;cursor:pointer;transition:all .15s}.sp-card:hover{border-color:#0D9488}.sp--active{background:#F0FDFA;border-color:#0D9488}.sp-icon{font-size:22px;color:#0D9488;font-variation-settings:'FILL' 1;display:block;margin-bottom:6px}.sp-name{font-size:13px;font-weight:800;color:#1C1C1E;margin-bottom:3px}.sp-desc{font-size:11px;color:#8B8B85}
.tech-list{display:flex;flex-direction:column;gap:8px}.tech-card{display:flex;align-items:center;gap:12px;padding:12px 14px;border-radius:12px;background:#F4F4F1;border:1.5px solid transparent;cursor:pointer;transition:all .15s}.tech-card:hover{border-color:#0D9488}.tc--active{background:#F0FDFA;border-color:#0D9488}.tc-avatar{width:36px;height:36px;border-radius:50%;background:#CCFBF1;color:#0D9488;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}.tc-name{font-size:13px;font-weight:700;color:#1C1C1E}.tc-meta{font-size:11px;color:#8B8B85}.tc-jobs{margin-left:auto;font-size:11.5px;font-weight:700;color:#52525B}
.path-banner{grid-column:1/-1;display:flex;align-items:center;gap:12px;padding:14px;background:#F0FDFA;border-radius:12px}.path-banner .ms{font-size:24px;color:#0D9488;font-variation-settings:'FILL' 1}.pb-name{font-size:14px;font-weight:800;color:#1C1C1E}.pb-note{font-size:11.5px;color:#8B8B85}.auto-badge{margin-left:auto;display:flex;align-items:center;gap:5px;font-size:11px;font-weight:700;color:#7C3AED;background:#F5F3FF;padding:5px 10px;border-radius:8px}
.auto-reg-panel{grid-column:1/-1;border:1.5px solid #DDD6FE;border-radius:14px;overflow:hidden}.arp-header{display:flex;align-items:center;gap:8px;padding:12px 16px;background:#F5F3FF;font-size:13px;font-weight:700;color:#6D28D9}.arp-row{display:flex;align-items:center;gap:12px;padding:12px 16px;border-top:1px solid #EDE9FE}.arp-mail{font-size:20px;color:#4F46E5;font-variation-settings:'FILL' 1}.arp-wa{font-size:20px;color:#059669;font-variation-settings:'FILL' 1}.arp-label{flex:1;font-size:13px;font-weight:600;color:#3F3F46}.arp-note{padding:8px 16px;background:#FFFBEB;font-size:10.5px;color:#92400E;font-weight:600;display:flex;align-items:center;gap:5px}
.summary-card{grid-column:1/-1;background:#FAFAF8;border:1px solid #ECECE8;border-radius:12px;padding:16px;margin-top:8px}.sum-row{display:flex;justify-content:space-between;padding:7px 0;border-bottom:1px solid #F4F4F1;font-size:13px}.sum-row:last-child{border-bottom:none}.sum-row span:first-child{color:#8B8B85;font-weight:600}.sum-row span:last-child{color:#1C1C1E;font-weight:700}
.toggle-btn{display:flex;align-items:center;gap:6px;padding:8px 14px;border-radius:10px;border:1.5px solid #ECECE8;background:#F4F4F1;font-size:12.5px;font-weight:700;cursor:pointer;color:#9A9A93;font-family:inherit;width:fit-content}.tb--on{background:#F0FDFA;border-color:#0D9488;color:#0D9488}
.wizard-nav{display:flex;align-items:center;gap:10px;background:#fff;border:1px solid #ECECE8;border-radius:14px;padding:16px 20px}
.text--amber{color:#D97706;font-weight:700}
.btn{display:inline-flex;align-items:center;gap:6px;padding:10px 20px;border-radius:10px;font-size:13px;font-weight:700;border:none;cursor:pointer;font-family:inherit;transition:all .15s}.btn:disabled{opacity:.5;cursor:not-allowed}.btn--dark{background:#1C1C1E;color:#fff}.btn--teal{background:#0D9488;color:#fff}.btn--outline{background:#fff;border:1px solid #ECECE8;color:#52525B}.btn--secondary{background:#F4F4F1;color:#3F3F46;border:none}.btn--sm{padding:7px 12px;font-size:12px}
@keyframes spin{to{transform:rotate(360deg)}}.spin{display:inline-block;animation:spin 1s linear infinite}
.ms{font-family:'Material Symbols Rounded';font-weight:normal;font-style:normal;line-height:1;font-size:18px}
</style>
