<!--
  ActionScreen — Engine-driven outcome capture screen.
  Shows the primary action for a ticket with its configured form fields.
  Uses the same action definitions as OUTCOME_MAP / ACTION_REGISTRY.
-->
<template>
  <Teleport to="body">
    <transition name="lav-slide-up">
      <div v-if="visible" class="lav-action-screen" @click.self="$emit('close')">
        <div class="lav-action-panel">
          <!-- Header -->
          <div class="lav-action-header">
            <div class="lav-action-header__left">
              <button class="lav-icon-btn" @click="$emit('close')" aria-label="Close">
                <span class="material-symbols-outlined">close</span>
              </button>
              <div>
                <h2 class="font-headline-md text-headline-md text-on-surface">{{ ticket?.name }}</h2>
                <p class="font-body-sm text-on-surface-variant">{{ ticket?.customer_name }} · {{ ticket?.product?.brand || '' }}</p>
              </div>
            </div>
            <div class="lav-action-header__right">
              <SlaBadge
                :agreement-status="ticket?.sla?.agreement_status"
                :response-by="ticket?.sla?.response_by"
                :resolution-by="ticket?.sla?.resolution_by"
              />
            </div>
          </div>

          <!-- Ticket Summary -->
          <div class="lav-action-summary">
            <div class="lav-summary-row">
              <span class="font-label-md text-on-surface-variant">Product</span>
              <span class="font-body-md text-on-surface">{{ ticket?.product?.item || ticket?.product?.type || 'N/A' }}</span>
            </div>
            <div class="lav-summary-row">
              <span class="font-label-md text-on-surface-variant">Stage</span>
              <span class="font-body-md text-on-surface">{{ ticket?.stage?.current_service_stage || 'N/A' }}</span>
            </div>
            <div class="lav-summary-row">
              <span class="font-label-md text-on-surface-variant">Flow</span>
              <span class="font-body-md text-on-surface">{{ ticket?.stage?.service_flow_type || 'N/A' }}</span>
            </div>
          </div>

          <!-- Primary Action Section — form-based -->
          <div v-if="primaryAction" class="lav-action-section">
            <div class="lav-action-section__header">
              <span class="material-symbols-outlined" :style="{ color: primaryActionColor }">
                {{ primaryActionIcon }}
              </span>
              <h3 class="font-headline-sm text-headline-sm text-on-surface">
                {{ primaryActionLabel }}
              </h3>
            </div>

            <!-- Action fields form -->
            <form class="space-y-3" @submit.prevent="submitAction">
              <div v-for="f in actionFields" :key="f.key" class="space-y-1">
                <label class="text-label-md font-label-md text-on-surface-variant block">
                  {{ f.label }} <span v-if="isRequiredField(f)" class="text-error">*</span>
                </label>
                <select
                  v-if="f.type === 'select'"
                  v-model="actionForm[f.key]"
                  class="w-full h-10 px-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow"
                >
                  <option value="" disabled>Select...</option>
                  <option v-for="o in f.options" :key="o" :value="o">{{ o }}</option>
                </select>
                <textarea
                  v-else-if="f.type === 'textarea'"
                  v-model="actionForm[f.key]"
                  rows="3"
                  :placeholder="f.placeholder || ''"
                  class="w-full p-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow resize-none"
                ></textarea>
                <input
                  v-else
                  v-model="actionForm[f.key]"
                  :type="f.type || 'text'"
                  :placeholder="f.placeholder || ''"
                  class="w-full h-10 px-3 bg-surface-container-lowest border border-outline-variant rounded-lg text-on-surface text-body-md focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-shadow"
                />
                <p v-if="f.hint" class="text-label-md font-label-md text-on-surface-variant">{{ f.hint }}</p>
              </div>
              <button
                type="submit"
                :disabled="submitting || !actionValid"
                class="w-full px-4 py-3 rounded-xl font-label-md bg-primary text-on-primary hover:opacity-90 active:scale-[0.98] transition-all disabled:opacity-50 font-bold"
              >
                {{ primaryActionLabel }}
              </button>
            </form>
          </div>

          <!-- No action available -->
          <div v-else class="lav-action-section text-center py-6">
            <span class="material-symbols-outlined text-on-surface-variant" style="font-size:32px">check_circle</span>
            <p class="font-body-md text-on-surface-variant mt-2">No action required for this ticket.</p>
          </div>

          <!-- Error message -->
          <div v-if="actionError" class="rounded-lg bg-error-container text-on-error-container p-3 font-body-md flex items-center gap-2">
            <span class="material-symbols-outlined" style="font-size:18px">error</span>
            {{ actionError }}
          </div>

          <!-- Loading State -->
          <div v-if="submitting" class="lav-action-loading">
            <div class="lav-spinner"></div>
            <span class="font-body-md text-on-surface-variant">Recording outcome...</span>
          </div>

          <!-- Success Message -->
          <div v-if="submitted" class="lav-action-success">
            <span class="material-symbols-outlined" style="color: var(--lav-success); font-size: 32px">check_circle</span>
            <span class="font-body-md text-on-surface">Outcome recorded successfully</span>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { call } from '@/api'
import SlaBadge from '@/components/SlaBadge.vue'
import { getPrimaryAction, ACTION_REGISTRY as ENGINE_REGISTRY } from '@/config/outcome-map.js'
import { useToast } from '@/utils/toast'

const { show: showToast } = useToast()

const props = defineProps({
  ticketId: { type: String, required: true },
})

const emit = defineEmits(['close', 'refresh'])

const ticket = ref(null)
const visible = ref(false)
const submitting = ref(false)
const submitted = ref(false)
const actionError = ref('')

const primaryAction = computed(() => ticket.value ? getPrimaryAction(ticket.value) : null)
const primaryActionLabel = computed(() => primaryAction.value?.label || primaryAction.value?.key || '')
const primaryActionIcon = computed(() => primaryAction.value?.icon || 'touch_app')
const primaryActionColor = computed(() => {
  const c = primaryAction.value?.color
  if (!c) return 'var(--lav-primary)'
  if (c.startsWith('var(') || c.startsWith('#') || c.startsWith('rgb')) return c
  return `var(--lav-${c})`
})

const actionForm = reactive({})
const actionFields = computed(() => primaryAction.value?.fields || [])

watch(primaryAction, (action) => {
  Object.keys(actionForm).forEach(k => delete actionForm[k])
  if (action?.fields) {
    for (const f of action.fields) actionForm[f.key] = ''
  }
}, { immediate: true })

function isRequiredField(f) {
  return typeof f.required === 'function' ? f.required(actionForm) : !!f.required
}

const actionValid = computed(() => {
  const action = primaryAction.value
  if (!action) return false
  return (action.fields || []).every(f => !isRequiredField(f) || String(actionForm[f.key] ?? '').trim() !== '')
})

async function loadTicket() {
  try {
    const result = await call('lavanya_service.api.stitch_console.get_ticket_detail', {
      ticket_id: props.ticketId,
    })
    ticket.value = result
    visible.value = true
  } catch (e) {
    console.error('Failed to load ticket:', e)
    showToast('Failed to load ticket', 'error')
    emit('close')
  }
}

async function submitAction() {
  if (!actionValid.value || !primaryAction.value) return

  submitting.value = true
  actionError.value = ''
  try {
    const endpoint = primaryAction.value.endpoint
    if (!endpoint) {
      throw new Error('No endpoint defined for action: ' + primaryAction.value.key)
    }

    const payload = { ticket_name: props.ticketId }
    for (const f of primaryAction.value.fields || []) {
      const v = String(actionForm[f.key] ?? '').trim()
      if (v) payload[f.key] = v
    }

    await call(endpoint, payload)
    submitted.value = true
    showToast('Outcome recorded successfully')
    emit('refresh')

    setTimeout(() => emit('close'), 2000)
  } catch (e) {
    actionError.value = e.message || 'Action failed'
    showToast(e.message || 'Action failed', 'error')
  } finally {
    submitting.value = false
  }
}

onMounted(loadTicket)

watch(() => props.ticketId, (newId) => {
  if (newId) {
    submitted.value = false
    actionError.value = ''
    loadTicket()
  }
})
</script>

<style scoped>
.lav-action-screen {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
}

.lav-action-panel {
  width: 100%;
  max-width: 480px;
  max-height: 85vh;
  background: var(--lav-surface);
  border-radius: 16px 16px 0 0;
  box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.15);
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.lav-action-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.lav-action-header__left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.lav-action-header__right {
  flex-shrink: 0;
}

.lav-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--lav-on-surface);
  cursor: pointer;
  transition: background 0.2s;
}

.lav-icon-btn:hover {
  background: var(--lav-surface-variant);
}

.lav-action-summary {
  background: var(--lav-surface-variant);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.lav-summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.lav-action-section {
  border-top: 1px solid var(--lav-outline-variant);
  padding-top: 16px;
}

.lav-action-section__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.lav-action-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px;
}

.lav-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--lav-outline);
  border-top-color: var(--lav-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.lav-action-success {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px;
  background: color-mix(in srgb, var(--lav-success) 10%, transparent);
  border-radius: 12px;
}

/* Transitions */
.lav-slide-up-enter-active,
.lav-slide-up-leave-active {
  transition: opacity 0.3s ease;
}

.lav-slide-up-enter-active .lav-action-panel,
.lav-slide-up-leave-active .lav-action-panel {
  transition: transform 0.3s ease;
}

.lav-slide-up-enter-from,
.lav-slide-up-leave-to {
  opacity: 0;
}

.lav-slide-up-enter-from .lav-action-panel,
.lav-slide-up-leave-to .lav-action-panel {
  transform: translateY(100%);
}
</style>
