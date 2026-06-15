<!--
  Reports Center — ported from the Stitch "Reports Center" screen.
  Read-only manager KPIs from lavanya_service.api.manager_reports.get_manager_dashboard
  (role-aware: non-managers see operational counts only). Grouped metric cards
  reuse the Stitch lav-metric styling.
-->
<template>
  <AppShell>
    <div class="mb-gutter">
      <h2 class="font-headline-lg text-headline-lg text-on-surface">Reports Center</h2>
      <p class="font-body-md text-on-surface-variant">Service performance overview</p>
    </div>

    <div v-if="loading" class="text-on-surface-variant font-body-md py-12 text-center">
      Loading reports…
    </div>
    <div v-else-if="error" class="text-error font-body-md py-12 text-center">
      Could not load reports. Check your access or contact the manager.
    </div>

    <template v-else>
      <section v-for="group in SECTIONS" :key="group.title" class="mb-8">
        <h3 class="font-label-md text-label-md uppercase tracking-wide text-on-surface-variant mb-3">
          {{ group.title }}
        </h3>
        <div class="lav-metric-grid">
          <div
            v-for="m in group.metrics"
            :key="m.key"
            class="lav-metric"
            :style="{ '--lav-accent': m.accent }"
          >
            <span class="material-symbols-outlined lav-metric__icon">{{ m.icon }}</span>
            <div class="lav-metric__label">{{ m.label }}</div>
            <div class="lav-metric__num">{{ summary[m.key] ?? 0 }}</div>
          </div>
        </div>
      </section>
    </template>
  </AppShell>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { call } from '@/api'
import AppShell from '@/components/AppShell.vue'

const raw = ref({})
const loading = ref(true)
const error = ref(false)

onMounted(async () => {
  try {
    raw.value = (await call('lavanya_service.api.manager_reports.get_manager_dashboard')) || {}
  } catch (e) {
    error.value = true
  } finally {
    loading.value = false
  }
})

const summary = computed(() => raw.value.summary || {})

const SECTIONS = [
  {
    title: 'Operational',
    metrics: [
      { key: 'overdue_followups', label: 'Overdue Follow-ups', icon: 'warning', accent: '#ba1a1a' },
      { key: 'due_today', label: 'Due Today', icon: 'event', accent: '#943700' },
      { key: 'waiting_on_customer', label: 'Waiting on Customer', icon: 'hourglass_top', accent: '#0053db' },
      { key: 'waiting_on_part', label: 'Waiting on Part', icon: 'build', accent: '#943700' },
    ],
  },
  {
    title: 'Brand & Registration',
    metrics: [
      { key: 'registration_pending', label: 'Reg Pending', icon: 'app_registration', accent: '#2563eb' },
      { key: 'registration_recommended', label: 'Reg Recommended', icon: 'recommend', accent: '#004ac6' },
      { key: 'warranty_overrides', label: 'Warranty Overrides', icon: 'verified', accent: '#712ae2' },
    ],
  },
  {
    title: 'Product at Store',
    metrics: [
      { key: 'products_in_store', label: 'In Store', icon: 'inventory_2', accent: '#004ac6' },
      { key: 'ready_for_pickup', label: 'Ready Pickup', icon: 'local_shipping', accent: '#1a7f37' },
      { key: 'product_receipt_missing', label: 'Receipt Missing', icon: 'error', accent: '#ba1a1a' },
    ],
  },
  {
    title: 'Closure & Quality',
    metrics: [
      { key: 'closure_pending', label: 'Closure Pending', icon: 'pending_actions', accent: '#434655' },
      { key: 'closed_today', label: 'Closed Today', icon: 'check_circle', accent: '#1a7f37' },
      { key: 'repeat_complaints', label: 'Repeat Complaints', icon: 'repeat', accent: '#712ae2' },
      { key: 'new_today', label: 'New Today', icon: 'fiber_new', accent: '#004ac6' },
    ],
  },
]
</script>
