<template>
  <div
    class="rounded-xl border bg-surface transition-shadow"
    :class="[
      elevated ? 'shadow-sm' : '',
      hover ? 'hover:shadow-md' : '',
      padding === 'default' ? 'p-4' : padding === 'compact' ? 'p-3' : 'p-0',
      interactive ? 'cursor-pointer' : '',
    ]"
  >
    <slot />
  </div>
</template>

<script setup>
defineProps({
  elevated: { type: Boolean, default: true },
  hover: { type: Boolean, default: false },
  padding: { type: String, default: 'default' },
  interactive: { type: Boolean, default: false },
})
</script>
