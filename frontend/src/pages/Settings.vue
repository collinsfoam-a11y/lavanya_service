<template>
  <AppShell>
    <div class="max-w-3xl mx-auto">
      <LavSectionHeader title="Settings" icon="settings" class="mb-6" />

      <LavLoadingState v-if="loading" layout="card-list" />
      <LavEmptyState
        v-else-if="error"
        icon="error"
        :title="error"
        message="Could not load settings from the server."
        tone="error"
      />
      <template v-else>
        <LavConfirm />
        <div v-if="saveStatus" class="mb-4 rounded-lg px-4 py-3 font-body-md" :class="saveStatusClass" role="status">
          {{ saveStatus }}
        </div>

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
              <label
                v-for="flag in themeFlags"
                :key="flag.key"
                class="flex items-start gap-3 p-3 rounded-lg border border-outline-variant bg-surface-container-low cursor-pointer"
              >
                <span class="material-symbols-outlined text-primary mt-0.5" aria-hidden="true">{{ flag.icon }}</span>
                <div class="flex-1">
                  <div class="font-body-md text-body-md text-on-surface">{{ flag.label }}</div>
                  <div class="font-label-md text-label-md text-on-surface-variant">{{ flag.description }}</div>
                </div>
                <input
                  v-if="canManage"
                  type="checkbox"
                  v-model="draft[flag.key]"
                  class="accent-primary"
                />
                <span v-else class="material-symbols-outlined" :class="draft[flag.key] ? 'text-success' : 'text-muted'">
                  {{ draft[flag.key] ? 'check_circle' : 'cancel' }}
                </span>
              </label>
            </div>
          </div>
        </LavCard>

        <LavCard class="mb-6">
          <LavSectionHeader title="Safety Locks" icon="lock" />
          <LavSafetyLockPanel :locks="safetyLocks" />
          <p class="font-label-md text-label-md text-on-surface-variant mt-3">
            Safety locks are read-only mirrors of backend gates. They protect against live sends, ERP posting, and unintended penalties.
          </p>
        </LavCard>

        <LavCard class="mb-6">
          <LavSectionHeader title="UI Feature Flags" icon="tune" />
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <label
              v-for="flag in uiFlags"
              :key="flag.key"
              class="flex items-center justify-between p-3 rounded-lg border border-outline-variant bg-surface-container-low cursor-pointer"
            >
              <div class="font-body-md text-body-md text-on-surface">{{ flag.label }}</div>
              <input
                v-if="canManage"
                type="checkbox"
                v-model="draft[flag.key]"
                class="accent-primary"
              />
              <span v-else class="material-symbols-outlined" :class="draft[flag.key] ? 'text-success' : 'text-muted'">
                {{ draft[flag.key] ? 'check_circle' : 'cancel' }}
              </span>
            </label>
          </div>
        </LavCard>

        <div v-if="canManage" class="flex flex-wrap items-center gap-3">
          <button
            @click="saveSettings"
            :disabled="saving"
            class="px-5 py-2.5 rounded-lg bg-primary text-on-primary font-label-md hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ saving ? 'Saving…' : 'Save settings' }}
          </button>
          <button
            @click="confirmReset"
            :disabled="saving"
            class="px-5 py-2.5 rounded-lg bg-error text-on-error font-label-md hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Reset to safe defaults
          </button>
        </div>
        <div v-else class="font-label-md text-label-md text-on-surface-variant">
          Contact a Lavanya Manager to change settings.
        </div>
      </template>
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
import LavLoadingState from '@/components/LavLoadingState.vue'
import LavEmptyState from '@/components/LavEmptyState.vue'
import LavConfirm from '@/components/LavConfirm.vue'
import { call, post } from '@/api.js'
import { useConfirm } from '@/utils/confirm'

const { confirm } = useConfirm()
const settings = ref({})
const draft = ref({})
const loading = ref(true)
const saving = ref(false)
const error = ref(null)
const canManage = ref(false)
const saveStatus = ref('')

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
  { key: 'show_next_action_bar', label: 'Next action bar' },
  { key: 'show_workflow_timeline', label: 'Workflow timeline' },
  { key: 'show_customer_journey_summary', label: 'Customer journey summary' },
  { key: 'show_followup_quality_badge', label: 'Follow-up quality badge' },
  { key: 'show_mobile_field_mode', label: 'Mobile field mode' },
  { key: 'show_penalty_tab', label: 'Penalty tab' },
  { key: 'show_notification_tab', label: 'Notification tab' },
  { key: 'show_erp_status_panel', label: 'ERP status panel' },
])

const saveStatusClass = computed(() => {
  if (saveStatus.value.startsWith('Saved')) return 'bg-success-container text-on-success'
  if (saveStatus.value.startsWith('Error')) return 'bg-error-container text-on-error'
  return 'bg-primary-container text-on-primary'
})

onMounted(async () => {
  try {
    const [fetched, manage] = await Promise.all([
      call('lavanya_service.api.ui_settings.get_lavanya_service_settings'),
      call('lavanya_service.api.ui_settings.can_manage_lavanya_settings'),
    ])
    settings.value = fetched
    draft.value = buildDraft(fetched)
    canManage.value = !!manage
  } catch (e) {
    error.value = e.message || 'Could not load settings.'
  } finally {
    loading.value = false
  }
})

function buildDraft(src) {
  const out = {}
  const keys = [
    'allow_user_theme_override', 'compact_mode_enabled', 'large_text_mode_enabled', 'high_contrast_mode_enabled',
    'show_next_action_bar', 'show_workflow_timeline', 'show_customer_journey_summary', 'show_followup_quality_badge',
    'show_mobile_field_mode', 'show_penalty_tab', 'show_notification_tab', 'show_erp_status_panel',
  ]
  keys.forEach((k) => { out[k] = src[k] === 1 })
  return out
}

async function saveSettings() {
  saving.value = true
  saveStatus.value = ''
  try {
    const payload = {}
    Object.keys(draft.value).forEach((k) => { payload[k] = draft.value[k] ? 1 : 0 })
    const updated = await post('lavanya_service.api.ui_settings.save_lavanya_service_settings', { values: payload })
    settings.value = updated
    draft.value = buildDraft(updated)
    saveStatus.value = 'Saved successfully.'
  } catch (e) {
    saveStatus.value = 'Error: ' + (e.message || 'Could not save settings.')
  } finally {
    saving.value = false
  }
}

async function confirmReset() {
  saveStatus.value = ''
  const ok = await confirm('Reset all settings to safe defaults? This cannot be undone.', 'Reset settings', true)
  if (!ok) return
  saving.value = true
  try {
    const updated = await post('lavanya_service.api.ui_settings.reset_lavanya_service_settings')
    settings.value = updated
    draft.value = buildDraft(updated)
    saveStatus.value = 'Settings reset to safe defaults.'
  } catch (e) {
    saveStatus.value = 'Error: ' + (e.message || 'Could not reset settings.')
  } finally {
    saving.value = false
  }
}
</script>
