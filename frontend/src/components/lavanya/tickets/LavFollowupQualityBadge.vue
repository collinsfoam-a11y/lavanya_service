<template>
  <span
    class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-label-md text-label-md"
    :style="{ backgroundColor: bg, color: fg }"
    :title="reason"
  >
    <span class="w-2 h-2 rounded-full" :style="{ backgroundColor: fg }" aria-hidden="true"></span>
    {{ level }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { computeFollowupQuality, qualityReason, qualityColor } from '@/utils/followup-quality.js'
import { hexToRgba } from '@/utils/theme.js'

const props = defineProps({
  ticket: { type: Object, required: true },
})

const level = computed(() => computeFollowupQuality(props.ticket))
const reason = computed(() => qualityReason(props.ticket))
const color = computed(() => qualityColor(level.value))
const bg = computed(() => hexToRgba(color.value, 0.12))
const fg = computed(() => color.value)
</script>
