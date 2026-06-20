<template>
  <div class="relative">
    <button
      type="button"
      ref="trigger"
      @click="open = !open"
      @keydown="onKeydown"
      class="flex items-center gap-2 px-3 py-2 rounded-lg border border-outline-variant bg-surface-container-low text-on-surface hover:bg-surface-container-high transition-colors"
      :aria-expanded="open"
      aria-haspopup="listbox"
      :aria-label="`Current theme: ${currentLabel}. Change theme`"
    >
      <span class="material-symbols-outlined" aria-hidden="true">palette</span>
      <span class="hidden sm:inline font-label-md text-label-md">{{ currentLabel }}</span>
      <span class="material-symbols-outlined" aria-hidden="true">expand_more</span>
    </button>

    <div
      v-if="open"
      ref="panel"
      role="listbox"
      aria-label="Theme selector"
      class="absolute right-0 mt-2 w-64 rounded-xl shadow-xl border border-outline-variant bg-surface-container-lowest z-50 overflow-hidden"
    >
      <div class="px-3 py-2 text-label-md font-label-md text-on-surface-variant border-b border-outline-variant">
        Choose theme
      </div>
      <button
        v-for="t in themes"
        :key="t.name"
        role="option"
        :aria-selected="t.active"
        @click="select(t.name)"
        class="w-full text-left px-3 py-2 flex items-center gap-3 hover:bg-surface-container-low transition-colors"
        :class="t.active ? 'bg-surface-container-high' : ''"
      >
        <span
          class="w-6 h-6 rounded-full border border-outline-variant shrink-0"
          :style="swatchStyle(t.name)"
          aria-hidden="true"
        />
        <div class="flex-1 min-w-0">
          <div class="font-body-md text-body-md text-on-surface truncate">{{ t.label }}</div>
          <div class="font-label-md text-label-md text-on-surface-variant truncate">{{ t.description }}</div>
        </div>
        <span v-if="t.active" class="material-symbols-outlined text-primary" aria-hidden="true">check</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useTheme, DEFAULT_THEME } from '@/composables/useTheme.js'

const { theme, themes, setTheme } = useTheme()
const open = ref(false)
const trigger = ref(null)
const panel = ref(null)

const currentLabel = computed(() => {
  const t = themes.value.find((x) => x.active)
  return t ? t.label : DEFAULT_THEME
})

function select(name) {
  setTheme(name)
  open.value = false
  trigger.value?.focus()
}

function swatchStyle(name) {
  const map = {
    'lavanya-light': 'linear-gradient(135deg, #f8f9ff 50%, #004ac6 50%)',
    'lavanya-dark': 'linear-gradient(135deg, #1a1c2e 50%, #8ab4f8 50%)',
    'lavanya-blue': 'linear-gradient(135deg, #f0f7ff 50%, #005ce6 50%)',
    'lavanya-green': 'linear-gradient(135deg, #f0fdf4 50%, #15803d 50%)',
    'high-contrast': 'linear-gradient(135deg, #000000 50%, #ffff00 50%)',
    'compact-counter': 'linear-gradient(135deg, #f8f9ff 50%, #004ac6 50%)',
  }
  return { background: map[name] || map[DEFAULT_THEME] }
}

function onKeydown(e) {
  if (e.key === 'Escape' && open.value) {
    e.preventDefault()
    open.value = false
    trigger.value?.focus()
  }
}

function onClickOutside(e) {
  if (open.value && !trigger.value?.contains(e.target) && !panel.value?.contains(e.target)) {
    open.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', onClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside)
})
</script>
