
import { ref, computed } from 'vue'
import { frappeCall } from './frappe.js'

export function useTicketList(initialFilters = {}) {
  const tickets   = ref([])
  const total     = ref(0)
  const loading   = ref(false)
  const error     = ref(null)
  const page      = ref(1)
  const pageSize  = 20
  const filters   = ref({ ...initialFilters })
  const search    = ref('')
  const sortBy    = ref('creation desc')   // FIXED: was 'newest' which caused SQL error

  async function fetch() {
    loading.value = true
    error.value   = null
    try {
      const r = await frappeCall('lavanya_service.api.tickets.get_list', {
        filters:   filters.value,
        page:      page.value,
        page_size: pageSize,
        search:    search.value,
        sort_by:   sortBy.value,
      })
      if (r) { tickets.value = r.tickets || []; total.value = r.total || 0 }
    } catch (e) {
      error.value = e?.message || 'Failed to load tickets'
    } finally {
      loading.value = false
    }
  }

  const totalPages = computed(() => Math.ceil(total.value / pageSize))

  function setStatus(s) { filters.value.status = s || undefined; page.value = 1; fetch() }
  function setSearch(q) { search.value = q; page.value = 1; fetch() }
  function setPage(p)   { page.value = p; fetch() }

  fetch()
  return { tickets, total, totalPages, loading, error, page, pageSize, filters, search, setStatus, setSearch, setPage, refresh: fetch }
}

export function useTicket(ticketId) {
  const ticket  = ref(null)
  const loading = ref(false)
  const error   = ref(null)

  async function fetch(id) {
    const name = id || ticketId
    if (!name) return
    loading.value = true
    error.value   = null
    try {
      ticket.value = await frappeCall('lavanya_service.api.tickets.get_ticket', { name })
    } catch (e) {
      error.value = e?.message || 'Failed to load ticket'
    } finally {
      loading.value = false
    }
  }

  async function saveFollowup(data) {
    const r = await frappeCall('lavanya_service.api.tickets.save_followup', {
      ticket: ticket.value?.name, ...data
    })
    if (r) await fetch()
    return r
  }

  async function escalate(reason) {
    const r = await frappeCall('lavanya_service.api.tickets.escalate_ticket', {
      ticket: ticket.value?.name, reason
    })
    if (r) await fetch()
    return r
  }

  async function closeTicket(data) {
    return frappeCall('lavanya_service.api.tickets.close_ticket', {
      ticket: ticket.value?.name, ...data
    })
  }

  if (ticketId) fetch(ticketId)
  return { ticket, loading, error, fetch, saveFollowup, escalate, closeTicket }
}

export function useTodaysWork() {
  const buckets = ref({ critical: [], important: [], normal: [], counts: {} })
  const loading = ref(false)
  const error   = ref(null)

  async function fetch() {
    loading.value = true
    error.value   = null
    try {
      const r = await frappeCall('lavanya_service.api.today.get_todays_work')
      if (r) buckets.value = r
    } catch (e) {
      error.value = e?.message || 'Failed to load today\'s work'
    } finally {
      loading.value = false
    }
  }

  fetch()
  return { buckets, loading, error, refresh: fetch }
}

export function useSidebarCounts() {
  const counts = ref({ today: 0, tickets: 0, whatsapp: 0, critical: 0 })

  async function refresh() {
    const r = await frappeCall('lavanya_service.api.today.get_sidebar_counts')
    if (r) counts.value = r
  }

  refresh()
  return { counts, refresh }
}

export async function searchCustomer(phone) {
  return frappeCall('lavanya_service.api.tickets.search_customer', { phone })
}

export async function createTicket(data) {
  return frappeCall('lavanya_service.api.tickets.create_ticket', { data: JSON.stringify(data) })
}
