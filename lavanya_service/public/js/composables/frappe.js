
/**
 * Frappe API bridge for Vue 3 composables.
 * All frappe.call() wrappers live here.
 * Falls back to mock data in dev (when window.frappe is absent).
 */

export function frappeCall(method, args = {}) {
  return new Promise((resolve, reject) => {
    if (window.frappe?.call) {
      window.frappe.call({
        method,
        args,
        callback: r => resolve(r.message ?? r),
        error:    e => reject(e),
      })
    } else {
      // dev fallback — resolve empty so pages at least mount
      console.warn('[LavanyaService] frappe not available — returning null for', method)
      resolve(null)
    }
  })
}

export function showAlert(msg, indicator = 'green') {
  if (window.frappe?.show_alert) {
    window.frappe.show_alert({ message: msg, indicator })
  } else {
    console.info('[Alert]', msg)
  }
}

export function showError(msg) {
  if (window.frappe?.msgprint) {
    window.frappe.msgprint({ title: 'Error', message: msg, indicator: 'red' })
  } else {
    console.error('[Error]', msg)
  }
}

export function currentUser() {
  return window.frappe?.session?.user ?? 'guest'
}

export function currentUserName() {
  return window.frappe?.session?.full_name ?? 'User'
}

export function hasRole(role) {
  if (!window.frappe?.user?.has_role) return false
  return window.frappe.user.has_role(role)
}

export function navigate(page, params = '') {
  if (window.frappe?.set_route) {
    window.frappe.set_route(page + (params ? '?' + params : ''))
  }
}
