<template>
  <span
    class="inline-flex items-center justify-center rounded-full font-label-md text-label-md"
    :class="[
      size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1',
      solid ? 'text-on-primary' : '',
    ]"
    :style="style"
  >
    <slot />
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { hexToRgba } from '@/utils/theme.js'

const props = defineProps({
  color: { type: String, default: 'var(--lav-primary)' },
  textColor: { type: String, default: '#ffffff' },
  size: { type: String, default: 'md' },
  solid: { type: Boolean, default: true },
})

const style = computed(() => {
  if (props.solid) {
    return { backgroundColor: props.color, color: props.textColor }
  }
  return { backgroundColor: hexToRgba(props.color, 0.12), color: props.color }
})
</script>
