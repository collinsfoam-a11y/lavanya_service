<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">WhatsApp Inbox</h1>
        <p class="page-sub">{{ unreadCount }} messages need review</p>
      </div>
      <div class="header-badges">
        <span class="dry-badge"><span class="ms">lock</span> Live sending: DISABLED</span>
        <span class="dry-badge dry-badge--amber"><span class="ms">smart_toy</span> Bot: {{ botMode.toUpperCase() }}</span>
        <button class="btn btn--outline btn--sm" @click="fetch"><span class="ms">refresh</span></button>
      </div>
    </div>

    <div class="inbox-layout">
      <!-- Bucket sidebar -->
      <div class="inbox-left">
        <div class="bucket-list">
          <div v-for="b in BUCKETS" :key="b.key"
            class="bucket-tab" :class="{ 'bt--active': activeBucket === b.key }"
            @click="activeBucket = b.key">
            <span class="ms bt-icon">{{ b.icon }}</span>
            <span class="bt-label">{{ b.label }}</span>
            <span v-if="bucketCount(b.key)" class="bt-count"
              :class="b.urgent ? 'bc--red' : 'bc--gray'">
              {{ bucketCount(b.key) }}
            </span>
          </div>
        </div>

        <div class="msg-list">
          <div v-if="loading" class="loading-sm"><span class="ms spin">sync</span></div>
          <div v-else-if="!activeMessages.length" class="empty-sm">
            <span class="ms">inbox</span> No messages
          </div>
          <div v-for="m in activeMessages" :key="m.name"
            class="msg-card" :class="{ 'mc--active': selectedMsg?.name === m.name, 'mc--unread': !m.reviewed }"
            @click="selectedMsg = m">
            <div class="mc-avatar">{{ initials(m.matched_customer_name || 'Unknown') }}</div>
            <div class="mc-body">
              <div class="mc-header">
                <span class="mc-name">{{ m.matched_customer_name || 'Unknown' }}</span>
                <span class="mc-time">{{ timeAgo(m.received_at) }}</span>
              </div>
              <div class="mc-phone">{{ m.phone }}</div>
              <div class="mc-preview">{{ (m.message_text||'').slice(0,60) }}…</div>
              <div class="mc-chips">
                <span class="intent-chip" :class="'ic--'+intentClass(m.bot_intent)">{{ m.bot_intent || 'unknown' }}</span>
                <span v-if="m.matched_ticket" class="ticket-chip">#{{ m.matched_ticket }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: detail -->
      <div class="inbox-right" v-if="selectedMsg">
        <div class="detail-header">
          <div class="dh-avatar">{{ initials(selectedMsg.matched_customer_name || 'Unknown') }}</div>
          <div class="dh-info">
            <div class="dh-name">{{ selectedMsg.matched_customer_name || 'Unknown Customer' }}</div>
            <div class="dh-phone">{{ selectedMsg.phone }}</div>
            <div class="dh-chips">
              <span class="intent-chip" :class="'ic--'+intentClass(selectedMsg.bot_intent)">
                {{ selectedMsg.bot_intent || 'unknown' }}
              </span>
              <span v-if="selectedMsg.matched_ticket" class="ticket-chip cursor"
                @click="navigate('lavanya-ticket-detail','name='+selectedMsg.matched_ticket)">
                #{{ selectedMsg.matched_ticket }}
              </span>
              <span class="badge" :class="selectedMsg.matched_customer ? 'badge--teal':'badge--amber'">
                {{ selectedMsg.matched_customer ? 'Matched' : 'Unmatched' }}
              </span>
            </div>
          </div>
          <div class="dh-actions">
            <button v-if="selectedMsg.matched_ticket" class="btn btn--outline btn--sm"
              @click="navigate('lavanya-ticket-detail','name='+selectedMsg.matched_ticket)">
              <span class="ms">open_in_new</span> View Ticket
            </button>
            <button v-else class="btn btn--teal btn--sm"
              @click="navigate('lavanya-new-ticket','phone='+selectedMsg.phone)">
              <span class="ms">add</span> Create Ticket
            </button>
          </div>
        </div>

        <!-- Message bubble -->
        <div class="conversation">
          <div class="bubble-wrap bubble-wrap--in">
            <div class="bubble bubble--in">
              <div class="bubble-text">{{ selectedMsg.message_text }}</div>
              <div class="bubble-meta">{{ timeAgo(selectedMsg.received_at) }} · Customer</div>
            </div>
          </div>
          <div v-if="threadMessages.length > 1">
            <div v-for="m in threadMessages.slice(1)" :key="m.name"
              class="bubble-wrap" :class="m.direction==='in'?'bubble-wrap--in':'bubble-wrap--out'">
              <div class="bubble" :class="m.direction==='in'?'bubble--in':'bubble--out'">
                <div class="bubble-text">{{ m.message_text }}</div>
                <div class="bubble-meta">{{ timeAgo(m.received_at) }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- AI analysis -->
        <div class="ai-panel" v-if="selectedMsg.bot_intent">
          <div class="ai-header"><span class="ms">auto_awesome</span> AI Analysis</div>
          <div class="ai-body">
            <div class="ai-row"><span class="ai-k">Intent</span><span class="ai-v">{{ selectedMsg.bot_intent }}</span></div>
            <div class="ai-row"><span class="ai-k">Confidence</span><span class="ai-v">{{ selectedMsg.intent_confidence || '—' }}%</span></div>
            <div class="ai-row"><span class="ai-k">Suggested</span><span class="ai-v text--teal">{{ suggestedAction }}</span></div>
          </div>
        </div>

        <!-- Draft reply -->
        <div class="draft-panel">
          <div class="dp-header">
            <span class="ms">edit_note</span> Draft Reply
            <select v-model="selectedTemplate" class="template-sel" @change="loadTemplate">
              <option value="">Load template…</option>
              <option v-for="t in WA_TEMPLATES" :key="t.key" :value="t.key">{{ t.label }}</option>
            </select>
          </div>
          <textarea v-model="draftText" rows="4" class="draft-ta" placeholder="Type a draft reply…"></textarea>
          <div class="dp-actions">
            <button class="btn btn--outline btn--sm" @click="copyDraft">
              <span class="ms">content_copy</span> Copy
            </button>
            <button class="btn btn--outline btn--sm" @click="doMarkReviewed" :disabled="actionLoading">
              <span class="ms">done_all</span> Mark Reviewed
            </button>
            <button v-if="selectedMsg.matched_ticket" class="btn btn--outline btn--sm"
              @click="logToTicket" :disabled="actionLoading">
              <span class="ms">history</span> Log to Ticket
            </button>
            <span class="live-disabled"><span class="ms">lock</span> Live send disabled</span>
          </div>
        </div>
      </div>

      <div class="inbox-right inbox-right--empty" v-else>
        <span class="ms empty-lg">chat</span>
        <div class="empty-title">Select a message</div>
        <div class="empty-sub">Choose a message from the inbox to draft a reply</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useWhatsAppInbox } from '../composables/useWhatsApp.js'
import { navigate, showAlert } from '../composables/frappe.js'
import { frappeCall } from '../composables/frappe.js'

const props = defineProps({ frappePage: Object, onOpenTicket: Function, onCreateTicket: Function })
const { messages, buckets, loading, fetch, generateDraft, markReviewed } = useWhatsAppInbox()

const activeBucket    = ref('new_messages')
const selectedMsg     = ref(null)
const selectedTemplate= ref('')
const draftText       = ref('')
const actionLoading   = ref(false)
const threadMessages  = ref([])
const botMode         = ref('dry_run')

const BUCKETS = [
  { key:'new_messages',       label:'New Messages',           icon:'mark_unread_chat_alt', urgent:true },
  { key:'unmatched',          label:'Unmatched Customers',    icon:'person_off',           urgent:true },
  { key:'possible_updates',   label:'Possible Ticket Updates',icon:'update',               urgent:false },
  { key:'complaint_drafts',   label:'Complaint Intake Drafts',icon:'draft',                urgent:false },
  { key:'satisfaction_replies',label:'Satisfaction Replies',  icon:'sentiment_satisfied',  urgent:false },
  { key:'technician_replies', label:'Technician Replies',     icon:'engineering',          urgent:false },
  { key:'escalation_risk',    label:'Escalation Risk',        icon:'warning',              urgent:true },
  { key:'spam',               label:'Spam / Irrelevant',      icon:'block',                urgent:false },
]

const WA_TEMPLATES = [
  { key:'complaint_registered',  label:'Complaint Registered',  text:'Dear {name}, your complaint #{id} has been registered. We will keep you informed. — Lavanya Service' },
  { key:'technician_call_check', label:'Technician Call Check', text:'Dear {name}, has the {brand} technician called you regarding complaint #{id}? Reply YES or NO.' },
  { key:'technician_visit_check',label:'Technician Visit Check',text:'Dear {name}, has the technician visited and completed the repair for #{id}? Reply YES or NO.' },
  { key:'satisfaction_check',    label:'Satisfaction Check',    text:'Dear {name}, is complaint #{id} resolved to your satisfaction? Reply SATISFIED or NOT SATISFIED.' },
  { key:'no_response_reminder',  label:'No-Response Reminder',  text:'Dear {name}, we tried reaching you for #{id}. Please call us or reply at your earliest convenience.' },
  { key:'product_ready',         label:'Product Ready',         text:'Dear {name}, your product for complaint #{id} is ready for collection. Open 9AM–8PM.' },
]

const unreadCount    = computed(() => messages.value.filter(m => !m.reviewed).length)
const activeMessages = computed(() => (buckets.value[activeBucket.value] || []))
function bucketCount(key) { return (buckets.value[key]||[]).length }

function intentClass(intent) {
  if (!intent) return 'gray'
  if (['technician_visited_no','escalation_risk','issue_resolved_no'].includes(intent)) return 'red'
  if (['issue_resolved_yes','technician_visited_yes'].includes(intent)) return 'teal'
  if (['new_complaint','ticket_status'].includes(intent)) return 'blue'
  return 'amber'
}

const suggestedAction = computed(() => {
  const m = selectedMsg.value
  if (!m) return ''
  const map = {
    'ticket_status':          'Send service center follow-up update',
    'technician_visited_no':  'Mark visit not done + follow up service center',
    'issue_resolved_yes':     'Close ticket — customer confirmed',
    'issue_resolved_no':      'Reopen ticket + escalate',
    'new_complaint':          'Create new ticket',
    'escalation_risk':        'Escalate to L4 — contact manager immediately',
    'technician_called_no':   'Verify call with service center',
  }
  return map[m.bot_intent] || 'Review and take appropriate action'
})

function loadTemplate() {
  const t = WA_TEMPLATES.find(x => x.key === selectedTemplate.value)
  if (t && selectedMsg.value) {
    draftText.value = t.text
      .replace('{name}', selectedMsg.value.matched_customer_name || 'Customer')
      .replace('{id}',   selectedMsg.value.matched_ticket || 'TKT')
      .replace('{brand}','the service center')
  }
}

function copyDraft() {
  navigator.clipboard?.writeText(draftText.value)
  showAlert('Draft copied to clipboard')
}

async function doMarkReviewed() {
  if (!selectedMsg.value) return
  actionLoading.value = true
  try {
    await markReviewed(selectedMsg.value.name)
    showAlert('Message marked as reviewed')
    selectedMsg.value = null
  } finally { actionLoading.value = false }
}

async function logToTicket() {
  if (!selectedMsg.value?.matched_ticket || !draftText.value) return
  actionLoading.value = true
  try {
    await frappeCall('lavanya_service.api.tickets.save_followup', {
      ticket:            selectedMsg.value.matched_ticket,
      action_type:       'WhatsApp Reply Received',
      detail:            'Customer message: ' + selectedMsg.value.message_text + (draftText.value ? '\n\nDraft reply: ' + draftText.value : ''),
      customer_informed: 'No',
      channel:           'WhatsApp',
    })
    showAlert('Logged to ticket #' + selectedMsg.value.matched_ticket)
  } finally { actionLoading.value = false }
}

function initials(n) { return (n||'?').split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase() }
function timeAgo(d) {
  if (!d) return ''
  const diff = Math.round((new Date()-new Date(d))/60000)
  if (diff<60) return diff+'m ago'; if (diff<1440) return Math.round(diff/60)+'h ago'
  return Math.round(diff/1440)+'d ago'
}

defineExpose({ refresh: fetch })
</script>

<style scoped>
.page{padding:28px 32px;max-width:1600px}.page-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}.page-title{font-size:24px;font-weight:800;color:#1C1C1E;letter-spacing:-0.02em;margin:0}.page-sub{font-size:13px;color:#8B8B85;margin:4px 0 0}.header-badges{display:flex;gap:8px;align-items:center}.dry-badge{display:inline-flex;align-items:center;gap:6px;padding:7px 13px;border-radius:9px;background:#1C1C1E;color:#fff;font-size:12px;font-weight:700}.dry-badge--amber{background:#FFFBEB;color:#92400E;border:1px solid #FDE68A}
.inbox-layout{display:grid;grid-template-columns:360px 1fr;gap:14px;height:calc(100vh-180px)}
.inbox-left{display:flex;flex-direction:column;background:#fff;border:1px solid #ECECE8;border-radius:16px;overflow:hidden}
.bucket-list{border-bottom:1px solid #ECECE8}.bucket-tab{display:flex;align-items:center;gap:10px;padding:10px 16px;cursor:pointer;transition:background .15s;border-left:3px solid transparent}.bucket-tab:hover{background:#FAFAF8}.bt--active{background:#F0FDFA;border-left-color:#0D9488}.bt-icon{font-size:17px;color:#9A9A93}.bt--active .bt-icon{color:#0D9488;font-variation-settings:'FILL' 1}.bt-label{flex:1;font-size:12.5px;font-weight:600;color:#52525B}.bt--active .bt-label{color:#0F766E;font-weight:700}.bt-count{min-width:20px;height:18px;border-radius:6px;font-size:10.5px;font-weight:700;display:flex;align-items:center;justify-content:center;padding:0 5px}.bc--red{background:#E11D48;color:#fff}.bc--gray{background:#F0F0EC;color:#9A9A93}
.msg-list{flex:1;overflow-y:auto}.msg-card{display:flex;gap:11px;padding:13px 16px;border-bottom:1px solid #F4F4F1;cursor:pointer;transition:background .15s}.msg-card:hover{background:#FAFAF8}.mc--active{background:#F0FDFA}.mc-unread .mc-name{font-weight:800;color:#1C1C1E}.mc-avatar{width:36px;height:36px;border-radius:50%;background:#EEF2FF;color:#4F46E5;font-size:13px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}.mc-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:1px}.mc-name{font-size:13px;font-weight:700;color:#3F3F46}.mc-time{font-size:10.5px;color:#A1A19B}.mc-phone{font-size:11px;color:#9A9A93;margin-bottom:3px}.mc-preview{font-size:12px;color:#6B6B66;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:240px;margin-bottom:5px}.mc-chips{display:flex;gap:5px;flex-wrap:wrap}
.inbox-right{background:#fff;border:1px solid #ECECE8;border-radius:16px;display:flex;flex-direction:column;overflow:hidden}.inbox-right--empty{align-items:center;justify-content:center;gap:10px}.empty-lg{font-size:48px;color:#C4C4BD;font-family:'Material Symbols Rounded';font-variation-settings:'FILL' 1}.empty-title{font-size:17px;font-weight:800;color:#9A9A93}.empty-sub{font-size:13px;color:#A1A19B;text-align:center;max-width:240px}
.detail-header{display:flex;align-items:center;gap:13px;padding:16px 20px;border-bottom:1px solid #ECECE8}.dh-avatar{width:42px;height:42px;border-radius:12px;background:#EEF2FF;color:#4F46E5;font-size:15px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}.dh-name{font-size:15px;font-weight:800;color:#1C1C1E}.dh-phone{font-size:12px;color:#8B8B85}.dh-chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:5px}.dh-actions{margin-left:auto;display:flex;gap:7px}
.conversation{flex:1;overflow-y:auto;padding:16px 20px;display:flex;flex-direction:column;gap:10px;background:#F6F6F3}.bubble-wrap{display:flex}.bubble-wrap--in{justify-content:flex-start}.bubble-wrap--out{justify-content:flex-end}.bubble{max-width:70%;padding:10px 14px;border-radius:14px}.bubble--in{background:#fff;border:1px solid #ECECE8;border-bottom-left-radius:4px}.bubble--out{background:#F0FDFA;border:1px solid #CCFBF1;border-bottom-right-radius:4px}.bubble-text{font-size:13.5px;color:#1C1C1E;line-height:1.45}.bubble-meta{font-size:10px;color:#A1A19B;margin-top:5px}
.ai-panel{margin:12px 20px 0;background:#F5F3FF;border:1px solid #DDD6FE;border-radius:12px;overflow:hidden}.ai-header{display:flex;align-items:center;gap:7px;padding:10px 14px;background:#EDE9FE;font-size:12px;font-weight:700;color:#6D28D9}.ai-body{padding:10px 14px;display:flex;gap:20px}.ai-row{display:flex;flex-direction:column;gap:2px}.ai-k{font-size:9.5px;font-weight:700;color:#9A9A93;text-transform:uppercase;letter-spacing:.04em}.ai-v{font-size:12.5px;font-weight:700;color:#1C1C1E}
.draft-panel{padding:14px 20px 16px;border-top:1px solid #ECECE8}.dp-header{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:700;color:#1C1C1E;margin-bottom:10px}.template-sel{margin-left:auto;height:32px;padding:0 10px;border-radius:9px;border:1px solid #ECECE8;font-size:12px;font-family:inherit;background:#fff}.draft-ta{width:100%;border:1.5px solid #ECECE8;border-radius:11px;padding:10px 14px;font-size:13px;font-family:inherit;outline:none;resize:none;background:#FAFAF8;box-sizing:border-box}.draft-ta:focus{border-color:#0D9488;background:#fff}.dp-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:10px}.live-disabled{margin-left:auto;display:inline-flex;align-items:center;gap:5px;font-size:10.5px;color:#E11D48;font-weight:700;background:#FFF1F3;padding:4px 10px;border-radius:7px}
.intent-chip{padding:2px 8px;border-radius:6px;font-size:10.5px;font-weight:700}.ic--red{background:#FFF1F3;color:#E11D48}.ic--teal{background:#F0FDFA;color:#0D9488}.ic--blue{background:#EEF2FF;color:#4F46E5}.ic--amber{background:#FFF7ED;color:#D97706}.ic--gray{background:#F4F4F1;color:#71717A}
.ticket-chip{padding:2px 8px;border-radius:6px;font-size:10.5px;font-weight:700;background:#F0FDFA;color:#0F766E;font-family:'JetBrains Mono',monospace}.cursor{cursor:pointer}.cursor:hover{text-decoration:underline}
.badge{padding:2px 8px;border-radius:6px;font-size:10.5px;font-weight:700}.badge--teal{background:#F0FDFA;color:#0D9488}.badge--amber{background:#FFF7ED;color:#D97706}
.loading-sm{padding:20px;text-align:center;color:#A1A19B}.empty-sm{padding:30px;text-align:center;display:flex;flex-direction:column;align-items:center;gap:6px;color:#A1A19B;font-size:13px}.empty-sm .ms{font-size:24px;color:#C4C4BD;font-variation-settings:'FILL' 1}
.text--teal{color:#0D9488;font-weight:700}
.btn{display:inline-flex;align-items:center;gap:5px;padding:8px 14px;border-radius:9px;font-size:12.5px;font-weight:700;border:none;cursor:pointer;font-family:inherit}.btn--sm{padding:6px 11px;font-size:11.5px}.btn--teal{background:#0D9488;color:#fff}.btn--outline{background:#fff;border:1px solid #ECECE8;color:#52525B}.btn:disabled{opacity:.5;cursor:not-allowed}
@keyframes spin{to{transform:rotate(360deg)}}.spin{display:inline-block;animation:spin 1s linear infinite}
.ms{font-family:'Material Symbols Rounded';font-weight:normal;font-style:normal;line-height:1;font-size:18px}
</style>
