<template>
  <div class="flex items-center gap-2 mb-3">
    <span v-if="icon" class="material-symbols-outlined" :style="{ color: accent }" aria-hidden="true">{{ icon }}</span>
    <h2 class="font-headline-md text-headline-md text-on-surface" :style="accent ? { color: accent } : {}">{{ title }}</h2>
    <span v-if="badge != null && badge !== ''" class="ml-1 inline-flex items-center justify-center min-w-[1.5rem] h-6 px-2 rounded-full font-label-md text-label-md text-on-primary" :style="{ background: accent || 'var(--lav-primary)' }">{{ badge }}</span>
    <div v-if="$slots.actions" class="ml-auto">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  icon: { type: String, default: '' },
  badge: { type: [String, Number], default: null },
  accent: { type: String, default: '' },
})
</script>
