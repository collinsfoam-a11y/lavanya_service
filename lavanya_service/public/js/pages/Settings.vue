<template>
  <div class="page">
    <div class="page-header">
      <div><h1 class="page-title">Settings</h1><p class="page-sub">Manager governance · Safety locks · Integration config</p></div>
      <div class="live-status-strip">
        <div v-for="lock in quickLocks" :key="lock.key" class="ls-item" :class="lock.safe?'ls--safe':'ls--risk'">
          <span class="ls-dot"></span>{{ lock.label }}: <strong>{{ lock.display }}</strong>
        </div>
      </div>
    </div>

    <div v-if="loading" class="loading-state"><span class="ms spin">sync</span> Loading settings…</div>

    <template v-else-if="form">
      <div class="tab-nav">
        <div v-for="t in tabs" :key="t.key" class="tab" :class="{ 'tab--active': activeTab===t.key }" @click="activeTab=t.key">
          <span class="ms">{{ t.icon }}</span> {{ t.label }}
        </div>
      </div>

      <!-- SAFETY LOCKS -->
      <div v-if="activeTab==='safety'" class="settings-body">
        <div class="settings-section">
          <div class="ss-header"><span class="ms">shield</span><div><div class="ss-title">Safety Locks</div><div class="ss-desc">Defaults protect customers and financial data. Only Lavanya Owner can enable dangerous features.</div></div></div>
          <div class="lock-grid">
            <div v-for="lock in safetyLocks" :key="lock.key" class="lock-card" :class="{ 'lock-card--danger': lock.danger }">
              <div class="lc-left">
                <div class="lc-icon" :class="form[lock.key]?'lci--on':'lci--off'">
                  <span class="ms">{{ lock.icon }}</span>
                </div>
                <div class="lc-info">
                  <div class="lc-name">{{ lock.label }}</div>
                  <div class="lc-desc">{{ lock.desc }}</div>
                  <div v-if="lock.danger" class="lc-warning"><span class="ms">warning</span> {{ lock.warning }}</div>
                </div>
              </div>
              <div class="lc-right">
                <div class="toggle-wrap" :class="{ 'tw--disabled': lock.ownerOnly && !isOwner }" @click="toggleLock(lock)">
                  <div class="toggle" :class="form[lock.key]?'toggle--on':'toggle--off'"><div class="toggle-thumb"></div></div>
                  <span class="tl" :class="form[lock.key]?'tl--on':'tl--off'">{{ form[lock.key]?'ENABLED':'DISABLED' }}</span>
                </div>
                <div v-if="lock.ownerOnly && !isOwner" class="owner-only"><span class="ms">lock</span> Owner only</div>
              </div>
            </div>
          </div>
          <div class="danger-note"><span class="ms">info</span> Dangerous settings are red-bordered. Changing them creates an audit log entry. Only Lavanya Owner can enable them.</div>
        </div>
      </div>

      <!-- FOLLOW-UP RULES -->
      <div v-if="activeTab==='followup'" class="settings-body">
        <div class="settings-section">
          <div class="ss-header"><span class="ms">schedule</span><div><div class="ss-title">SLA & Follow-up Rules</div><div class="ss-desc">Configure follow-up cadences and escalation thresholds.</div></div></div>
          <div class="field-grid">
            <div class="field"><label>Brand Warranty SLA (days)</label><input v-model.number="form.brand_sla_days" type="number" min="1" max="14" class="input" /><div class="field-hint">Days before first follow-up after brand registration</div></div>
            <div class="field"><label>Part Pending Follow-up (days)</label><input v-model.number="form.part_sla_days" type="number" min="1" max="14" class="input" /></div>
            <div class="field"><label>Customer Confirmation SLA (days)</label><input v-model.number="form.confirmation_sla_days" type="number" min="1" max="7" class="input" /></div>
            <div class="field"><label>Auto-escalate After (days)</label><input v-model.number="form.auto_escalate_days" type="number" min="1" max="10" class="input" /></div>
            <div class="field"><label>Min Attempts (No-response closure)</label><input v-model.number="form.non_response_attempts" type="number" min="2" max="5" class="input" /></div>
            <div class="field">
              <label>Business Hours</label>
              <div class="time-range"><input v-model="form.biz_start" type="time" class="input" /><span class="time-sep">to</span><input v-model="form.biz_end" type="time" class="input" /></div>
            </div>
          </div>
        </div>
      </div>

      <!-- WHATSAPP BOT -->
      <div v-if="activeTab==='whatsapp'" class="settings-body">
        <div class="settings-section">
          <div class="ss-header"><span class="ms">smart_toy</span><div><div class="ss-title">WhatsApp Bot Settings</div><div class="ss-desc">Configure bot mode, webhook and API token.</div></div></div>
          <div class="bot-modes">
            <div v-for="m in botModes" :key="m.key"
              class="bm-card" :class="{ 'bm--active': form.bot_mode===m.key, 'bm--locked': m.locked && !isOwner }"
              @click="(!m.locked||isOwner) && (form.bot_mode=m.key)">
              <span class="ms bm-icon">{{ m.icon }}</span>
              <div class="bm-name">{{ m.label }}</div>
              <div class="bm-desc">{{ m.desc }}</div>
              <div v-if="m.locked" class="bm-lock"><span class="ms">lock</span> Owner</div>
            </div>
          </div>
          <div class="field-grid mt-16">
            <div class="field field--full"><label>Webhook URL</label><input v-model="form.wa_webhook_url" type="url" class="input" placeholder="https://…/webhook" /></div>
            <div class="field field--full">
              <label>API Token</label>
              <div class="secret-field">
                <input v-model="form.wa_api_token" :type="showToken?'text':'password'" class="input" />
                <button class="icon-btn" @click="showToken=!showToken"><span class="ms">{{ showToken?'visibility_off':'visibility' }}</span></button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- INTEGRATIONS -->
      <div v-if="activeTab==='integrations'" class="settings-body">
        <div class="settings-section">
          <div class="ss-header"><span class="ms">cable</span><div><div class="ss-title">Integrations</div><div class="ss-desc">Connect to Frappe CRM and ERPNext.</div></div></div>
          <div class="intg-list">
            <div v-for="intg in integrations" :key="intg.key" class="intg-card">
              <div class="intg-logo">{{ intg.logo }}</div>
              <div class="intg-info"><div class="intg-name">{{ intg.name }}</div><div class="intg-desc">{{ intg.desc }}</div><div v-if="intg.warning" class="intg-warn"><span class="ms">warning</span>{{ intg.warning }}</div></div>
              <div class="intg-right">
                <div class="toggle-wrap" @click="form[intg.key]=!form[intg.key]">
                  <div class="toggle" :class="form[intg.key]?'toggle--on':'toggle--off'"><div class="toggle-thumb"></div></div>
                </div>
                <span class="intg-status" :class="form[intg.key]?'is--on':'is--off'">{{ form[intg.key]?'Connected':'Disabled' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Save bar -->
      <div class="save-bar" v-if="isDirty">
        <span class="ms" style="color:#D97706;font-size:20px">edit</span>
        <span>You have unsaved changes</span>
        <button class="btn btn--ghost" @click="discard">Discard</button>
        <button class="btn btn--teal" @click="saveSettings" :disabled="saving">
          <span v-if="saving" class="ms spin">sync</span>
          <span v-else class="ms">save</span> {{ saving?'Saving…':'Save Settings' }}
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useSettings } from '../composables/useDashboard.js'
import { hasRole, showAlert, showError } from '../composables/frappe.js'

const props = defineProps({ frappePage: Object, isOwner: { type: Boolean, default: false } })

const activeTab = ref('safety')
const showToken = ref(false)
const saving    = ref(false)
const form      = ref(null)
const original  = ref(null)
const isDirty   = computed(() => form.value && JSON.stringify(form.value) !== JSON.stringify(original.value))

const { settings, loading, save, reset } = useSettings()

watch(settings, (s) => {
  if (s && !form.value) {
    form.value     = JSON.parse(JSON.stringify(s))
    original.value = JSON.parse(JSON.stringify(s))
  }
}, { immediate: true })

const isOwner = computed(() => props.isOwner || hasRole('Lavanya Owner'))

const tabs = [
  { key:'safety',       label:'Safety Locks',   icon:'shield' },
  { key:'followup',     label:'Follow-up Rules', icon:'schedule' },
  { key:'whatsapp',     label:'WhatsApp Bot',    icon:'smart_toy' },
  { key:'integrations', label:'Integrations',    icon:'cable' },
]

const safetyLocks = [
  { key:'closure_guard',         label:'Closure Guard',            icon:'shield',      desc:'Blocks closure without customer confirmation.',      ownerOnly:false, danger:false, warning:'' },
  { key:'customer_confirmation', label:'Customer Confirmation Required', icon:'how_to_reg',desc:'Customer must confirm before closing.',           ownerOnly:false, danger:false, warning:'' },
  { key:'live_whatsapp',         label:'Live WhatsApp Sending',    icon:'send',        desc:'Sends real WhatsApp messages. Keep OFF until tested.', ownerOnly:true, danger:true, warning:'Live messages cannot be unsent. Requires thorough testing.' },
  { key:'erp_posting',           label:'ERP Auto-posting',         icon:'receipt_long',desc:'Posts entries to ERPNext automatically.',            ownerOnly:true, danger:true, warning:'Wrong ERP entries require manual correction.' },
  { key:'auto_closure',          label:'Automatic Ticket Closure', icon:'close',       desc:'Closes tickets without staff action.',               ownerOnly:true, danger:true, warning:'Bypasses closure guard — only after pilot testing.' },
  { key:'penalty',               label:'Penalty Application',      icon:'money_off',   desc:'Applies financial penalties automatically.',         ownerOnly:true, danger:true, warning:'Financial penalties cannot be easily reversed.' },
]

const quickLocks = computed(() => [
  { key:'live_whatsapp', label:'Live WA',      display: form.value?.live_whatsapp  ?'ON':'OFF', safe: !form.value?.live_whatsapp },
  { key:'erp_posting',   label:'ERP Post',     display: form.value?.erp_posting    ?'ON':'OFF', safe: !form.value?.erp_posting },
  { key:'auto_closure',  label:'Auto-close',   display: form.value?.auto_closure   ?'ON':'OFF', safe: !form.value?.auto_closure },
  { key:'closure_guard', label:'Closure Guard',display: form.value?.closure_guard  ?'ON':'OFF', safe:  !!form.value?.closure_guard },
])

const botModes = [
  { key:'disabled',        label:'Disabled',       icon:'block',                   desc:'WhatsApp bot completely off.',                          locked:false },
  { key:'dry_run',         label:'Dry-run',         icon:'science',                 desc:'Receives messages. No auto-sends. Staff reviews only.', locked:false },
  { key:'staff_approved',  label:'Staff Approved',  icon:'supervised_user_circle',  desc:'Bot drafts. Staff approves each send.',                 locked:true },
  { key:'controlled_auto', label:'Controlled Auto', icon:'smart_toy',               desc:'Auto-sends approved templates. Full audit trail.',      locked:true },
]

const integrations = [
  { key:'frappe_crm', name:'Frappe CRM', logo:'🤝', desc:'Link tickets to CRM leads and deals. Create CRM opportunities from service cases.', warning:'' },
  { key:'erpnext',    name:'ERPNext',    logo:'📊', desc:'Link to invoices and stock. ERP posting disabled by default — see Safety Locks.', warning:'ERP posting must also be enabled in Safety Locks.' },
]

function toggleLock(lock) {
  if (lock.ownerOnly && !isOwner.value) return
  form.value[lock.key] = !form.value[lock.key]
}

async function saveSettings() {
  saving.value = true
  try {
    await save(form.value)
    original.value = JSON.parse(JSON.stringify(form.value))
    showAlert('Settings saved')
  } catch(e) { showError(e.message || 'Failed to save settings') }
  finally { saving.value = false }
}

function discard() {
  form.value = JSON.parse(JSON.stringify(original.value))
}

async function resetDefaults() {
  try {
    await reset()
    showAlert('Settings reset to safe defaults', 'orange')
    window.location.reload()
  } catch(e) { showError(e.message || 'Failed to reset') }
}

defineExpose({ saveSettings, resetDefaults })
</script>

<style scoped>
.page{padding:28px 32px;max-width:1100px}.page-header{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:22px;flex-wrap:wrap;gap:12px}.page-title{font-size:24px;font-weight:800;color:#1C1C1E;letter-spacing:-0.02em;margin:0}.page-sub{font-size:13px;color:#8B8B85;margin:4px 0 0}
.live-status-strip{display:flex;gap:8px;flex-wrap:wrap}.ls-item{display:flex;align-items:center;gap:5px;padding:5px 11px;border-radius:8px;font-size:11.5px;font-weight:600}.ls--safe{background:#F0FDFA;color:#0F766E}.ls--risk{background:#FFF1F3;color:#E11D48}.ls-dot{width:6px;height:6px;border-radius:50%;background:currentColor}
.tab-nav{display:flex;gap:4px;background:#fff;border:1px solid #ECECE8;border-radius:14px;padding:6px;margin-bottom:20px;flex-wrap:wrap}.tab{display:flex;align-items:center;gap:7px;padding:9px 16px;border-radius:10px;font-size:13px;font-weight:600;color:#6B6B66;cursor:pointer;transition:all .15s}.tab:hover{background:#F4F4F1}.tab--active{background:#1C1C1E;color:#fff;font-weight:700}
.settings-body{display:flex;flex-direction:column;gap:16px}.settings-section{background:#fff;border:1px solid #ECECE8;border-radius:18px;padding:24px}.ss-header{display:flex;align-items:flex-start;gap:14px;margin-bottom:22px}.ss-header .ms{font-size:24px;color:#0D9488;font-variation-settings:'FILL' 1;margin-top:2px}.ss-title{font-size:16px;font-weight:800;color:#1C1C1E}.ss-desc{font-size:13px;color:#8B8B85;margin-top:4px;line-height:1.5}
.lock-grid{display:flex;flex-direction:column;gap:10px}.lock-card{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding:16px 18px;border-radius:14px;background:#FAFAF8;border:1.5px solid #ECECE8}.lock-card--danger{background:#FFFBFB;border-color:#FCE7EA}.lc-left{display:flex;align-items:flex-start;gap:13px;flex:1}.lc-icon{width:40px;height:40px;border-radius:11px;display:flex;align-items:center;justify-content:center;flex:none}.lci--on{background:#F0FDFA}.lci--on .ms{color:#0D9488;font-size:22px;font-variation-settings:'FILL' 1}.lci--off{background:#F4F4F1}.lci--off .ms{color:#9A9A93;font-size:22px}.lc-name{font-size:14px;font-weight:800;color:#1C1C1E}.lc-desc{font-size:12px;color:#6B6B66;margin-top:3px;line-height:1.4}.lc-warning{display:flex;align-items:center;gap:5px;font-size:11px;color:#E11D48;font-weight:700;margin-top:6px}.lc-warning .ms{font-size:14px}.lc-right{display:flex;flex-direction:column;align-items:flex-end;gap:6px}
.toggle-wrap{display:flex;align-items:center;gap:10px;cursor:pointer}.tw--disabled{opacity:.4;cursor:not-allowed}.toggle{width:44px;height:24px;border-radius:12px;position:relative;transition:background .2s;flex:none}.toggle--on{background:#0D9488}.toggle--off{background:#D1D5DB}.toggle-thumb{width:18px;height:18px;border-radius:50%;background:#fff;position:absolute;top:3px;transition:left .2s;box-shadow:0 1px 3px rgba(0,0,0,.2)}.toggle--on .toggle-thumb{left:23px}.toggle--off .toggle-thumb{left:3px}.tl{font-size:11.5px;font-weight:700}.tl--on{color:#0D9488}.tl--off{color:#9A9A93}.owner-only{display:inline-flex;align-items:center;gap:4px;font-size:10px;color:#9A9A93;font-weight:600}
.danger-note{display:flex;align-items:flex-start;gap:9px;background:#FFFBEB;border:1px solid #FDE68A;border-radius:11px;padding:12px 16px;font-size:12px;color:#92400E;line-height:1.5;margin-top:10px}
.field-grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}.field{display:flex;flex-direction:column;gap:6px}.field--full{grid-column:1/-1}.mt-16{margin-top:16px}label{font-size:12px;font-weight:700;color:#52525B}.input{height:40px;border-radius:11px;border:1px solid #ECECE8;padding:0 14px;font-size:13px;font-family:inherit;outline:none;background:#FAFAF8}.input:focus{border-color:#0D9488;background:#fff}.field-hint{font-size:11px;color:#A1A19B}.time-range{display:flex;align-items:center;gap:8px}.time-sep{font-size:12px;color:#9A9A93;font-weight:600}
.bot-modes{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.bm-card{padding:16px;border-radius:14px;background:#F4F4F1;border:1.5px solid transparent;cursor:pointer;transition:all .15s}.bm-card:hover:not(.bm--locked){border-color:#0D9488}.bm--active{background:#F0FDFA;border-color:#0D9488}.bm--locked{opacity:.6;cursor:not-allowed}.bm-icon{font-size:24px;color:#0D9488;font-variation-settings:'FILL' 1;display:block;margin-bottom:8px}.bm-name{font-size:13px;font-weight:800;color:#1C1C1E;margin-bottom:4px}.bm-desc{font-size:11px;color:#6B6B66;line-height:1.4}.bm-lock{display:flex;align-items:center;gap:4px;font-size:10px;color:#A1A19B;margin-top:8px;font-weight:700}
.intg-list{display:flex;flex-direction:column;gap:10px}.intg-card{display:flex;align-items:center;gap:16px;padding:16px 18px;border-radius:14px;background:#FAFAF8;border:1px solid #ECECE8}.intg-logo{font-size:32px;flex:none}.intg-name{font-size:14px;font-weight:800;color:#1C1C1E}.intg-desc{font-size:12px;color:#6B6B66;margin-top:3px;line-height:1.4}.intg-warn{display:flex;align-items:center;gap:5px;font-size:11px;color:#D97706;font-weight:700;margin-top:6px}.intg-right{margin-left:auto;display:flex;flex-direction:column;align-items:center;gap:6px}.intg-status{font-size:11px;font-weight:700}.is--on{color:#0D9488}.is--off{color:#9A9A93}
.secret-field{display:flex;gap:8px}.secret-field .input{flex:1}
.icon-btn{width:40px;height:40px;border-radius:11px;border:1px solid #ECECE8;background:#F4F4F1;display:flex;align-items:center;justify-content:center;cursor:pointer;flex:none}
.save-bar{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);display:flex;align-items:center;gap:12px;background:#1C1C1E;color:#fff;padding:14px 20px;border-radius:16px;box-shadow:0 8px 32px -8px rgba(17,17,26,.5);z-index:100}
.loading-state{padding:60px;text-align:center;display:flex;align-items:center;justify-content:center;gap:10px;color:#9A9A93;font-weight:600}
.btn{display:inline-flex;align-items:center;gap:6px;padding:9px 16px;border-radius:10px;font-size:13px;font-weight:700;border:none;cursor:pointer;font-family:inherit}.btn--teal{background:#0D9488;color:#fff}.btn--ghost{background:rgba(255,255,255,.1);color:#fff;border:1px solid rgba(255,255,255,.2)}.btn:disabled{opacity:.5;cursor:not-allowed}
@keyframes spin{to{transform:rotate(360deg)}}.spin{display:inline-block;animation:spin 1s linear infinite}
.ms{font-family:'Material Symbols Rounded';font-weight:normal;font-style:normal;line-height:1;font-size:18px}
</style>
