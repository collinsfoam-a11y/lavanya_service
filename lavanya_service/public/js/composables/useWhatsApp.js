
import { ref } from 'vue'
import { frappeCall } from './frappe.js'

export function useWhatsAppInbox() {
  const messages = ref([])
  const buckets  = ref({})
  const loading  = ref(false)

  async function fetch() {
    loading.value = true
    try {
      const r = await frappeCall('lavanya_service.api.whatsapp.get_inbox')
      if (r) { messages.value = r.messages || []; buckets.value = r.buckets || {} }
    } finally { loading.value = false }
  }

  async function generateDraft(ticketId, templateKey) {
    return frappeCall('lavanya_service.api.whatsapp.generate_draft', {
      ticket_id: ticketId, template_key: templateKey
    })
  }

  async function markReviewed(msgId) {
    const r = await frappeCall('lavanya_service.api.whatsapp.mark_reviewed', { msg_id: msgId })
    await fetch()
    return r
  }

  fetch()
  return { messages, buckets, loading, fetch, generateDraft, markReviewed }
}
