<template>
  <AppShell>
    <div class="max-w-3xl mx-auto">
      <LavSectionHeader title="Settings" icon="settings" class="mb-6" />

      <LavCard class="mb-6">
        <LavSectionHeader title="Theme & Accessibility" icon="palette" />
        <div class="space-y-4">
          <div class="flex items-center justify-between gap-4">
            <div>
              <div class="font-body-md text-body-md text-on-surface">Active theme</div>
              <div class="font-label-md text-label-md text-on-surface-variant">
                Choose a look that works for your environment.
              </div>
            </div>
            <LavThemeToggle />
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            <div
              v-for="flag in themeFlags"
              :key="flag.key"
              class="flex items-start gap-3 p-3 rounded-lg border border-outline-variant bg-surface-container-low"
            >
              <span class="material-symbols-outlined text-primary mt-0.5" aria-hidden="true">{{ flag.icon }}</span>
              <div>
                <div class="font-body-md text-body-md text-on-surface">{{ flag.label }}</div>
                <div class="font-label-md text-label-md text-on-surface-variant">{{ flag.description }}</div>
              </div>
            </div>
          </div>
        </div>
      </LavCard>

      <LavCard class="mb-6">
        <LavSectionHeader title="Safety Locks" icon="lock" />
        <LavSafetyLockPanel :locks="safetyLocks" />
      </LavCard>

      <LavCard>
        <LavSectionHeader title="UI Feature Flags" icon="tune" />
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="flag in uiFlags"
            :key="flag.key"
            class="flex items-center justify-between p-3 rounded-lg border border-outline-variant bg-surface-container-low"
          >
            <div class="font-body-md text-body-md text-on-surface">{{ flag.label }}</div>
            <span
              class="material-symbols-outlined"
              :class="flag.enabled ? 'text-success' : 'text-muted'"
              aria-hidden="true"
            >{{ flag.enabled ? 'check_circle' : 'cancel' }}</span>
          </div>
        </div>
      </LavCard>
    </div>
  </AppShell>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import AppShell from '@/components/AppShell.vue'
import LavThemeToggle from '@/components/LavThemeToggle.vue'
import LavSectionHeader from '@/components/LavSectionHeader.vue'
import LavCard from '@/components/LavCard.vue'
import LavSafetyLockPanel from '@/components/LavSafetyLockPanel.vue'
import { call } from '@/api.js'

const settings = ref({})
const loading = ref(true)
const error = ref(null)

const themeFlags = [
  { key: 'allow_user_theme_override', label: 'User theme override', description: 'Staff can pick their own theme.', icon: 'person' },
  { key: 'compact_mode_enabled', label: 'Compact mode', description: 'Tighter spacing for counter screens.', icon: 'zoom_out_map' },
  { key: 'large_text_mode_enabled', label: 'Large text mode', description: 'Larger text across the app.', icon: 'text_increase' },
  { key: 'high_contrast_mode_enabled', label: 'High contrast mode', description: 'Maximum contrast for accessibility.', icon: 'contrast' },
]

const safetyLocks = computed(() => [
  { key: 'live_notifications_blocked', label: 'Live notifications', locked: settings.value.live_notifications_blocked === 1 },
  { key: 'erp_posting_disabled', label: 'ERP posting', locked: settings.value.erp_posting_disabled === 1 },
  { key: 'penalty_apply_disabled', label: 'Penalty apply', locked: settings.value.penalty_apply_disabled === 1 },
  { key: 'dry_run_mode_on', label: 'Dry-run mode', locked: settings.value.dry_run_mode_on === 1 },
])

const uiFlags = computed(() => [
  { key: 'show_next_action_bar', label: 'Next action bar', enabled: settings.value.show_next_action_bar === 1 },
  { key: 'show_workflow_timeline', label: 'Workflow timeline', enabled: settings.value.show_workflow_timeline === 1 },
  { key: 'show_customer_journey_summary', label: 'Customer journey summary', enabled: settings.value.show_customer_journey_summary === 1 },
  { key: 'show_followup_quality_badge', label: 'Follow-up quality badge', enabled: settings.value.show_followup_quality_badge === 1 },
  { key: 'show_mobile_field_mode', label: 'Mobile field mode', enabled: settings.value.show_mobile_field_mode === 1 },
  { key: 'show_penalty_tab', label: 'Penalty tab', enabled: settings.value.show_penalty_tab === 1 },
  { key: 'show_notification_tab', label: 'Notification tab', enabled: settings.value.show_notification_tab === 1 },
  { key: 'show_erp_status_panel', label: 'ERP status panel', enabled: settings.value.show_erp_status_panel === 1 },
])

onMounted(async () => {
  try {
    settings.value = await call('lavanya_service.api.ui_settings.get_lavanya_service_settings')
  } catch (e) {
    error.value = e.message || 'Could not load settings.'
  } finally {
    loading.value = false
  }
})
</script>
