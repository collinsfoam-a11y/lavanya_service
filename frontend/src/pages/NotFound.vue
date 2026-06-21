<template>
  <AppShell>
    <div class="py-20 text-center">
      <div class="text-6xl mb-4">404</div>
      <h2 class="font-headline-lg text-headline-lg text-on-surface mb-2">Page not found</h2>
      <p class="font-body-md text-on-surface-variant mb-6">This page doesn't exist or was removed.</p>
      <router-link to="/" class="inline-flex px-5 h-10 rounded-lg bg-primary text-on-primary font-label-md text-body-md items-center">
        Back to Today's Work
      </router-link>
    </div>
  </AppShell>
</template>

<script setup>
import AppShell from '@/components/AppShell.vue'
</script>
