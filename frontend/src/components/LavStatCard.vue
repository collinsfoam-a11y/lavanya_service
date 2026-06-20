<template>
  <div
    class="relative overflow-hidden rounded-xl border bg-surface p-4 flex flex-col justify-between cursor-pointer transition-transform"
    :class="hover ? 'hover:-translate-y-1 hover:shadow-md' : ''"
    :style="{ borderLeft: '4px solid ' + accent }"
    @click="$emit('click', $event)"
  >
    <span class="material-symbols-outlined absolute -right-3 -top-3 text-7xl opacity-5" :style="{ color: accent }" aria-hidden="true">{{ icon }}</span>
    <div class="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant relative z-10">{{ label }}</div>
    <div class="font-display text-display text-on-surface relative z-10" :style="{ color: accent }">{{ value }}</div>
    <div v-if="caption || sub" class="font-label-md text-label-md text-on-surface-variant relative z-10">{{ caption || sub }}</div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  icon: { type: String, default: 'label' },
  accent: { type: String, default: 'var(--lav-primary)' },
  sub: { type: String, default: '' },
  caption: { type: String, default: '' },
  hover: { type: Boolean, default: true },
})
defineEmits(['click'])
</script>
