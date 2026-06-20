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
                 border-l-4 border-transparent text-on-surface-variant hover:bg-surface-container-low hover:text-on-surface"
          :class="isActive(item) ? '!border-primary bg-surface-container-low !text-primary font-bold' : ''"
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
        <h2 class="font-headline-md text-headline-md font-bold text-primary md:hidden">Lavanya</h2>
        <div class="hidden md:block font-body-md text-on-surface-variant">{{ headerTitle }}</div>
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
          <div class="w-9 h-9 rounded-full bg-primary-container text-on-primary flex items-center justify-center shrink-0" aria-hidden="true">
            <span class="material-symbols-outlined" aria-hidden="true">person</span>
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
          v-for="item in navItems.filter((i) => !i.external)"
          :key="'m-' + item.label"
          :to="item.to"
          class="flex flex-col items-center gap-0.5 px-2 py-1 text-on-surface-variant"
          :class="isActive(item) ? '!text-primary' : ''"
          :aria-label="item.label"
        >
          <span class="material-symbols-outlined" :class="isActive(item) ? 'fill' : ''" aria-hidden="true">{{ item.icon }}</span>
          <span class="font-label-md text-label-md">{{ item.label }}</span>
        </router-link>
      </nav>
    </main>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from '@/utils/toast'
import { useConfirm } from '@/utils/confirm'
import LavConfirm from '@/components/LavConfirm.vue'
import LavThemeToggle from '@/components/LavThemeToggle.vue'

const route = useRoute()
const router = useRouter()
const { toasts, dismiss } = useToast()
const { confirm } = useConfirm()
const { show: showToast } = useToast()
const q = ref('')

let gPressed = false

function goSearch() {
  const term = q.value.trim()
  router.push({ path: '/tickets', query: term ? { search: term } : {} })
}

function onKeyDown(e) {
  if (e.key === 'g') {
    gPressed = true
    setTimeout(() => { gPressed = false }, 500)
    return
  }
  if (gPressed && e.key === 't') {
    gPressed = false
    e.preventDefault()
    router.push('/tickets')
    return
  }
  gPressed = false
  if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
    e.preventDefault()
    showToast('Shortcuts: g+t → Tickets, ? → this help')
  }
}

onMounted(() => document.addEventListener('keydown', onKeyDown))
onUnmounted(() => document.removeEventListener('keydown', onKeyDown))

const navItems = [
  { label: 'Today’s Work', icon: 'dashboard', to: '/' },
  { label: 'Tickets', icon: 'confirmation_number', to: '/tickets' },
  { label: 'Reports', icon: 'assessment', to: '/reports' },
  { label: 'New Ticket', icon: 'add_box', to: '/new-ticket' },
  { label: 'Settings', icon: 'settings', to: '/settings' },
]

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
