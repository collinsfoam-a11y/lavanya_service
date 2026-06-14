<!--
  Reports — placeholder scaffold (Stitch "Reports Center" screen). Wires the
  shell + heading now; the report tables (lavanya_service.api.manager_reports)
  are a follow-up slice.
-->
<template>
  <AppShell>
    <div class="mb-gutter">
      <h2 class="font-headline-lg text-headline-lg text-on-surface">Reports</h2>
      <p class="font-body-md text-on-surface-variant">Manager service reports</p>
    </div>
    <div
      class="rounded-xl border border-dashed border-outline-variant bg-surface-container-lowest
             p-8 text-center text-on-surface-variant font-body-md"
    >
      Report tables are coming next. The data API
      (<code class="font-label-md">lavanya_service.api.manager_reports.get_manager_dashboard</code>)
      is already live and tested.
    </div>
  </AppShell>
</template>

<script setup>
import AppShell from '@/components/AppShell.vue'
</script>
