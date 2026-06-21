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
        <div class="w-10 h-10 rounded-lg bg-primary text-on-primary flex items-center justify-center shrink-0" aria-hidden="true">
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
                 border-l-4 border-transparent text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface focus-visible:ring-2 focus-visible:ring-primary"
          :class="isActive(item) ? '!border-primary bg-surface-container-low !text-primary font-bold shadow-sm' : ''"
          :title="item.label"
        >
          <span class="material-symbols-outlined" :class="isActive(item) ? 'fill' : ''">{{ item.icon }}</span>
          <span class="truncate">{{ item.label }}</span>
        </component>
      </nav>

      <div class="px-2 mt-2">
        <button
          @click="confirmLogout"
          class="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface"
          aria-label="Logout"
        >
          <span class="material-symbols-outlined" aria-hidden="true">logout</span>
          <span class="font-label-md text-body-md">Logout</span>
        </button>
      </div>
    </aside>

    <!-- Main -->
    <main class="lav-main">
      <header class="lav-header">
        <div class="min-w-0">
          <h2 class="font-headline-md text-headline-md font-bold text-primary truncate">{{ headerTitle }}</h2>
          <p class="hidden sm:block font-label-md text-label-md text-on-surface-variant truncate">{{ headerSubtitle }}</p>
        </div>
        <div class="flex items-center gap-3">
          <form
            role="search"
            class="hidden sm:flex items-center gap-2 h-9 px-3 rounded-lg border border-outline-variant bg-surface-container-lowest focus-within:border-primary transition-colors"
            style="min-width: 240px"
            @submit.prevent="goSearch"
          >
            <span class="material-symbols-outlined text-on-surface-variant" style="font-size: 18px">search</span>
            <input
              v-model="q"
              type="search"
              placeholder="Search tickets…"
              class="flex-1 min-w-0 bg-transparent border-none outline-none font-body-md text-on-surface"
              aria-label="Search tickets"
            />
          </form>
          <LavThemeToggle />
          <div class="hidden sm:flex items-center gap-2 rounded-full bg-surface-container-low border border-outline-variant pl-2 pr-3 h-9 text-on-surface-variant">
            <span class="material-symbols-outlined" aria-hidden="true">person</span>
            <span class="font-label-md text-label-md">Staff</span>
          </div>
        </div>
      </header>

      <div class="flex-1 px-container-padding py-gutter w-full max-w-max-content-width mx-auto">
        <slot />
      </div>

      <!-- Mobile bottom nav -->
      <!-- Toast container -->
      <div class="fixed top-4 right-4 z-[60] flex flex-col gap-2 pointer-events-none">
        <div
          v-for="t in toasts"
          :key="t.id"
          class="pointer-events-auto px-4 py-3 rounded-lg shadow-lg text-body-md font-body-md text-on-primary max-w-sm animate-in slide-in-from-right-2 fade-in duration-200"
          :class="t.kind === 'error' ? 'bg-error' : 'bg-primary'"
          @click="dismiss(t.id)"
          role="alert"
        >
          {{ t.message }}
        </div>
      </div>

      <LavConfirm />

      <nav class="lav-mobile-nav" aria-label="Mobile navigation">
        <router-link
          v-for="item in mobileNavItems"
          :key="'m-' + item.label"
          :to="item.to"
          class="flex flex-col items-center gap-0.5 px-2 py-1 text-on-surface-variant rounded-lg min-w-[56px]"
          :class="isActive(item) ? '!text-primary bg-surface-container-low font-bold' : ''"
          :aria-label="item.label"
        >
          <span class="material-symbols-outlined" :class="isActive(item) ? 'fill' : ''" aria-hidden="true">{{ item.icon }}</span>
          <span class="font-label-md text-label-md">{{ item.mobileLabel || item.label }}</span>
        </router-link>
      </nav>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '@/utils/toast'
import { useConfirm } from '@/utils/confirm'
import LavConfirm from '@/components/LavConfirm.vue'
import LavThemeToggle from '@/components/LavThemeToggle.vue'

const route = useRoute()
const router = useRouter()
const { toasts, dismiss, show: showToast } = useToast()
const { confirm } = useConfirm()
const q = ref('')

function goSearch() {
  const term = q.value.trim()
  router.push({ path: '/tickets', query: term ? { search: term } : {} })
}

// Keyboard shortcuts are handled centrally in App.vue (g+h, g+t, g+n, g+r, g+s, ?, Esc).
// AppShell does not register its own document-level keydown listener.

const navItems = [
  { label: 'Today\'s Work', mobileLabel: 'Work', icon: 'dashboard', to: '/', subtitle: 'Critical, important, and normal follow-ups' },
  { label: 'Tickets', mobileLabel: 'Tickets', icon: 'confirmation_number', to: '/tickets', subtitle: 'Search, filters, and ticket detail drawer' },
  { label: 'Reports', mobileLabel: 'Reports', icon: 'assessment', to: '/reports', subtitle: 'Manager reports and safety previews' },
  { label: 'Field Mode', mobileLabel: 'Field', icon: 'phone_iphone', to: '/field', subtitle: 'Counter-friendly phone lookup and quick work' },
  { label: 'New Ticket', mobileLabel: 'New', icon: 'add_box', to: '/new-ticket', subtitle: 'Register a customer complaint' },
  { label: 'Settings', mobileLabel: 'Settings', icon: 'settings', to: '/settings', subtitle: 'Theme, safety locks, and feature flags' },
]

const mobileNavItems = computed(() => navItems.filter((i) => ['/', '/tickets', '/field', '/settings'].includes(i.to)))

async function confirmLogout() {
  const ok = await confirm('Are you sure you want to log out?', 'Logout')
  if (ok) {
    window.location.href = '/api/method/logout'
  }
}

const headerTitle = computed(() => {
  const active = navItems.find((i) => !i.external && i.to === route.path)
  return active ? active.label : 'Service Console'
})

const headerSubtitle = computed(() => {
  const active = navItems.find((i) => !i.external && i.to === route.path)
  return active?.subtitle || 'Lavanya service follow-up command system'
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
