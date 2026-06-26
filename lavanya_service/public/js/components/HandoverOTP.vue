<template>
  <div class="otp-panel">
    <template v-if="!verified">
      <div class="otp-header">
        <span class="ms" style="font-size:22px;color:#0D9488;font-variation-settings:'FILL' 1;">verified_user</span>
        <div>
          <div class="otp-title">Handover OTP</div>
          <div class="otp-sub">Sent to {{ maskedPhone }}</div>
        </div>
        <div class="otp-timer" :class="{ 'otp-timer--expire': timeLeft < 60 }">
          <span class="ms" style="font-size:13px;">schedule</span>
          {{ formattedTimer }}
        </div>
      </div>

      <!-- OTP display (for demo: show the generated OTP) -->
      <div class="otp-digits-sent">
        <div v-for="(d, i) in sentOtp" :key="i" class="otp-digit-sent">{{ d }}</div>
      </div>
      <div class="otp-hint">Customer reads OTP to staff</div>

      <!-- Staff entry -->
      <div class="otp-entry">
        <input v-for="i in 4" :key="i" :ref="el => inputRefs[i-1] = el"
          v-model="enteredDigits[i-1]" maxlength="1" class="otp-input"
          :class="{ 'otp-input--filled': enteredDigits[i-1], 'otp-input--error': showError }"
          @input="onInput(i-1, $event)" @keydown.backspace="onBackspace(i-1)" type="tel" />
      </div>
      <div v-if="showError" class="otp-error">Incorrect OTP. Please try again.</div>

      <div class="otp-actions">
        <button class="btn btn-primary" style="flex:1;" @click="verify">
          <span class="ms" style="font-size:16px;font-variation-settings:'FILL' 1;">verified_user</span>
          Verify &amp; Hand Over
        </button>
        <button class="btn btn-secondary" @click="resend" :disabled="timeLeft > 0">Resend</button>
      </div>
    </template>

    <!-- Success state -->
    <template v-else>
      <div class="otp-success">
        <div class="otp-success-icon"><span class="ms">task_alt</span></div>
        <div class="otp-success-title">Handover Complete</div>
        <div class="otp-success-meta">OTP verified · {{ new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' }) }} · {{ staffName }}</div>
        <div class="otp-success-detail">Product handed to <strong>{{ customerName }}</strong>. Timeline entry logged automatically.</div>
        <button class="btn btn-primary" style="width:100%;margin-top:12px;justify-content:center;" @click="$emit('done')">
          Close Ticket Now
        </button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  phone: { type: String, required: true },
  customerName: { type: String, default: 'Customer' },
  staffName: { type: String, default: 'Staff' },
})
defineEmits(['done', 'verified'])

const OTP_EXPIRY = 600 // 10 minutes
const sentOtp = ref(Array.from({ length: 4 }, () => Math.floor(Math.random() * 10).toString()))
const enteredDigits = ref(['', '', '', ''])
const inputRefs = ref([])
const timeLeft = ref(OTP_EXPIRY)
const showError = ref(false)
const verified = ref(false)
let timerInterval = null

onMounted(() => { timerInterval = setInterval(() => { if (timeLeft.value > 0) timeLeft.value-- }, 1000) })
onUnmounted(() => clearInterval(timerInterval))

const maskedPhone = computed(() => props.phone.replace(/(d{2})d{6}(d{4})/, '$1xxxxxx$2'))
const formattedTimer = computed(() => {
  const m = Math.floor(timeLeft.value / 60)
  const s = timeLeft.value % 60
  return `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
})

const onInput = (idx, e) => {
  const val = e.target.value.replace(/\D/g, '')
  enteredDigits.value[idx] = val.charAt(0) || ''
  showError.value = false
  if (val && idx < 3) inputRefs.value[idx + 1]?.focus()
}
const onBackspace = (idx) => {
  if (!enteredDigits.value[idx] && idx > 0) inputRefs.value[idx - 1]?.focus()
}
const verify = () => {
  const entered = enteredDigits.value.join('')
  const expected = sentOtp.value.join('')
  if (entered === expected) { verified.value = true }
  else { showError.value = true; enteredDigits.value = ['','','',''] }
}
const resend = () => {
  sentOtp.value = Array.from({ length: 4 }, () => Math.floor(Math.random() * 10).toString())
  enteredDigits.value = ['','','','']
  timeLeft.value = OTP_EXPIRY
  showError.value = false
}
</script>

<style scoped>
.otp-panel { background: #0F172A; border-radius: 14px; padding: 20px; }
.otp-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.otp-title { font-size: 14px; font-weight: 800; color: #fff; }
.otp-sub { font-size: 11px; color: #64748B; margin-top: 2px; }
.otp-timer { margin-left: auto; display: flex; align-items: center; gap: 5px; font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 700; color: #5EEAD4; }
.otp-timer--expire { color: #EF4444; }
.otp-digits-sent { display: flex; gap: 8px; justify-content: center; margin-bottom: 6px; }
.otp-digit-sent { width: 52px; height: 64px; border-radius: 10px; background: #1E293B; border: 2px solid #0D9488; display: flex; align-items: center; justify-content: center; font-family: 'JetBrains Mono', monospace; font-size: 26px; font-weight: 800; color: #fff; }
.otp-hint { font-size: 11px; color: #64748B; text-align: center; margin-bottom: 14px; }
.otp-entry { display: flex; gap: 8px; justify-content: center; margin-bottom: 6px; }
.otp-input { width: 52px; height: 56px; border-radius: 10px; border: 2px solid #334155; background: #1E293B; font-family: 'JetBrains Mono', monospace; font-size: 22px; font-weight: 800; color: #fff; text-align: center; outline: none; transition: border-color 0.15s; }
.otp-input--filled { border-color: #0D9488; }
.otp-input--error { border-color: #EF4444; }
.otp-error { font-size: 11.5px; color: #EF4444; text-align: center; margin-bottom: 8px; font-weight: 600; }
.otp-actions { display: flex; gap: 8px; margin-top: 14px; }
.otp-success { text-align: center; }
.otp-success-icon .ms { font-size: 48px; color: #34D399; font-variation-settings: 'FILL' 1; }
.otp-success-title { font-size: 18px; font-weight: 800; color: #fff; margin-top: 8px; }
.otp-success-meta { font-size: 11px; color: #64748B; margin-top: 4px; }
.otp-success-detail { font-size: 12.5px; color: #94A3B8; margin-top: 10px; line-height: 1.5; }
</style>
