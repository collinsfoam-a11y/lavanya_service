<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
    <div
      v-for="lock in locks"
      :key="lock.key"
      class="flex items-center gap-3 p-3 rounded-lg border"
      :class="lock.locked ? 'border-danger bg-danger-container/10' : 'border-outline-variant bg-surface-container-low'"
    >
      <span
        class="material-symbols-outlined"
        :class="lock.locked ? 'text-danger' : 'text-success'"
        aria-hidden="true"
      >{{ lock.locked ? 'lock' : 'lock_open' }}</span>
      <div>
        <div class="font-body-md text-body-md text-on-surface">{{ lock.label }}</div>
        <div class="font-label-md text-label-md text-on-surface-variant">{{ lock.locked ? 'Blocked' : 'Allowed' }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  locks: { type: Array, required: true },
})
</script>
