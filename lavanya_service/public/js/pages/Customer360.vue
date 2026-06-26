<template>
  <div class="page">
    <!-- Search hero -->
    <div v-if="!customer" class="search-hero">
      <span class="ms hero-icon">person_search</span>
      <h2 class="sh-title">Customer 360</h2>
      <p class="sh-sub">Search by phone number, name or ticket ID</p>
      <div class="sh-input-wrap">
        <span class="ms">search</span>
        <input v-model="searchQ" class="sh-input" placeholder="Phone number or name…"
          @keyup.enter="doSearch" @input="onInput" autofocus />
        <button class="btn btn--teal" @click="doSearch" :disabled="searching">
          <span v-if="searching" class="ms spin">sync</span>
          <span v-else class="ms">search</span> Search
        </button>
      </div>
      <div v-if="results.length" class="results-list">
        <div v-for="r in results" :key="r.name" class="result-row" @click="loadCustomer(r.name)">
          <div class="r-avatar" :style="avatarStyle(r)">{{ initials(r.customer_name) }}</div>
          <div class="r-info">
            <div class="r-name">{{ r.customer_name }}</div>
            <div class="r-meta">{{ r.customer_phone }}</div>
          </div>
          <span v-if="r.is_vip" class="badge badge--gold">VIP</span>
          <span class="ms r-arrow">chevron_right</span>
        </div>
      </div>
      <div v-else-if="searched && !searching" class="no-results">No customers found for "{{ searchQ }}"</div>
    </div>

    <!-- Customer profile -->
    <div v-else>
      <div class="page-header">
        <div class="breadcrumb" @click="customer=null; results=[]; searched=false">
          <span class="ms">arrow_back</span> Search
        </div>
        <h1 class="page-title">Customer 360</h1>
        <button class="btn btn--dark" @click="navigate('lavanya-new-ticket','phone='+customer.customer_phone)">
          <span class="ms">add</span> New Ticket
        </button>
      </div>

      <div v-if="profileLoading" class="loading-state"><span class="ms spin">sync</span> Loading profile…</div>
      <div v-else class="c360-layout">

        <!-- LEFT -->
        <div class="c360-left">
          <div class="card">
            <div class="profile-head">
              <div class="profile-avatar">{{ initials(customer.customer_name) }}</div>
              <div class="profile-info">
                <div class="profile-name">{{ customer.customer_name }}</div>
                <div class="profile-phone">{{ customer.customer_phone }}</div>
                <div class="profile-addr">{{ customer.address }}</div>
                <div class="profile-badges">
                  <span v-if="customer.is_vip" class="badge badge--gold">VIP</span>
                  <span class="badge badge--gray">{{ customer.customer_type }}</span>
                  <span v-if="customer.whatsapp_optin" class="badge badge--teal"><span class="ms">chat</span> WhatsApp</span>
                  <span v-if="customer.is_sensitive" class="badge badge--amber">Sensitive</span>
                </div>
              </div>
              <div class="profile-actions">
                <a class="icon-btn" :href="'tel:'+customer.customer_phone"><span class="ms">phone</span></a>
                <button class="icon-btn"><span class="ms">edit</span></button>
              </div>
            </div>
            <div class="profile-stats">
              <div class="ps-item"><div class="ps-n">{{ stats.total }}</div><div class="ps-l">Total Tickets</div></div>
              <div class="ps-item"><div class="ps-n ps-n--red">{{ stats.open }}</div><div class="ps-l">Open</div></div>
              <div class="ps-item"><div class="ps-n ps-n--amber">{{ stats.repeat }}</div><div class="ps-l">Repeat Complaints</div></div>
              <div class="ps-item"><div class="ps-n ps-n--teal">{{ stats.csat }}%</div><div class="ps-l">CSAT</div></div>
            </div>
          </div>

          <!-- Products -->
          <div class="card">
            <div class="card-title"><span class="ms">devices</span> Products & Warranty</div>
            <div v-if="products.length" class="product-list">
              <div v-for="p in products" :key="p.name" class="product-card">
                <div class="pc-brand">{{ p.brand }}</div>
                <div class="pc-info">
                  <div class="pc-model">{{ p.product_model }}</div>
                  <div class="pc-serial mono">SN: {{ p.serial_number || '—' }}</div>
                  <div class="pc-date">Purchased {{ fmtDate(p.purchase_date) }}</div>
                </div>
                <div class="pc-warranty" :class="isWarrantyValid(p) ? 'pw--valid' : 'pw--expired'">
                  <span class="ms">{{ isWarrantyValid(p) ? 'verified' : 'verified_off' }}</span>
                  <div>
                    <div class="pw-status">{{ isWarrantyValid(p) ? 'In Warranty' : 'Expired' }}</div>
                    <div class="pw-date">{{ p.warranty_end_date || '—' }}</div>
                  </div>
                </div>
                <span class="badge badge--gray">{{ p.ticket_count || 0 }} tickets</span>
              </div>
            </div>
            <div v-else class="empty-sm">No products on record</div>
          </div>
        </div>

        <!-- RIGHT -->
        <div class="c360-right">
          <div class="card">
            <div class="card-title"><span class="ms">confirmation_number</span> Ticket History</div>
            <div v-if="tickets.length" class="ticket-history">
              <div v-for="t in tickets" :key="t.name"
                class="th-row" @click="navigate('lavanya-ticket-detail','name='+t.name)">
                <div class="th-dot" :class="'dot--'+qualityColor(t.quality_badge)"></div>
                <div class="th-info">
                  <div class="th-subject">{{ t.subject }}</div>
                  <div class="th-meta"><span class="mono text--teal">#{{ t.name }}</span> · {{ t.brand }} · {{ fmtDate(t.creation) }}</div>
                </div>
                <StatusBadge :status="t.status" />
                <span class="ms th-arr">chevron_right</span>
              </div>
            </div>
            <div v-else class="empty-sm">No tickets yet</div>
            <button class="btn btn--outline full mt-10" @click="navigate('lavanya-new-ticket','phone='+customer.customer_phone)">
              <span class="ms">add</span> New Ticket for this Customer
            </button>
          </div>

          <!-- WhatsApp history -->
          <div class="card">
            <div class="card-title"><span class="ms">chat</span> WhatsApp Messages</div>
            <div v-if="waMessages.length" class="wa-history">
              <div v-for="m in waMessages" :key="m.name"
                class="wam" :class="m.direction==='in' ? 'wam--in' : 'wam--out'">
                <div class="wam-text">{{ m.message_text }}</div>
                <div class="wam-meta">{{ timeAgo(m.received_at) }} · {{ m.direction==='in' ? 'Customer':'Lavanya' }}</div>
              </div>
            </div>
            <div v-else class="empty-sm">No WhatsApp messages</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import StatusBadge from '../components/StatusBadge.vue'
import { navigate } from '../composables/frappe.js'
import { frappeCall } from '../composables/frappe.js'

const props = defineProps({ frappePage: Object, customerId: String, onOpenTicket: Function, onNewTicket: Function })

const searchQ     = ref('')
const results     = ref([])
const searching   = ref(false)
const searched    = ref(false)
const customer    = ref(null)
const profileLoading = ref(false)
const tickets     = ref([])
const products    = ref([])
const waMessages  = ref([])

const stats = computed(() => ({
  total:  tickets.value.length,
  open:   tickets.value.filter(t => !['Closed','Cancelled'].includes(t.status)).length,
  repeat: customer.value?.repeat_complaint_count || 0,
  csat:   Math.round(tickets.value.filter(t=>t.customer_satisfaction==='Satisfied').length / Math.max(tickets.value.filter(t=>t.status==='Closed').length,1)*100) || 0,
}))

let searchTimer = null
function onInput() {
  clearTimeout(searchTimer)
  if (searchQ.value.length >= 3) searchTimer = setTimeout(doSearch, 500)
}

async function doSearch() {
  if (!searchQ.value || searchQ.value.length < 2) return
  searching.value = true; searched.value = false
  try {
    // FIXED: frappe.client.get_list does not support or_filters parameter.
    // Use two separate queries and merge/deduplicate results.
    const q = searchQ.value
    const [byName, byPhone] = await Promise.all([
      frappeCall('frappe.client.get_list', {
        doctype: 'Lavanya Customer',
        fields: ['name', 'customer_name', 'customer_phone', 'is_vip', 'customer_type'],
        filters: [['customer_name', 'like', '%' + q + '%']],
        limit: 10,
      }),
      frappeCall('frappe.client.get_list', {
        doctype: 'Lavanya Customer',
        fields: ['name', 'customer_name', 'customer_phone', 'is_vip', 'customer_type'],
        filters: [['customer_phone', 'like', '%' + q + '%']],
        limit: 10,
      }),
    ])
    // Deduplicate by name
    const seen = new Set()
    const merged = []
    for (const r of [...(byName || []), ...(byPhone || [])]) {
      if (!seen.has(r.name)) { seen.add(r.name); merged.push(r) }
    }
    results.value = merged
    searched.value = true
  } finally { searching.value = false }
}

async function loadCustomer(id) {
  profileLoading.value = true
  customer.value = null; tickets.value = []; products.value = []; waMessages.value = []
  try {
    const [cust, tix, prods, wa] = await Promise.all([
      frappeCall('frappe.client.get', { doctype:'Lavanya Customer', name: id }),
      frappeCall('frappe.client.get_list', {
        doctype:'Lavanya Ticket', fields:['name','subject','status','brand','quality_badge','customer_satisfaction','creation'],
        filters:[['customer','=',id]], order_by:'creation desc', limit:20
      }),
      frappeCall('frappe.client.get_list', {
        doctype:'Lavanya Customer Product', fields:['*'],
        filters:[['customer','=',id]], limit:10
      }),
      frappeCall('frappe.client.get_list', {
        doctype:'Lavanya Whatsapp Message', fields:['name','message_text','direction','received_at'],
        filters:[['matched_customer','=',id]], order_by:'received_at desc', limit:20
      }),
    ])
    customer.value  = cust
    tickets.value   = tix || []
    products.value  = prods || []
    waMessages.value= wa || []
  } finally { profileLoading.value = false }
}

function isWarrantyValid(p) {
  if (!p.warranty_end_date) return false
  return new Date(p.warranty_end_date) >= new Date()
}
function qualityColor(badge) {
  return { 'Critical':'red','At Risk':'amber','Needs Update':'blue','Good':'teal' }[badge] || 'gray'
}
const COLORS = ['#EEF2FF/#4F46E5','#EDE9FE/#7C3AED','#DCFCE7/#059669','#FFF1F3/#E11D48','#CCFBF1/#0D9488']
function avatarStyle(r) {
  const idx = (r.customer_name?.charCodeAt(0)||0) % COLORS.length
  const [bg, color] = COLORS[idx].split('/')
  return { background: bg, color }
}
function initials(n) { return (n||'?').split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase() }
function fmtDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'2-digit'})
}
function timeAgo(d) {
  if (!d) return ''
  const diff = Math.round((new Date()-new Date(d))/60000)
  if (diff<60) return diff+'m ago'; if (diff<1440) return Math.round(diff/60)+'h ago'
  return Math.round(diff/1440)+'d ago'
}

defineExpose({ loadCustomer })
</script>

<style scoped>
.page{padding:28px 32px;max-width:1400px}
.search-hero{max-width:600px;margin:80px auto;text-align:center}.hero-icon{font-size:52px;color:#0D9488;font-variation-settings:'FILL' 1;display:block;margin-bottom:14px;font-family:'Material Symbols Rounded'}.sh-title{font-size:26px;font-weight:800;color:#1C1C1E;margin:0 0 8px}.sh-sub{font-size:14px;color:#8B8B85;margin:0 0 24px}.sh-input-wrap{display:flex;align-items:center;gap:10px;background:#fff;border:1.5px solid #ECECE8;border-radius:14px;padding:10px 16px;margin-bottom:16px}.sh-input{flex:1;border:none;outline:none;font-size:15px;font-family:inherit}
.results-list{background:#fff;border:1px solid #ECECE8;border-radius:14px;overflow:hidden;text-align:left}.result-row{display:flex;align-items:center;gap:13px;padding:14px 18px;border-bottom:1px solid #F4F4F1;cursor:pointer;transition:background .15s}.result-row:hover{background:#FAFAF8}.result-row:last-child{border-bottom:none}.r-avatar{width:38px;height:38px;border-radius:11px;font-size:14px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}.r-name{font-size:14px;font-weight:700;color:#1C1C1E}.r-meta{font-size:11.5px;color:#9A9A93}.r-arrow{color:#C4C4BD;font-size:20px;margin-left:auto}.no-results{font-size:13px;color:#A1A19B;text-align:center;padding:20px}
.page-header{display:flex;align-items:center;gap:14px;margin-bottom:20px}.breadcrumb{display:flex;align-items:center;gap:6px;font-size:12px;color:#9A9A93;cursor:pointer;font-weight:600}.page-title{font-size:24px;font-weight:800;color:#1C1C1E;margin:0;flex:1}
.c360-layout{display:grid;grid-template-columns:420px 1fr;gap:16px;align-items:start}.c360-left,.c360-right{display:flex;flex-direction:column;gap:14px}
.card{background:#fff;border:1px solid #ECECE8;border-radius:16px;padding:20px}.card-title{display:flex;align-items:center;gap:8px;font-size:14px;font-weight:800;color:#1C1C1E;margin-bottom:16px}.card-title .ms{font-size:17px;color:#0D9488;font-variation-settings:'FILL' 1}
.profile-head{display:flex;align-items:flex-start;gap:14px;margin-bottom:18px}.profile-avatar{width:52px;height:52px;border-radius:14px;background:linear-gradient(140deg,#0D9488,#15B8A6);color:#fff;font-size:19px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}.profile-name{font-size:17px;font-weight:800;color:#1C1C1E}.profile-phone{font-size:13px;color:#8B8B85;margin-top:2px}.profile-addr{font-size:12px;color:#A1A19B;margin-top:1px}.profile-badges{display:flex;flex-wrap:wrap;gap:5px;margin-top:8px}.profile-actions{margin-left:auto;display:flex;gap:7px}
.profile-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding-top:14px;border-top:1px solid #F4F4F1}.ps-item{text-align:center}.ps-n{font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;color:#1C1C1E}.ps-n--red{color:#E11D48}.ps-n--amber{color:#D97706}.ps-n--teal{color:#0D9488}.ps-l{font-size:10px;font-weight:600;color:#A1A19B;margin-top:2px}
.product-list{display:flex;flex-direction:column;gap:10px}.product-card{display:grid;grid-template-columns:auto 1fr auto auto;align-items:center;gap:12px;padding:12px 14px;background:#FAFAF8;border:1px solid #F0F0EC;border-radius:12px}.pc-brand{padding:3px 10px;border-radius:7px;font-size:11px;font-weight:800;background:#EEF2FF;color:#4338CA}.pc-model{font-size:13px;font-weight:700;color:#1C1C1E}.pc-serial{font-size:11px;color:#8B8B85;margin-top:1px}.pc-date{font-size:11px;color:#A1A19B}.pc-warranty{display:flex;align-items:center;gap:6px}.pw--valid .ms{color:#0D9488;font-size:17px;font-variation-settings:'FILL' 1}.pw--expired .ms{color:#E11D48;font-size:17px;font-variation-settings:'FILL' 1}.pw-status{font-size:11px;font-weight:700}.pw--valid .pw-status{color:#0D9488}.pw--expired .pw-status{color:#E11D48}.pw-date{font-size:10px;color:#A1A19B}
.ticket-history{display:flex;flex-direction:column}.th-row{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid #F4F4F1;cursor:pointer;transition:background .1s}.th-row:hover{background:#FAFAF8;padding:12px 8px;border-radius:10px;margin:0 -8px}.th-row:last-child{border-bottom:none}.th-dot{width:8px;height:8px;border-radius:50%;flex:none}.dot--red{background:#E11D48}.dot--amber{background:#D97706}.dot--teal{background:#0D9488}.dot--blue{background:#4F46E5}.dot--gray{background:#BDBDB6}.th-subject{font-size:13.5px;font-weight:700;color:#1C1C1E}.th-meta{font-size:11.5px;color:#9A9A93;margin-top:2px}.th-arr{color:#C4C4BD;margin-left:auto}
.wa-history{display:flex;flex-direction:column;gap:10px;max-height:320px;overflow-y:auto}.wam{max-width:85%;padding:10px 13px;border-radius:12px}.wam--in{align-self:flex-start;background:#F4F4F1;border-bottom-left-radius:4px}.wam--out{align-self:flex-end;background:#F0FDFA;border-bottom-right-radius:4px}.wam-text{font-size:13px;color:#1C1C1E;line-height:1.4}.wam-meta{font-size:10px;color:#A1A19B;margin-top:4px}
.badge{padding:3px 9px;border-radius:7px;font-size:10.5px;font-weight:700;display:inline-flex;align-items:center;gap:4px}.badge--gray{background:#F4F4F1;color:#52525B}.badge--teal{background:#F0FDFA;color:#0D9488}.badge--gold{background:#FFFBEB;color:#92400E}.badge--amber{background:#FFF7ED;color:#D97706}.badge .ms{font-size:12px}
.icon-btn{width:36px;height:36px;border-radius:10px;border:1px solid #ECECE8;background:#F4F4F1;display:flex;align-items:center;justify-content:center;cursor:pointer;text-decoration:none}
.loading-state{padding:60px;text-align:center;display:flex;align-items:center;justify-content:center;gap:10px;color:#9A9A93;font-weight:600}.empty-sm{padding:20px;text-align:center;color:#A1A19B;font-size:13px}
.mono{font-family:'JetBrains Mono',monospace}.text--teal{color:#0D9488;font-weight:600}.full{width:100%;justify-content:center}.mt-10{margin-top:10px}
.btn{display:inline-flex;align-items:center;gap:6px;padding:9px 16px;border-radius:10px;font-size:13px;font-weight:700;border:none;cursor:pointer}.btn--dark{background:#1C1C1E;color:#fff}.btn--teal{background:#0D9488;color:#fff}.btn--outline{background:#fff;border:1px solid #ECECE8;color:#52525B}.btn:disabled{opacity:.5;cursor:not-allowed}
@keyframes spin{to{transform:rotate(360deg)}}.spin{display:inline-block;animation:spin 1s linear infinite}
.ms{font-family:'Material Symbols Rounded';font-weight:normal;font-style:normal;line-height:1;font-size:18px}
</style>
