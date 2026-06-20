<template>
  <div @keydown="onKey">
    <div v-if="fatal" class="fixed inset-0 z-[100] bg-surface-container-lowest flex items-center justify-center p-8">
      <div class="max-w-md text-center">
        <div class="text-5xl mb-4">!</div>
        <h2 class="font-headline-lg text-headline-lg text-on-surface mb-2">Something went wrong</h2>
        <p class="font-body-md text-on-surface-variant mb-6">{{ fatal }}</p>
        <button @click="recover" class="px-5 h-10 rounded-lg bg-primary text-on-primary font-label-md text-body-md">
          Reload
        </button>
      </div>
    </div>

    <!-- Keyboard shortcuts help overlay -->
    <div v-if="showShortcuts" class="fixed inset-0 z-50 bg-black/30 flex items-center justify-center" @click="showShortcuts = false">
      <div class="bg-surface-container-lowest rounded-xl shadow-xl p-6 max-w-sm w-full mx-4" @click.stop>
        <h3 class="font-headline-md text-headline-md text-on-surface mb-4">Keyboard shortcuts</h3>
        <div class="flex flex-col gap-2 font-body-md">
          <div class="flex justify-between"><kbd class="px-2 py-0.5 bg-surface-container-high rounded text-label-md font-label-md">g</kbd> <kbd class="px-2 py-0.5 bg-surface-container-high rounded text-label-md font-label-md">h</kbd> <span class="text-on-surface-variant">→</span> <span>Home (Today's Work)</span></div>
          <div class="flex justify-between"><kbd class="px-2 py-0.5 bg-surface-container-high rounded text-label-md font-label-md">g</kbd> <kbd class="px-2 py-0.5 bg-surface-container-high rounded text-label-md font-label-md">t</kbd> <span class="text-on-surface-variant">→</span> <span>Tickets</span></div>
          <div class="flex justify-between"><kbd class="px-2 py-0.5 bg-surface-container-high rounded text-label-md font-label-md">g</kbd> <kbd class="px-2 py-0.5 bg-surface-container-high rounded text-label-md font-label-md">n</kbd> <span class="text-on-surface-variant">→</span> <span>New Ticket</span></div>
          <div class="flex justify-between"><kbd class="px-2 py-0.5 bg-surface-container-high rounded text-label-md font-label-md">g</kbd> <kbd class="px-2 py-0.5 bg-surface-container-high rounded text-label-md font-label-md">r</kbd> <span class="text-on-surface-variant">→</span> <span>Reports</span></div>
          <div class="flex justify-between"><kbd class="px-2 py-0.5 bg-surface-container-high rounded text-label-md font-label-md">g</kbd> <kbd class="px-2 py-0.5 bg-surface-container-high rounded text-label-md font-label-md">s</kbd> <span class="text-on-surface-variant">→</span> <span>Settings</span></div>
          <div class="flex justify-between"><kbd class="px-2 py-0.5 bg-surface-container-high rounded text-label-md font-label-md">?</kbd> <span class="text-on-surface-variant">→</span> <span>Toggle this help</span></div>
          <div class="flex justify-between"><kbd class="px-2 py-0.5 bg-surface-container-high rounded text-label-md font-label-md">Esc</kbd> <span class="text-on-surface-variant">→</span> <span>Close drawer / help</span></div>
        </div>
        <button @click="showShortcuts = false" class="mt-6 w-full py-2 rounded-lg border border-outline-variant text-primary font-label-md hover:bg-surface-container-low">
          Close
        </button>
      </div>
    </div>

    <router-view v-if="!fatal" />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, onErrorCaptured } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '@/composables/useTheme.js'

const router = useRouter()
const fatal = ref(null)
const showShortcuts = ref(false)
useTheme()

// Keyboard navigation shortcuts (two-key sequences like g+t, g+h)
let pendingG = false
function onKey(e) {
  // Don't trigger shortcuts when typing in inputs
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) return

  if (e.key === '?') {
    showShortcuts.value = !showShortcuts.value
    return
  }
  if (e.key === 'g' && !pendingG) {
    pendingG = true
    setTimeout(() => { pendingG = false }, 800)
    return
  }
  if (pendingG) {
    pendingG = false
    if (e.key === 'h') router.push('/')
    else if (e.key === 't') router.push('/tickets')
    else if (e.key === 'n') router.push('/new-ticket')
    else if (e.key === 'r') router.push('/reports')
    else if (e.key === 's') router.push('/settings')
  }
}

onMounted(() => document.addEventListener('keydown', onKey))
onUnmounted(() => document.removeEventListener('keydown', onKey))

onErrorCaptured((err) => {
  fatal.value = err.message || 'An unexpected error occurred.'
  return false
})
function recover() {
  fatal.value = null
  window.location.reload()
}
</script>
