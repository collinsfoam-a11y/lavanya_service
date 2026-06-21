<template>
  <!-- card-list: metric grid + queue rows (matches Today's Work / Tickets) -->
  <div v-if="layout === 'card-list'">
    <div class="lav-metric-grid mb-gutter">
      <div v-for="i in 6" :key="'m' + i" class="lav-metric" style="pointer-events:none">
        <div class="lav-skeleton" style="width:20px;height:20px;border-radius:999px"></div>
        <div style="display:flex;flex-direction:column;gap:4px">
          <div class="lav-skeleton" style="width:70px;height:12px"></div>
          <div class="lav-skeleton" style="width:30px;height:20px"></div>
        </div>
      </div>
    </div>
    <div class="flex flex-col gap-2">
      <div v-for="i in 5" :key="'r' + i" class="lav-skeleton" style="width:100%;height:52px;border-radius:8px"></div>
    </div>
  </div>
  <!-- rows: simple stacked skeleton bars -->
  <div v-else class="space-y-3 p-4">
    <div v-for="i in lines" :key="i" class="lav-skeleton h-4 rounded" :style="{ width: (100 - (i % 3) * 20) + '%' }" />
  </div>
</template>

<script setup>
defineProps({
  lines: { type: Number, default: 4 },
  layout: { type: String, default: 'rows' },
})
</script>
