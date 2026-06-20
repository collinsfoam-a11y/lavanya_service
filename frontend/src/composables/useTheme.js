/**
 * Reactive theme composable.
 *
 * Provides a Vue-friendly wrapper around the theme engine so components can
 * read and switch the active theme reactively.
 */

import { ref, computed, onMounted } from 'vue'
import {
  initTheme,
  applyTheme,
  saveTheme,
  readSavedTheme,
  resolveTheme,
  getAllThemeMeta,
  DEFAULT_THEME,
} from '@/utils/theme-engine.js'

const activeTheme = ref(DEFAULT_THEME)
const isReady = ref(false)

export function useTheme() {
  onMounted(() => {
    if (!isReady.value) {
      activeTheme.value = initTheme()
      isReady.value = true
    }
  })

  const setTheme = (name) => {
    const resolved = applyTheme(name)
    saveTheme(resolved)
    activeTheme.value = resolved
    return resolved
  }

  const resetTheme = () => setTheme(DEFAULT_THEME)

  const themeMeta = computed(() =>
    getAllThemeMeta().map((t) => ({
      ...t,
      active: t.name === activeTheme.value,
    })),
  )

  const compact = computed(() => activeTheme.value === 'compact-counter')
  const highContrast = computed(() => activeTheme.value === 'high-contrast')
  const largeText = computed(() => {
    // Large text can be a separate toggle or combined with high-contrast later.
    return false
  })

  return {
    theme: activeTheme,
    isReady,
    setTheme,
    resetTheme,
    themes: themeMeta,
    compact,
    highContrast,
    largeText,
    refresh: () => {
      activeTheme.value = readSavedTheme()
      applyTheme(activeTheme.value)
    },
  }
}

export { DEFAULT_THEME, resolveTheme, getAllThemeMeta }
