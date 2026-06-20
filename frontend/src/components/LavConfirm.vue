<template>
  <LavModal
    :show="state.show"
    :title="state.title"
    :icon="state.danger ? 'warning' : 'help'"
    :danger="state.danger"
    :max-width="'md'"
    :closable="true"
    :submit-label="state.danger ? 'Yes, proceed' : 'Yes'"
    :submit-icon="state.danger ? 'warning' : 'check_circle'"
    :body-id="'confirm-body-' + uid"
    @close="cancel"
    @submit="confirm"
    @backdrop="cancel"
  >
    <p :id="'confirm-body-' + uid" class="font-body-md text-on-surface">{{ state.message }}</p>
  </LavModal>
</template>

<script setup>
import LavModal from '@/components/LavModal.vue'
import { useConfirm } from '@/utils/confirm'

const { state, confirmResolve } = useConfirm()
const uid = Math.random().toString(36).slice(2, 9)

function cancel() {
  confirmResolve(false)
}

function confirm() {
  confirmResolve(true)
}
</script>
