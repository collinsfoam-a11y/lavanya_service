import { ref } from 'vue'

const toasts = ref([])
let nextId = 0

export function useToast() {
  function show(message, kind = 'success') {
    const id = ++nextId
    toasts.value.push({ id, message, kind })
    setTimeout(() => {
      toasts.value = toasts.value.filter(t => t.id !== id)
    }, 4000)
  }
  function dismiss(id) {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }
  return { toasts, show, dismiss }
}
