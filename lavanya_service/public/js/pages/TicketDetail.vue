<template>
  <div class="page">
    <div class="breadcrumb" @click="navigate('lavanya-tickets')">
      <span class="ms">arrow_back</span> Tickets
      <span class="ms bc-sep">chevron_right</span>
      <span class="bc-id">#{{ ticketId }}</span>
    </div>

    <div v-if="loading" class="loading-state"><span class="ms spin">sync</span> Loading ticket…</div>
    <div v-else-if="error" class="error-state">
      <span class="ms">error</span> {{ error }}
      <button class="btn btn--outline" @click="fetch(ticketId)">Retry</button>
    </div>

    <div class="detail-layout" v-else-if="ticket">
      <!-- LEFT -->
      <div class="detail-left">

        <!-- Hero: header + journey stepper -->
        <div class="card card--hero">
          <div class="hero-top">
            <div class="hero-id-block">
              <div class="hero-avatar">{{ initials(ticket.customer_name) }}</div>
              <div>
                <div class="hero-id-row">
                  <span class="hero-id">#{{ ticket.name }}</span>
                  <StatusBadge :status="ticket.status" />
                  <span class="lav-badge lav-badge--gray">{{ ticket.priority }}</span>
                  <QualityBadge :badge="ticket.quality_badge" />
                </div>
                <div class="hero-sub">{{ ticket.subject }} · {{ ticket.brand }} {{ ticket.product_model }} · {{ ticket.days_open }} days old</div>
              </div>
            </div>
            <div class="sla-box" :class="ticket.sla_breached ? 'sla--breached' : 'sla--ok'">
              <div class="sla-lbl">{{ ticket.sla_breached ? 'SLA breached' : 'SLA remaining' }}</div>
              <div class="sla-val">{{ slaDisplay }}</div>
            </div>
          </div>

          <!-- Journey stepper -->
          <div class="stepper">
            <template v-for="(step, i) in STAGES" :key="step.key">
              <div class="step" :class="stepClass(step.key)">
                <div class="step-dot"><span class="ms">{{ step.icon }}</span></div>
                <div class="step-lbl">{{ step.label }}</div>
              </div>
              <div v-if="i < STAGES.length-1" class="step-line" :class="{ 'sl--done': isStepDone(step.key) }"></div>
            </template>
          </div>
        </div>

        <!-- Next Action Bar (dark) -->
        <div class="next-action-bar">
          <div class="na-top">
            <div class="na-icon"><span class="ms">bolt</span></div>
            <div class="na-body">
              <div class="na-label">Next action</div>
              <div class="na-text">{{ ticket.next_action || 'Review and take appropriate action' }}</div>
            </div>
            <div class="na-due">
              <div class="na-due-lbl">Due</div>
              <div class="na-due-val">{{ dueLabel }}</div>
            </div>
          </div>
          <div class="na-actions">
            <button class="na-btn na-btn--primary" @click="openFollowup('Register Complaint')">
              <span class="ms">verified</span>Register Complaint
            </button>
            <button class="na-btn" @click="openFollowup('Call Customer')">
              <span class="ms">call</span>Call Customer
            </button>
            <button class="na-btn" @click="openFollowup('Customer Informed')">
              <span class="ms">campaign</span>Inform Customer
            </button>
            <button class="na-btn" @click="openFollowup('Service Center Called')">
              <span class="ms">support_agent</span>Follow Up SC
            </button>
            <div class="na-divider"></div>
            <button class="na-btn na-btn--danger" @click="showEscalateModal = true">
              <span class="ms">priority_high</span>Escalate
            </button>
            <button class="na-btn na-btn--danger" @click="showCloseModal = true" :disabled="!closureAllowed">
              <span class="ms">replay</span>Close
            </button>
          </div>
        </div>

        <!-- Service Stage + Reminder Intelligence -->
        <div class="grid-2">
          <div class="card">
            <div class="card-title"><span class="ms">account_tree</span>Service Stage</div>
            <div class="kv-list">
              <div class="kv-row"><span>Next follow-up</span><span class="mono">{{ fmtDate(ticket.next_followup_date) }}</span></div>
              <div class="kv-row"><span>Brand ticket</span><span class="mono">{{ ticket.brand_ticket_number || 'Not registered' }}</span></div>
              <div class="kv-row"><span>Service center</span><span>{{ ticket.service_center || '—' }}</span></div>
              <div class="kv-row"><span>Escalation</span><span class="lav-badge lav-badge--red">{{ ticket.escalation_level || 'L1' }}</span></div>
              <div class="kv-row"><span>Customer informed</span>
                <span :class="ticket.customer_informed ? 'text--teal' : 'text--muted'">{{ ticket.customer_informed ? 'Yes' : 'Not yet' }}</span>
              </div>
            </div>
          </div>
          <div class="card">
            <div class="card-title"><span class="ms" style="color:#7C3AED">neurology</span>Reminder Intelligence</div>
            <div class="kv-list">
              <div class="kv-row"><span>Due status</span>
                <span class="lav-badge" :class="ticket.followup_overdue ? 'lav-badge--red' : 'lav-badge--green'">{{ ticket.followup_overdue ? 'Overdue' : 'On track' }}</span>
              </div>
              <div class="kv-row"><span>Part pending</span>
                <span :class="ticket.part_pending ? 'text--amber' : 'text--muted'">{{ ticket.part_pending ? 'Yes' : 'No' }}</span>
              </div>
              <div class="kv-row"><span>Promise breach</span><span class="mono">{{ ticket.promise_breach_count || 0 }}</span></div>
              <div class="kv-row"><span>WhatsApp pending</span>
                <span :class="ticket.whatsapp_pending ? 'text--red' : 'text--muted'">{{ ticket.whatsapp_pending ? '1 new' : 'None' }}</span>
              </div>
              <div class="kv-row"><span>AI advisory</span>
                <span class="ai-insight"><span class="ms">auto_awesome</span>1 insight</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Context cards: Product / CRM / WhatsApp -->
        <div class="grid-3">
          <div class="card">
            <div class="card-title"><span class="ms">inventory_2</span>Product / Warranty</div>
            <div class="ctx-brand">{{ ticket.brand }} · {{ ticket.product_category || 'Product' }}</div>
            <div class="ctx-model">{{ ticket.product_model || '—' }}</div>
            <div class="ctx-list">
              <div class="ctx-row"><span>Warranty</span>
                <span class="lav-badge" :class="warrantyClass">{{ ticket.warranty_status || '—' }}</span>
              </div>
              <div class="ctx-row"><span>Serial</span><span class="mono">{{ ticket.serial_number || '—' }}</span></div>
              <div class="ctx-row"><span>Invoice</span><span class="mono">{{ ticket.invoice_number || '—' }}</span></div>
            </div>
          </div>
          <div class="card">
            <div class="card-title"><span class="ms" style="color:#4F46E5">handshake</span>CRM Relationship</div>
            <div class="ctx-list">
              <div class="ctx-row"><span>Contact linked</span>
                <span :class="ticket.customer ? 'text--green' : 'text--muted'">{{ ticket.customer ? 'Yes' : 'No' }}</span>
              </div>
              <div class="ctx-row"><span>Open deals</span><span class="mono">{{ ticket.crm_deals?.length || 0 }}</span></div>
              <div class="ctx-row"><span>Upgrade signal</span>
                <span class="lav-badge lav-badge--violet">Repeat repair</span>
              </div>
            </div>
            <button class="ctx-action ctx-action--indigo" @click="navigate('lavanya-customer360', 'customer=' + ticket.customer)">
              <span class="ms">add</span>Create Opportunity
            </button>
          </div>
          <div class="card">
            <div class="card-title">
              <span class="ms" style="color:#16A34A">chat</span>WhatsApp
              <span class="dry-tag">DRY RUN</span>
            </div>
            <div class="ctx-list">
              <div class="ctx-row"><span>Opt-in</span>
                <span :class="ticket.whatsapp_optin ? 'text--green' : 'text--muted'">{{ ticket.whatsapp_optin ? 'Active' : 'Off' }}</span>
              </div>
              <div class="ctx-row"><span>Pending reply</span>
                <span class="lav-badge" :class="ticket.whatsapp_pending ? 'lav-badge--red' : 'lav-badge--gray'">{{ ticket.whatsapp_pending ? '1 new' : 'None' }}</span>
              </div>
            </div>
            <div class="wa-draft-area">
              <select v-model="waTemplate" class="wa-select">
                <option value="">Select template…</option>
                <option v-for="t in WA_TEMPLATES" :key="t.key" :value="t.key">{{ t.label }}</option>
              </select>
              <button class="ctx-action ctx-action--green" @click="genDraft" :disabled="!waTemplate || draftLoading">
                <span v-if="draftLoading" class="ms spin">sync</span>
                <span v-else class="ms">edit_note</span>Draft reply
              </button>
            </div>
            <div v-if="waDraft" class="wa-draft-text">{{ waDraft }}</div>
          </div>
        </div>

        <!-- Customer Journey + Closure Guard -->
        <div class="card">
          <div class="card-title-row">
            <div class="card-title"><span class="ms">route</span>Customer Journey</div>
            <QualityBadge :badge="ticket.quality_badge" />
          </div>
          <div class="journey-tiles">
            <div class="lav-stat-tile">
              <div class="lav-stat-tile-label">Days open</div>
              <div class="lav-stat-tile-val">{{ ticket.days_open }}</div>
            </div>
            <div class="lav-stat-tile">
              <div class="lav-stat-tile-label">Last customer update</div>
              <div class="lav-stat-tile-val" style="font-size:12.5px">{{ lastCustomerUpdate }}</div>
            </div>
            <div class="lav-stat-tile">
              <div class="lav-stat-tile-label">Last SC follow-up</div>
              <div class="lav-stat-tile-val" style="font-size:12.5px">{{ lastScFollowup }}</div>
            </div>
            <div class="lav-stat-tile">
              <div class="lav-stat-tile-label">Satisfaction</div>
              <div class="lav-stat-tile-val" style="font-size:12.5px">{{ ticket.customer_satisfaction || 'Pending' }}</div>
            </div>
          </div>
          <div class="closure-guard" v-if="!closureAllowed">
            <div class="cg-icon"><span class="ms">lock</span></div>
            <div class="cg-body">
              <div class="cg-title">Closure blocked</div>
              <div class="cg-text">{{ closureBlockReason }}</div>
            </div>
            <button class="cg-btn" @click="openFollowup('Customer Informed')">
              <span class="ms">how_to_reg</span>Confirm with customer
            </button>
          </div>
        </div>

        <!-- Follow-up Plan + Non-response ladder -->
        <div class="card">
          <div class="card-title-row">
            <div class="card-title"><span class="ms">event_repeat</span>Follow-up Plan</div>
            <span class="cadence-pill"><span class="ms">schedule</span>Brand cadence · every 2 days</span>
          </div>
          <div class="next-scheduled">
            <div class="ns-icon"><span class="ms">notifications_active</span></div>
            <div class="ns-body">
              <div class="ns-lbl">Next scheduled follow-up</div>
              <div class="ns-text">Service-center call · <span class="mono">{{ fmtDate(ticket.next_followup_date) }}</span></div>
            </div>
          </div>
          <div class="ladder-lbl">Non-response policy · attempt {{ nonResponseAttempt }} of 3</div>
          <div class="ladder">
            <div class="ld-step" :class="{'ld--done': nonResponseAttempt >= 1}">
              <div class="ld-dot"><span class="ms">{{ nonResponseAttempt >= 1 ? 'check' : 'call' }}</span></div>
              <div class="ld-lbl">Attempt 1<br><span class="ld-sub">Call</span></div>
            </div>
            <div class="ld-line" :class="{'ldl--done': nonResponseAttempt >= 2}"></div>
            <div class="ld-step" :class="{'ld--current': nonResponseAttempt === 2}">
              <div class="ld-dot"><span class="ms">hourglass_top</span></div>
              <div class="ld-lbl">Attempt 2<br><span class="ld-sub">Call + WhatsApp · due</span></div>
            </div>
            <div class="ld-line"></div>
            <div class="ld-step ld--future">
              <div class="ld-dot"><span class="ms">call</span></div>
              <div class="ld-lbl">Attempt 3<br><span class="ld-sub">Final · +1 day</span></div>
            </div>
            <div class="ld-line"></div>
            <div class="ld-step ld--future">
              <div class="ld-dot"><span class="ms">lock_open</span></div>
              <div class="ld-lbl">Closure unlocks<br><span class="ld-sub">No-response</span></div>
            </div>
          </div>
        </div>

        <!-- Timeline + inline log composer -->
        <div class="card">
          <div class="card-title-row">
            <div class="card-title"><span class="ms">history</span>Follow-up Timeline</div>
            <span class="proof-tag">proof of every action</span>
          </div>
          <div v-if="ticket.timeline?.length" class="timeline">
            <div v-for="(e, i) in ticket.timeline" :key="i" class="tl-entry">
              <div class="tl-dot" :class="'tl-dot--' + dotClass(e.action_type)"></div>
              <div class="tl-body">
                <div class="tl-header">
                  <span class="tl-action">{{ e.action_type }}</span>
                  <span class="tl-time mono">{{ timeAgo(e.creation) }}</span>
                </div>
                <div class="tl-detail">{{ e.detail }}</div>
                <div class="tl-tags">
                  <span class="tl-staff">{{ e.staff }} · {{ e.channel }}</span>
                  <span v-if="e.customer_informed !== undefined" class="tl-informed" :class="e.customer_informed === 'Yes' ? 'tl-informed--yes' : 'tl-informed--no'">
                    <span class="ms">person_off</span>Customer informed: {{ e.customer_informed }}
                  </span>
                </div>
              </div>
            </div>
          </div>
          <div v-else class="empty-state-sm">No activity yet</div>

          <!-- Inline log composer -->
          <div class="log-composer">
            <div class="lc-title">Log a follow-up</div>
            <div class="lc-row">
              <select v-model="fu.action_type" class="lc-select">
                <option value="">Action type</option>
                <option v-for="a in FU_ACTION_TYPES" :key="a" :value="a">{{ a }}</option>
              </select>
              <select v-model="fu.channel" class="lc-select">
                <option>Manual</option><option>Phone</option><option>WhatsApp</option><option>Email</option>
              </select>
            </div>
            <textarea v-model="fu.detail" rows="2" class="lc-textarea" placeholder="What happened? What was discussed?"></textarea>
            <div class="lc-informed-panel">
              <div class="lc-ip-head">
                <span class="ms">priority_high</span>
                <span class="lc-ip-q">Was the customer informed?</span>
                <span class="lc-req">Required</span>
              </div>
              <div class="lc-ip-opts">
                <div class="lc-opt" :class="{'lc-opt--active': fu.customer_informed === 'Yes'}" @click="fu.customer_informed = 'Yes'">Yes</div>
                <div class="lc-opt" :class="{'lc-opt--active': fu.customer_informed === 'No'}" @click="fu.customer_informed = 'No'">No</div>
                <div class="lc-opt" :class="{'lc-opt--active': fu.customer_informed === 'Not Required'}" @click="fu.customer_informed = 'Not Required'">Not required</div>
              </div>
              <div class="lc-ip-note">A follow-up can't be saved without this. "No" and "Not required" prompt for a reason — keeping closure proof honest.</div>
            </div>
            <div class="lc-foot">
              <div class="lc-auto"><span class="ms">event</span>Next follow-up auto-set <span class="mono text--teal">+2 days</span></div>
              <button class="btn btn--teal" @click="submitFollowup" :disabled="!canSaveFu || saving">
                <span v-if="saving" class="ms spin">sync</span>
                <span v-else class="ms">add</span>Save entry
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- RIGHT RAIL -->
      <div class="detail-right">
        <div class="card">
          <div class="card-title-sm">Quick Actions</div>
          <div class="quick-actions">
            <button class="qa-btn qa-btn--primary" @click="openFollowup('Service Center Called')">
              <span class="ms">verified</span>Register Brand Complaint
            </button>
            <button class="qa-btn" @click="openFollowup('Customer Informed')"><span class="ms">receipt_long</span>Need Invoice</button>
            <button class="qa-btn" @click="openFollowup('Service Center Called')"><span class="ms">support_agent</span>Follow Up Service Center</button>
            <button class="qa-btn" @click="openFollowup('Appointment Scheduled')"><span class="ms">calendar_month</span>Schedule Appointment</button>
            <button class="qa-btn" @click="openFollowup('Customer Informed')"><span class="ms">handshake</span>Set Customer Promise</button>
          </div>
        </div>

        <div class="card">
          <div class="card-title-sm">Follow-up Journey</div>
          <div class="journey-actions">
            <button class="ja-btn ja--violet" @click="openFollowup('Other')"><span class="ms">note_add</span>Create Product Receipt</button>
            <button class="ja-btn ja--green" @click="markReady"><span class="ms">inventory_2</span>Mark Ready for Pickup</button>
            <button class="ja-btn ja--amber" @click="openFollowup('Customer Satisfied')"><span class="ms">how_to_reg</span>Customer Confirmed</button>
            <button class="ja-btn ja--red" @click="showCloseModal = true" :disabled="!closureAllowed"><span class="ms">task_alt</span>Close Ticket</button>
          </div>
        </div>

        <div class="shield-note">
          <span class="ms">shield</span>
          <span>Actions are role-gated and validated server-side. You'll see a clear message if your role can't run one.</span>
        </div>
      </div>
    </div>

    <!-- ESCALATE MODAL -->
    <div v-if="showEscalateModal" class="modal-overlay" @click.self="showEscalateModal=false">
      <div class="modal modal--sm">
        <div class="modal-header">
          <div class="modal-title">Escalate Ticket</div>
          <button class="icon-btn" @click="showEscalateModal=false"><span class="ms">close</span></button>
        </div>
        <div class="modal-body">
          <div class="esc-current">
            Current level: <strong>{{ ticket?.escalation_level || 'L1' }}</strong>
            → <strong class="text--red">{{ nextLevel }}</strong>
          </div>
          <div class="field">
            <label>Reason <span class="req">*</span></label>
            <textarea v-model="escalateReason" rows="3" class="textarea" placeholder="Why is this being escalated?"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn--outline" @click="showEscalateModal=false">Cancel</button>
          <button class="btn btn--danger" @click="submitEscalate" :disabled="!escalateReason || saving">
            <span class="ms">priority_high</span> Escalate to {{ nextLevel }}
          </button>
        </div>
      </div>
    </div>

    <!-- CLOSE MODAL -->
    <div v-if="showCloseModal" class="modal-overlay" @click.self="showCloseModal=false">
      <div class="modal">
        <div class="modal-header">
          <div class="modal-title">Close Ticket</div>
          <button class="icon-btn" @click="showCloseModal=false"><span class="ms">close</span></button>
        </div>
        <div class="modal-body">
          <div class="field">
            <label>Closure Type <span class="req">*</span></label>
            <select v-model="closeData.closure_type" class="select-ctrl full">
              <option>Resolved</option>
              <option>No Response After Attempts</option>
              <option>Duplicate</option>
              <option>Other</option>
            </select>
          </div>
          <div class="field">
            <label>Customer Satisfaction</label>
            <div class="radio-row">
              <label v-for="s in ['Satisfied','Neutral','Dissatisfied']" :key="s" class="radio-opt">
                <input type="radio" v-model="closeData.customer_satisfaction" :value="s" /> {{ s }}
              </label>
            </div>
          </div>
          <div class="field" v-if="closeData.closure_type === 'No Response After Attempts'">
            <label>Number of attempts made</label>
            <input v-model.number="closeData.non_response_attempt_count" type="number" min="1" class="input" />
          </div>
          <div class="field">
            <label>Closure Remarks <span class="req">*</span></label>
            <textarea v-model="closeData.remarks" rows="3" class="textarea" placeholder="Summarise the resolution…"></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn--outline" @click="showCloseModal=false">Cancel</button>
          <button class="btn btn--teal" @click="submitClose" :disabled="!closeData.closure_type || !closeData.remarks || saving">
            <span v-if="saving" class="ms spin">sync</span>
            <span v-else class="ms">task_alt</span>
            {{ saving ? 'Closing…' : 'Close Ticket' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import StatusBadge from '../components/StatusBadge.vue'
import QualityBadge from '../components/QualityBadge.vue'
import { useTicket } from '../composables/useTickets.js'
import { navigate, showAlert, showError, frappeCall } from '../composables/frappe.js'

const props = defineProps({ frappePage: Object, ticketId: String })
const { ticket, loading, error, fetch, saveFollowup, escalate, closeTicket } = useTicket(props.ticketId)

const showEscalateModal = ref(false)
const showCloseModal    = ref(false)
const saving            = ref(false)
const draftLoading      = ref(false)
const waTemplate        = ref('')
const waDraft           = ref('')

const fu = ref({ action_type: '', detail: '', channel: 'Manual', customer_informed: '', customer_informed_reason: '', next_followup_date: '' })
const escalateReason = ref('')
const closeData = ref({ closure_type: '', customer_satisfaction: 'Satisfied', non_response_attempt_count: 0, remarks: '' })

const FU_ACTION_TYPES = [
  'Service Center Called','Technician Call Verified','Technician Visit Verified',
  'Customer Informed','Part Pending Recorded','Appointment Scheduled',
  'Escalation','WhatsApp Draft Generated','Customer Satisfied','Customer Not Satisfied',
  'Ticket Reopened','Other',
]
const WA_TEMPLATES = [
  { key:'complaint_registered',   label:'Complaint Registered' },
  { key:'technician_call_check',  label:'Technician Call Check' },
  { key:'technician_visit_check', label:'Technician Visit Check' },
  { key:'satisfaction_check',     label:'Satisfaction Check' },
  { key:'no_response_reminder',   label:'No-Response Reminder' },
  { key:'product_ready',          label:'Product Ready for Pickup' },
  { key:'closure_confirmation',   label:'Closure Confirmation' },
]

const STAGES = [
  { key:'new',          label:'New',          icon:'add_circle' },
  { key:'registered',   label:'Registration', icon:'app_registration' },
  { key:'in_progress',  label:'In Progress',  icon:'sync' },
  { key:'ready',        label:'Ready',        icon:'inventory_2' },
  { key:'closed',       label:'Resolved',     icon:'task_alt' },
]
const STATUS_STAGE_MAP = {
  'New':'new','Registered':'registered','In Follow-up':'in_progress',
  'Waiting':'in_progress','Resolved by Brand':'ready',
  'Customer Confirmation Pending':'ready','Closed':'closed',
}
function stepClass(key) {
  const cur = STATUS_STAGE_MAP[ticket.value?.status] || 'new'
  const order = STAGES.map(s=>s.key)
  const ci = order.indexOf(cur), si = order.indexOf(key)
  if (si < ci) return 'step--done'
  if (si === ci) return 'step--current'
  return 'step--future'
}
function isStepDone(key) { return stepClass(key) === 'step--done' }

const slaDisplay = computed(() => {
  if (!ticket.value?.sla_due_date) return '—'
  const ms = new Date(ticket.value.sla_due_date) - new Date()
  const abs = Math.abs(ms), d = Math.floor(abs/86400000), h = Math.floor((abs%86400000)/3600000)
  const p = ms < 0 ? '+' : ''
  return d > 0 ? p+d+'d '+h+'h' : p+h+'h'
})

const dueLabel = computed(() => {
  if (ticket.value?.followup_overdue) return 'Overdue'
  if (ticket.value?.sla_breached) return 'SLA breached'
  return fmtDate(ticket.value?.next_followup_date) || '—'
})

const closureAllowed = computed(() => {
  const t = ticket.value
  if (!t) return false
  return t.customer_informed && (t.customer_satisfied || t.closure_type === 'No Response After Attempts')
    && !(t.part_pending && !t.part_received)
})
const closureBlockReason = computed(() => {
  const t = ticket.value
  if (!t) return ''
  if (!t.customer_informed) return 'Customer has not been informed. Closure unlocks after confirmation or a documented non-response policy.'
  if (t.part_pending && !t.part_received) return 'Spare part is still pending and not yet received.'
  if (!t.customer_satisfied) return 'Customer satisfaction not confirmed.'
  return ''
})

const nextLevel = computed(() => ({ 'L1':'L2','L2':'L3','L3':'L4','L4':'L4' })[ticket.value?.escalation_level || 'L1'])

const warrantyClass = computed(() => {
  const w = ticket.value?.warranty_status
  if (w === 'In Warranty' || w === 'Extended Warranty' || w === 'AMC') return 'lav-badge--green'
  return 'lav-badge--amber'
})

const lastCustomerUpdate = computed(() => {
  const tl = ticket.value?.timeline || []
  const informed = tl.find(e => e.action_type === 'Customer Informed')
  return informed ? timeAgo(informed.creation) : 'Never'
})
const lastScFollowup = computed(() => {
  const tl = ticket.value?.timeline || []
  const sc = tl.find(e => e.action_type === 'Service Center Called')
  return sc ? timeAgo(sc.creation) : '—'
})

const nonResponseAttempt = computed(() => {
  const tl = ticket.value?.timeline || []
  const calls = tl.filter(e => ['Service Center Called','Customer Informed','Call Customer'].includes(e.action_type))
  return Math.min(3, calls.length + 1)
})

const canSaveFu = computed(() => fu.value.action_type && fu.value.detail && fu.value.customer_informed)

function openFollowup(actionType) {
  fu.value.action_type = actionType
  // scroll to composer
  document.querySelector('.log-composer')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

async function submitFollowup() {
  if (!canSaveFu.value) { showError('Please fill all required fields'); return }
  saving.value = true
  try {
    await saveFollowup(fu.value)
    showAlert('Follow-up saved')
    fu.value = { action_type:'', detail:'', channel:'Manual', customer_informed:'', customer_informed_reason:'', next_followup_date:'' }
  } catch(e) { showError(e.message || 'Failed to save follow-up') }
  finally { saving.value = false }
}

async function submitEscalate() {
  if (!escalateReason.value) return
  saving.value = true
  try {
    await escalate(escalateReason.value)
    showAlert('Ticket escalated to ' + nextLevel.value, 'orange')
    showEscalateModal.value = false
    escalateReason.value = ''
  } catch(e) { showError(e.message || 'Failed to escalate') }
  finally { saving.value = false }
}

async function submitClose() {
  saving.value = true
  try {
    await closeTicket(closeData.value)
    showAlert('Ticket closed successfully')
    showCloseModal.value = false
    navigate('lavanya-tickets')
  } catch(e) { showError(e.message || 'Cannot close ticket') }
  finally { saving.value = false }
}

function markReady() {
  fu.value.action_type = 'Other'
  fu.value.detail = 'Product marked ready for pickup.'
  openFollowup('Other')
}

async function genDraft() {
  draftLoading.value = true
  try {
    const r = await frappeCall('lavanya_service.api.whatsapp.generate_draft', {
      ticket_id: ticket.value.name, template_key: waTemplate.value
    })
    if (r) waDraft.value = r.draft
  } finally { draftLoading.value = false }
}

function initials(n) { return (n||'?').split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase() }
function fmtDate(d) {
  if (!d) return '—'
  const dt = new Date(d), diff = Math.round((dt-new Date())/86400000)
  if (diff===0) return 'Today'; if (diff===-1) return 'Yesterday'
  if (diff<0) return Math.abs(diff)+'d overdue'
  if (diff===1) return 'Tomorrow'
  return dt.toLocaleDateString('en-IN',{day:'numeric',month:'short'})
}
function timeAgo(d) {
  if (!d) return ''
  const diff = Math.round((new Date()-new Date(d))/60000)
  if (diff<60) return diff+'m ago'
  if (diff<1440) return Math.round(diff/60)+'h ago'
  return Math.round(diff/1440)+'d ago'
}
function dotClass(action) {
  if (!action) return 'gray'
  if (action.toLowerCase().includes('escalat')) return 'red'
  if (action.toLowerCase().includes('closed')) return 'teal'
  if (action.toLowerCase().includes('breach')) return 'red'
  if (action.toLowerCase().includes('satisfied')) return 'teal'
  return 'amber'
}

defineExpose({ refresh: () => fetch(props.ticketId), setTicket: (id) => fetch(id) })
</script>

<style scoped>
.page{padding:24px 28px;max-width:1400px}
.breadcrumb{display:flex;align-items:center;gap:7px;font-size:12px;color:#9A9A93;margin-bottom:16px;cursor:pointer;font-weight:600}
.bc-sep{font-size:14px}.bc-id{font-family:'JetBrains Mono',monospace;color:#0F766E;font-weight:600}

.detail-layout{display:grid;grid-template-columns:1fr 300px;gap:16px;align-items:start}
.detail-left,.detail-right{display:flex;flex-direction:column;gap:14px}
.detail-right{position:sticky;top:80px}

.card{background:#fff;border:1px solid #ECECE8;border-radius:14px;padding:18px;box-shadow:0 1px 2px rgba(17,17,26,0.04)}
.card--hero{padding:22px}
.card-title{display:flex;align-items:center;gap:7px;font-size:12.5px;font-weight:800;color:#1C1C1E;margin-bottom:14px}
.card-title .ms{font-size:17px;color:#0D9488}
.card-title-sm{font-size:10px;font-weight:700;color:#A1A19B;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:11px}
.card-title-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}

/* Hero */
.hero-top{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:20px}
.hero-id-block{display:flex;align-items:flex-start;gap:13px}
.hero-avatar{width:46px;height:46px;border-radius:13px;background:#EEF2FF;color:#4F46E5;font-size:18px;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}
.hero-id-row{display:flex;align-items:center;flex-wrap:wrap;gap:7px;margin-bottom:4px}
.hero-id{font-family:'JetBrains Mono',monospace;font-size:18px;font-weight:700;color:#1C1C1E}
.hero-sub{font-size:13px;color:#8B8B85}
.sla-box{border-radius:12px;padding:10px 16px;text-align:right;min-width:130px;flex:none}
.sla--ok{background:#F0FDFA;border:1px solid #CCFBF1}
.sla--breached{background:#FFF1F3;border:1px solid #FCE7EA;animation:lav-pulse 2s infinite}
.sla-lbl{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.05em}
.sla--ok .sla-lbl{color:#0F766E}.sla--breached .sla-lbl{color:#9F1239}
.sla-val{font-family:'JetBrains Mono',monospace;font-size:20px;font-weight:700;margin-top:2px}
.sla--ok .sla-val{color:#0D9488}.sla--breached .sla-val{color:#E11D48}

/* Stepper */
.stepper{display:flex;align-items:flex-start}
.step{display:flex;flex-direction:column;align-items:center;gap:6px;flex:1}
.step-dot{width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center}
.step--done .step-dot{background:#0D9488}.step--done .step-dot .ms{color:#fff;font-variation-settings:'FILL' 1}
.step--current .step-dot{background:#fff;border:2px solid #0D9488}.step--current .step-dot .ms{color:#0D9488}
.step--future .step-dot{background:#F4F4F1}.step--future .step-dot .ms{color:#BDBDB6}
.step-lbl{font-size:10.5px;font-weight:700;white-space:nowrap}
.step--done .step-lbl,.step--current .step-lbl{color:#0F766E}.step--future .step-lbl{color:#BDBDB6}
.step-line{height:2px;flex:none;width:44px;margin-bottom:22px}
.sl--done{background:#0D9488}.step-line:not(.sl--done){background:#E4E4DF}

/* Next Action Bar (dark) */
.next-action-bar{background:#1C1C1E;border-radius:14px;padding:18px}
.na-top{display:flex;align-items:center;gap:13px;margin-bottom:14px}
.na-icon{width:38px;height:38px;border-radius:11px;background:rgba(45,212,191,0.18);display:flex;align-items:center;justify-content:center;flex:none}
.na-icon .ms{font-size:21px;color:#2DD4BF}
.na-body{flex:1;min-width:0}
.na-label{font-size:10.5px;font-weight:700;color:#5EEAD4;text-transform:uppercase;letter-spacing:.06em}
.na-text{font-size:15px;font-weight:700;color:#fff;margin-top:2px}
.na-due{flex:none;text-align:right}
.na-due-lbl{font-size:10px;font-weight:700;color:#9CA3AF;text-transform:uppercase;letter-spacing:.05em}
.na-due-val{font-family:'JetBrains Mono',monospace;font-size:12.5px;font-weight:600;color:#FCA5A5;margin-top:2px}
.na-actions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.na-btn{display:inline-flex;align-items:center;gap:6px;padding:9px 14px;border-radius:10px;background:rgba(255,255,255,0.08);color:#E4E4E7;font-size:12.5px;font-weight:600;border:none;cursor:pointer;font-family:inherit}
.na-btn:disabled{opacity:.4;cursor:not-allowed}
.na-btn--primary{background:#0D9488;color:#fff;font-weight:700;box-shadow:0 3px 10px -3px rgba(13,148,136,0.6)}
.na-btn--danger{background:rgba(244,63,94,0.14);color:#FCA5A5;font-weight:700}
.na-divider{width:1px;height:22px;background:rgba(255,255,255,0.14);margin:0 2px}

/* Grids */
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.grid-3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.kv-list{display:flex;flex-direction:column;gap:11px}
.kv-row{display:flex;justify-content:space-between;align-items:center;font-size:11.5px;color:#9A9A93;font-weight:600}
.kv-row span:last-child{color:#1C1C1E;font-weight:600}
.ai-insight{display:inline-flex;align-items:center;gap:3px;font-size:11px;font-weight:700;color:#7C3AED}
.ai-insight .ms{font-size:13px}

/* Context cards */
.ctx-brand{font-size:12.5px;font-weight:700;color:#1C1C1E}
.ctx-model{font-size:11px;color:#9A9A93;margin-top:1px}
.ctx-list{display:flex;flex-direction:column;gap:7px;margin-top:11px}
.ctx-row{display:flex;justify-content:space-between;align-items:center;font-size:11px;color:#9A9A93;font-weight:600}
.ctx-row span:last-child{font-weight:700}
.ctx-action{display:flex;align-items:center;justify-content:center;gap:5px;margin-top:12px;padding:8px;border-radius:9px;font-size:11.5px;font-weight:700;border:none;cursor:pointer;font-family:inherit}
.ctx-action--indigo{background:#EEF2FF;color:#4F46E5}
.ctx-action--green{background:#F0FDF4;color:#16A34A;flex:1}
.dry-tag{margin-left:auto;padding:1px 7px;border-radius:6px;background:#F4F4F1;color:#71717A;font-size:9.5px;font-weight:700;letter-spacing:.03em}
.wa-draft-area{display:flex;flex-direction:column;gap:8px;margin-top:11px}
.wa-select{height:34px;border-radius:9px;border:1px solid #ECECE8;padding:0 10px;font-size:12px;font-family:inherit;background:#FAFAF8}
.wa-draft-text{font-size:11px;color:#6B6B66;font-style:italic;background:#FAFAF8;border-radius:8px;padding:7px 9px;line-height:1.35;margin-top:7px}

/* Customer Journey */
.journey-tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:14px}
.closure-guard{display:flex;align-items:center;gap:12px;background:#FFF8F8;border:1px solid #FCE7EA;border-radius:12px;padding:13px 16px}
.cg-icon{width:36px;height:36px;border-radius:10px;background:#FFE4E6;display:flex;align-items:center;justify-content:center;flex:none}
.cg-icon .ms{font-size:20px;color:#E11D48;font-variation-settings:'FILL' 1}
.cg-body{flex:1}
.cg-title{font-size:12.5px;font-weight:800;color:#9F1239}
.cg-text{font-size:11.5px;color:#B45369;margin-top:1px;line-height:1.4}
.cg-btn{display:inline-flex;align-items:center;gap:5px;padding:8px 13px;border-radius:9px;background:#fff;border:1px solid #FCE7EA;color:#E11D48;font-size:11.5px;font-weight:700;cursor:pointer;flex:none;font-family:inherit}

/* Follow-up Plan */
.cadence-pill{display:inline-flex;align-items:center;gap:4px;font-size:11px;font-weight:700;color:#D97706;background:#FFF7ED;padding:2px 9px;border-radius:7px}
.cadence-pill .ms{font-size:13px}
.next-scheduled{display:flex;align-items:center;gap:12px;background:#F0FDFA;border:1px solid #CCFBF1;border-radius:12px;padding:12px 15px;margin-bottom:16px}
.ns-icon{width:36px;height:36px;border-radius:10px;background:#fff;display:flex;align-items:center;justify-content:center;flex:none}
.ns-icon .ms{font-size:20px;color:#0D9488}
.ns-body{flex:1}
.ns-lbl{font-size:10px;font-weight:700;color:#0F766E;text-transform:uppercase;letter-spacing:.05em}
.ns-text{font-size:13.5px;font-weight:700;color:#1C1C1E;margin-top:1px}
.ladder-lbl{font-size:10px;font-weight:700;color:#A1A19B;text-transform:uppercase;letter-spacing:.05em;margin-bottom:10px}
.ladder{display:flex;align-items:center;gap:0}
.ld-step{flex:1;display:flex;flex-direction:column;align-items:center;gap:6px}
.ld-dot{width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#F4F4F1;color:#BDBDB6}
.ld--done .ld-dot{background:#0D9488;color:#fff}.ld--done .ld-dot .ms{font-variation-settings:'FILL' 1}
.ld--current .ld-dot{background:#fff;border:2px solid #D97706;color:#D97706}
.ld-lbl{font-size:10px;font-weight:700;color:#BDBDB6;text-align:center;line-height:1.25}
.ld--done .ld-lbl,.ld--current .ld-lbl{color:#1C1C1E}
.ld-sub{font-weight:600;color:#A1A19B;font-size:9.5px}
.ld-line{height:2px;flex:none;width:30px;background:#E4E4DF;margin-bottom:26px}
.ldl--done{background:#0D9488}

/* Timeline */
.proof-tag{font-size:10.5px;font-weight:600;color:#A1A19B}
.timeline{display:flex;flex-direction:column}
.tl-entry{display:flex;gap:13px;padding-bottom:15px;border-left:2px solid #F0F0EC;margin-left:5px;padding-left:18px;position:relative}
.tl-entry:last-child{border-left-color:transparent;padding-bottom:0}
.tl-dot{position:absolute;left:-6px;top:2px;width:11px;height:11px;border-radius:50%;border:2px solid #fff}
.tl-dot--red{background:#E11D48}.tl-dot--amber{background:#D97706}.tl-dot--teal{background:#0D9488}.tl-dot--gray{background:#BDBDB6}
.tl-header{display:flex;justify-content:space-between;margin-bottom:3px}
.tl-action{font-size:12.5px;font-weight:700;color:#1C1C1E}
.tl-time{font-size:10.5px;color:#A1A19B}
.tl-detail{font-size:11.5px;color:#8B8B85;line-height:1.4}
.tl-tags{display:flex;align-items:center;gap:8px;margin-top:6px;flex-wrap:wrap}
.tl-staff{font-size:9.5px;color:#A1A19B;font-weight:600}
.tl-informed{display:inline-flex;align-items:center;gap:3px;padding:1px 7px;border-radius:5px;font-size:9.5px;font-weight:700}
.tl-informed .ms{font-size:11px}
.tl-informed--yes{background:#ECFDF5;color:#059669}
.tl-informed--no{background:#FFF1F3;color:#E11D48}

/* Log composer */
.log-composer{margin-top:16px;border-top:1px dashed #E4E4DF;padding-top:16px}
.lc-title{font-size:11px;font-weight:800;color:#1C1C1E;margin-bottom:10px}
.lc-row{display:flex;gap:8px;margin-bottom:11px}
.lc-select{flex:1;height:36px;padding:0 12px;border-radius:9px;background:#FAFAF8;border:1px solid #F0F0EC;font-size:12px;color:#9A9A93;font-family:inherit}
.lc-textarea{width:100%;border-radius:9px;border:1px solid #F0F0EC;padding:10px 12px;font-size:12px;font-family:inherit;outline:none;background:#FAFAF8;resize:vertical;margin-bottom:11px}
.lc-informed-panel{background:#FFF8F8;border:1px solid #FCE7EA;border-radius:11px;padding:12px 14px}
.lc-ip-head{display:flex;align-items:center;gap:6px;margin-bottom:9px}
.lc-ip-head .ms{font-size:15px;color:#E11D48}
.lc-ip-q{font-size:11.5px;font-weight:800;color:#9F1239;flex:1}
.lc-req{font-size:10px;font-weight:700;color:#E11D48;background:#FFE4E6;padding:1px 7px;border-radius:5px}
.lc-ip-opts{display:flex;gap:7px}
.lc-opt{flex:1;text-align:center;padding:8px;border-radius:8px;background:#fff;border:1px solid #E4E4DF;color:#52525B;font-size:12px;font-weight:600;cursor:pointer}
.lc-opt--active{border:1.5px solid #0D9488;color:#0F766E;font-weight:700}
.lc-ip-note{font-size:10.5px;color:#B45369;margin-top:9px;line-height:1.4}
.lc-foot{display:flex;align-items:center;justify-content:space-between;margin-top:11px}
.lc-auto{display:flex;align-items:center;gap:6px;font-size:11px;color:#9A9A93;font-weight:600}
.lc-auto .ms{font-size:15px}

/* Right rail */
.quick-actions{display:flex;flex-direction:column;gap:7px;margin-bottom:0}
.qa-btn{display:flex;align-items:center;gap:11px;padding:12px 14px;border-radius:11px;background:#F6F6F3;border:1px solid #ECECE8;color:#3F3F46;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;text-align:left}
.qa-btn .ms{font-size:19px;color:#0D9488}
.qa-btn--primary{background:#0D9488;color:#fff;border-color:transparent;font-weight:700;box-shadow:0 3px 10px -3px rgba(13,148,136,0.5)}
.qa-btn--primary .ms{color:#fff}
.journey-actions{display:flex;flex-direction:column;gap:7px}
.ja-btn{display:flex;align-items:center;gap:11px;padding:11px 14px;border-radius:11px;font-size:12.5px;font-weight:700;border:none;cursor:pointer;font-family:inherit;text-align:left}
.ja-btn .ms{font-size:18px}
.ja--violet{background:#F5F3FF;color:#6D28D9}
.ja--green{background:#ECFDF5;color:#047857}
.ja--amber{background:#FFF7ED;color:#C2410C}
.ja--red{background:#FFF1F3;color:#E11D48}
.ja--red:disabled{opacity:.4;cursor:not-allowed}
.shield-note{padding:13px;border-radius:12px;background:#FBFBFA;border:1px solid #ECECE8;display:flex;gap:9px;font-size:11px;color:#71717A;line-height:1.45}
.shield-note .ms{font-size:17px;color:#A1A19B;flex:none}

/* Modals */
.modal-overlay{position:fixed;inset:0;background:rgba(17,17,26,.4);display:flex;align-items:center;justify-content:center;z-index:100}
.modal{background:#fff;border-radius:20px;width:560px;max-height:90vh;overflow-y:auto;box-shadow:0 24px 64px -12px rgba(17,17,26,.3)}
.modal--sm{width:420px}
.modal-header{display:flex;align-items:center;justify-content:space-between;padding:22px 24px 0}
.modal-title{font-size:17px;font-weight:800;color:#1C1C1E}
.modal-body{padding:20px 24px;display:flex;flex-direction:column;gap:14px}
.modal-footer{padding:0 24px 22px;display:flex;justify-content:flex-end;gap:10px}
.field{display:flex;flex-direction:column;gap:6px}
label{font-size:12px;font-weight:700;color:#52525B}.req{color:#E11D48}
.input{height:40px;border-radius:11px;border:1px solid #ECECE8;padding:0 14px;font-size:13px;font-family:inherit;outline:none;background:#FAFAF8}
.textarea{border-radius:11px;border:1px solid #ECECE8;padding:12px 14px;font-size:13px;font-family:inherit;outline:none;background:#FAFAF8;resize:vertical}
.select-ctrl{height:40px;padding:0 14px;border-radius:11px;border:1px solid #ECECE8;font-size:13px;font-family:inherit;background:#FAFAF8}
.full{width:100%}
.radio-row{display:flex;gap:16px}.radio-opt{display:flex;align-items:center;gap:6px;font-size:13px;cursor:pointer}
.esc-current{padding:12px;background:#FFF1F3;border-radius:10px;font-size:13px;color:#3F3F46;margin-bottom:4px}
.empty-state-sm{padding:24px;text-align:center;color:#A1A19B;font-size:13px}

.loading-state,.error-state{padding:60px;text-align:center;display:flex;align-items:center;justify-content:center;gap:10px;color:#9A9A93;font-weight:600}
.text--teal{color:#0D9488;font-weight:700}.text--red{color:#E11D48;font-weight:700}.text--amber{color:#D97706;font-weight:700}.text--green{color:#059669;font-weight:700}.text--muted{color:#BDBDB6}.mono{font-family:'JetBrains Mono',monospace}
.icon-btn{width:32px;height:32px;border-radius:9px;border:1px solid #ECECE8;background:#F4F4F1;display:flex;align-items:center;justify-content:center;cursor:pointer}
.btn{display:inline-flex;align-items:center;gap:6px;padding:9px 16px;border-radius:10px;font-size:12.5px;font-weight:700;border:none;cursor:pointer;font-family:inherit}
.btn:disabled{opacity:.5;cursor:not-allowed}
.btn--teal{background:#0D9488;color:#fff;box-shadow:0 2px 8px -2px rgba(13,148,136,.5)}
.btn--danger{background:#FFF1F3;color:#E11D48}
.btn--outline{background:#fff;border:1px solid #ECECE8;color:#52525B}
@keyframes spin{to{transform:rotate(360deg)}}.spin{display:inline-block;animation:spin 1s linear infinite}
@keyframes lav-pulse{0%,100%{box-shadow:0 0 0 0 rgba(225,29,72,.4)}50%{box-shadow:0 0 0 6px rgba(225,29,72,0)}}
.ms{font-family:'Material Symbols Rounded';font-weight:normal;font-style:normal;line-height:1;font-size:18px}
.lav-badge{display:inline-flex;align-items:center;gap:4px;padding:2px 9px;border-radius:6px;font-size:11px;font-weight:700}
.lav-badge--gray{background:#F4F4F1;color:#52525B}.lav-badge--teal{background:#F0FDFA;color:#0D9488}
.lav-badge--red{background:#FEF2F2;color:#B91C1C}.lav-badge--amber{background:#FFF7ED;color:#D97706}
.lav-badge--green{background:#ECFDF5;color:#059669}.lav-badge--violet{background:#F5F3FF;color:#7C3AED}
</style>
