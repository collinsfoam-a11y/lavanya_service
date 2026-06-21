<!--
  ActionScreen — Engine-driven outcome capture screen.
  Shows the primary action for a ticket with outcome-specific buttons.
  Replaces manual form filling with verb-specific outcome capture.
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
                <p class="font-body-sm text-on-surface-variant">{{ ticket?.customer_name }} · {{ ticket?.brand }}</p>
              </div>
            </div>
            <div class="lav-action-header__right">
              <SlaBadge :ticket="ticket" />
            </div>
          </div>

          <!-- Ticket Summary -->
          <div class="lav-action-summary">
            <div class="lav-summary-row">
              <span class="font-label-md text-on-surface-variant">Product</span>
              <span class="font-body-md text-on-surface">{{ ticket?.product_type || 'N/A' }}</span>
            </div>
            <div class="lav-summary-row">
              <span class="font-label-md text-on-surface-variant">Stage</span>
              <span class="font-body-md text-on-surface">{{ ticket?.current_service_stage || 'N/A' }}</span>
            </div>
            <div class="lav-summary-row">
              <span class="font-label-md text-on-surface-variant">Flow</span>
              <span class="font-body-md text-on-surface">{{ ticket?.service_flow_type || 'N/A' }}</span>
            </div>
          </div>

          <!-- Primary Action Section -->
          <div v-if="primaryAction" class="lav-action-section">
            <div class="lav-action-section__header">
              <span class="material-symbols-outlined" :style="{ color: primaryActionColor }">
                {{ primaryActionIcon }}
              </span>
              <h3 class="font-headline-sm text-headline-sm text-on-surface">
                {{ primaryActionLabel }}
              </h3>
            </div>
            
            <!-- Outcome Buttons -->
            <div class="lav-outcome-buttons">
              <button
                v-for="outcome in primaryAction.outcomes"
                :key="outcome.value"
                class="lav-outcome-btn"
                :class="{
                  'lav-outcome-btn--success': outcome.value === 'success',
                  'lav-outcome-btn--partial': outcome.value === 'partial',
                  'lav-outcome-btn--failed': outcome.value === 'failed',
                  'lav-outcome-btn--parked': outcome.value === 'parked',
                }"
                @click="handleOutcome(outcome)"
                :disabled="submitting"
              >
                <span class="material-symbols-outlined">{{ outcome.icon }}</span>
                <span class="font-label-lg text-label-lg">{{ outcome.label }}</span>
              </button>
            </div>
          </div>

          <!-- Successor Actions (shown after submission) -->
          <div v-if="successorActions.length" class="lav-action-section lav-successor-section">
            <div class="lav-action-section__header">
              <span class="material-symbols-outlined" style="color: var(--lav-primary)">arrow_forward</span>
              <h3 class="font-headline-sm text-headline-sm text-on-surface">
                Successor Actions
              </h3>
            </div>
            <div class="lav-successor-list">
              <div
                v-for="(action, idx) in successorActions"
                :key="idx"
                class="lav-successor-item"
              >
                <span class="material-symbols-outlined" :style="{ color: getActionColor(action) }">
                  {{ getActionIcon(action) }}
                </span>
                <div class="lav-successor-item__text">
                  <span class="font-body-md text-on-surface">{{ getActionLabel(action) }}</span>
                  <span v-if="action.due_in_days" class="font-body-sm text-on-surface-variant">
                    Due in {{ action.due_in_days }} days
                  </span>
                </div>
              </div>
            </div>
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
import { ref, computed, onMounted, watch } from 'vue'
import { call } from '@/api'
import SlaBadge from '@/components/SlaBadge.vue'
import { resolveActions as resolveEngineActions, getPrimaryAction, ACTION_REGISTRY as ENGINE_REGISTRY } from '@/config/outcome-map.js'

const props = defineProps({
  ticketId: { type: String, required: true },
})

const emit = defineEmits(['close', 'refresh'])

const ticket = ref(null)
const visible = ref(false)
const submitting = ref(false)
const submitted = ref(false)
const successorActions = ref([])

const primaryAction = computed(() => ticket.value ? getPrimaryAction(ticket.value) : null)
const primaryActionLabel = computed(() => primaryAction.value ? (ENGINE_REGISTRY[primaryAction.value.action]?.label || primaryAction.value.action) : '')
const primaryActionIcon = computed(() => primaryAction.value ? (ENGINE_REGISTRY[primaryAction.value.action]?.icon || 'touch_app') : 'touch_app')
const primaryActionColor = computed(() => primaryAction.value ? (ENGINE_REGISTRY[primaryAction.value.action]?.color || 'var(--lav-primary)') : 'var(--lav-primary)')

function getActionLabel(action) {
  return ENGINE_REGISTRY[action.action]?.label || action.action
}

function getActionIcon(action) {
  return ENGINE_REGISTRY[action.action]?.icon || 'touch_app'
}

function getActionColor(action) {
  return ENGINE_REGISTRY[action.action]?.color || 'var(--lav-primary)'
}

async function loadTicket() {
  try {
    const result = await call('lavanya_service.api.stitch_console.get_ticket_detail', {
      name: props.ticketId,
    })
    ticket.value = result
    visible.value = true
  } catch (e) {
    console.error('Failed to load ticket:', e)
    emit('close')
  }
}

async function handleOutcome(outcome) {
  if (submitting.value || !primaryAction.value) return
  
  submitting.value = true
  try {
    const actionDef = ENGINE_REGISTRY[primaryAction.value.action]
    if (!actionDef || !actionDef.endpoint) {
      throw new Error('No endpoint defined for action: ' + primaryAction.value.action)
    }

    // Build payload from outcome data
    const payload = {
      name: props.ticketId,
      action_type: primaryAction.value.action,
      outcome: outcome.value,
      ...outcome.payload,
    }

    // Call the backend endpoint
    await call(actionDef.endpoint, payload)
    
    submitted.value = true
    
    // Reload ticket to get successor actions
    await loadTicket()
    
    // Emit refresh to update the parent
    emit('refresh')
    
    // Auto-close after 2 seconds
    setTimeout(() => {
      emit('close')
    }, 2000)
  } catch (e) {
    console.error('Failed to record outcome:', e)
    // TODO: Show error toast
  } finally {
    submitting.value = false
  }
}

onMounted(loadTicket)

watch(() => props.ticketId, (newId) => {
  if (newId) {
    submitted.value = false
    successorActions.value = []
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

.lav-outcome-buttons {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.lav-outcome-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 16px 8px;
  border-radius: 12px;
  border: 2px solid var(--lav-outline);
  background: var(--lav-surface);
  color: var(--lav-on-surface);
  cursor: pointer;
  transition: all 0.2s ease;
}

.lav-outcome-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.lav-outcome-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.lav-outcome-btn--success {
  border-color: var(--lav-success);
  color: var(--lav-success);
}

.lav-outcome-btn--success:hover:not(:disabled) {
  background: var(--lav-success);
  color: white;
}

.lav-outcome-btn--partial {
  border-color: var(--lav-warning);
  color: var(--lav-warning);
}

.lav-outcome-btn--partial:hover:not(:disabled) {
  background: var(--lav-warning);
  color: white;
}

.lav-outcome-btn--failed {
  border-color: var(--lav-danger);
  color: var(--lav-danger);
}

.lav-outcome-btn--failed:hover:not(:disabled) {
  background: var(--lav-danger);
  color: white;
}

.lav-outcome-btn--parked {
  border-color: var(--lav-on-surface-variant);
  color: var(--lav-on-surface-variant);
}

.lav-outcome-btn--parked:hover:not(:disabled) {
  background: var(--lav-on-surface-variant);
  color: white;
}

.lav-successor-section {
  background: var(--lav-surface-variant);
  border-radius: 12px;
  padding: 12px;
  border-top: none;
}

.lav-successor-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.lav-successor-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  background: var(--lav-surface);
  border-radius: 8px;
}

.lav-successor-item__text {
  display: flex;
  flex-direction: column;
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
