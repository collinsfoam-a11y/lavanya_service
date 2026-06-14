import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'TodayWork',
    component: () => import('@/pages/TodayWork.vue'),
  },
  {
    path: '/reports',
    name: 'Reports',
    component: () => import('@/pages/Reports.vue'),
  },
]

let router = createRouter({
  history: createWebHistory('/frontend'),
  routes,
})

export default router
