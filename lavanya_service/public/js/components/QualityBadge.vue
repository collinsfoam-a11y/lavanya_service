<template>
  <span class="quality-badge" :class="`quality-${norm}`">
    <span class="ms quality-icon">{{ iconMap[norm] }}</span>
    {{ labelMap[norm] }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ badge: { type: String, default: 'Good' } })
const norm = computed(() => (props.badge || 'Good').toLowerCase().replace(/\s+/g, '_'))
const labelMap = { good: 'Good', needs_update: 'Needs Update', at_risk: 'At Risk', critical: 'Critical' }
const iconMap  = { good: 'check_circle', needs_update: 'edit_notifications', at_risk: 'warning', critical: 'error' }
</script>

<style scoped>
.quality-badge { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 6px; font-size: 10px; font-weight: 700; }
.quality-icon { font-size: 12px; font-variation-settings: 'FILL' 1; }
.quality-good        { background: #ECFDF5; color: #059669; }
.quality-good .quality-icon { color: #059669; }
.quality-needs_update{ background: #FEF9C3; color: #A16207; }
.quality-needs_update .quality-icon { color: #A16207; }
.quality-at_risk     { background: #FFF7ED; color: #D97706; }
.quality-at_risk .quality-icon { color: #D97706; }
.quality-critical    { background: #FFE4E6; color: #E11D48; }
.quality-critical .quality-icon { color: #E11D48; }
</style>
