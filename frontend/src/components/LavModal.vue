<template>
  <Teleport to="body">
    <div
      v-if="show"
      ref="dialogRef"
      class="fixed inset-0 bg-inverse-surface/40 backdrop-blur-sm flex items-center justify-center p-4 z-50"
      @click.self="onBackdrop"
      @keydown.escape="onEscape"
      role="dialog"
      :aria-modal="true"
      :aria-label="title"
      :aria-describedby="bodyId"
      tabindex="-1"
    >
      <div
        ref="panelRef"
        class="bg-surface-container-lowest rounded-xl w-full shadow-[0_10px_15px_-3px_rgba(0,0,0,0.1)] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-200"
        :class="maxWidthClass"
        :style="{ maxHeight: '90vh' }"
        @click.stop
      >
        <div class="px-6 py-5 border-b border-outline-variant/30 flex justify-between items-center bg-surface-bright">
          <div class="flex items-center gap-3 min-w-0">
            <div
              v-if="icon"
              class="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
              :class="iconBgClass"
            >
              <span class="material-symbols-outlined">{{ icon }}</span>
            </div>
            <div class="min-w-0">
              <h2 class="text-headline-md font-headline-md text-on-surface truncate">{{ title }}</h2>
              <p v-if="subtitle" class="text-body-md font-body-md text-on-surface-variant mt-1 truncate">{{ subtitle }}</p>
            </div>
          </div>
          <button
            v-if="closable !== false"
            @click="close"
            class="text-on-surface-variant hover:text-on-surface transition-colors rounded-full p-1 hover:bg-surface-variant/50 shrink-0"
            :aria-label="'Close ' + title"
          >
            <span class="material-symbols-outlined" aria-hidden="true">close</span>
          </button>
        </div>

        <div :id="bodyId" class="px-6 py-6 space-y-6 overflow-y-auto">
          <div v-if="error" class="p-3 bg-error-container text-on-error-container rounded font-body-md" role="alert" aria-live="assertive">
            {{ error }}
          </div>
          <slot />
        </div>

        <div
          v-if="$slots.footer || showFooter"
          class="px-6 py-4 bg-surface-bright border-t border-outline-variant/30 flex justify-end gap-3 rounded-b-xl"
        >
          <slot name="footer">
            <button
              ref="cancelBtnRef"
              @click="close"
              :disabled="loading"
              class="px-5 h-10 rounded-lg text-body-md font-body-md font-medium text-on-surface-variant hover:bg-surface-variant/50 transition-colors border border-transparent disabled:opacity-50"
              type="button"
            >
              Cancel
            </button>
            <button
              ref="submitBtnRef"
              @click="onSubmit"
              :disabled="loading || submitDisabled"
              class="px-5 h-10 rounded-lg text-body-md font-body-md font-medium text-on-primary hover:opacity-90 transition-all shadow-sm flex items-center gap-2 disabled:opacity-50"
              :class="danger ? 'bg-error' : 'bg-primary'"
              type="button"
              :aria-label="submitLabel || 'Submit'"
            >
              <span v-if="loading" class="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
              <span v-else class="material-symbols-outlined text-[18px]">{{ submitIcon }}</span>
              {{ submitLabel || 'Submit' }}
            </button>
          </slot>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, nextTick, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  show: { type: Boolean, default: false },
  title: { type: String, default: '' },
  subtitle: { type: String, default: '' },
  icon: { type: String, default: '' },
  iconBg: { type: String, default: '' },
  danger: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  submitDisabled: { type: Boolean, default: false },
  submitLabel: { type: String, default: '' },
  submitIcon: { type: String, default: 'check_circle' },
  closable: { type: Boolean, default: true },
  maxWidth: { type: String, default: 'lg' },
  showFooter: { type: Boolean, default: true },
  error: { type: String, default: '' },
  bodyId: { type: String, default: '' },
})

const emit = defineEmits(['close', 'submit', 'backdrop'])

const panelRef = ref(null)
const dialogRef = ref(null)
const cancelBtnRef = ref(null)
const submitBtnRef = ref(null)

const uid = `lav-modal-${Math.random().toString(36).slice(2, 9)}`
const bodyId = computed(() => props.bodyId || `${uid}-body`)

const maxWidthClass = computed(() => {
  const m = { sm: 'max-w-sm', md: 'max-w-md', lg: 'max-w-lg', xl: 'max-w-2xl', '2xl': 'max-w-4xl' }
  return m[props.maxWidth] || 'max-w-lg'
})

const iconBgClass = computed(() => {
  if (props.iconBg) return props.iconBg
  return props.danger ? 'bg-error-container text-error' : 'bg-primary-container text-on-primary'
})

let previousFocus = null

watch(() => props.show, (val) => {
  if (val) {
    previousFocus = document.activeElement
    nextTick(() => {
      const focusable = panelRef.value?.querySelectorAll('input, select, textarea, button, [tabindex]:not([tabindex="-1"])')
      if (focusable && focusable.length) {
        if (props.danger) {
          focusable[focusable.length - 1].focus()
        } else {
          focusable[0].focus()
        }
      }
    })
  }
})

function getFocusable() {
  if (!panelRef.value) return []
  return Array.from(panelRef.value.querySelectorAll('input, select, textarea, button, [tabindex]:not([tabindex="-1"])'))
    .filter(el => el.tabIndex !== -1 && !el.disabled)
}

function handleKeydown(e) {
  if (!props.show) return
  if (e.key !== 'Tab') return
  const focusable = getFocusable()
  if (focusable.length === 0) return
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (e.shiftKey && document.activeElement === first) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && document.activeElement === last) {
    e.preventDefault()
    first.focus()
  }
}

onMounted(() => document.addEventListener('keydown', handleKeydown))
onUnmounted(() => document.removeEventListener('keydown', handleKeydown))

function close() {
  emit('close')
  if (previousFocus && typeof previousFocus.focus === 'function') {
    nextTick(() => {
      try { previousFocus.focus() } catch (_) {}
    })
  }
}

function onEscape() {
  if (props.closable) close()
}

function onBackdrop() {
  if (props.closable) emit('backdrop')
}

function onSubmit() {
  emit('submit')
}
</script>
