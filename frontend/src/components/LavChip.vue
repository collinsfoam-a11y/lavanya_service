<template>
  <button
    type="button"
    class="inline-flex items-center rounded-full border font-label-md text-label-md transition-colors"
    :class="[
      active
        ? 'bg-primary text-on-primary border-primary'
        : 'bg-surface text-on-surface-variant border-outline-variant hover:bg-surface-container-low',
      size === 'sm' ? 'px-2.5 py-1' : 'px-3 py-1.5',
    ]"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup>
defineProps({
  active: { type: Boolean, default: false },
  size: { type: String, default: 'md' },
})
defineEmits(['click'])
</script>
