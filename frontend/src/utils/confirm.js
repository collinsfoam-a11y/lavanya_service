import { ref } from 'vue'

const state = ref({ show: false, title: '', message: '', danger: false, resolve: null })

export function useConfirm() {
  function confirm(message, title = 'Confirm', danger = false) {
    return new Promise((res) => {
      state.value = { show: true, title, message, danger, resolve: res }
    })
  }

  function confirmResolve(value) {
    const r = state.value.resolve
    state.value = { show: false, title: '', message: '', danger: false, resolve: null }
    if (r) r(value)
  }

  return { state, confirm, confirmResolve }
}
