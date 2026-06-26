
import { ref } from 'vue'
import { frappeCall } from './frappe.js'

export function useManagerDashboard() {
  const data    = ref(null)
  const loading = ref(false)
  const period  = ref('Today')

  async function fetch() {
    loading.value = true
    try {
      const r = await frappeCall('lavanya_service.api.dashboard.get_manager_dashboard', { period: period.value })
      if (r) data.value = r
    } finally { loading.value = false }
  }

  function setPeriod(p) { period.value = p; fetch() }

  fetch()
  return { data, loading, period, setPeriod, refresh: fetch }
}

export function useReports() {
  const rows    = ref([])
  const loading = ref(false)
  const report  = ref('overdue_followups')
  const period  = ref('This Month')

  async function fetch() {
    loading.value = true
    try {
      const r = await frappeCall('lavanya_service.api.reports.get_report_data', {
        report_key: report.value, period: period.value
      })
      if (r) rows.value = r.rows || []
    } finally { loading.value = false }
  }

  function setReport(key) { report.value = key; fetch() }
  function setPeriod(p)   { period.value = p;   fetch() }

  fetch()
  return { rows, loading, report, period, setReport, setPeriod, refresh: fetch }
}

export function useSettings() {
  const settings = ref(null)
  const loading  = ref(false)
  const saving   = ref(false)

  async function fetch() {
    loading.value = true
    try {
      const r = await frappeCall('lavanya_service.api.settings.get_settings')
      if (r) settings.value = r
    } finally { loading.value = false }
  }

  async function save(data) {
    saving.value = true
    try {
      return await frappeCall('lavanya_service.api.settings.save_settings', { data: JSON.stringify(data) })
    } finally { saving.value = false }
  }

  async function reset() {
    return frappeCall('lavanya_service.api.settings.reset_defaults')
  }

  fetch()
  return { settings, loading, saving, fetch, save, reset }
}
