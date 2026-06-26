/**
 * Lavanya Service — Production entry point
 * Built with Vite → lavanya_bundle.iife.js
 * Loaded by hooks.py app_include_js in every Frappe desk session.
 * Each Frappe page JS calls: LavanyaService.mountPage('PageName', domEl, props)
 */

import { createApp } from 'vue'

// Pages
import TodaysWork       from './pages/TodaysWork.vue'
import Tickets          from './pages/Tickets.vue'
import TicketDetail     from './pages/TicketDetail.vue'
import NewTicket        from './pages/NewTicket.vue'
import Customer360      from './pages/Customer360.vue'
import ManagerDashboard from './pages/ManagerDashboard.vue'
import WhatsAppInbox    from './pages/WhatsAppInbox.vue'
import ServiceCenters   from './pages/ServiceCenters.vue'
import Reports          from './pages/Reports.vue'
import Settings         from './pages/Settings.vue'

// Shared components (auto-registered globally)
import StatusBadge  from './components/StatusBadge.vue'
import QualityBadge from './components/QualityBadge.vue'
import SLACountdown from './components/SLACountdown.vue'

const PAGE_MAP = {
  TodaysWork, Tickets, TicketDetail, NewTicket,
  Customer360, ManagerDashboard, WhatsAppInbox,
  ServiceCenters, Reports, Settings,
}

// Cache mounted instances so Frappe page show/hide can call refresh()
const INSTANCES = {}

window.LavanyaService = {
  /**
   * mountPage(name, el, props)
   * Called by each lavanya_*.js Frappe page file.
   * Returns the Vue component instance (exposes refresh, setFilter, etc.)
   */
  mountPage(name, el, props = {}) {
    const Component = PAGE_MAP[name]
    if (!Component) {
      console.error('[LavanyaService] Unknown page:', name)
      el.innerHTML = '<div style="padding:40px;color:#E11D48;font-family:sans-serif">Unknown page: ' + name + '</div>'
      return null
    }

    // Unmount previous instance on same element if re-navigating
    if (INSTANCES[name]) {
      try { INSTANCES[name].__app?.unmount() } catch(e) {}
    }

    const app = createApp(Component, props)

    // Global component registration (no need to import in every page)
    app.component('StatusBadge',  StatusBadge)
    app.component('QualityBadge', QualityBadge)
    app.component('SLACountdown', SLACountdown)

    // Global nav helper (uses Frappe routing)
    app.config.globalProperties.$nav = {
      toTicket:    (id) => frappe?.set_route('lavanya-ticket-detail', id),
      toTickets:   ()   => frappe?.set_route('lavanya-tickets'),
      toNewTicket: (p)  => frappe?.set_route('lavanya-new-ticket' + (p ? '?phone=' + p : '')),
      toCustomer:  (id) => frappe?.set_route('lavanya-customer360?customer=' + id),
      toWhatsApp:  ()   => frappe?.set_route('lavanya-whatsapp'),
      toReports:   ()   => frappe?.set_route('lavanya-reports'),
      toSettings:  ()   => frappe?.set_route('lavanya-settings'),
    }

    // Global error handler — surface to Frappe msgprint in production
    app.config.errorHandler = (err, vm, info) => {
      console.error('[LavanyaService]', err)
      if (window.frappe?.msgprint) {
        frappe.msgprint({
          title: 'UI Error',
          message: err.message || String(err),
          indicator: 'red',
        })
      }
    }

    const instance = app.mount(el)
    instance.__app = app
    INSTANCES[name] = instance
    return instance
  },

  /** Refresh currently mounted page (called on page re-show) */
  refresh(name) {
    const inst = INSTANCES[name]
    if (inst?.refresh) inst.refresh()
  },

  /** Unmount a page (called when Frappe navigates away) */
  unmount(name) {
    const inst = INSTANCES[name]
    if (inst?.__app) { inst.__app.unmount(); delete INSTANCES[name] }
  },
}

console.log('[LavanyaService] v1.0.0 loaded — pages:', Object.keys(PAGE_MAP).join(', '))
