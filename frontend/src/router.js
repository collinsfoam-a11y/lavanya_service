import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'TodayWork',
    component: () => import('@/pages/TodayWork.vue'),
  },
  {
    path: '/tickets',
    name: 'Tickets',
    component: () => import('@/pages/Tickets.vue'),
  },
  {
    path: '/new-ticket',
    name: 'NewTicket',
    component: () => import('@/pages/NewTicket.vue'),
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/pages/Reports.vue'),
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('@/pages/Settings.vue'),
  },
  {
    path: '/field',
    name: 'FieldMode',
    component: () => import('@/pages/FieldMode.vue'),
  },
  {
    path: '/whatsapp',
    name: 'WhatsAppInbox',
    component: () => import('@/pages/WhatsAppInbox.vue'),
  },
  {
    path: '/customer-360',
    name: 'Customer360',
    component: () => import('@/pages/Customer360.vue'),
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/pages/NotFound.vue'),
  },
]

let router = createRouter({
  history: createWebHistory('/frontend'),
  routes,
})

export default router
