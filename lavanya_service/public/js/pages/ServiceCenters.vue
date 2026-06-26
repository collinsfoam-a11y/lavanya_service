<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Service Centers & Brands</h1>
        <p class="page-sub">Master records — brands, service centers, technicians</p>
      </div>
      <div class="header-actions">
        <button v-for="t in TABS" :key="t.key"
          class="btn" :class="activeTab===t.key?'btn--dark':'btn--outline'"
          @click="activeTab=t.key">
          <span class="ms">{{ t.icon }}</span> {{ t.label }}
        </button>
        <button class="btn btn--teal" @click="openModal">
          <span class="ms">add</span> Add New
        </button>
      </div>
    </div>

    <!-- BRANDS -->
    <div v-if="activeTab==='brands'">
      <div class="toolbar"><div class="search-box"><span class="ms">search</span><input v-model="q.brands" class="search-input" placeholder="Search brands…" /></div></div>
      <div v-if="loading" class="loading-state"><span class="ms spin">sync</span> Loading…</div>
      <div v-else class="card-grid">
        <div v-for="b in filteredBrands" :key="b.name" class="brand-card">
          <div class="bc-head">
            <div class="bc-logo">{{ b.logo_emoji || '🏷️' }}</div>
            <div class="bc-info"><div class="bc-name">{{ b.brand_name }}</div><div class="bc-cats">{{ b.product_categories }}</div></div>
            <span class="pill" :class="b.is_active?'pill--on':'pill--off'">{{ b.is_active?'Active':'Inactive' }}</span>
          </div>
          <div class="bc-contacts">
            <div class="cr"><span class="ms">phone</span> {{ b.toll_free_number||'—' }}</div>
            <div class="cr"><span class="ms">chat</span> {{ b.whatsapp_number||'—' }}</div>
            <div class="cr"><span class="ms">mail</span> {{ b.escalation_email||'—' }}</div>
          </div>
          <div class="bc-footer">
            <div class="bf-stat"><span class="bfs-n">{{ brandTickets(b.name) }}</span><span class="bfs-l">Open</span></div>
            <div class="bf-stat"><span class="bfs-n">{{ b.default_sla_days||2 }}d</span><span class="bfs-l">SLA</span></div>
            <div class="bf-actions">
              <button class="icon-btn" @click="editItem('brand', b)"><span class="ms">edit</span></button>
              <button v-if="b.auto_email_enabled||b.auto_wa_enabled" class="icon-btn icon-btn--auto" title="Auto-reg enabled" @click="testAutoReg(b)">
                <span class="ms">auto_awesome</span>
              </button>
            </div>
          </div>
        </div>
        <div class="brand-card brand-card--add" @click="openModal('Brand')">
          <span class="ms add-icon">add_circle</span><div class="add-label">Add Brand</div>
        </div>
      </div>
    </div>

    <!-- SERVICE CENTERS -->
    <div v-if="activeTab==='centers'">
      <div class="toolbar">
        <div class="search-box"><span class="ms">search</span><input v-model="q.centers" class="search-input" placeholder="Search service centers…" /></div>
        <select v-model="q.centerBrand" class="select-ctrl"><option value="">All Brands</option><option v-for="b in brands" :key="b.name" :value="b.name">{{ b.brand_name }}</option></select>
      </div>
      <div v-if="loading" class="loading-state"><span class="ms spin">sync</span> Loading…</div>
      <div v-else class="sc-table">
        <div class="sc-head">
          <span>Name</span><span>Brand</span><span>Area</span><span>Phone</span>
          <span>SLA</span><span>Open</span><span>On-time%</span><span>Status</span><span></span>
        </div>
        <div v-for="sc in filteredCenters" :key="sc.name" class="sc-row">
          <div><div class="sc-name">{{ sc.service_center_name }}</div><div class="sc-cp">{{ sc.contact_person }}</div></div>
          <div><span class="brand-pill">{{ sc.brand }}</span></div>
          <div>{{ sc.area_coverage }}</div>
          <div><div class="sc-phone">{{ sc.phone }}</div></div>
          <div><span class="sla-pill" :class="sc.sla_days<=2?'sla--fast':sc.sla_days<=4?'sla--ok':'sla--slow'">{{ sc.sla_days }}d</span></div>
          <div class="mono">{{ sc.open_count || 0 }}</div>
          <div>
            <div class="perf-wrap"><div class="perf-bar" :style="{ width: (sc.performance_pct||0)+'%', background: (sc.performance_pct||0)>=80?'#0D9488':(sc.performance_pct||0)>=60?'#D97706':'#E11D48' }"></div></div>
            <span class="perf-val">{{ sc.performance_pct||0 }}%</span>
          </div>
          <div><span class="pill" :class="sc.is_active?'pill--on':'pill--off'">{{ sc.is_active?'Active':'Inactive' }}</span></div>
          <div class="sc-actions">
            <button class="icon-btn" @click="editItem('center',sc)"><span class="ms">edit</span></button>
            <a class="icon-btn" :href="'tel:'+sc.phone"><span class="ms">phone</span></a>
          </div>
        </div>
        <div v-if="!filteredCenters.length" class="dt-empty">No service centers found</div>
      </div>
    </div>

    <!-- TECHNICIANS -->
    <div v-if="activeTab==='technicians'">
      <div class="toolbar">
        <div class="search-box"><span class="ms">search</span><input v-model="q.techs" class="search-input" placeholder="Search technicians…" /></div>
        <select v-model="q.techSkill" class="select-ctrl"><option value="">All Skills</option><option>AC / Refrigerator</option><option>TV / Electronics</option><option>Washing Machine</option></select>
      </div>
      <div v-if="loading" class="loading-state"><span class="ms spin">sync</span> Loading…</div>
      <div v-else class="tech-grid">
        <div v-for="t in filteredTechs" :key="t.name" class="tech-card">
          <div class="tc-head">
            <div class="tca">{{ initials(t.technician_name) }}</div>
            <div class="tc-info"><div class="tc-name">{{ t.technician_name }}</div><div class="tc-area">{{ t.area_coverage }}</div></div>
            <span class="pill" :class="t.is_available?'pill--on':'pill--busy'">{{ t.is_available?'Available':'Busy' }}</span>
          </div>
          <div class="tech-skills">
            <span v-for="s in (t.skill_categories||'').split(',')" :key="s" class="skill-chip">{{ s.trim() }}</span>
          </div>
          <div class="tech-metrics">
            <div class="tm"><div class="tm-n">{{ t.open_jobs||0 }}</div><div class="tm-l">Open jobs</div></div>
            <div class="tm"><div class="tm-n text--teal">★ {{ t.rating||0 }}</div><div class="tm-l">Rating</div></div>
            <div class="tm"><div class="tm-n">₹{{ t.visit_charge||0 }}</div><div class="tm-l">Visit</div></div>
          </div>
          <div class="tc-footer">
            <a class="btn btn--outline btn--sm" :href="'tel:'+t.phone"><span class="ms">phone</span> {{ t.phone }}</a>
            <button class="btn btn--teal btn--sm" @click="assignTech(t)"><span class="ms">assignment_ind</span> Assign</button>
          </div>
        </div>
        <div class="tech-card tech-card--add" @click="openModal('Technician')">
          <span class="ms add-icon">add_circle</span><div class="add-label">Add Technician</div>
        </div>
      </div>
    </div>

    <!-- ADD/EDIT MODAL -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal=false">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">{{ modalMode==='add'?'Add':'Edit' }} {{ modalEntity }}</div>
          <button class="icon-btn" @click="showModal=false"><span class="ms">close</span></button>
        </div>
        <div class="modal-body">
          <template v-if="modalEntity==='Brand'">
            <div class="field"><label>Brand Name <span class="req">*</span></label><input v-model="mf.brand_name" class="input" /></div>
            <div class="field"><label>Logo Emoji</label><input v-model="mf.logo_emoji" class="input" placeholder="🔵" /></div>
            <div class="field field--full"><label>Toll-free Number</label><input v-model="mf.toll_free_number" class="input" /></div>
            <div class="field field--full"><label>WhatsApp Number</label><input v-model="mf.whatsapp_number" class="input" /></div>
            <div class="field field--full"><label>Escalation Email</label><input v-model="mf.escalation_email" class="input" type="email" /></div>
            <div class="field"><label>Default SLA (days)</label><input v-model.number="mf.default_sla_days" class="input" type="number" /></div>
            <div class="field"><label>Auto-reg Email</label><div class="toggle-mini" @click="mf.auto_email_enabled=!mf.auto_email_enabled"><span class="ms">{{ mf.auto_email_enabled?'toggle_on':'toggle_off' }}</span> {{ mf.auto_email_enabled?'ON':'OFF' }}</div></div>
            <div class="field"><label>Auto-reg WhatsApp</label><div class="toggle-mini" @click="mf.auto_wa_enabled=!mf.auto_wa_enabled"><span class="ms">{{ mf.auto_wa_enabled?'toggle_on':'toggle_off' }}</span> {{ mf.auto_wa_enabled?'ON':'OFF' }}</div></div>
          </template>
          <template v-else-if="modalEntity==='Service Center'">
            <div class="field field--full"><label>Name <span class="req">*</span></label><input v-model="mf.service_center_name" class="input" /></div>
            <div class="field"><label>Brand <span class="req">*</span></label><select v-model="mf.brand" class="select full"><option value="">Select…</option><option v-for="b in brands" :key="b.name" :value="b.name">{{ b.brand_name }}</option></select></div>
            <div class="field"><label>Area Coverage</label><input v-model="mf.area_coverage" class="input" /></div>
            <div class="field"><label>Phone</label><input v-model="mf.phone" class="input" /></div>
            <div class="field"><label>Contact Person</label><input v-model="mf.contact_person" class="input" /></div>
            <div class="field"><label>SLA (days)</label><input v-model.number="mf.sla_days" class="input" type="number" /></div>
          </template>
          <template v-else>
            <div class="field"><label>Name <span class="req">*</span></label><input v-model="mf.technician_name" class="input" /></div>
            <div class="field"><label>Phone <span class="req">*</span></label><input v-model="mf.phone" class="input" /></div>
            <div class="field field--full"><label>Skill Categories</label><input v-model="mf.skill_categories" class="input" placeholder="AC, Refrigerator, Washing Machine" /></div>
            <div class="field"><label>Area Coverage</label><input v-model="mf.area_coverage" class="input" /></div>
            <div class="field"><label>Visit Charge (₹)</label><input v-model.number="mf.visit_charge" class="input" type="number" /></div>
          </template>
        </div>
        <div class="modal-footer">
          <button class="btn btn--outline" @click="showModal=false">Cancel</button>
          <button class="btn btn--teal" @click="saveModal" :disabled="saving">
            <span v-if="saving" class="ms spin">sync</span>
            <span v-else class="ms">save</span> {{ saving?'Saving…':'Save' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { navigate, showAlert, showError } from '../composables/frappe.js'
import { frappeCall } from '../composables/frappe.js'

const props = defineProps({ frappePage: Object })
const loading   = ref(false)
const saving    = ref(false)
const showModal = ref(false)
const modalEntity = ref('Brand')
const modalMode   = ref('add')
const activeTab   = ref('brands')
const brands    = ref([])
const centers   = ref([])
const techs     = ref([])
const ticketCounts = ref({})
const mf = ref({})

const TABS = [
  { key:'brands',     label:'Brands',          icon:'verified' },
  { key:'centers',    label:'Service Centers',  icon:'business' },
  { key:'technicians',label:'Technicians',      icon:'engineering' },
]

const q = ref({ brands:'', centers:'', centerBrand:'', techs:'', techSkill:'' })

const filteredBrands  = computed(() => brands.value.filter(b => !q.value.brands || b.brand_name?.toLowerCase().includes(q.value.brands.toLowerCase())))
const filteredCenters = computed(() => centers.value.filter(sc => {
  return (!q.value.centers || sc.service_center_name?.toLowerCase().includes(q.value.centers.toLowerCase()))
    && (!q.value.centerBrand || sc.brand === q.value.centerBrand)
}))
const filteredTechs = computed(() => techs.value.filter(t =>
  (!q.value.techs || t.technician_name?.toLowerCase().includes(q.value.techs.toLowerCase()))
  && (!q.value.techSkill || (t.skill_categories||'').toLowerCase().includes(q.value.techSkill.toLowerCase()))
))

function brandTickets(brand) { return ticketCounts.value[brand] || 0 }

async function loadAll() {
  loading.value = true
  try {
    const [br, sc, tech] = await Promise.all([
      frappeCall('frappe.client.get_list', { doctype:'Lavanya Brand Master', fields:['*'], limit:50 }),
      frappeCall('frappe.client.get_list', { doctype:'Lavanya Service Center', fields:['*'], limit:100 }),
      frappeCall('frappe.client.get_list', { doctype:'Lavanya Technician', fields:['*'], limit:100 }),
    ])
    brands.value  = br || []
    centers.value = sc || []
    techs.value   = tech || []
  } finally { loading.value = false }
}

function openModal(entity) {
  modalEntity.value = entity || 'Brand'
  modalMode.value   = 'add'
  mf.value = { default_sla_days:2, sla_days:2, auto_email_enabled:0, auto_wa_enabled:0 }
  showModal.value = true
}

function editItem(type, item) {
  modalEntity.value = type==='brand' ? 'Brand' : type==='center' ? 'Service Center' : 'Technician'
  modalMode.value   = 'edit'
  mf.value = { ...item }
  showModal.value = true
}

async function saveModal() {
  saving.value = true
  try {
    const docMap = { 'Brand':'Lavanya Brand Master','Service Center':'Lavanya Service Center','Technician':'Lavanya Technician' }
    const dt = docMap[modalEntity.value]
    if (modalMode.value === 'add') {
      await frappeCall('frappe.client.insert', { doc: { doctype: dt, ...mf.value } })
      showAlert(modalEntity.value + ' added successfully')
    } else {
      await frappeCall('frappe.client.save', { doc: { doctype: dt, ...mf.value } })
      showAlert(modalEntity.value + ' saved')
    }
    showModal.value = false
    await loadAll()
  } catch(e) { showError(e.message || 'Failed to save') }
  finally { saving.value = false }
}

function testAutoReg(b) { showAlert('Dry-run: Auto-registration test for ' + b.brand_name + ' — no live messages', 'blue') }
function assignTech(t)  { showAlert('Assign ' + t.technician_name + ' via the ticket detail page', 'blue') }
function initials(n)    { return (n||'?').split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase() }

defineExpose({ setTab: (t) => { activeTab.value = t }, openAddModal: () => openModal() })

onMounted(loadAll)
</script>

<style scoped>
.page{padding:28px 32px;max-width:1600px}.page-header{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:22px;flex-wrap:wrap;gap:12px}.page-title{font-size:24px;font-weight:800;color:#1C1C1E;letter-spacing:-0.02em;margin:0}.page-sub{font-size:13px;color:#8B8B85;margin:4px 0 0}.header-actions{display:flex;gap:8px;flex-wrap:wrap}
.toolbar{display:flex;gap:8px;margin-bottom:16px}.search-box{flex:1;display:flex;align-items:center;gap:8px;height:42px;padding:0 16px;border-radius:12px;background:#fff;border:1px solid #ECECE8}.search-input{flex:1;border:none;outline:none;font-size:13px;font-family:inherit;background:transparent}.select-ctrl{height:42px;padding:0 14px;border-radius:12px;border:1px solid #ECECE8;font-size:13px;font-family:inherit;background:#fff}
.card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.brand-card{background:#fff;border:1px solid #ECECE8;border-radius:16px;padding:18px;cursor:pointer;transition:box-shadow .15s,transform .1s}.brand-card:hover{box-shadow:0 6px 24px -8px rgba(17,17,26,.14);transform:translateY(-2px)}.brand-card--add{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;border-style:dashed;background:#FAFAF8;min-height:180px}
.bc-head{display:flex;align-items:center;gap:11px;margin-bottom:14px}.bc-logo{font-size:28px;flex:none}.bc-name{font-size:15px;font-weight:800;color:#1C1C1E}.bc-cats{font-size:10.5px;color:#9A9A93;margin-top:2px}
.bc-contacts{display:flex;flex-direction:column;gap:5px;margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid #F4F4F1}.cr{display:flex;align-items:center;gap:7px;font-size:12px;color:#6B6B66}.cr .ms{font-size:15px;color:#A1A19B}
.bc-footer{display:flex;align-items:center;gap:8px}.bf-stat{flex:1;text-align:center}.bfs-n{font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700;color:#1C1C1E;display:block}.bfs-l{font-size:9.5px;color:#A1A19B;font-weight:600}.bf-actions{display:flex;gap:5px;margin-left:auto}
.sc-table{background:#fff;border:1px solid #ECECE8;border-radius:16px;overflow:hidden}.sc-head{display:grid;grid-template-columns:200px 90px 100px 130px 70px 50px 120px 80px 60px;gap:8px;padding:10px 18px;background:#F4F4F1;font-size:10.5px;font-weight:700;color:#9A9A93;text-transform:uppercase;letter-spacing:.04em}.sc-row{display:grid;grid-template-columns:200px 90px 100px 130px 70px 50px 120px 80px 60px;gap:8px;padding:14px 18px;border-bottom:1px solid #F4F4F1;align-items:center;font-size:13px;transition:background .1s}.sc-row:hover{background:#FAFAF8}.sc-row:last-child{border-bottom:none}.sc-name{font-size:13px;font-weight:700;color:#1C1C1E}.sc-cp{font-size:11px;color:#9A9A93}.sc-phone{font-size:12px;color:#3F3F46}.sc-actions{display:flex;gap:4px}.brand-pill{padding:3px 9px;border-radius:7px;background:#EEF2FF;color:#4338CA;font-size:11px;font-weight:700}.sla-pill{padding:3px 9px;border-radius:7px;font-size:11px;font-weight:700}.sla--fast{background:#F0FDFA;color:#0D9488}.sla--ok{background:#FFF7ED;color:#D97706}.sla--slow{background:#FFF1F3;color:#E11D48}
.perf-wrap{width:80px;height:6px;background:#F0F0EC;border-radius:3px;overflow:hidden;margin-bottom:2px}.perf-bar{height:100%;border-radius:3px}.perf-val{font-size:11px;font-weight:700;color:#6B6B66}
.tech-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}.tech-card{background:#fff;border:1px solid #ECECE8;border-radius:16px;padding:18px}.tech-card--add{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:10px;border-style:dashed;background:#FAFAF8;min-height:200px;cursor:pointer}
.tc-head{display:flex;align-items:center;gap:12px;margin-bottom:12px}.tca{width:42px;height:42px;border-radius:50%;background:linear-gradient(140deg,#0D9488,#15B8A6);color:#fff;font-size:14px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}.tc-name{font-size:14px;font-weight:800;color:#1C1C1E}.tc-area{font-size:11.5px;color:#8B8B85;margin-top:2px}
.tech-skills{display:flex;flex-wrap:wrap;gap:5px;margin-bottom:14px}.skill-chip{padding:3px 9px;border-radius:7px;background:#F0FDFA;color:#0F766E;font-size:11px;font-weight:700}
.tech-metrics{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;margin-bottom:14px;padding:12px 0;border-top:1px solid #F4F4F1;border-bottom:1px solid #F4F4F1}.tm{text-align:center}.tm-n{font-family:'JetBrains Mono',monospace;font-size:16px;font-weight:700;color:#1C1C1E}.tm-l{font-size:9.5px;color:#A1A19B;font-weight:600;margin-top:2px}.tc-footer{display:flex;gap:8px}
.pill{padding:3px 9px;border-radius:7px;font-size:11px;font-weight:700}.pill--on{background:#F0FDFA;color:#0D9488}.pill--off{background:#F4F4F1;color:#9A9A93}.pill--busy{background:#FFF7ED;color:#D97706}
.add-icon{font-size:32px;color:#0D9488;font-variation-settings:'FILL' 1;font-family:'Material Symbols Rounded'}.add-label{font-size:13px;font-weight:700;color:#0D9488}
.modal-overlay{position:fixed;inset:0;background:rgba(17,17,26,.4);display:flex;align-items:center;justify-content:center;z-index:100}.modal{background:#fff;border-radius:20px;width:560px;max-height:90vh;overflow-y:auto;box-shadow:0 24px 64px -12px rgba(17,17,26,.3)}.modal-header{display:flex;align-items:center;justify-content:space-between;padding:22px 24px 0}.modal-title{font-size:17px;font-weight:800;color:#1C1C1E}.modal-body{padding:20px 24px;display:grid;grid-template-columns:1fr 1fr;gap:14px}.modal-footer{padding:0 24px 22px;display:flex;justify-content:flex-end;gap:10px}
.field{display:flex;flex-direction:column;gap:6px}.field--full{grid-column:1/-1}label{font-size:12px;font-weight:700;color:#52525B}.req{color:#E11D48}.input{height:40px;border-radius:11px;border:1px solid #ECECE8;padding:0 14px;font-size:13px;font-family:inherit;outline:none;background:#FAFAF8}.input:focus{border-color:#0D9488;background:#fff}.select,.full{height:40px;border-radius:11px;border:1px solid #ECECE8;padding:0 14px;font-size:13px;font-family:inherit;background:#FAFAF8;width:100%}
.toggle-mini{display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:700;cursor:pointer;color:#6B6B66}.toggle-mini .ms{font-size:24px;color:#0D9488}
.icon-btn{width:32px;height:32px;border-radius:9px;border:1px solid #ECECE8;background:#F4F4F1;display:flex;align-items:center;justify-content:center;cursor:pointer;text-decoration:none}.icon-btn--auto{background:#F5F3FF;border-color:#DDD6FE}.icon-btn--auto .ms{color:#7C3AED}
.loading-state{padding:48px;text-align:center;display:flex;align-items:center;justify-content:center;gap:10px;color:#9A9A93;font-weight:600}.dt-empty{padding:24px;text-align:center;color:#A1A19B;font-size:13px}
.mono{font-family:'JetBrains Mono',monospace}.text--teal{color:#0D9488;font-weight:700}
.btn{display:inline-flex;align-items:center;gap:6px;padding:9px 16px;border-radius:10px;font-size:13px;font-weight:700;border:none;cursor:pointer;font-family:inherit}.btn--sm{padding:6px 12px;font-size:12px;flex:1;justify-content:center}.btn--dark{background:#1C1C1E;color:#fff}.btn--teal{background:#0D9488;color:#fff}.btn--outline{background:#fff;border:1px solid #ECECE8;color:#52525B}.btn:disabled{opacity:.5;cursor:not-allowed}
@keyframes spin{to{transform:rotate(360deg)}}.spin{display:inline-block;animation:spin 1s linear infinite}
.ms{font-family:'Material Symbols Rounded';font-weight:normal;font-style:normal;line-height:1;font-size:18px}
</style>
