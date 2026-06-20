/**
 * Theme engine for Lavanya Service Console.
 *
 * Design goals:
 * - Single source of truth for all themes.
 * - Runtime theme switch via a `data-theme` attribute on <html>.
 * - CSS custom properties are consumed by Tailwind (tailwind.config.mjs) and
 *   by the semantic `lav-*` classes in index.css.
 * - Backward-compatible with the existing static exports in theme.js.
 */

export const THEME_STORAGE_KEY = 'lavanya-theme'

export const THEMES = {
  'lavanya-light': {
    label: 'Lavanya Light',
    description: 'Default clean light theme for service desks.',
    tokens: {
      background: '#f8f9ff',
      surface: '#ffffff',
      surfaceElevated: '#eef4ff',
      surfaceContainerLow: '#eef4ff',
      surfaceContainerHigh: '#dfe9fa',
      surfaceContainerHighest: '#d9e3f4',
      textPrimary: '#121c28',
      textSecondary: '#434655',
      textMuted: '#737686',
      border: '#c3c6d7',
      borderLight: 'rgba(195, 198, 215, 0.5)',
      primary: '#004ac6',
      primaryContainer: '#2563eb',
      onPrimary: '#ffffff',
      onPrimaryContainer: '#eeefff',
      secondary: '#712ae2',
      secondaryContainer: '#8a4cfc',
      onSecondary: '#ffffff',
      tertiary: '#943700',
      tertiaryContainer: '#bc4800',
      onTertiary: '#ffffff',
      success: '#1a7f37',
      successContainer: '#d1fae5',
      onSuccess: '#ffffff',
      warning: '#f59e0b',
      warningContainer: '#fff7ed',
      onWarning: '#78350f',
      danger: '#ba1a1a',
      dangerContainer: '#ffdad6',
      onDanger: '#ffffff',
      info: '#2563eb',
      infoContainer: '#dbeafe',
      onInfo: '#ffffff',
      muted: '#737686',
      chipDefault: '#eef4ff',
      chipDefaultText: '#434655',
      timelineCompleted: '#1a7f37',
      timelineCurrent: '#004ac6',
      timelineWaiting: '#f59e0b',
      timelineBlocked: '#ba1a1a',
      timelinePending: '#c3c6d7',
      qualityGood: '#1a7f37',
      qualityNeedsUpdate: '#f59e0b',
      qualityAtRisk: '#ea580c',
      qualityCritical: '#ba1a1a',
      bucketCritical: '#ba1a1a',
      bucketImportant: '#f59e0b',
      bucketNormal: '#004ac6',
    },
    spacing: {
      scale: 1,
      gutter: '16px',
      containerPadding: '24px',
      cardPadding: '16px',
      metricHeight: '128px',
    },
    typography: {
      scale: 1,
    },
  },
  'lavanya-dark': {
    label: 'Lavanya Dark',
    description: 'Dark theme for low-light environments.',
    tokens: {
      background: '#0f111a',
      surface: '#1a1c2e',
      surfaceElevated: '#232538',
      surfaceContainerLow: '#1e2033',
      surfaceContainerHigh: '#2a2d40',
      surfaceContainerHighest: '#32354a',
      textPrimary: '#e3e2e7',
      textSecondary: '#c3c6d7',
      textMuted: '#8f92a8',
      border: '#434655',
      borderLight: 'rgba(67, 70, 85, 0.5)',
      primary: '#8ab4f8',
      primaryContainer: '#004ac6',
      onPrimary: '#0f111a',
      onPrimaryContainer: '#e3e2e7',
      secondary: '#c7b0ff',
      secondaryContainer: '#712ae2',
      onSecondary: '#0f111a',
      tertiary: '#ffb59b',
      tertiaryContainer: '#943700',
      onTertiary: '#0f111a',
      success: '#7ddba8',
      successContainer: '#1a7f37',
      onSuccess: '#0f111a',
      warning: '#fcd34d',
      warningContainer: '#92400e',
      onWarning: '#0f111a',
      danger: '#ffb4ab',
      dangerContainer: '#ba1a1a',
      onDanger: '#0f111a',
      info: '#93c5fd',
      infoContainer: '#1e40af',
      onInfo: '#0f111a',
      muted: '#8f92a8',
      chipDefault: '#2a2d40',
      chipDefaultText: '#c3c6d7',
      timelineCompleted: '#7ddba8',
      timelineCurrent: '#8ab4f8',
      timelineWaiting: '#fcd34d',
      timelineBlocked: '#ffb4ab',
      timelinePending: '#434655',
      qualityGood: '#7ddba8',
      qualityNeedsUpdate: '#fcd34d',
      qualityAtRisk: '#fdba74',
      qualityCritical: '#ffb4ab',
      bucketCritical: '#ffb4ab',
      bucketImportant: '#fcd34d',
      bucketNormal: '#8ab4f8',
    },
    spacing: {
      scale: 1,
      gutter: '16px',
      containerPadding: '24px',
      cardPadding: '16px',
      metricHeight: '128px',
    },
    typography: {
      scale: 1,
    },
  },
  'lavanya-blue': {
    label: 'Lavanya Blue',
    description: 'Blue-tinted variant for brand consistency.',
    tokens: {
      background: '#f0f7ff',
      surface: '#ffffff',
      surfaceElevated: '#e6f1ff',
      surfaceContainerLow: '#e6f1ff',
      surfaceContainerHigh: '#d9e8ff',
      surfaceContainerHighest: '#cce0ff',
      textPrimary: '#0a1a2e',
      textSecondary: '#3d4e63',
      textMuted: '#6b7c91',
      border: '#b8d0f0',
      borderLight: 'rgba(184, 208, 240, 0.5)',
      primary: '#005ce6',
      primaryContainer: '#2563eb',
      onPrimary: '#ffffff',
      onPrimaryContainer: '#e6f1ff',
      secondary: '#3b82f6',
      secondaryContainer: '#60a5fa',
      onSecondary: '#ffffff',
      tertiary: '#0ea5e9',
      tertiaryContainer: '#38bdf8',
      onTertiary: '#ffffff',
      success: '#10b981',
      successContainer: '#d1fae5',
      onSuccess: '#ffffff',
      warning: '#f59e0b',
      warningContainer: '#fff7ed',
      onWarning: '#78350f',
      danger: '#ef4444',
      dangerContainer: '#fee2e2',
      onDanger: '#ffffff',
      info: '#2563eb',
      infoContainer: '#dbeafe',
      onInfo: '#ffffff',
      muted: '#6b7c91',
      chipDefault: '#e6f1ff',
      chipDefaultText: '#3d4e63',
      timelineCompleted: '#10b981',
      timelineCurrent: '#005ce6',
      timelineWaiting: '#f59e0b',
      timelineBlocked: '#ef4444',
      timelinePending: '#b8d0f0',
      qualityGood: '#10b981',
      qualityNeedsUpdate: '#f59e0b',
      qualityAtRisk: '#f97316',
      qualityCritical: '#ef4444',
      bucketCritical: '#ef4444',
      bucketImportant: '#f59e0b',
      bucketNormal: '#005ce6',
    },
    spacing: {
      scale: 1,
      gutter: '16px',
      containerPadding: '24px',
      cardPadding: '16px',
      metricHeight: '128px',
    },
    typography: {
      scale: 1,
    },
  },
  'lavanya-green': {
    label: 'Lavanya Green',
    description: 'Green-tinted variant for a calmer service desk feel.',
    tokens: {
      background: '#f0fdf4',
      surface: '#ffffff',
      surfaceElevated: '#ecfdf5',
      surfaceContainerLow: '#ecfdf5',
      surfaceContainerHigh: '#d1fae5',
      surfaceContainerHighest: '#bbf7d0',
      textPrimary: '#052e16',
      textSecondary: '#166534',
      textMuted: '#4b5563',
      border: '#86efac',
      borderLight: 'rgba(134, 239, 172, 0.5)',
      primary: '#15803d',
      primaryContainer: '#16a34a',
      onPrimary: '#ffffff',
      onPrimaryContainer: '#ecfdf5',
      secondary: '#059669',
      secondaryContainer: '#34d399',
      onSecondary: '#ffffff',
      tertiary: '#0d9488',
      tertiaryContainer: '#2dd4bf',
      onTertiary: '#ffffff',
      success: '#16a34a',
      successContainer: '#dcfce7',
      onSuccess: '#ffffff',
      warning: '#d97706',
      warningContainer: '#fef3c7',
      onWarning: '#78350f',
      danger: '#dc2626',
      dangerContainer: '#fee2e2',
      onDanger: '#ffffff',
      info: '#0891b2',
      infoContainer: '#cffafe',
      onInfo: '#ffffff',
      muted: '#4b5563',
      chipDefault: '#ecfdf5',
      chipDefaultText: '#166534',
      timelineCompleted: '#16a34a',
      timelineCurrent: '#15803d',
      timelineWaiting: '#d97706',
      timelineBlocked: '#dc2626',
      timelinePending: '#86efac',
      qualityGood: '#16a34a',
      qualityNeedsUpdate: '#d97706',
      qualityAtRisk: '#ea580c',
      qualityCritical: '#dc2626',
      bucketCritical: '#dc2626',
      bucketImportant: '#d97706',
      bucketNormal: '#15803d',
    },
    spacing: {
      scale: 1,
      gutter: '16px',
      containerPadding: '24px',
      cardPadding: '16px',
      metricHeight: '128px',
    },
    typography: {
      scale: 1,
    },
  },
  'high-contrast': {
    label: 'High Contrast',
    description: 'WCAG AAA-friendly high-contrast mode for accessibility.',
    tokens: {
      background: '#000000',
      surface: '#000000',
      surfaceElevated: '#111111',
      surfaceContainerLow: '#111111',
      surfaceContainerHigh: '#222222',
      surfaceContainerHighest: '#333333',
      textPrimary: '#ffffff',
      textSecondary: '#ffffff',
      textMuted: '#ffffff',
      border: '#ffffff',
      borderLight: '#ffffff',
      primary: '#ffff00',
      primaryContainer: '#000000',
      onPrimary: '#000000',
      onPrimaryContainer: '#ffff00',
      secondary: '#00ffff',
      secondaryContainer: '#000000',
      onSecondary: '#000000',
      tertiary: '#ff00ff',
      tertiaryContainer: '#000000',
      onTertiary: '#000000',
      success: '#00ff00',
      successContainer: '#000000',
      onSuccess: '#000000',
      warning: '#ffff00',
      warningContainer: '#000000',
      onWarning: '#000000',
      danger: '#ff0000',
      dangerContainer: '#000000',
      onDanger: '#ffffff',
      info: '#00ffff',
      infoContainer: '#000000',
      onInfo: '#000000',
      muted: '#ffffff',
      chipDefault: '#000000',
      chipDefaultText: '#ffffff',
      timelineCompleted: '#00ff00',
      timelineCurrent: '#ffff00',
      timelineWaiting: '#ff8800',
      timelineBlocked: '#ff0000',
      timelinePending: '#ffffff',
      qualityGood: '#00ff00',
      qualityNeedsUpdate: '#ff8800',
      qualityAtRisk: '#ff0000',
      qualityCritical: '#ff0000',
      bucketCritical: '#ff0000',
      bucketImportant: '#ff8800',
      bucketNormal: '#00ffff',
    },
    spacing: {
      scale: 1,
      gutter: '16px',
      containerPadding: '24px',
      cardPadding: '16px',
      metricHeight: '128px',
    },
    typography: {
      scale: 1.05,
    },
  },
  'compact-counter': {
    label: 'Compact Counter Mode',
    description: 'Tight spacing for showroom/service-counter screens.',
    tokens: {
      background: '#f8f9ff',
      surface: '#ffffff',
      surfaceElevated: '#eef4ff',
      surfaceContainerLow: '#eef4ff',
      surfaceContainerHigh: '#dfe9fa',
      surfaceContainerHighest: '#d9e3f4',
      textPrimary: '#121c28',
      textSecondary: '#434655',
      textMuted: '#737686',
      border: '#c3c6d7',
      borderLight: 'rgba(195, 198, 215, 0.5)',
      primary: '#004ac6',
      primaryContainer: '#2563eb',
      onPrimary: '#ffffff',
      onPrimaryContainer: '#eeefff',
      secondary: '#712ae2',
      secondaryContainer: '#8a4cfc',
      onSecondary: '#ffffff',
      tertiary: '#943700',
      tertiaryContainer: '#bc4800',
      onTertiary: '#ffffff',
      success: '#1a7f37',
      successContainer: '#d1fae5',
      onSuccess: '#ffffff',
      warning: '#f59e0b',
      warningContainer: '#fff7ed',
      onWarning: '#78350f',
      danger: '#ba1a1a',
      dangerContainer: '#ffdad6',
      onDanger: '#ffffff',
      info: '#2563eb',
      infoContainer: '#dbeafe',
      onInfo: '#ffffff',
      muted: '#737686',
      chipDefault: '#eef4ff',
      chipDefaultText: '#434655',
      timelineCompleted: '#1a7f37',
      timelineCurrent: '#004ac6',
      timelineWaiting: '#f59e0b',
      timelineBlocked: '#ba1a1a',
      timelinePending: '#c3c6d7',
      qualityGood: '#1a7f37',
      qualityNeedsUpdate: '#f59e0b',
      qualityAtRisk: '#ea580c',
      qualityCritical: '#ba1a1a',
      bucketCritical: '#ba1a1a',
      bucketImportant: '#f59e0b',
      bucketNormal: '#004ac6',
    },
    spacing: {
      scale: 0.75,
      gutter: '8px',
      containerPadding: '12px',
      cardPadding: '10px',
      metricHeight: '88px',
    },
    typography: {
      scale: 0.95,
    },
  },
}

export const DEFAULT_THEME = 'lavanya-light'

export function isValidTheme(name) {
  return Boolean(name && THEMES[name])
}

export function getThemeNames() {
  return Object.keys(THEMES)
}

export function getThemeMeta(name) {
  if (!isValidTheme(name)) return null
  const { label, description } = THEMES[name]
  return { name, label, description }
}

export function getAllThemeMeta() {
  return getThemeNames().map(getThemeMeta)
}

/**
 * Resolve a saved theme id to a valid theme name.
 */
export function resolveTheme(name) {
  return isValidTheme(name) ? name : DEFAULT_THEME
}

/**
 * Read the saved theme from localStorage.
 */
export function readSavedTheme() {
  try {
    return resolveTheme(localStorage.getItem(THEME_STORAGE_KEY))
  } catch {
    return DEFAULT_THEME
  }
}

/**
 * Persist theme choice to localStorage.
 */
export function saveTheme(name) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, resolveTheme(name))
  } catch {
    // storage may be unavailable (private mode)
  }
}

/**
 * Apply a theme to the document root by setting CSS custom properties and a
 * `data-theme` attribute. Safe to call repeatedly and from SSR-unaware code.
 */
export function applyTheme(name) {
  const themeName = resolveTheme(name)
  const theme = THEMES[themeName]
  if (typeof document === 'undefined') return themeName

  const root = document.documentElement
  root.setAttribute('data-theme', themeName)
  if (themeName === 'compact-counter') {
    root.setAttribute('data-compact', 'true')
  } else {
    root.removeAttribute('data-compact')
  }

  const { tokens, spacing, typography } = theme
  for (const [key, value] of Object.entries(tokens)) {
    root.style.setProperty(`--lav-${camelToKebab(key)}`, value)
  }

  root.style.setProperty('--lav-spacing-scale', String(spacing.scale))
  root.style.setProperty('--lav-gutter', spacing.gutter)
  root.style.setProperty('--lav-container-padding', spacing.containerPadding)
  root.style.setProperty('--lav-card-padding', spacing.cardPadding)
  root.style.setProperty('--lav-metric-height', spacing.metricHeight)
  root.style.setProperty('--lav-typography-scale', String(typography.scale))

  return themeName
}

function camelToKebab(str) {
  return str.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`)
}

/**
 * Initialise theme from localStorage or a supplied default.
 */
export function initTheme(fallback = DEFAULT_THEME) {
  return applyTheme(readSavedTheme() || fallback)
}
