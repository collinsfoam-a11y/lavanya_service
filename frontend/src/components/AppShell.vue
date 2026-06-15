<!--
  AppShell — Lavanya Service Console layout.
  Ported from the Stitch "Lavanya Service Console" design: 260px sidebar
  (surface-container-highest), sticky header, mobile bottom nav. Wraps the
  routed page via the default slot.
-->
<template>
  <div class="lav-shell">
    <!-- Sidebar -->
    <aside class="lav-sidebar">
      <div class="px-gutter mb-8 flex items-center gap-3">
        <div class="w-10 h-10 rounded-lg bg-primary text-on-primary flex items-center justify-center shrink-0">
          <span class="material-symbols-outlined fill">storefront</span>
        </div>
        <div class="leading-tight">
          <h1 class="font-headline-md text-headline-md font-bold text-primary truncate">Lavanya eMart</h1>
          <p class="font-label-md text-label-md text-on-surface-variant">Service Console</p>
        </div>
      </div>

      <nav class="flex-1 flex flex-col gap-1 px-2">
        <component
          :is="item.external ? 'a' : 'router-link'"
          v-for="item in navItems"
          :key="item.label"
          :to="item.external ? undefined : item.to"
          :href="item.external ? item.to : undefined"
          :target="item.external ? '_blank' : undefined"
          class="flex items-center gap-3 px-3 py-2 rounded-lg font-label-md text-body-md transition-colors
                 border-l-4 border-transparent text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface"
          :class="isActive(item) ? '!border-primary bg-surface-container-low !text-primary font-bold' : ''"
        >
          <span class="material-symbols-outlined" :class="isActive(item) ? 'fill' : ''">{{ item.icon }}</span>
          <span class="truncate">{{ item.label }}</span>
        </component>
      </nav>

      <div class="px-2 mt-2">
        <a
          :href="logoutUrl"
          class="flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface"
        >
          <span class="material-symbols-outlined">logout</span>
          <span class="font-label-md text-body-md">Logout</span>
        </a>
      </div>
    </aside>

    <!-- Main -->
    <main class="lav-main">
      <header class="lav-header">
        <h2 class="font-headline-md text-headline-md font-bold text-primary md:hidden">Lavanya</h2>
        <div class="hidden md:block font-body-md text-on-surface-variant">{{ headerTitle }}</div>
        <div class="flex items-center gap-3">
          <span class="font-body-md text-on-surface-variant hidden sm:inline">{{ today }}</span>
          <div class="w-9 h-9 rounded-full bg-primary-container text-on-primary flex items-center justify-center">
            <span class="material-symbols-outlined">person</span>
          </div>
        </div>
      </header>

      <div class="flex-1 px-container-padding py-gutter w-full max-w-max-content-width mx-auto">
        <slot />
      </div>

      <!-- Mobile bottom nav -->
      <nav class="lav-mobile-nav">
        <router-link
          v-for="item in navItems.filter((i) => !i.external)"
          :key="'m-' + item.label"
          :to="item.to"
          class="flex flex-col items-center gap-0.5 px-2 py-1 text-on-surface-variant"
          :class="isActive(item) ? '!text-primary' : ''"
        >
          <span class="material-symbols-outlined" :class="isActive(item) ? 'fill' : ''">{{ item.icon }}</span>
          <span class="font-label-md text-label-md">{{ item.label }}</span>
        </router-link>
      </nav>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const navItems = [
  { label: 'Today’s Work', icon: 'dashboard', to: '/' },
  { label: 'Tickets', icon: 'confirmation_number', to: '/tickets' },
  { label: 'Reports', icon: 'assessment', to: '/reports' },
  { label: 'New Ticket', icon: 'add_box', to: '/helpdesk/tickets/new', external: true },
]

const logoutUrl = '/api/method/logout'

const headerTitle = computed(() => {
  const active = navItems.find((i) => !i.external && i.to === route.path)
  return active ? active.label : 'Service Console'
})

const today = new Date().toLocaleDateString(undefined, {
  weekday: 'short',
  day: 'numeric',
  month: 'short',
})

function isActive(item) {
  if (item.external) return false
  return route.path === item.to
}
</script>
