<template>
  <div
    class="flex flex-col items-center justify-center text-center p-8 rounded-xl border bg-surface"
    :class="tone === 'error' ? 'border-error/40 bg-error-container/30' : 'border-outline-variant'"
  >
    <span v-if="icon" class="material-symbols-outlined text-5xl mb-3" :class="tone === 'error' ? 'text-error' : 'text-on-surface-variant'" aria-hidden="true">{{ icon }}</span>
    <h3 class="font-headline-md text-headline-md text-on-surface mb-1">{{ title }}</h3>
    <p v-if="description || message" class="font-body-md text-body-md text-on-surface-variant mb-4 max-w-sm">{{ description || message }}</p>
    <slot />
  </div>
</template>

<script setup>
defineProps({
  icon: { type: String, default: 'inbox' },
  title: { type: String, default: 'Nothing here' },
  description: { type: String, default: '' },
  message: { type: String, default: '' },
  tone: { type: String, default: '' },
})
</script>
