<template>
  <span class="status-badge" :class="`status-${normalised}`">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ status: String })
const MAP = {
  'New': 'new', 'Open': 'open', 'Registered': 'registered', 'Replied': 'replied',
  'In Follow-up': 'infollowup', 'Waiting': 'waiting',
  'Resolved by Brand': 'resolved', 'Resolved': 'resolved',
  'Customer Confirmation Pending': 'pending',
  'Closed': 'closed', 'Cancelled': 'cancelled', 'Reopened': 'reopened',
}
const normalised = computed(() => MAP[props.status] || 'open')
const label = computed(() => props.status || 'Open')
</script>

<style scoped>
.status-badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 8px; font-size: 11.5px; font-weight: 700; white-space: nowrap; }
.status-new        { background: #EEF2FF; color: #4F46E5; }
.status-open       { background: #F4F4F1; color: #52525B; }
.status-registered { background: #F0FDFA; color: #0D9488; }
.status-replied    { background: #F0FDFA; color: #0D9488; }
.status-infollowup { background: #EEF2FF; color: #4F46E5; }
.status-waiting    { background: #FFF7ED; color: #D97706; }
.status-resolved   { background: #ECFDF5; color: #059669; }
.status-pending    { background: #F5F3FF; color: #7C3AED; }
.status-closed     { background: #F4F4F1; color: #52525B; }
.status-cancelled  { background: #FFF1F3; color: #E11D48; }
.status-reopened   { background: #FFF1F3; color: #E11D48; }
</style>
