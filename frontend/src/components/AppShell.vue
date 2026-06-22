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
import { computed, ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { call } from '@/api'
import { useToast } from '@/utils/toast'
import { useConfirm } from '@/utils/confirm'
import LavConfirm from '@/components/LavConfirm.vue'
import LavThemeToggle from '@/components/LavThemeToggle.vue'

const route = useRoute()
const router = useRouter()
const { toasts, dismiss, show: showToast } = useToast()
const { confirm } = useConfirm()
const q = ref('')
const isAdmin = ref(false)

onMounted(async () => {
  try {
    isAdmin.value = !!(await call('lavanya_service.api.ui_settings.can_manage_lavanya_settings'))
  } catch { isAdmin.value = false }
})

function goSearch() {
  const term = q.value.trim()
  router.push({ path: '/tickets', query: term ? { search: term } : {} })
}

// Keyboard shortcuts are handled centrally in App.vue (g+h, g+t, g+n, g+r, g+s, ?, Esc).
// AppShell does not register its own document-level keydown listener.

const ALL_NAV_ITEMS = [
  { label: 'Today\'s Work', mobileLabel: 'Work', icon: 'dashboard', to: '/', subtitle: 'Critical, important, and normal follow-ups' },
  { label: 'Tickets', mobileLabel: 'Tickets', icon: 'confirmation_number', to: '/tickets', subtitle: 'Search, filters, and ticket detail drawer' },
  { label: 'Reports', mobileLabel: 'Reports', icon: 'assessment', to: '/reports', subtitle: 'Manager reports and safety previews' },
  { label: 'Field Mode', mobileLabel: 'Field', icon: 'phone_iphone', to: '/field', subtitle: 'Counter-friendly phone lookup and quick work', adminOnly: true },
  { label: 'WhatsApp Drafts', mobileLabel: 'Drafts', icon: 'chat', to: '/whatsapp', subtitle: 'Read-only inbox and draft outbound queue (no live send)' },
  { label: 'Customer 360', mobileLabel: 'Customer', icon: 'person_search', to: '/customer-360', subtitle: 'Customer profile, products, tickets, and CRM context' },
  { label: 'New Ticket', mobileLabel: 'New', icon: 'add_box', to: '/new-ticket', subtitle: 'Register a customer complaint' },
  { label: 'Settings', mobileLabel: 'Settings', icon: 'settings', to: '/settings', subtitle: 'Theme, safety locks, and feature flags', adminOnly: true },
]

const navItems = computed(() => ALL_NAV_ITEMS.filter((i) => !i.adminOnly || isAdmin.value))

const mobileNavItems = computed(() => navItems.value.filter((i) => ['/', '/new-ticket', '/customer-360', '/whatsapp', '/tickets'].includes(i.to)))

async function confirmLogout() {
  const ok = await confirm('Are you sure you want to log out?', 'Logout')
  if (ok) {
    window.location.href = '/api/method/logout'
  }
}

const activeItem = computed(() => navItems.value.find((i) => isActive(i)))

const headerTitle = computed(() => activeItem.value?.label || 'Service Console')

const headerSubtitle = computed(
  () => activeItem.value?.subtitle || 'Lavanya service follow-up command system'
)

const today = new Date().toLocaleDateString(undefined, {
  weekday: 'short',
  day: 'numeric',
  month: 'short',
})

function isActive(item) {
  if (item.external) return false
  // Root is exact-only; everything else also matches its nested detail routes
  // (e.g. "/tickets" stays highlighted on "/tickets/0846").
  if (item.to === '/') return route.path === '/'
  return route.path === item.to || route.path.startsWith(item.to + '/')
}
</script>
